-- ============================================================================
-- SIOAT · Sistema de Orientación para la Elección de Área Terminal
-- LGDN 2024 · Facultad de Contaduría y Administración · UV
-- MySQL 8.0+
-- ============================================================================

CREATE DATABASE IF NOT EXISTS sioat
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE sioat;

-- ---------------------------------------------------------------- personas
CREATE TABLE usuario (
  id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  matricula       VARCHAR(20)  NULL UNIQUE,      -- NULL para docentes
  nombre          VARCHAR(120) NOT NULL,
  correo          VARCHAR(160) NOT NULL UNIQUE,
  password_hash   VARCHAR(255) NOT NULL,
  rol             ENUM('estudiante','docente','admin') NOT NULL DEFAULT 'estudiante',
  periodo_cursado TINYINT UNSIGNED NULL,         -- en qué semestre va
  activo          BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ultimo_acceso   TIMESTAMP NULL,
  INDEX idx_rol (rol)
) ENGINE=InnoDB;

-- La fecha límite vive aquí, no en el código: el docente la mueve sin deploy.
CREATE TABLE aplicacion (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre        VARCHAR(80) NOT NULL,            -- "Feb-Jul 2026"
  fecha_inicio  DATETIME NOT NULL,
  fecha_limite  DATETIME NOT NULL,
  activa        BOOLEAN NOT NULL DEFAULT TRUE,
  creada_por    INT UNSIGNED NOT NULL,
  FOREIGN KEY (creada_por) REFERENCES usuario(id),
  CHECK (fecha_limite > fecha_inicio)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------- catálogos
CREATE TABLE academia (
  clave   CHAR(3) PRIMARY KEY,                   -- ADM, CYF, DER…
  nombre  VARCHAR(60) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE optativa (
  clave        VARCHAR(5) PRIMARY KEY,           -- EI, GA, PCE…
  nombre       VARCHAR(120) NOT NULL,
  academia     CHAR(3) NOT NULL,
  creditos     TINYINT UNSIGNED NOT NULL DEFAULT 6,
  idioma       CHAR(2) NOT NULL DEFAULT 'es',
  descripcion  TEXT NULL,
  FOREIGN KEY (academia) REFERENCES academia(clave)
) ENGINE=InnoDB;

-- Matriz de afinidad. Es una TABLA, no constantes en el código: las
-- coordinaciones de academia van a querer ajustarla y la validación
-- retrospectiva la va a recalibrar.
CREATE TABLE peso_academia_optativa (
  academia  CHAR(3)    NOT NULL,
  optativa  VARCHAR(5) NOT NULL,
  peso      DECIMAL(3,2) NOT NULL,
  PRIMARY KEY (academia, optativa),
  FOREIGN KEY (academia) REFERENCES academia(clave),
  FOREIGN KEY (optativa) REFERENCES optativa(clave),
  CHECK (peso BETWEEN 0 AND 1)
) ENGINE=InnoDB;

CREATE TABLE itinerario (
  id       TINYINT UNSIGNED PRIMARY KEY,
  nombre   VARCHAR(120) NOT NULL,
  nombre_en VARCHAR(120) NULL,
  perfil   TEXT NOT NULL,
  salidas  JSON NOT NULL
) ENGINE=InnoDB;

CREATE TABLE itinerario_optativa (
  itinerario TINYINT UNSIGNED NOT NULL,
  optativa   VARCHAR(5) NOT NULL,
  orden      TINYINT UNSIGNED NOT NULL,
  PRIMARY KEY (itinerario, optativa),
  FOREIGN KEY (itinerario) REFERENCES itinerario(id) ON DELETE CASCADE,
  FOREIGN KEY (optativa)  REFERENCES optativa(clave)
) ENGINE=InnoDB;

-- EE de los periodos I a V (fase 1)
CREATE TABLE ee_curricular (
  clave     VARCHAR(6) PRIMARY KEY,
  nombre    VARCHAR(120) NOT NULL,
  periodo   TINYINT UNSIGNED NOT NULL,
  academia  CHAR(3) NOT NULL,
  FOREIGN KEY (academia) REFERENCES academia(clave),
  INDEX idx_periodo (periodo)
) ENGINE=InnoDB;

CREATE TABLE reactivo (
  numero    TINYINT UNSIGNED PRIMARY KEY,
  enunciado VARCHAR(255) NOT NULL,
  en_breve  BOOLEAN NOT NULL DEFAULT FALSE       -- ¿entra en la versión corta?
) ENGINE=InnoDB;

CREATE TABLE opcion_reactivo (
  id        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  reactivo  TINYINT UNSIGNED NOT NULL,
  letra     CHAR(1) NOT NULL,
  texto     VARCHAR(255) NOT NULL,
  optativa  VARCHAR(5) NOT NULL,
  puntos    TINYINT UNSIGNED NOT NULL DEFAULT 3,
  UNIQUE KEY uq_reactivo_letra (reactivo, letra),
  FOREIGN KEY (reactivo) REFERENCES reactivo(numero) ON DELETE CASCADE,
  FOREIGN KEY (optativa) REFERENCES optativa(clave)
) ENGINE=InnoDB;

CREATE TABLE pregunta_contexto (
  numero    TINYINT UNSIGNED PRIMARY KEY,
  enunciado VARCHAR(255) NOT NULL,
  nota      VARCHAR(255) NULL                    -- advertencia que genera
) ENGINE=InnoDB;

CREATE TABLE opcion_contexto (
  id       INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  pregunta TINYINT UNSIGNED NOT NULL,
  letra    CHAR(1) NOT NULL,
  texto    VARCHAR(255) NOT NULL,
  ajustes  JSON NOT NULL,                        -- {"FCD": -5}
  UNIQUE KEY uq_pregunta_letra (pregunta, letra),
  FOREIGN KEY (pregunta) REFERENCES pregunta_contexto(numero) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------- sesiones
-- Una sesión por estudiante y aplicación. El progreso vive en las tablas de
-- respuesta: cada respuesta se escribe al momento, así que abandonar la
-- pestaña no pierde nada y no hace falta un botón de "guardar".
CREATE TABLE sesion (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  usuario       INT UNSIGNED NOT NULL,
  aplicacion    INT UNSIGNED NOT NULL,
  modo          ENUM('completo','breve') NOT NULL DEFAULT 'completo',
  estado        ENUM('en_progreso','completada','expirada') NOT NULL DEFAULT 'en_progreso',
  paso_actual   VARCHAR(20) NOT NULL DEFAULT 'fase0',   -- fase0 | f1-p3 | f2-r7 | fase3 | resultado
  ya_decidio    BOOLEAN NULL,                            -- respuesta de la fase 0
  itinerario_previo TINYINT UNSIGNED NULL,               -- lo que creía antes de contestar
  iniciada_en   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizada_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  completada_en TIMESTAMP NULL,
  UNIQUE KEY uq_usuario_aplicacion (usuario, aplicacion),
  FOREIGN KEY (usuario)    REFERENCES usuario(id) ON DELETE CASCADE,
  FOREIGN KEY (aplicacion) REFERENCES aplicacion(id),
  FOREIGN KEY (itinerario_previo) REFERENCES itinerario(id),
  INDEX idx_estado (aplicacion, estado)
) ENGINE=InnoDB;

CREATE TABLE respuesta_fase1 (
  sesion    INT UNSIGNED NOT NULL,
  periodo   TINYINT UNSIGNED NOT NULL,
  posicion  ENUM('fav1','fav2','fav3','rechazada') NOT NULL,
  ee        VARCHAR(6) NOT NULL,
  guardada_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (sesion, periodo, posicion),
  UNIQUE KEY uq_no_repetir_ee (sesion, periodo, ee),   -- no puede ser favorita y rechazada
  FOREIGN KEY (sesion) REFERENCES sesion(id) ON DELETE CASCADE,
  FOREIGN KEY (ee)     REFERENCES ee_curricular(clave)
) ENGINE=InnoDB;

CREATE TABLE respuesta_fase2 (
  sesion    INT UNSIGNED NOT NULL,
  reactivo  TINYINT UNSIGNED NOT NULL,
  opcion    INT UNSIGNED NOT NULL,
  guardada_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (sesion, reactivo),
  FOREIGN KEY (sesion)   REFERENCES sesion(id) ON DELETE CASCADE,
  FOREIGN KEY (reactivo) REFERENCES reactivo(numero),
  FOREIGN KEY (opcion)   REFERENCES opcion_reactivo(id)
) ENGINE=InnoDB;

CREATE TABLE respuesta_fase3 (
  sesion    INT UNSIGNED NOT NULL,
  pregunta  TINYINT UNSIGNED NOT NULL,
  opcion    INT UNSIGNED NOT NULL,
  guardada_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (sesion, pregunta),
  FOREIGN KEY (sesion)   REFERENCES sesion(id) ON DELETE CASCADE,
  FOREIGN KEY (pregunta) REFERENCES pregunta_contexto(numero),
  FOREIGN KEY (opcion)   REFERENCES opcion_contexto(id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------- resultados
-- Se congela el resultado al completar. Si mañana se recalibra la matriz,
-- el reporte que el estudiante ya vio no cambia bajo sus pies.
CREATE TABLE resultado (
  sesion            INT UNSIGNED PRIMARY KEY,
  calculado_en      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  version_matriz    VARCHAR(20) NOT NULL DEFAULT 'v2.0',
  itinerario        TINYINT UNSIGNED NULL,
  coincidencia      ENUM('exacta','parcial','ninguna') NOT NULL,
  materia_que_cambia VARCHAR(5) NULL,
  empate_tecnico    BOOLEAN NOT NULL DEFAULT FALSE,
  perfil_academias  JSON NOT NULL,
  explicacion       JSON NOT NULL,
  FOREIGN KEY (sesion)     REFERENCES sesion(id) ON DELETE CASCADE,
  FOREIGN KEY (itinerario) REFERENCES itinerario(id)
) ENGINE=InnoDB;

-- Una fila por optativa: esto es lo que alimenta el reporte de demanda.
CREATE TABLE resultado_optativa (
  sesion    INT UNSIGNED NOT NULL,
  optativa  VARCHAR(5) NOT NULL,
  posicion  TINYINT UNSIGNED NOT NULL,
  afinidad  DECIMAL(6,2) NOT NULL,
  indice    DECIMAL(5,1) NOT NULL,
  f1        DECIMAL(5,4) NOT NULL,
  f2        DECIMAL(5,4) NOT NULL,
  ajuste_f3 DECIMAL(4,1) NOT NULL DEFAULT 0,
  PRIMARY KEY (sesion, optativa),
  FOREIGN KEY (sesion)   REFERENCES resultado(sesion) ON DELETE CASCADE,
  FOREIGN KEY (optativa) REFERENCES optativa(clave),
  INDEX idx_demanda (optativa, posicion)
) ENGINE=InnoDB;

-- Oferta real por periodo. Sin esto el sistema recomienda materias que
-- Escolar no va a abrir.
CREATE TABLE oferta (
  aplicacion INT UNSIGNED NOT NULL,
  optativa   VARCHAR(5) NOT NULL,
  se_abre    BOOLEAN NOT NULL DEFAULT TRUE,
  cupo       SMALLINT UNSIGNED NULL,
  PRIMARY KEY (aplicacion, optativa),
  FOREIGN KEY (aplicacion) REFERENCES aplicacion(id) ON DELETE CASCADE,
  FOREIGN KEY (optativa)   REFERENCES optativa(clave)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------- reportes
-- LA consulta que justifica todo el sistema: cuánta demanda tiene cada
-- optativa, para decidir qué abrir el próximo semestre.
CREATE OR REPLACE VIEW v_demanda_optativa AS
SELECT
  s.aplicacion,
  o.clave,
  o.nombre,
  o.academia,
  SUM(ro.posicion = 1)                AS primera_opcion,
  SUM(ro.posicion <= 3)               AS en_top3,
  SUM(ro.posicion BETWEEN 4 AND 5)    AS como_respaldo,
  ROUND(AVG(ro.indice), 1)            AS indice_promedio,
  COALESCE(of.se_abre, TRUE)          AS se_abre,
  of.cupo
FROM resultado_optativa ro
JOIN resultado  r ON r.sesion = ro.sesion
JOIN sesion     s ON s.id = ro.sesion
JOIN optativa   o ON o.clave = ro.optativa
LEFT JOIN oferta of ON of.aplicacion = s.aplicacion AND of.optativa = o.clave
WHERE s.estado = 'completada'
GROUP BY s.aplicacion, o.clave, o.nombre, o.academia, of.se_abre, of.cupo;

CREATE OR REPLACE VIEW v_avance_aplicacion AS
SELECT
  a.id AS aplicacion,
  a.nombre,
  a.fecha_limite,
  COUNT(s.id)                                       AS sesiones,
  SUM(s.estado = 'completada')                      AS completadas,
  SUM(s.estado = 'en_progreso')                     AS en_progreso,
  SUM(s.estado = 'expirada')                        AS expiradas,
  ROUND(100 * SUM(s.estado='completada') / NULLIF(COUNT(s.id),0), 1) AS pct_completado
FROM aplicacion a
LEFT JOIN sesion s ON s.aplicacion = a.id
GROUP BY a.id, a.nombre, a.fecha_limite;

-- Concordancia entre lo que el estudiante creía y lo que salió.
-- Es la métrica que mide si la fase 0 estaba sirviendo de algo.
CREATE OR REPLACE VIEW v_concordancia_decision_previa AS
SELECT
  s.aplicacion,
  s.ya_decidio,
  COUNT(*) AS n,
  SUM(s.itinerario_previo = r.itinerario) AS coincidieron
FROM sesion s
JOIN resultado r ON r.sesion = s.id
WHERE s.itinerario_previo IS NOT NULL
GROUP BY s.aplicacion, s.ya_decidio;
