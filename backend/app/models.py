"""
Modelos mapeados contra db/schema.sql. El esquema SQL es la fuente de verdad:
estas clases sólo lo reflejan. Si cambias una tabla, cambia primero el .sql.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Usuario(db.Model):
    __tablename__ = "usuario"
    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(20), unique=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum("estudiante", "docente", "admin"), default="estudiante")
    periodo_cursado = db.Column(db.SmallInteger)
    seccion = db.Column(db.String(10))
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)

    def publico(self):
        return {"id": self.id, "nombre": self.nombre, "correo": self.correo,
                "matricula": self.matricula, "rol": self.rol,
                "periodo_cursado": self.periodo_cursado, "seccion": self.seccion}


class Aplicacion(db.Model):
    __tablename__ = "aplicacion"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_limite = db.Column(db.DateTime, nullable=False)
    activa = db.Column(db.Boolean, default=True)
    creada_por = db.Column(db.Integer, db.ForeignKey("usuario.id"))

    @property
    def vencida(self):
        return datetime.now() > self.fecha_limite

    def publico(self):
        return {"id": self.id, "nombre": self.nombre,
                "fecha_limite": self.fecha_limite.isoformat(),
                "vencida": self.vencida}


class Academia(db.Model):
    __tablename__ = "academia"
    clave = db.Column(db.String(3), primary_key=True)
    nombre = db.Column(db.String(60), nullable=False)


class Optativa(db.Model):
    __tablename__ = "optativa"
    clave = db.Column(db.String(5), primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    academia = db.Column(db.String(3), db.ForeignKey("academia.clave"))
    creditos = db.Column(db.SmallInteger, default=6)
    idioma = db.Column(db.String(2), default="es")
    descripcion = db.Column(db.Text)


class PesoAcademiaOptativa(db.Model):
    __tablename__ = "peso_academia_optativa"
    academia = db.Column(db.String(3), db.ForeignKey("academia.clave"), primary_key=True)
    optativa = db.Column(db.String(5), db.ForeignKey("optativa.clave"), primary_key=True)
    peso = db.Column(db.Numeric(3, 2), nullable=False)


class Itinerario(db.Model):
    __tablename__ = "itinerario"
    id = db.Column(db.SmallInteger, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    nombre_en = db.Column(db.String(120))
    frase = db.Column(db.String(160), nullable=False)      # "gestor especializado en..."
    resumen = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.Text, nullable=False)
    salidas = db.Column(db.JSON, nullable=False)

    def publico(self, con_perfil=True):
        d = {"id": self.id, "nombre": self.nombre, "frase": self.frase,
             "resumen": self.resumen}
        if con_perfil:
            d.update(perfil=self.perfil, salidas=self.salidas)
        return d


class ItinerarioOptativa(db.Model):
    __tablename__ = "itinerario_optativa"
    itinerario = db.Column(db.SmallInteger, db.ForeignKey("itinerario.id"), primary_key=True)
    optativa = db.Column(db.String(5), db.ForeignKey("optativa.clave"), primary_key=True)
    orden = db.Column(db.SmallInteger, nullable=False)


class EECurricular(db.Model):
    __tablename__ = "ee_curricular"
    clave = db.Column(db.String(6), primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    periodo = db.Column(db.SmallInteger, nullable=False)
    academia = db.Column(db.String(3), db.ForeignKey("academia.clave"))


class Reactivo(db.Model):
    __tablename__ = "reactivo"
    numero = db.Column(db.SmallInteger, primary_key=True)
    enunciado = db.Column(db.String(255), nullable=False)
    en_breve = db.Column(db.Boolean, default=False)


class OpcionReactivo(db.Model):
    __tablename__ = "opcion_reactivo"
    id = db.Column(db.Integer, primary_key=True)
    reactivo = db.Column(db.SmallInteger, db.ForeignKey("reactivo.numero"))
    letra = db.Column(db.String(1), nullable=False)
    texto = db.Column(db.String(255), nullable=False)
    optativa = db.Column(db.String(5), db.ForeignKey("optativa.clave"))
    puntos = db.Column(db.SmallInteger, default=3)


class PreguntaContexto(db.Model):
    __tablename__ = "pregunta_contexto"
    numero = db.Column(db.SmallInteger, primary_key=True)
    enunciado = db.Column(db.String(255), nullable=False)
    nota = db.Column(db.String(255))


class OpcionContexto(db.Model):
    __tablename__ = "opcion_contexto"
    id = db.Column(db.Integer, primary_key=True)
    pregunta = db.Column(db.SmallInteger, db.ForeignKey("pregunta_contexto.numero"))
    letra = db.Column(db.String(1), nullable=False)
    texto = db.Column(db.String(255), nullable=False)
    ajustes = db.Column(db.JSON, nullable=False)


class Sesion(db.Model):
    __tablename__ = "sesion"
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    aplicacion = db.Column(db.Integer, db.ForeignKey("aplicacion.id"), nullable=False)
    modo = db.Column(db.Enum("completo", "breve", "eleccion_directa"), default="completo")
    estado = db.Column(db.Enum("en_progreso", "completada", "expirada"), default="en_progreso")
    paso_actual = db.Column(db.String(20), default="fase0")
    ya_decidio = db.Column(db.Boolean)
    itinerario_previo = db.Column(db.SmallInteger, db.ForeignKey("itinerario.id"))
    itinerario_elegido = db.Column(db.SmallInteger, db.ForeignKey("itinerario.id"))
    iniciada_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizada_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completada_en = db.Column(db.DateTime)
    eleccion_en = db.Column(db.DateTime)
    veces_cambiada = db.Column(db.SmallInteger, default=0)


class RespuestaFase1(db.Model):
    __tablename__ = "respuesta_fase1"
    sesion = db.Column(db.Integer, db.ForeignKey("sesion.id"), primary_key=True)
    periodo = db.Column(db.SmallInteger, primary_key=True)
    posicion = db.Column(db.Enum("fav1", "fav2", "fav3", "rechazada"), primary_key=True)
    ee = db.Column(db.String(6), db.ForeignKey("ee_curricular.clave"), nullable=False)


class RespuestaFase2(db.Model):
    __tablename__ = "respuesta_fase2"
    sesion = db.Column(db.Integer, db.ForeignKey("sesion.id"), primary_key=True)
    reactivo = db.Column(db.SmallInteger, db.ForeignKey("reactivo.numero"), primary_key=True)
    opcion = db.Column(db.Integer, db.ForeignKey("opcion_reactivo.id"), nullable=False)


class RespuestaFase3(db.Model):
    __tablename__ = "respuesta_fase3"
    sesion = db.Column(db.Integer, db.ForeignKey("sesion.id"), primary_key=True)
    pregunta = db.Column(db.SmallInteger, db.ForeignKey("pregunta_contexto.numero"), primary_key=True)
    opcion = db.Column(db.Integer, db.ForeignKey("opcion_contexto.id"), nullable=False)


class Resultado(db.Model):
    __tablename__ = "resultado"
    sesion = db.Column(db.Integer, db.ForeignKey("sesion.id"), primary_key=True)
    calculado_en = db.Column(db.DateTime, default=datetime.utcnow)
    version_matriz = db.Column(db.String(20), default="v2.0")
    itinerario = db.Column(db.SmallInteger, db.ForeignKey("itinerario.id"))
    empate_tecnico = db.Column(db.Boolean, default=False)
    perfil_plano = db.Column(db.Boolean, default=False)
    optativa_debil = db.Column(db.String(5), db.ForeignKey("optativa.clave"))
    pos_debil = db.Column(db.SmallInteger)
    perfil_academias = db.Column(db.JSON, nullable=False)
    explicacion = db.Column(db.JSON, nullable=False)


class ResultadoOptativa(db.Model):
    __tablename__ = "resultado_optativa"
    sesion = db.Column(db.Integer, db.ForeignKey("resultado.sesion"), primary_key=True)
    optativa = db.Column(db.String(5), db.ForeignKey("optativa.clave"), primary_key=True)
    posicion = db.Column(db.SmallInteger, nullable=False)
    afinidad = db.Column(db.Numeric(6, 2), nullable=False)
    indice = db.Column(db.Numeric(5, 1), nullable=False)
    f1 = db.Column(db.Numeric(5, 4), nullable=False)
    f2 = db.Column(db.Numeric(5, 4), nullable=False)
    ajuste_f3 = db.Column(db.Numeric(4, 1), default=0)


class ResultadoItinerario(db.Model):
    """Ranking de los 13 bloques para una sesión. Es lo que el estudiante ve."""
    __tablename__ = "resultado_itinerario"
    sesion = db.Column(db.Integer, db.ForeignKey("resultado.sesion"), primary_key=True)
    itinerario = db.Column(db.SmallInteger, db.ForeignKey("itinerario.id"), primary_key=True)
    posicion = db.Column(db.SmallInteger, nullable=False)
    score = db.Column(db.Numeric(6, 2), nullable=False)
    indice = db.Column(db.Numeric(5, 1), nullable=False)
    media = db.Column(db.Numeric(6, 2), nullable=False)
    peor = db.Column(db.Numeric(6, 2), nullable=False)


class Oferta(db.Model):
    __tablename__ = "oferta"
    aplicacion = db.Column(db.Integer, db.ForeignKey("aplicacion.id"), primary_key=True)
    optativa = db.Column(db.String(5), db.ForeignKey("optativa.clave"), primary_key=True)
    se_abre = db.Column(db.Boolean, default=True)
    cupo = db.Column(db.Integer)