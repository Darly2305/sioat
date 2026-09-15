"""
Gestión de cuentas desde la terminal.

Existe para el caso en que nadie puede entrar al panel: contraseña olvidada,
cuenta desactivada, o el primer administrador después de instalar. Todo lo
demás se hace desde la pestaña Cuentas.

    python cuenta.py listar
    python cuenta.py password admin@sioat.local
    python cuenta.py correo admin@sioat.local nuevo@uv.mx
    python cuenta.py crear "Ana Docente" ana@uv.mx docente
    python cuenta.py rol ana@uv.mx admin
"""
import argparse
import getpass
import sys

from argon2 import PasswordHasher

from app import crear_app
from app.models import Usuario, db

ph = PasswordHasher()


def _buscar(correo):
    u = Usuario.query.filter_by(correo=correo.lower()).first()
    if not u:
        sys.exit(f"No existe ninguna cuenta con el correo {correo}.")
    return u


def _pedir_password():
    p1 = getpass.getpass("Contraseña nueva: ")
    if len(p1) < 8:
        sys.exit("La contraseña necesita al menos 8 caracteres.")
    if p1 != getpass.getpass("Repítela: "):
        sys.exit("No coinciden.")
    return p1


def listar():
    print(f"\n{'ROL':<10} {'CORREO':<34} {'NOMBRE':<28} ACTIVO")
    print("-" * 82)
    for u in Usuario.query.filter(Usuario.rol != "estudiante").order_by(Usuario.rol, Usuario.nombre):
        print(f"{u.rol:<10} {u.correo:<34} {u.nombre[:27]:<28} {'sí' if u.activo else 'NO'}")
    n = Usuario.query.filter_by(rol="estudiante").count()
    print(f"\n({n} estudiantes registrados, no se listan aquí)\n")


def password(correo):
    u = _buscar(correo)
    u.password_hash = ph.hash(_pedir_password())
    db.session.commit()
    print(f"Contraseña actualizada para {u.correo}.")


def correo(viejo, nuevo):
    u = _buscar(viejo)
    nuevo = nuevo.lower().strip()
    if Usuario.query.filter(Usuario.correo == nuevo, Usuario.id != u.id).first():
        sys.exit(f"Ya existe otra cuenta con {nuevo}.")
    u.correo = nuevo
    db.session.commit()
    print(f"Correo actualizado: {viejo} → {nuevo}")


def crear(nombre, correo_, rol):
    if rol not in ("docente", "admin"):
        sys.exit("El rol debe ser 'docente' o 'admin'.")
    if Usuario.query.filter_by(correo=correo_.lower()).first():
        sys.exit(f"Ya existe una cuenta con {correo_}.")
    u = Usuario(nombre=nombre, correo=correo_.lower(), rol=rol,
                password_hash=ph.hash(_pedir_password()))
    db.session.add(u)
    db.session.commit()
    print(f"Cuenta creada: {u.correo} ({u.rol})")


def rol(correo_, nuevo):
    if nuevo not in ("docente", "admin"):
        sys.exit("El rol debe ser 'docente' o 'admin'.")
    u = _buscar(correo_)
    u.rol = nuevo
    db.session.commit()
    print(f"{u.correo} ahora es {nuevo}.")


def activar(correo_, valor):
    u = _buscar(correo_)
    u.activo = valor
    db.session.commit()
    print(f"{u.correo} {'activada' if valor else 'desactivada'}.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Cuentas de SIOAT")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("listar")
    s = sub.add_parser("password"); s.add_argument("correo")
    s = sub.add_parser("correo");   s.add_argument("viejo"); s.add_argument("nuevo")
    s = sub.add_parser("crear");    s.add_argument("nombre"); s.add_argument("correo"); s.add_argument("rol")
    s = sub.add_parser("rol");      s.add_argument("correo"); s.add_argument("nuevo")
    s = sub.add_parser("activar");  s.add_argument("correo")
    s = sub.add_parser("desactivar"); s.add_argument("correo")
    a = p.parse_args()

    with crear_app().app_context():
        if a.cmd == "listar":       listar()
        elif a.cmd == "password":   password(a.correo)
        elif a.cmd == "correo":     correo(a.viejo, a.nuevo)
        elif a.cmd == "crear":      crear(a.nombre, a.correo, a.rol)
        elif a.cmd == "rol":        rol(a.correo, a.nuevo)
        elif a.cmd == "activar":    activar(a.correo, True)
        elif a.cmd == "desactivar": activar(a.correo, False)
