"""
Panel docente y administración.

Todo aquí existe para una sola decisión: qué optativas abrir el próximo
periodo y con cuántos grupos. Dos niveles de acceso:

  docente  → lee (resumen, padrón, export)
  admin    → además cambia el estado del sistema (oferta, fecha límite)
"""
import csv
import io

from flask import Blueprint, Response, jsonify, request
from sqlalchemy import text

from ..models import Aplicacion, Oferta, db
from .auth import requiere_admin, requiere_docente

bp = Blueprint("docente", __name__)

# Cómo llegó el estudiante a su bloque, en lenguaje de coordinación.
# Son cuatro situaciones distintas y conviene no confundirlas: aceptar el
# diagnóstico y descartarlo dicen cosas muy diferentes sobre el instrumento.
METODO = """CASE
    WHEN r.sesion IS NULL                    THEN 'Elección directa'
    WHEN s.itinerario_elegido IS NULL        THEN 'Sin confirmar'
    WHEN s.itinerario_elegido = r.itinerario THEN 'Aceptó el diagnóstico'
    ELSE 'Eligió distinto'
END"""


def _app_id():
    pedido = request.args.get("aplicacion", type=int)
    if pedido:
        return pedido
    a = Aplicacion.query.filter_by(activa=True).order_by(Aplicacion.id.desc()).first()
    return a.id if a else None


# ───────────────────────────────────────────────── resumen (gráficas)
@bp.get("/resumen")
@requiere_docente
def resumen():
    """Los agregados que alimentan las gráficas, en una sola llamada."""
    aid = _app_id()
    q = lambda sql: db.session.execute(text(sql), {"a": aid}).mappings().all()

    avance = q("""
        SELECT nombre, fecha_limite, sesiones, completadas, en_progreso,
               expiradas, eleccion_directa, pct_completado
        FROM v_avance_aplicacion WHERE aplicacion = :a""")

    metodo = q("""
        SELECT CASE ba.origen
                 WHEN 'eleccion_directa'   THEN 'Elección directa'
                 WHEN 'acepto_diagnostico' THEN 'Aceptó el diagnóstico'
                 WHEN 'eligio_distinto'    THEN 'Eligió distinto'
                 ELSE 'Sin confirmar'
               END AS metodo,
               COUNT(*) AS alumnos
        FROM v_bloque_asignado ba
        WHERE ba.aplicacion = :a GROUP BY ba.origen""")

    aceptacion = q("""
        SELECT diagnosticados, aceptaron, cambiaron, sin_confirmar, pct_aceptacion
        FROM v_aceptacion_diagnostico WHERE aplicacion = :a""")

    cambios = q("""
        SELECT recomendado, elegido, alumnos
        FROM v_cambios_de_bloque WHERE aplicacion = :a LIMIT 12""")

    bloques = q("""
        SELECT id, nombre, frase, alumnos, eligieron_directo, por_cuestionario,
               aceptaron_diagnostico, eligieron_distinto, sin_confirmar
        FROM v_demanda_bloque WHERE aplicacion = :a ORDER BY alumnos DESC""")

    optativas = q("""
        SELECT clave, nombre, academia, alumnos, bloques_que_la_piden,
               se_abre, cupo, grupos_necesarios
        FROM v_demanda_optativa WHERE aplicacion = :a
        ORDER BY alumnos DESC, nombre""")

    academias = q("""
        SELECT ac.nombre AS academia, SUM(d.alumnos) AS alumnos
        FROM v_demanda_optativa d
        JOIN academia ac ON ac.clave = d.academia
        WHERE d.aplicacion = :a GROUP BY ac.nombre ORDER BY alumnos DESC""")

    secciones = q("""
        SELECT seccion, alumnos, terminaron, a_medias, eleccion_directa, pct
        FROM v_avance_seccion WHERE aplicacion = :a ORDER BY seccion""")

    vacios = q("""
        SELECT i.id, i.nombre FROM itinerario i
        WHERE i.id NOT IN (SELECT itinerario FROM v_bloque_asignado WHERE aplicacion = :a)
        ORDER BY i.id""")

    return jsonify(aplicacion=aid,
                   avance=dict(avance[0]) if avance else None,
                   metodo=[dict(f) for f in metodo],
                   bloques=[dict(f) for f in bloques],
                   optativas=[dict(f) for f in optativas],
                   academias=[dict(f) for f in academias],
                   secciones=[dict(f) for f in secciones],
                   aceptacion=dict(aceptacion[0]) if aceptacion else None,
                   cambios=[dict(f) for f in cambios],
                   bloques_vacios=[dict(f) for f in vacios])


