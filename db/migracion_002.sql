-- ============================================================================
-- SIOAT · migración 002
-- De "ranking de optativas sueltas" a "bloques cerrados de área terminal"
--
-- Aplicar sobre una base que ya tiene schema.sql corrido:
--     mysql -u sioat -p sioat < db/migracion_002.sql
-- Después, volver a correr:  python seed.py
--
-- Para una instalación nueva NO hace falta: schema.sql ya viene actualizado.
-- ============================================================================
USE sioat;

-- ── 1. El bloque necesita su frase de identidad ─────────────────────────────
-- Es lo que encabeza el reporte del estudiante: "vas a ser un gestor
-- especializado en...". Sin ella el resultado vuelve a ser un porcentaje.
ALTER TABLE itinerario
  ADD COLUMN frase   VARCHAR(160) NOT NULL DEFAULT '' AFTER nombre_en,
  ADD COLUMN resumen VARCHAR(255) NOT NULL DEFAULT '' AFTER frase;

-- ── 2. Elección directa: contestar "ya sé cuál quiero" termina el flujo ─────
ALTER TABLE sesion
  MODIFY COLUMN modo ENUM('completo','breve','eleccion_directa')
    NOT NULL DEFAULT 'completo',
  ADD COLUMN itinerario_elegido TINYINT UNSIGNED NULL AFTER itinerario_previo,
  ADD CONSTRAINT fk_sesion_elegido
    FOREIGN KEY (itinerario_elegido) REFERENCES itinerario(id);

-- ── 3. El resultado ya no es una coincidencia parcial con un bloque ─────────
-- Antes el sistema entregaba tres optativas sueltas y medía qué tan cerca
-- quedaban de un bloque. Ahora entrega el bloque directamente, así que
-- 'coincidencia' y 'materia_que_cambia' dejan de tener sentido.
ALTER TABLE resultado
  DROP COLUMN coincidencia,
  DROP COLUMN materia_que_cambia,
  ADD COLUMN perfil_plano    BOOLEAN NOT NULL DEFAULT FALSE AFTER empate_tecnico,
  ADD COLUMN optativa_debil  VARCHAR(5) NULL AFTER perfil_plano,
  ADD COLUMN pos_debil       TINYINT UNSIGNED NULL AFTER optativa_debil,
  ADD CONSTRAINT fk_resultado_debil
    FOREIGN KEY (optativa_debil) REFERENCES optativa(clave);

-- ── 4. Ranking de los 13 bloques, uno por sesión ────────────────────────────
CREATE TABLE IF NOT EXISTS resultado_itinerario (
  sesion      INT UNSIGNED NOT NULL,
  itinerario  TINYINT UNSIGNED NOT NULL,
  posicion    TINYINT UNSIGNED NOT NULL,
  score       DECIMAL(6,2) NOT NULL,
  indice      DECIMAL(5,1) NOT NULL,
  media       DECIMAL(6,2) NOT NULL,
  peor        DECIMAL(6,2) NOT NULL,
  PRIMARY KEY (sesion, itinerario),
  FOREIGN KEY (sesion)     REFERENCES resultado(sesion) ON DELETE CASCADE,
  FOREIGN KEY (itinerario) REFERENCES itinerario(id),
  INDEX idx_demanda_bloque (itinerario, posicion)
) ENGINE=InnoDB;

-- ── 5. Vistas de demanda, reescritas ────────────────────────────────────────
-- El bloque asignado tiene dos orígenes y los dos cuentan igual para la
-- coordinación: el que lo eligió directo y el que salió del cuestionario.
-- Si sólo contáramos el segundo, la demanda quedaría incompleta.
CREATE OR REPLACE VIEW v_bloque_asignado AS
SELECT
  s.id          AS sesion,
  s.aplicacion,
  s.usuario,
  COALESCE(s.itinerario_elegido, r.itinerario) AS itinerario,
  CASE WHEN s.itinerario_elegido IS NOT NULL
       THEN 'eleccion_directa' ELSE 'cuestionario' END AS origen
FROM sesion s
LEFT JOIN resultado r ON r.sesion = s.id
WHERE s.estado = 'completada'
  AND COALESCE(s.itinerario_elegido, r.itinerario) IS NOT NULL;

CREATE OR REPLACE VIEW v_demanda_bloque AS
SELECT
  ba.aplicacion,
  i.id,
  i.nombre,
  i.frase,
  COUNT(*)                                     AS alumnos,
  SUM(ba.origen = 'eleccion_directa')          AS eligieron_directo,
  SUM(ba.origen = 'cuestionario')              AS por_cuestionario
FROM v_bloque_asignado ba
JOIN itinerario i ON i.id = ba.itinerario
GROUP BY ba.aplicacion, i.id, i.nombre, i.frase;

-- Cuántos alumnos van a necesitar cada optativa. Ya no se cuenta "cuántos la
-- pusieron en su top 3": se cuenta cuántos quedaron en un bloque que la
-- contiene, porque los bloques son cerrados y esa es la matrícula real.
CREATE OR REPLACE VIEW v_demanda_optativa AS
SELECT
  ba.aplicacion,
  o.clave,
  o.nombre,
  o.academia,
  COUNT(DISTINCT ba.sesion)                 AS alumnos,
  COUNT(DISTINCT io.itinerario)             AS bloques_que_la_piden,
  COALESCE(ofe.se_abre, TRUE)               AS se_abre,
  ofe.cupo,
  CASE WHEN ofe.cupo IS NOT NULL AND COUNT(DISTINCT ba.sesion) > ofe.cupo
       THEN CEIL(COUNT(DISTINCT ba.sesion) / ofe.cupo) ELSE 1 END AS grupos_necesarios
FROM v_bloque_asignado ba
JOIN itinerario_optativa io ON io.itinerario = ba.itinerario
JOIN optativa o             ON o.clave = io.optativa
LEFT JOIN oferta ofe        ON ofe.aplicacion = ba.aplicacion AND ofe.optativa = o.clave
GROUP BY ba.aplicacion, o.clave, o.nombre, o.academia, ofe.se_abre, ofe.cupo;

-- Concordancia: de los que dijeron "ya sé cuál quiero", ¿el cuestionario les
-- habría dado lo mismo? Es la métrica que dice si la fase 0 sirve de algo.
CREATE OR REPLACE VIEW v_concordancia_decision_previa AS
SELECT
  s.aplicacion,
  s.modo,
  COUNT(*)                                          AS n,
  SUM(s.itinerario_previo = r.itinerario)           AS coincidieron
FROM sesion s
JOIN resultado r ON r.sesion = s.id
WHERE s.itinerario_previo IS NOT NULL
GROUP BY s.aplicacion, s.modo;
