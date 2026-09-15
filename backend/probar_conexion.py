"""
Comprueba la conexión a la base de datos antes de importar nada.

    python probar_conexion.py

Existe porque los tres errores típicos de un MySQL gestionado —puerto
equivocado, TLS mal configurado y base inexistente— dan mensajes crípticos
cuando aparecen a media importación de un archivo de 300 líneas. Vale más
descubrirlos en dos segundos.
"""
import sys

from sqlalchemy import inspect, text

from app import crear_app
from app.config import Config
from app.models import db

TABLAS_ESPERADAS = {
    "usuario", "aplicacion", "academia", "optativa", "peso_academia_optativa",
    "itinerario", "itinerario_optativa", "ee_curricular", "reactivo",
    "opcion_reactivo", "pregunta_contexto", "opcion_contexto", "sesion",
    "respuesta_fase1", "respuesta_fase2", "respuesta_fase3", "resultado",
    "resultado_optativa", "resultado_itinerario", "oferta",
}
VISTAS_ESPERADAS = {
    "v_bloque_asignado", "v_demanda_bloque", "v_demanda_optativa",
    "v_avance_aplicacion", "v_avance_seccion", "v_concordancia_decision_previa",
}


def main():
    app = crear_app()
    destino = Config.SQLALCHEMY_DATABASE_URI.split("@")[-1]
    ssl = "sí" if "connect_args" in Config.SQLALCHEMY_ENGINE_OPTIONS else "no"
    print(f"\nDestino : {destino}")
    print(f"TLS     : {ssl}")

    with app.app_context():
        try:
            version = db.session.execute(text("SELECT VERSION()")).scalar()
            base = db.session.execute(text("SELECT DATABASE()")).scalar()
        except Exception as e:
            print("\n  NO SE PUDO CONECTAR\n")
            msg = str(e)
            if "Can't connect" in msg or "timed out" in msg:
                print("  Revisa el host y el puerto. En Aiven el puerto no es 3306:")
                print("  es un número alto que aparece en la pestaña Overview del servicio.")
            elif "Access denied" in msg:
                print("  Usuario o contraseña incorrectos. En Aiven el usuario suele ser avnadmin.")
            elif "SSL" in msg or "certificate" in msg.lower():
                print("  Problema de TLS. Descarga el ca.pem del panel del proveedor y ponlo")
                print("  en DB_SSL_CA (ruta) o DB_SSL_CA_CONTENT (contenido) dentro del .env.")
            elif "Unknown database" in msg:
                print("  Esa base no existe. Créala desde el panel del proveedor,")
                print("  o usa la que viene por omisión (en Aiven se llama defaultdb).")
            print(f"\n  Mensaje original:\n  {msg[:300]}\n")
            sys.exit(1)

        print(f"Conectado a MySQL {version}, base «{base}»\n")

        insp = inspect(db.engine)
        tablas = set(insp.get_table_names())
        vistas = set(insp.get_view_names())

        faltan_t = TABLAS_ESPERADAS - tablas
        faltan_v = VISTAS_ESPERADAS - vistas

        if not tablas:
            print("La base está vacía. Importa el esquema:")
            print("  mysql -h <host> -P <puerto> -u avnadmin -p \\")
            print("        --ssl-ca=ca.pem -D <base> < db/schema_remoto.sql\n")
            sys.exit(0)

        print(f"Tablas: {len(tablas & TABLAS_ESPERADAS)} de {len(TABLAS_ESPERADAS)}")
        print(f"Vistas: {len(vistas & VISTAS_ESPERADAS)} de {len(VISTAS_ESPERADAS)}")
        if faltan_t:
            print(f"\n  Faltan tablas: {', '.join(sorted(faltan_t))}")
        if faltan_v:
            print(f"  Faltan vistas: {', '.join(sorted(faltan_v))}")
            print("  Suele significar que el esquema se importó a medias.")

        if not faltan_t and not faltan_v:
            filas = db.session.execute(text("SELECT COUNT(*) FROM optativa")).scalar()
            bloques = db.session.execute(text("SELECT COUNT(*) FROM itinerario")).scalar()
            alumnos = db.session.execute(text(
                "SELECT COUNT(*) FROM usuario WHERE rol='estudiante'")).scalar()
            print(f"\nCatálogos: {filas} optativas, {bloques} bloques")
            print(f"Estudiantes registrados: {alumnos}")
            if filas == 0:
                print("\nEsquema completo pero sin catálogos. Corre: python seed.py")
            else:
                print("\nTodo en orden.")
        print()


if __name__ == "__main__":
    main()
