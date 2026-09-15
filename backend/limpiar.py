"""
Borrado de datos de prueba.

Se usa para dejar el sistema limpio antes de aplicarlo de verdad. NO toca los
catálogos: optativas, bloques, reactivos, preguntas de contexto y la matriz de
afinidad se quedan como están, porque son la configuración del sistema y no
datos de nadie.

    python limpiar.py ver                 # qué hay, sin borrar nada
    python limpiar.py respuestas          # borra sesiones y resultados, conserva cuentas
    python limpiar.py estudiantes         # borra alumnos y todo lo suyo
    python limpiar.py cuentas-prueba      # borra admin@sioat.local y docente@sioat.local
    python limpiar.py todo                # las tres anteriores

Todo pide confirmación escrita. Añade --si para saltarla en un script.

Cómo funciona el borrado: aunque el esquema declara ON DELETE CASCADE, aquí se
borra tabla por tabla en el orden correcto, de la hoja a la raíz. Depender del
CASCADE parece más elegante, pero deja de funcionar en cuanto alguien restaura
la base en otro motor, importa un respaldo con las llaves desactivadas o corre
esto contra SQLite, donde las foráneas están apagadas por omisión. Un borrado
que falla a medias y deja filas huérfanas es peor que no borrar nada.
"""
import argparse
import sys

from sqlalchemy import text

from app import crear_app
from app.models import Aplicacion, Usuario, db

CORREOS_PRUEBA = ["admin@sioat.local", "docente@sioat.local"]


def contar():
    q = lambda s: db.session.execute(text(s)).scalar()
    return {
        "estudiantes": q("SELECT COUNT(*) FROM usuario WHERE rol='estudiante'"),
        "docentes": q("SELECT COUNT(*) FROM usuario WHERE rol IN ('docente','admin')"),
        "sesiones": q("SELECT COUNT(*) FROM sesion"),
        "completadas": q("SELECT COUNT(*) FROM sesion WHERE estado='completada'"),
        "respuestas": (q("SELECT COUNT(*) FROM respuesta_fase1")
                       + q("SELECT COUNT(*) FROM respuesta_fase2")
                       + q("SELECT COUNT(*) FROM respuesta_fase3")),
        "resultados": q("SELECT COUNT(*) FROM resultado"),
        "aplicaciones": q("SELECT COUNT(*) FROM aplicacion"),
    }


def ver():
    c = contar()
    print("\nDatos actuales")
    print("-" * 44)
    print(f"  Estudiantes registrados     {c['estudiantes']:>6}")
    print(f"  Cuentas docente/admin       {c['docentes']:>6}")
    print(f"  Sesiones de cuestionario    {c['sesiones']:>6}  ({c['completadas']} terminadas)")
    print(f"  Respuestas guardadas        {c['respuestas']:>6}")
    print(f"  Resultados calculados       {c['resultados']:>6}")
    print(f"  Periodos de aplicación      {c['aplicaciones']:>6}")

    prueba = Usuario.query.filter(Usuario.correo.in_(CORREOS_PRUEBA)).all()
    if prueba:
        print("\n  Cuentas de prueba encontradas:")
        for u in prueba:
            print(f"    {u.correo}  ({u.rol})")
    print()
    return c


def confirmar(mensaje, saltar):
    if saltar:
        return True
    print(f"\n{mensaje}")
    return input("Escribe BORRAR para confirmar: ").strip() == "BORRAR"


# De la hoja a la raíz. El orden importa: cada tabla se borra antes que aquella
# a la que apunta.
CADENA_SESION = [
    "resultado_optativa",
    "resultado_itinerario",
    "resultado",
    "respuesta_fase1",
    "respuesta_fase2",
    "respuesta_fase3",
]


def _borrar_cadena(filtro_sesiones=""):
    """Borra todo lo que cuelga de una sesión, y luego la sesión."""
    donde = f" WHERE sesion IN (SELECT id FROM sesion{filtro_sesiones})" if filtro_sesiones else ""
    total = 0
    for tabla in CADENA_SESION:
        total += db.session.execute(text(f"DELETE FROM {tabla}{donde}")).rowcount
    n = db.session.execute(text(f"DELETE FROM sesion{filtro_sesiones}")).rowcount
    return n, total


