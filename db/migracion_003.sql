-- ============================================================================
-- SIOAT · migración 003
-- Sección del estudiante + gestión de cuentas
--
--     mysql -u sioat -p sioat < db/migracion_003.sql
-- ============================================================================
USE sioat;

-- La sección es como la coordinación ubica físicamente a un alumno: qué grupo,
-- con qué tutor, en qué horario. Sin ella el padrón sirve para contar pero no
-- para ir a buscar a alguien.
ALTER TABLE usuario
  ADD COLUMN seccion VARCHAR(10) NULL AFTER periodo_cursado,
  ADD INDEX idx_seccion (seccion);

-- Vista de avance por sección: sirve para saber a qué grupo hay que ir a
-- insistirle antes de que cierre la fecha.
CREATE OR REPLACE VIEW v_avance_seccion AS
SELECT
  s.aplicacion,
  COALESCE(u.seccion, 'Sin sección')            AS seccion,
  COUNT(*)                                      AS alumnos,
  SUM(s.estado = 'completada')                  AS terminaron,
  SUM(s.estado = 'en_progreso')                 AS a_medias,
  SUM(s.modo = 'eleccion_directa')              AS eleccion_directa,
  ROUND(100 * SUM(s.estado='completada') / NULLIF(COUNT(*),0), 1) AS pct
FROM sesion s
JOIN usuario u ON u.id = s.usuario
WHERE u.rol = 'estudiante'
GROUP BY s.aplicacion, COALESCE(u.seccion, 'Sin sección');
