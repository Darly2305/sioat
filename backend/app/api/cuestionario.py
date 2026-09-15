"""
API del cuestionario.

Regla de oro del autoguardado: cada respuesta se escribe en su propia fila en
el momento en que el estudiante la elige. No hay "guardar" ni borrador en
memoria. Cerrar la pestaña a media pregunta no pierde nada.
"""
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import text

from ..models import (Aplicacion, EECurricular, Itinerario, ItinerarioOptativa,
                      OpcionContexto, OpcionReactivo, Optativa, PesoAcademiaOptativa,
                      PreguntaContexto, Reactivo, Resultado, ResultadoItinerario,
                      ResultadoOptativa, RespuestaFase1, RespuestaFase2,
                      RespuestaFase3, Sesion, db)
from ..motor import datos as D
from ..motor.puntuacion import Respuestas, calcular, explicar
from .auth import usuario_actual

bp = Blueprint("cuestionario", __name__)


def cargar_pesos_desde_db():
    """Sobrescribe la matriz del motor con la que está en la base. Las
    coordinaciones de academia la ajustan ahí; el código no se toca."""
    filas = PesoAcademiaOptativa.query.all()
    if not filas:
        raise RuntimeError("tabla peso_academia_optativa vacía")
    for f in filas:
        if f.optativa in D.PESOS and f.academia in D.PESOS[f.optativa]:
            D.PESOS[f.optativa][f.academia] = float(f.peso)
    return len(filas)


def _aplicacion_activa():
    return Aplicacion.query.filter_by(activa=True).order_by(Aplicacion.id.desc()).first()


def _sesion_de(usuario, app_):
    """Obtiene la sesión del estudiante o la crea. Una sola por aplicación:
    el UNIQUE (usuario, aplicacion) del esquema lo garantiza."""
    s = Sesion.query.filter_by(usuario=usuario.id, aplicacion=app_.id).first()
    if not s:
        s = Sesion(usuario=usuario.id, aplicacion=app_.id)
        db.session.add(s)
        db.session.commit()
    if app_.vencida and s.estado == "en_progreso":
        s.estado = "expirada"
        db.session.commit()
    return s


# ───────────────────────────────────────────────────────── catálogo
@bp.get("/catalogo")
@jwt_required()
def catalogo():
    """Todo lo que la interfaz necesita para pintar el cuestionario.
    Nota: NO se envían los pesos de la matriz. Si el estudiante los pudiera
    leer desde el bundle, podría contestar para caer donde quisiera."""
    periodos = {}
    for ee in EECurricular.query.order_by(EECurricular.periodo, EECurricular.clave):
        periodos.setdefault(ee.periodo, []).append(
            {"clave": ee.clave, "nombre": ee.nombre})

    reactivos = []
    for r in Reactivo.query.order_by(Reactivo.numero):
        ops = OpcionReactivo.query.filter_by(reactivo=r.numero).order_by(OpcionReactivo.letra)
        reactivos.append({"numero": r.numero, "enunciado": r.enunciado,
                          "en_breve": r.en_breve,
                          "opciones": [{"id": o.id, "letra": o.letra, "texto": o.texto} for o in ops]})

    contexto = []
    for q in PreguntaContexto.query.order_by(PreguntaContexto.numero):
        ops = OpcionContexto.query.filter_by(pregunta=q.numero).order_by(OpcionContexto.letra)
        contexto.append({"numero": q.numero, "enunciado": q.enunciado,
                         "opciones": [{"id": o.id, "letra": o.letra, "texto": o.texto} for o in ops]})

    its = []
    for i in Itinerario.query.order_by(Itinerario.id):
        opts = (db.session.query(Optativa)
                .join(ItinerarioOptativa, ItinerarioOptativa.optativa == Optativa.clave)
                .filter(ItinerarioOptativa.itinerario == i.id)
                .order_by(ItinerarioOptativa.orden).all())
        its.append({**i.publico(),
                    "optativas": [{"clave": o.clave, "nombre": o.nombre} for o in opts]})

    app_ = _aplicacion_activa()
    return jsonify(periodos=periodos, reactivos=reactivos, contexto=contexto,
                   itinerarios=its, aplicacion=app_.publico() if app_ else None,
                   puntos=D.PUNTOS, periodos_sin_fav3=list(D.PERIODOS_SIN_FAV3))


