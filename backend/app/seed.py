"""
Carga los catálogos a la base a partir de app/motor/datos.py.

    python seed.py            # carga catálogos + crea la aplicación activa
    python seed.py --docente  # además crea un usuario docente de prueba

Es idempotente: puedes correrlo de nuevo sin duplicar nada.
"""
import argparse
from datetime import datetime, timedelta

from argon2 import PasswordHasher

from app import crear_app
from app.models import (Academia, Aplicacion, EECurricular, Itinerario,
                        ItinerarioOptativa, OpcionContexto, OpcionReactivo,
                        Optativa, PesoAcademiaOptativa, PreguntaContexto,
                        Reactivo, Usuario, db)
from app.motor import datos as D

PERFILES = {
    1:  ("Global Trade & Expansion", "Llevar un producto mexicano a mercados extranjeros: aduanas, tratados y planes de exportación.",
         ["Analista en agencia aduanal", "Coordinador de exportaciones", "Asesor en cámaras de comercio"]),
    2:  ("Supply Chain & Distribution", "Mover mercancía: almacenes, rutas, cruce de frontera y entrega de última milla.",
         ["Gerente de operaciones", "Supply Chain Analyst", "Responsable de fulfillment"]),
    3:  ("Digital Venture Builder", "Montar un negocio propio en línea: producto, narrativa y canal de venta.",
         ["Fundador de marca o tienda en línea", "Growth o e-commerce manager", "Consultor de digitalización para MiPyMEs"]),
    4:  ("Creative & Cultural Producer", "Profesionalizar festivales, museos y proyectos turísticos, que casi siempre operan con presupuesto público.",
         ["Director de proyectos turísticos y culturales", "Productor de eventos", "Gestor cultural institucional"]),
    5:  ("Sustainable Development Specialist", "Formular y evaluar proyectos de desarrollo con criterio ambiental, social y de gasto público.",
         ["Director de desarrollo económico municipal", "Gestor de proyectos regionales", "Evaluador de programas públicos"]),
    6:  ("Impact Organization Lead", "Dirigir empresas sociales y áreas de sostenibilidad, con el inglés que exigen los organismos internacionales.",
         ["Gerente de sustentabilidad o ESG", "Director de proyectos en ONG", "Fundador de empresa social"]),
    7:  ("People, Culture & Knowledge", "Diagnosticar la cultura de una organización y desarrollar a quienes van a dirigirla.",
         ["Business Partner de Recursos Humanos", "Especialista en desarrollo organizacional", "Consultor en gestión del cambio"]),
    8:  ("Family Business Succession Lead", "Profesionalizar el negocio familiar: gobierno corporativo, protocolo y transición generacional.",
         ["Sucesor profesionalizado", "Consultor en protocolos familiares", "Director general de MiPyME"]),
    9:  ("Process & Operations Consultant", "Medir una operación, rediseñarla y documentarla para que la mejora no se pierda.",
         ["Analista de mejora continua", "Consultor de procesos", "Coordinador de calidad"]),
    10: ("Global Business Management", "Operar y dirigir en inglés dentro de corporativos internacionales.",
         ["Analista en corporativo multinacional", "Key account manager internacional", "Consultor en expansión transfronteriza"]),
    11: ("Community Venture Builder", "Crear y sostener cooperativas y colectivos, donde el reto es el grupo humano.",
         ["Fundador de cooperativa o colectivo", "Coordinador de proyectos comunitarios", "Gestor de economía social"]),
    12: ("Sustainability Communications", "Traducir el desempeño ambiental y social de una empresa en información creíble.",
         ["Especialista en reporte ESG", "Comunicación corporativa", "Consultor en comunicación de impacto"]),
}

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
        PesoAcademiaOptativa.query.delete()
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

        print("→ itinerarios")
        ItinerarioOptativa.query.delete()
        for idx, nombre, opts in D.ITINERARIOS:
            en, perfil, salidas = PERFILES[idx]
            upsert(Itinerario, idx, id=idx, nombre=nombre, nombre_en=en,
                   perfil=perfil, salidas=salidas)
            db.session.flush()
            for orden, o in enumerate(opts, start=1):
                db.session.add(ItinerarioOptativa(itinerario=idx, optativa=o, orden=orden))
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

        print(f"\nListo. {Optativa.query.count()} optativas, "
              f"{Reactivo.query.count()} reactivos, "
              f"{Itinerario.query.count()} itinerarios, "
              f"{PesoAcademiaOptativa.query.count()} pesos.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--docente", action="store_true", help="crea un usuario docente de prueba")
    main(p.parse_args().docente)
