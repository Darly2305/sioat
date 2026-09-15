from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .config import Config
from .models import db

jwt = JWTManager()


def crear_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
         supports_credentials=True)

    from .api.auth import bp as bp_auth
    from .api.cuestionario import bp as bp_cuest
    from .api.docente import bp as bp_doc
    app.register_blueprint(bp_auth, url_prefix="/api/auth")
    app.register_blueprint(bp_cuest, url_prefix="/api")
    app.register_blueprint(bp_doc, url_prefix="/api/docente")

    @app.get("/api/salud")
    def salud():
        return {"ok": True}

    @app.errorhandler(404)
    def no_existe(_):
        return jsonify(error="No encontramos esa ruta."), 404

    @app.errorhandler(500)
    def falla(_):
        db.session.rollback()
        return jsonify(error="Algo falló de nuestro lado. Vuelve a intentarlo."), 500

    # La matriz de afinidad vive en la base para que las academias la puedan
    # ajustar sin un deploy. Al arrancar se carga sobre el motor.
    with app.app_context():
        try:
            from .api.cuestionario import cargar_pesos_desde_db
            cargar_pesos_desde_db()
        except Exception as e:      # base vacía todavía: se usan los de datos.py
            app.logger.warning("Matriz no cargada desde BD (%s). Usando datos.py", e)

    return app