# ───────────────────────────────────────────────────────── sesión
@bp.get("/sesion")
@jwt_required()
def obtener_sesion():
    """Devuelve el progreso guardado. Es lo que permite regresar donde te
    quedaste sin que el estudiante haga nada."""
    u = usuario_actual()
    app_ = _aplicacion_activa()
    if not app_:
        return jsonify(error="No hay un periodo de aplicación abierto."), 404
    s = _sesion_de(u, app_)

    f1 = {}
    for r in RespuestaFase1.query.filter_by(sesion=s.id):
        f1.setdefault(r.periodo, {})[r.posicion] = r.ee
    f2 = {r.reactivo: r.opcion for r in RespuestaFase2.query.filter_by(sesion=s.id)}
    f3 = {r.pregunta: r.opcion for r in RespuestaFase3.query.filter_by(sesion=s.id)}

    return jsonify(
        sesion={"id": s.id, "estado": s.estado, "modo": s.modo,
                "paso_actual": s.paso_actual, "ya_decidio": s.ya_decidio,
                "itinerario_previo": s.itinerario_previo,
                "itinerario_elegido": s.itinerario_elegido},
        aplicacion=app_.publico(),
        respuestas={"fase1": f1, "fase2": f2, "fase3": f3},
    )


@bp.put("/sesion/respuesta")
@jwt_required()
def guardar_respuesta():
    """Guarda UNA respuesta. La llama la interfaz cada vez que se toca una
    opción; por eso responde poco y rápido."""
    u = usuario_actual()
    app_ = _aplicacion_activa()
    if not app_:
        return jsonify(error="No hay un periodo de aplicación abierto."), 404
    s = _sesion_de(u, app_)

    if s.estado == "expirada":
        return jsonify(error="La fecha límite ya pasó. Habla con tu tutor."), 403
    if s.estado == "completada":
        return jsonify(error="Ya entregaste este cuestionario."), 409

    d = request.get_json(silent=True) or {}
    fase = d.get("fase")

    try:
        if fase == "fase1":
            periodo, posicion, ee = int(d["periodo"]), d["posicion"], d["ee"]
            if posicion not in ("fav1", "fav2", "fav3", "rechazada"):
                return jsonify(error="Posición no válida."), 400
            if periodo in D.PERIODOS_SIN_FAV3 and posicion == "fav3":
                return jsonify(error="Ese periodo sólo pide dos favoritas."), 400
            if not db.session.get(EECurricular, ee):
                return jsonify(error="Esa materia no existe."), 400
            # una EE no puede ser favorita y rechazada a la vez
            RespuestaFase1.query.filter_by(sesion=s.id, periodo=periodo, ee=ee).delete()
            RespuestaFase1.query.filter_by(sesion=s.id, periodo=periodo, posicion=posicion).delete()
            db.session.add(RespuestaFase1(sesion=s.id, periodo=periodo, posicion=posicion, ee=ee))

        elif fase == "fase2":
            num, opcion = int(d["reactivo"]), int(d["opcion"])
            op = db.session.get(OpcionReactivo, opcion)
            if not op or op.reactivo != num:
                return jsonify(error="Esa opción no corresponde a la pregunta."), 400
            RespuestaFase2.query.filter_by(sesion=s.id, reactivo=num).delete()
            db.session.add(RespuestaFase2(sesion=s.id, reactivo=num, opcion=opcion))

        elif fase == "fase3":
            num, opcion = int(d["pregunta"]), int(d["opcion"])
            op = db.session.get(OpcionContexto, opcion)
            if not op or op.pregunta != num:
                return jsonify(error="Esa opción no corresponde a la pregunta."), 400
            RespuestaFase3.query.filter_by(sesion=s.id, pregunta=num).delete()
            db.session.add(RespuestaFase3(sesion=s.id, pregunta=num, opcion=opcion))

        elif fase == "fase0":
            s.ya_decidio = bool(d.get("ya_decidio"))
            s.itinerario_previo = d.get("itinerario_previo")
            s.modo = "breve" if s.ya_decidio else "completo"

        else:
            return jsonify(error="Fase no reconocida."), 400

    except (KeyError, ValueError, TypeError):
        return jsonify(error="Faltan datos en la respuesta."), 400

    if d.get("paso_actual"):
        s.paso_actual = str(d["paso_actual"])[:20]
    s.actualizada_en = datetime.utcnow()
    db.session.commit()
    return jsonify(ok=True, guardado_en=s.actualizada_en.isoformat())


