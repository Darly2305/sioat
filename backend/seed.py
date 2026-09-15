"""
Carga los catálogos a la base a partir de app/motor/datos.py.

    python seed.py            # carga catálogos + crea la aplicación activa
    python seed.py --docente  # además crea un usuario docente de prueba

Es idempotente: puedes correrlo de nuevo sin duplicar nada.
"""
import argparse
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from sqlalchemy import text

from app import crear_app
from app.models import (Academia, Aplicacion, EECurricular, Itinerario,
                        ItinerarioOptativa, OpcionContexto, OpcionReactivo,
                        Optativa, PesoAcademiaOptativa, PreguntaContexto,
                        Reactivo, Usuario, db)
from app.motor import datos as D

def upsert_por(modelo, filtro, **campos):
    """Busca por una combinación de columnas en lugar de por llave primaria.

    Las opciones de los reactivos se identifican por (reactivo, letra), no por
    su id autoincremental. Actualizarlas en su sitio es obligatorio: la tabla
    respuesta_fase2 guarda el id de la opción elegida, así que borrarlas y
    recrearlas rompería la llave foránea y, peor aún, dejaría respuestas
    apuntando a opciones distintas de las que el estudiante eligió."""
    obj = modelo.query.filter_by(**filtro).first()
    if obj:
        for k, v in campos.items():
            setattr(obj, k, v)
    else:
        obj = modelo(**filtro, **campos)
        db.session.add(obj)
    return obj


def upsert(modelo, pk, **campos):
    obj = db.session.get(modelo, pk)
    if obj:
        for k, v in campos.items():
            setattr(obj, k, v)
    else:
        obj = modelo(**campos)
        db.session.add(obj)
    return obj


def main(crear_docente=False):
    app = crear_app()
    with app.app_context():
        print("→ academias")
        for clave, nombre in D.ACADEMIA_NOMBRE.items():
            upsert(Academia, clave, clave=clave, nombre=nombre)
        db.session.commit()

        print("→ optativas")
        for clave, m in D.OPTATIVAS.items():
            upsert(Optativa, clave, clave=clave, nombre=m["nombre"],
                   academia=m["academia"], creditos=m["creditos"],
                   idioma=m.get("idioma", "es"))
        db.session.commit()

        print("→ matriz de afinidad")
        PesoAcademiaOptativa.query.delete()   # sin referencias externas
        for opt, pesos in D.PESOS.items():
            for acad, peso in pesos.items():
                db.session.add(PesoAcademiaOptativa(academia=acad, optativa=opt, peso=peso))
        db.session.commit()

        print("→ experiencias educativas I–V")
        for periodo, ees in D.EE_CURRICULARES.items():
            for clave, nombre, acad in ees:
                upsert(EECurricular, clave, clave=clave, nombre=nombre,
                       periodo=periodo, academia=acad)
        db.session.commit()

        print("→ reactivos de la fase 2")
        for numero, enunciado, ops in D.REACTIVOS:
            upsert(Reactivo, numero, numero=numero, enunciado=enunciado,
                   en_breve=numero in D.REACTIVOS_VERSION_BREVE)
            db.session.flush()
            for letra, texto, optativa in ops:
                upsert_por(OpcionReactivo, {"reactivo": numero, "letra": letra},
                           texto=texto, optativa=optativa, puntos=D.PUNTOS_REACTIVO)
        db.session.commit()

        print("→ preguntas de contexto")
        for numero, enunciado, ops, nota in D.PREGUNTAS_CONTEXTO:
            upsert(PreguntaContexto, numero, numero=numero, enunciado=enunciado, nota=nota)
            db.session.flush()
            for letra, texto, ajustes in ops:
                upsert_por(OpcionContexto, {"pregunta": numero, "letra": letra},
                           texto=texto, ajustes=ajustes)
        db.session.commit()

        print("→ bloques de área terminal")
        # Esta sí se puede recrear: ninguna tabla de respuestas la referencia.
        ItinerarioOptativa.query.delete()
        for b in D.ITINERARIOS:
            upsert(Itinerario, b["id"], id=b["id"], nombre=b["nombre"],
                   nombre_en=b["nombre_en"], frase=b["frase"], resumen=b["resumen"],
                   perfil=b["perfil"], salidas=b["salidas"])
            db.session.flush()
            for orden, o in enumerate(b["opts"], start=1):
                db.session.add(ItinerarioOptativa(itinerario=b["id"], optativa=o, orden=orden))
        db.session.commit()

        admin = Usuario.query.filter_by(rol="admin").first()
        if not admin:
            admin = Usuario(nombre="Administrador", correo="admin@sioat.local",
                            password_hash=PasswordHasher().hash("admin12345"), rol="admin")
            db.session.add(admin)
            db.session.commit()
            print("→ admin creado: admin@sioat.local / admin12345  (CÁMBIALA)")

        if crear_docente and not Usuario.query.filter_by(correo="docente@sioat.local").first():
            db.session.add(Usuario(nombre="Docente de prueba", correo="docente@sioat.local",
                                   password_hash=PasswordHasher().hash("docente12345"),
                                   rol="docente"))
            db.session.commit()
            print("→ docente creado: docente@sioat.local / docente12345")

        if not Aplicacion.query.filter_by(activa=True).first():
            db.session.add(Aplicacion(
                nombre=f"Aplicación {datetime.now():%b %Y}",
                fecha_inicio=datetime.now(),
                fecha_limite=datetime.now() + timedelta(days=45),
                activa=True, creada_por=admin.id))
            db.session.commit()
            print("→ aplicación activa creada, con límite a 45 días")

        huerfanas = db.session.execute(text("""
            SELECT COUNT(*) FROM opcion_reactivo o
            WHERE NOT EXISTS (SELECT 1 FROM reactivo r WHERE r.numero = o.reactivo)
        """)).scalar()

        print(f"\nListo. {Optativa.query.count()} optativas, "
              f"{Reactivo.query.count()} reactivos, "
              f"{OpcionReactivo.query.count()} opciones, "
              f"{Itinerario.query.count()} bloques, "
              f"{PesoAcademiaOptativa.query.count()} pesos.")
        if huerfanas:
            print(f"Aviso: {huerfanas} opciones quedaron sin reactivo. Revísalas antes de aplicar.")

        respuestas = db.session.execute(text(
            "SELECT COUNT(*) FROM respuesta_fase2")).scalar()
        if respuestas:
            print(f"\nHay {respuestas} respuestas de la fase 2 ya guardadas. Se conservaron: "
                  "las opciones se actualizaron en su sitio y siguen apuntando a la misma "
                  "optativa, así que esas respuestas siguen siendo válidas.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--docente", action="store_true", help="crea un usuario docente de prueba")
    main(p.parse_args().docente)
