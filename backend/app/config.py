import os
import tempfile
from datetime import timedelta
from urllib.parse import quote_plus


def _ca_path():
    """Aiven y la mayoría de los MySQL gestionados exigen TLS con su propia
    autoridad certificadora, que no está en el almacén del sistema.

    Se acepta de dos formas: una ruta a un archivo .pem, o el contenido del
    certificado en una variable de entorno. La segunda existe porque en Render
    no hay dónde dejar archivos: se escribe a un temporal al arrancar."""
    ruta = os.getenv("DB_SSL_CA", "").strip()
    if ruta and os.path.exists(ruta):
        return ruta
    contenido = os.getenv("DB_SSL_CA_CONTENT", "").strip()
    if contenido:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)
        f.write(contenido.replace("\\n", "\n"))
        f.close()
        return f.name
    return None


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esto-en-produccion")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    # Algunos proveedores entregan la conexión completa en una sola variable.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or (
        f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASS)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    if SQLALCHEMY_DATABASE_URI.startswith("mysql://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "mysql://", "mysql+pymysql://", 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    _ca = _ca_path()
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,   # imprescindible: el MySQL gestionado corta
        "pool_recycle": 280,     # conexiones ociosas sin avisar
        "pool_size": 3,          # el plan gratuito tiene pocas conexiones
        "max_overflow": 2,
        **({"connect_args": {"ssl": {"ca": _ca}}} if _ca else {}),
    }

    CORS_ORIGINS = [o.strip().rstrip("/") for o in
                    os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

    # Dominios institucionales aceptados al registrarse. Se acepta más de uno
    # separados por coma, porque «@estudiantes.uv.mx» no termina en «@uv.mx»:
    # comparar con una sola cadena dejaría fuera a la mitad de la Facultad.
    # Vacío = cualquier correo puede registrarse.
    DOMINIOS_PERMITIDOS = [d.strip().lower() for d in
                           os.getenv("DOMINIO_PERMITIDO", "").split(",") if d.strip()]