# ───────────────────────────────────────────────────────── elección directa
@bp.post("/sesion/elegir-bloque")
@jwt_required()
def elegir_bloque():
    """El estudiante que ya sabe cuál quiere lo registra y termina aquí mismo.
    No se le aplica el cuestionario: el plan de estudios le permite elegir, y
    obligarlo a contestar quince reactivos para confirmar lo que ya decidió
    sólo lograría que abandone."""
    u = usuario_actual()
    app_ = _aplicacion_activa()
    if not app_:
        return jsonify(error="No hay un periodo de aplicación abierto."), 404
    s = _sesion_de(u, app_)

    if s.estado == "expirada":
        return jsonify(error="La fecha límite ya pasó. Habla con tu tutor."), 403

    d = request.get_json(silent=True) or {}
    it = db.session.get(Itinerario, d.get("itinerario"))
    if not it:
        return jsonify(error="Ese bloque no existe."), 400

    # Si ya había contestado el cuestionario, su resultado se descarta: la
    # decisión del estudiante manda sobre la recomendación del sistema.
    Resultado.query.filter_by(sesion=s.id).delete()

    s.itinerario_elegido = it.id
    s.modo = "eleccion_directa"
    s.ya_decidio = True
    s.estado = "completada"
    s.completada_en = datetime.utcnow()
    s.paso_actual = "resultado"
    db.session.commit()

    opts = (db.session.query(Optativa)
            .join(ItinerarioOptativa, ItinerarioOptativa.optativa == Optativa.clave)
            .filter(ItinerarioOptativa.itinerario == it.id)
            .order_by(ItinerarioOptativa.orden).all())
    return jsonify(ok=True, itinerario={**it.publico(),
                   "optativas": [{"clave": o.clave, "nombre": o.nombre} for o in opts]})


# ───────────────────────────────────────────────────────── entrega
@bp.post("/sesion/completar")
@jwt_required()
def completar():
    u = usuario_actual()
    app_ = _aplicacion_activa()
    s = _sesion_de(u, app_)

    if s.estado == "expirada":
        return jsonify(error="La fecha límite ya pasó."), 403
    if s.estado == "completada":
        return jsonify(ok=True, ya_estaba=True)

    f1 = {}
    for r in RespuestaFase1.query.filter_by(sesion=s.id):
        f1.setdefault(r.periodo, {})[r.posicion] = r.ee
    mapa2 = {o.id: (o.reactivo, o.letra) for o in OpcionReactivo.query.all()}
    mapa3 = {o.id: (o.pregunta, o.letra) for o in OpcionContexto.query.all()}
    f2 = {mapa2[r.opcion][0]: mapa2[r.opcion][1]
          for r in RespuestaFase2.query.filter_by(sesion=s.id) if r.opcion in mapa2}
    f3 = {mapa3[r.opcion][0]: mapa3[r.opcion][1]
          for r in RespuestaFase3.query.filter_by(sesion=s.id) if r.opcion in mapa3}

    minimo = len(D.REACTIVOS_VERSION_BREVE) if s.modo == "breve" else len(D.REACTIVOS)
    if len(f2) < minimo:
        return jsonify(error=f"Todavía te faltan {minimo - len(f2)} preguntas."), 400

    resp = Respuestas(fase1=f1, fase2=f2, fase3=f3)
    res = calcular(resp)
    g = res.bloques[0]

    Resultado.query.filter_by(sesion=s.id).delete()
    db.session.add(Resultado(
        sesion=s.id,
        # Si el perfil salió plano no se asigna bloque: el sistema no debe
        # fingir certeza cuando los trece quedaron casi iguales.
        itinerario=None if res.perfil_plano else g.id,
        empate_tecnico=res.empate_tecnico, perfil_plano=res.perfil_plano,
        optativa_debil=g.optativa_debil if g.alerta_debil else None,
        pos_debil=g.pos_debil if g.alerta_debil else None,
        perfil_academias=res.perfil_academias,
        explicacion={"razones": explicar(resp, res), "advertencias": res.advertencias},
    ))
    db.session.flush()
    for f in res.optativas:
        db.session.add(ResultadoOptativa(
            sesion=s.id, optativa=f.clave, posicion=f.posicion,
            afinidad=f.afinidad, indice=0, f1=f.f1, f2=f.f2, ajuste_f3=f.ajuste_f3))
    for b in res.bloques:
        db.session.add(ResultadoItinerario(
            sesion=s.id, itinerario=b.id, posicion=b.posicion,
            score=b.score, indice=b.indice, media=b.media, peor=b.peor))
    s.modo = "breve" if s.modo == "breve" else "completo"

    s.estado = "completada"
    s.completada_en = datetime.utcnow()
    s.paso_actual = "resultado"
    db.session.commit()
    return jsonify(ok=True)