# ───────────────────────────────────────────────── padrón
@bp.get("/padron")
@requiere_docente
def padron():
    """Quién obtuvo qué bloque y por qué vía.

    La matrícula va primero y es la llave: así funciona todo en la UV, y es lo
    que le permite a Escolar cruzar esta tabla con sus propios listados sin
    pelearse con nombres escritos de tres formas distintas."""
    aid = _app_id()
    filas = db.session.execute(text(f"""
        SELECT
          u.matricula,
          u.nombre,
          COALESCE(u.seccion, '') AS seccion,
          u.correo,
          s.estado,
          {METODO}                       AS metodo,
          i.id                           AS bloque_id,
          i.nombre                       AS bloque,
          i.frase,
          rec.nombre                     AS recomendado,
          s.veces_cambiada,
          r.perfil_plano,
          r.empate_tecnico,
          s.completada_en,
          s.actualizada_en,
          GROUP_CONCAT(o.nombre ORDER BY io.orden SEPARATOR ' | ') AS optativas
        FROM sesion s
        JOIN usuario u ON u.id = s.usuario
        LEFT JOIN resultado r  ON r.sesion = s.id
        LEFT JOIN itinerario i   ON i.id = COALESCE(s.itinerario_elegido, r.itinerario)
        LEFT JOIN itinerario rec ON rec.id = r.itinerario
        LEFT JOIN itinerario_optativa io ON io.itinerario = i.id
        LEFT JOIN optativa o ON o.clave = io.optativa
        WHERE s.aplicacion = :a
        GROUP BY u.matricula, u.nombre, u.seccion, u.correo, s.estado, s.modo,
                 s.itinerario_elegido, r.sesion, r.itinerario,
                 i.id, i.nombre, i.frase, rec.nombre, s.veces_cambiada,
                 r.perfil_plano, r.empate_tecnico, s.completada_en, s.actualizada_en
        ORDER BY u.seccion, u.matricula
    """), {"a": aid}).mappings().all()
    return jsonify(aplicacion=aid, alumnos=[dict(f) for f in filas])