def borrar_respuestas():
    n, filas = _borrar_cadena()
    db.session.commit()
    print(f"  {n} sesiones borradas, con {filas} filas de respuestas y resultados.")


def borrar_estudiantes():
    sub = " WHERE usuario IN (SELECT id FROM usuario WHERE rol='estudiante')"
    n, filas = _borrar_cadena(sub)
    u = db.session.execute(text("DELETE FROM usuario WHERE rol='estudiante'")).rowcount
    db.session.commit()
    print(f"  {u} estudiantes borrados, con {n} sesiones y {filas} filas asociadas.")


def borrar_cuentas_prueba():
    """Borra las cuentas que crea el seed.

    Antes verifica que quede al menos un administrador real: si no, nadie
    podría entrar al panel. Y reasigna las aplicaciones que esas cuentas hayan
    creado, porque aplicacion.creada_por apunta a usuario y no está en cascada
    a propósito: un periodo de aplicación no debe desaparecer porque se dio de
    baja a quien lo abrió."""
    prueba = Usuario.query.filter(Usuario.correo.in_(CORREOS_PRUEBA)).all()
    if not prueba:
        print("  No hay cuentas de prueba que borrar.")
        return

    ids = [u.id for u in prueba]
    sobreviviente = (Usuario.query
                     .filter(Usuario.rol == "admin", ~Usuario.id.in_(ids))
                     .first())
    if not sobreviviente:
        sys.exit(
            "\n  DETENIDO: no hay ningún otro administrador.\n"
            "  Si borro estas cuentas, nadie va a poder entrar al panel.\n"
            "  Crea primero la cuenta real:\n\n"
            '      python cuenta.py crear "Tu Nombre" tucorreo@uv.mx admin\n')

    reasignadas = (Aplicacion.query
                   .filter(Aplicacion.creada_por.in_(ids))
                   .update({"creada_por": sobreviviente.id}, synchronize_session=False))
    if reasignadas:
        print(f"  {reasignadas} aplicaciones reasignadas a {sobreviviente.correo}.")

    lista = ",".join(str(i) for i in ids)
    n, filas = _borrar_cadena(f" WHERE usuario IN ({lista})")
    if n:
        print(f"  {n} sesiones de esas cuentas borradas.")
    db.session.execute(text(f"DELETE FROM usuario WHERE id IN ({lista})"))
    db.session.commit()
    print(f"  {len(prueba)} cuentas de prueba borradas.")


ACCIONES = {
    "respuestas": ("Se van a borrar TODAS las sesiones, respuestas y resultados.\n"
                   "Las cuentas se conservan.", [borrar_respuestas]),
    "estudiantes": ("Se van a borrar TODOS los estudiantes y sus sesiones,\n"
                    "respuestas y resultados.", [borrar_estudiantes]),
    "cuentas-prueba": ("Se van a borrar las cuentas admin@sioat.local y\n"
                       "docente@sioat.local.", [borrar_cuentas_prueba]),
    "todo": ("Se van a borrar TODOS los estudiantes, todas las sesiones y las\n"
             "cuentas de prueba. Los catálogos se conservan.",
             [borrar_cuentas_prueba, borrar_estudiantes, borrar_respuestas]),
}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Borrado de datos de prueba de SIOAT")
    p.add_argument("accion", choices=["ver", *ACCIONES])
    p.add_argument("--si", action="store_true", help="no pedir confirmación")
    a = p.parse_args()

    with crear_app().app_context():
        if a.accion == "ver":
            ver()
            sys.exit()

        ver()
        mensaje, pasos = ACCIONES[a.accion]
        if not confirmar(mensaje, a.si):
            sys.exit("Cancelado. No se borró nada.")

        print()
        for paso in pasos:
            paso()

        print("\nListo. Estado final:")
        ver()
        print("Los catálogos siguen intactos. Si quieres re-sembrarlos, corre: python seed.py\n")