@bp.get("/sesion/resultado")
@jwt_required()
def resultado():
    """Lo que ve el estudiante: un BLOQUE, no optativas sueltas."""
    u = usuario_actual()
    app_ = _aplicacion_activa()
    s = _sesion_de(u, app_)

    # camino corto: eligió su bloque sin contestar
    if s.itinerario_elegido:
        it = db.session.get(Itinerario, s.itinerario_elegido)
        opts = (db.session.query(Optativa)
                .join(ItinerarioOptativa, ItinerarioOptativa.optativa == Optativa.clave)
                .filter(ItinerarioOptativa.itinerario == it.id)
                .order_by(ItinerarioOptativa.orden).all())
        return jsonify(origen="eleccion_directa",
                       bloque={**it.publico(),
                               "optativas": [{"clave": o.clave, "nombre": o.nombre} for o in opts]})

    r = db.session.get(Resultado, s.id)
    if not r:
        return jsonify(error="Todavía no has terminado el cuestionario."), 404

    filas = (db.session.query(ResultadoItinerario, Itinerario)
             .join(Itinerario, Itinerario.id == ResultadoItinerario.itinerario)
             .filter(ResultadoItinerario.sesion == s.id)
             .order_by(ResultadoItinerario.posicion).all())

    por_bloque = {}
    for io in ItinerarioOptativa.query.order_by(ItinerarioOptativa.orden):
        por_bloque.setdefault(io.itinerario, []).append(io.optativa)
    nombres = {o.clave: o.nombre for o in Optativa.query.all()}

    # Filtra contra la oferta real: no tiene caso recomendar un bloque cuyas
    # optativas no se van a abrir.
    cerradas = {row[0] for row in db.session.execute(text(
        "SELECT optativa FROM oferta WHERE aplicacion=:a AND se_abre=0"), {"a": app_.id})}

    ranking = [{
        "id": it.id, "nombre": it.nombre, "frase": it.frase, "resumen": it.resumen,
        "perfil": it.perfil, "salidas": it.salidas,
        "posicion": ri.posicion, "indice": float(ri.indice),
        "optativas": [{"clave": c, "nombre": nombres.get(c)} for c in por_bloque.get(it.id, [])],
        "bloqueado": bool(set(por_bloque.get(it.id, [])) & cerradas) if cerradas else False,
    } for ri, it in filas]

    return jsonify(
        origen="cuestionario",
        perfil_plano=r.perfil_plano,
        empate_tecnico=r.empate_tecnico,
        recomendado=None if r.perfil_plano else ranking[0],
        alternativos=ranking[1:3],
        ranking=ranking,
        alerta_debil=({"optativa": r.optativa_debil,
                       "nombre": nombres.get(r.optativa_debil),
                       "posicion": r.pos_debil} if r.optativa_debil else None),
        explicacion=r.explicacion,
        perfil_academias=r.perfil_academias,
    )