@bp.get("/padron.csv")
@requiere_docente
def padron_csv():
    """Mismo padrón en CSV, para que Escolar lo abra en Excel."""
    datos = padron().get_json()["alumnos"]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Matricula", "Seccion", "Nombre", "Correo", "Estado", "Metodo",
                "Bloque elegido", "Bloque recomendado", "Veces que lo cambio",
                "Optativas", "Sin definir", "Fecha"])
    for a in datos:
        w.writerow([a["matricula"], a["seccion"], a["nombre"], a["correo"], a["estado"],
                    a["metodo"], a["bloque"] or "", a["recomendado"] or "",
                    a["veces_cambiada"] or 0, a["optativas"] or "",
                    "Sí" if a["perfil_plano"] else "", a["completada_en"] or ""])
    # BOM para que Excel en Windows no rompa los acentos
    salida = "\ufeff" + buf.getvalue()
    return Response(salida, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="padron_sioat.csv"'})


@bp.get("/sin_definir")
@requiere_docente
def sin_definir():
    """Alumnos cuyo perfil salió plano: terminaron pero el sistema no les
    asignó bloque. Necesitan tutoría, no un correo automático."""
    aid = _app_id()
    filas = db.session.execute(text("""
        SELECT u.matricula, COALESCE(u.seccion,'') AS seccion,
               u.nombre, u.correo, s.completada_en
        FROM resultado r
        JOIN sesion s  ON s.id = r.sesion
        JOIN usuario u ON u.id = s.usuario
        WHERE s.aplicacion = :a AND r.perfil_plano = 1
        ORDER BY u.seccion, u.matricula
    """), {"a": aid}).mappings().all()
    return jsonify(alumnos=[dict(f) for f in filas])


@bp.get("/concordancia")
@requiere_docente
def concordancia():
    """De los que dijeron «ya sé cuál quiero», ¿el cuestionario coincidió?
    Es la métrica que dice si la fase 0 sirve de algo."""
    filas = db.session.execute(text(
        "SELECT * FROM v_concordancia_decision_previa")).mappings().all()
    return jsonify(filas=[dict(f) for f in filas])


# ───────────────────────────────────────────────── administración
@bp.get("/oferta")
@requiere_docente
def ver_oferta():
    aid = _app_id()
    filas = db.session.execute(text("""
        SELECT o.clave, o.nombre, o.academia,
               COALESCE(of2.se_abre, 1) AS se_abre, of2.cupo
        FROM optativa o
        LEFT JOIN oferta of2 ON of2.optativa = o.clave AND of2.aplicacion = :a
        ORDER BY o.nombre
    """), {"a": aid}).mappings().all()
    return jsonify(aplicacion=aid, optativas=[dict(f) for f in filas])


@bp.put("/oferta")
@requiere_admin
def actualizar_oferta():
    """Qué se abre y con qué cupo. El resultado del estudiante se filtra contra
    esto, así que cambiarlo a media aplicación altera lo que todos ven: por eso
    es exclusivo de administrador."""
    d = request.get_json(silent=True) or {}
    aid = d.get("aplicacion") or _app_id()
    for item in d.get("optativas", []):
        o = db.session.get(Oferta, (aid, item["clave"]))
        if not o:
            o = Oferta(aplicacion=aid, optativa=item["clave"])
            db.session.add(o)
        o.se_abre = bool(item.get("se_abre", True))
        o.cupo = item.get("cupo") or None
    db.session.commit()
    return jsonify(ok=True)


@bp.get("/usuarios")
@requiere_admin
def usuarios():
    """Cuentas de docente y administrador. Los estudiantes no salen aquí:
    para eso está el padrón."""
    filas = db.session.execute(text("""
        SELECT id, nombre, correo, rol, activo, ultimo_acceso
        FROM usuario WHERE rol IN ('docente','admin') ORDER BY rol, nombre
    """)).mappings().all()
    return jsonify(usuarios=[dict(f) for f in filas])


@bp.post("/usuarios")
@requiere_admin
def crear_usuario():
    """Alta de una cuenta de docente o administrador.

    La contraseña inicial la escribe el administrador y se entrega en persona.
    No se manda por correo: el sistema no tiene servidor de correo configurado
    y una contraseña en un correo institucional compartido no es una
    contraseña."""
    from argon2 import PasswordHasher
    from ..models import Usuario

    d = request.get_json(silent=True) or {}
    nombre = (d.get("nombre") or "").strip()
    correo = (d.get("correo") or "").strip().lower()
    rol = d.get("rol") if d.get("rol") in ("docente", "admin") else "docente"
    passwd = d.get("password") or ""

    if len(nombre) < 3:
        return jsonify(error="Escribe el nombre completo."), 400
    if "@" not in correo:
        return jsonify(error="Ese correo no parece válido."), 400
    if len(passwd) < 8:
        return jsonify(error="La contraseña necesita al menos 8 caracteres."), 400
    if Usuario.query.filter_by(correo=correo).first():
        return jsonify(error="Ese correo ya está registrado."), 409

    u = Usuario(nombre=nombre, correo=correo, rol=rol,
                password_hash=PasswordHasher().hash(passwd))
    db.session.add(u)
    db.session.commit()
    return jsonify(ok=True, usuario=u.publico()), 201


@bp.put("/usuarios/<int:uid>")
@requiere_admin
def actualizar_usuario(uid):
    """Activar, desactivar, cambiar rol o restablecer contraseña de otra cuenta.

    Se desactiva en lugar de borrar: un docente eliminado dejaría huérfanas las
    aplicaciones que creó."""
    from argon2 import PasswordHasher
    from ..models import Usuario
    from .auth import usuario_actual

    u = db.session.get(Usuario, uid)
    if not u or u.rol == "estudiante":
        return jsonify(error="Esa cuenta no existe."), 404

    yo = usuario_actual()
    d = request.get_json(silent=True) or {}

    if "activo" in d:
        if u.id == yo.id and not d["activo"]:
            return jsonify(error="No puedes desactivar tu propia cuenta."), 400
        u.activo = bool(d["activo"])
    if d.get("rol") in ("docente", "admin"):
        if u.id == yo.id and d["rol"] != "admin":
            return jsonify(error="No puedes quitarte a ti mismo el rol de administrador."), 400
        u.rol = d["rol"]
    if d.get("password"):
        if len(d["password"]) < 8:
            return jsonify(error="La contraseña necesita al menos 8 caracteres."), 400
        u.password_hash = PasswordHasher().hash(d["password"])

    db.session.commit()
    return jsonify(ok=True, usuario=u.publico())


@bp.put("/aplicacion")
@requiere_admin
def actualizar_aplicacion():
    """Mover la fecha límite sin un deploy."""
    d = request.get_json(silent=True) or {}
    a = db.session.get(Aplicacion, d.get("id") or _app_id())
    if not a:
        return jsonify(error="Esa aplicación no existe."), 404
    if d.get("fecha_limite"):
        from datetime import datetime
        try:
            a.fecha_limite = datetime.fromisoformat(d["fecha_limite"])
        except ValueError:
            return jsonify(error="Fecha con formato inválido."), 400
    if "activa" in d:
        a.activa = bool(d["activa"])
    db.session.commit()
    return jsonify(ok=True, aplicacion=a.publico())