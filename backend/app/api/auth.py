import re
from datetime import datetime

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from ..models import Usuario, db

bp = Blueprint("auth", __name__)
ph = PasswordHasher()

RE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)
RE_MATRICULA = re.compile(r"^[A-Za-z]?\d{6,10}$")
RE_SECCION = re.compile(r"^[A-Za-z0-9\- ]{1,10}$")


def _error(msg, code=400):
    return jsonify(error=msg), code


@bp.post("/registro")
def registro():
    d = request.get_json(silent=True) or {}
    nombre = (d.get("nombre") or "").strip()
    correo = (d.get("correo") or "").strip().lower()
    matricula = (d.get("matricula") or "").strip().upper() or None
    seccion = (d.get("seccion") or "").strip().upper() or None
    passwd = d.get("password") or ""

    if len(nombre) < 3:
        return _error("Escribe tu nombre completo.")
    if not RE_CORREO.match(correo):
        return _error("Ese correo no parece válido.")
    dominio = current_app.config["DOMINIO_PERMITIDO"]
    if dominio and not correo.endswith(dominio):
        return _error(f"Usa tu correo institucional (termina en {dominio}).")
    if matricula and not RE_MATRICULA.match(matricula):
        return _error("La matrícula no tiene el formato esperado.")
    if seccion and not RE_SECCION.match(seccion):
        return _error("La sección sólo admite letras, números y guiones.")
    if len(passwd) < 8:
        return _error("La contraseña necesita al menos 8 caracteres.")

    if Usuario.query.filter_by(correo=correo).first():
        return _error("Ese correo ya está registrado. Inicia sesión.", 409)
    if matricula and Usuario.query.filter_by(matricula=matricula).first():
        return _error("Esa matrícula ya está registrada.", 409)

    u = Usuario(nombre=nombre, correo=correo, matricula=matricula, seccion=seccion,
                password_hash=ph.hash(passwd), rol="estudiante",
                periodo_cursado=d.get("periodo_cursado"))
    db.session.add(u)
    db.session.commit()
    return jsonify(token=create_access_token(identity=str(u.id)), usuario=u.publico()), 201


@bp.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    ident = (d.get("correo") or d.get("matricula") or "").strip()
    passwd = d.get("password") or ""

    u = Usuario.query.filter(
        (Usuario.correo == ident.lower()) | (Usuario.matricula == ident.upper())
    ).first()

    # mismo mensaje en los dos casos: no revelamos si el correo existe
    if not u:
        ph.hash(passwd)              # gasta el mismo tiempo, evita enumerar usuarios
        return _error("Correo o contraseña incorrectos.", 401)
    try:
        ph.verify(u.password_hash, passwd)
    except (VerifyMismatchError, VerificationError):
        return _error("Correo o contraseña incorrectos.", 401)
    if not u.activo:
        return _error("Tu cuenta está desactivada. Habla con tu coordinación.", 403)

    if ph.check_needs_rehash(u.password_hash):
        u.password_hash = ph.hash(passwd)
    u.ultimo_acceso = datetime.utcnow()
    db.session.commit()
    return jsonify(token=create_access_token(identity=str(u.id)), usuario=u.publico())


@bp.get("/yo")
@jwt_required()
def yo():
    u = db.session.get(Usuario, int(get_jwt_identity()))
    return jsonify(usuario=u.publico()) if u else _error("Sesión no válida.", 401)


@bp.put("/perfil")
@jwt_required()
def actualizar_perfil():
    """Cambiar nombre, correo o sección propios. El rol no se toca aquí:
    nadie se asciende a sí mismo."""
    u = usuario_actual()
    d = request.get_json(silent=True) or {}

    if "nombre" in d:
        nombre = (d["nombre"] or "").strip()
        if len(nombre) < 3:
            return _error("Escribe tu nombre completo.")
        u.nombre = nombre
    if "correo" in d:
        correo = (d["correo"] or "").strip().lower()
        if not RE_CORREO.match(correo):
            return _error("Ese correo no parece válido.")
        dominio = current_app.config["DOMINIO_PERMITIDO"]
        if dominio and u.rol == "estudiante" and not correo.endswith(dominio):
            return _error(f"Usa tu correo institucional (termina en {dominio}).")
        otro = Usuario.query.filter(Usuario.correo == correo, Usuario.id != u.id).first()
        if otro:
            return _error("Ese correo ya está en uso por otra cuenta.", 409)
        u.correo = correo
    if "seccion" in d:
        seccion = (d["seccion"] or "").strip().upper() or None
        if seccion and not RE_SECCION.match(seccion):
            return _error("La sección sólo admite letras, números y guiones.")
        u.seccion = seccion

    db.session.commit()
    return jsonify(ok=True, usuario=u.publico())


@bp.put("/password")
@jwt_required()
def cambiar_password():
    """Cambio de contraseña propio. Exige la actual: si alguien deja la sesión
    abierta en un laboratorio, que no pueda dejar a su dueño fuera."""
    u = usuario_actual()
    d = request.get_json(silent=True) or {}
    actual = d.get("actual") or ""
    nueva = d.get("nueva") or ""

    try:
        ph.verify(u.password_hash, actual)
    except (VerifyMismatchError, VerificationError):
        return _error("Tu contraseña actual no es correcta.", 401)
    if len(nueva) < 8:
        return _error("La nueva contraseña necesita al menos 8 caracteres.")
    if nueva == actual:
        return _error("La nueva contraseña tiene que ser distinta.")

    u.password_hash = ph.hash(nueva)
    db.session.commit()
    return jsonify(ok=True)


def usuario_actual():
    return db.session.get(Usuario, int(get_jwt_identity()))


def requiere_docente(fn):
    """Lectura del panel: resumen, padrón y export. Docente y admin."""
    from functools import wraps

    @wraps(fn)
    @jwt_required()
    def envoltura(*a, **kw):
        u = usuario_actual()
        if not u or u.rol not in ("docente", "admin"):
            return _error("Esta sección es sólo para docentes.", 403)
        return fn(*a, **kw)

    return envoltura


def requiere_admin(fn):
    """Escritura: abrir o cerrar optativas, mover la fecha límite, tocar la
    matriz. El docente consulta; el administrador cambia el estado del sistema.
    Separarlos importa: un cambio de oferta a media aplicación altera lo que
    todos los alumnos ven."""
    from functools import wraps

    @wraps(fn)
    @jwt_required()
    def envoltura(*a, **kw):
        u = usuario_actual()
        if not u or u.rol != "admin":
            return _error("Esta acción requiere permisos de administrador.", 403)
        return fn(*a, **kw)

    return envoltura
