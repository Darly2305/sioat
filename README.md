# SIOAT

Sistema de Orientación para la Elección de Área Terminal
LGDN 2024 · Facultad de Contaduría y Administración · Universidad Veracruzana

El estudiante contesta un cuestionario de tres fases y el sistema ordena las
quince optativas del Área de Formación Terminal por afinidad. El docente ve la
demanda agregada y decide qué optativas abrir el siguiente periodo.

---

## Estructura

```
sioat/
├── backend/
│   ├── wsgi.py                    punto de entrada de Flask
│   ├── seed.py                    carga catálogos y crea la aplicación activa
│   ├── cuenta.py                  gestión de cuentas desde la terminal
│   ├── Procfile                   comando de arranque en producción
│   ├── requirements.txt
│   ├── .env.example               copiar a .env y llenar
│   ├── app/
│   │   ├── __init__.py            app factory: blueprints, JWT, CORS
│   │   ├── config.py              lee variables de entorno
│   │   ├── models.py              modelos SQLAlchemy (espejo de schema.sql)
│   │   ├── motor/
│   │   │   ├── datos.py           15 optativas, matriz, 15 reactivos, 12 itinerarios
│   │   │   └── puntuacion.py      el algoritmo. Sin Flask, sin base de datos.
│   │   └── api/
│   │       ├── auth.py            registro, login, JWT
│   │       ├── cuestionario.py    catálogo, sesión, autoguardado, entrega
│   │       └── docente.py         demanda, avance, concordancia, oferta
│   └── tests/
│       └── calibrar.py            corre perfiles sintéticos contra el motor
├── docs/
│   └── SIOAT_Documento_de_Diseno_v3.1.docx
├── db/
│   ├── schema.sql                 fuente de verdad del esquema
│   ├── migracion_002.sql          de optativas sueltas a bloques cerrados
│   └── migracion_003.sql          sección del estudiante y cuentas
└── frontend/
    ├── package.json · vite.config.js · tailwind.config.js · index.html
    └── src/
        ├── main.jsx · App.jsx     router y providers
        ├── api.js                 cliente HTTP + cola de autoguardado
        ├── auth.jsx               contexto de sesión
        ├── tema.js                paleta e iconos por bloque
        └── pages/
            ├── Login.jsx
            ├── Cuestionario.jsx   el flujo del estudiante, conectado al API
            └── Docente.jsx        panel de demanda
```

---

## Requisitos

- Python 3.10 o superior
- Node 18 o superior
- MySQL 8.0 o superior

---

## Instalación

### 1. Base de datos

```bash
mysql -u root -p
```

```sql
CREATE USER 'sioat'@'localhost' IDENTIFIED BY 'tu_password';
CREATE DATABASE sioat CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
GRANT ALL PRIVILEGES ON sioat.* TO 'sioat'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

```bash
mysql -u sioat -p sioat < db/schema.sql
```

Si ya tenías la base creada con la versión anterior, no la borres: aplica la
migración y vuelve a sembrar.

```bash
mysql -u sioat -p sioat < db/migracion_002.sql
mysql -u sioat -p sioat < db/migracion_003.sql
cd backend && python seed.py
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # Windows: copy .env.example .env
```

Abre `.env` y pon tu `DB_PASS`. Para las llaves secretas:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Carga los catálogos y arranca:

```bash
python seed.py --docente
python wsgi.py
```

Queda en `http://127.0.0.1:5000`. Verifica con `curl http://127.0.0.1:5000/api/salud`.

El seed crea dos cuentas de prueba con contraseñas conocidas y públicas.
**Cámbialas antes de que esto toque un servidor.**

| Cuenta | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@sioat.local` | `admin12345` |
| Docente | `docente@sioat.local` | `docente12345` |

---

## Cuentas: correo, contraseña y altas

Hay dos caminos. El normal es la pestaña **Cuenta** del panel:

- Cualquier docente o administrador cambia ahí su propio nombre, correo y
  contraseña. El cambio de contraseña pide la actual a propósito: si alguien
  deja la sesión abierta en un laboratorio, que no pueda dejar fuera al dueño.
- El administrador además da de alta cuentas, cambia roles, desactiva y
  restablece contraseñas de terceros.

El segundo camino es la terminal, para cuando nadie puede entrar al panel:

```bash
cd backend && source .venv/bin/activate

python cuenta.py listar                                  # ver qué cuentas existen
python cuenta.py password admin@sioat.local              # cambiar contraseña
python cuenta.py correo admin@sioat.local coord@uv.mx    # cambiar correo
python cuenta.py crear "Ana Docente" ana@uv.mx docente   # alta
python cuenta.py rol ana@uv.mx admin                     # cambiar rol
python cuenta.py desactivar ana@uv.mx
```

Las contraseñas se piden por `getpass`, así que no quedan en el historial de la
terminal. Se entregan en persona: el sistema no tiene servidor de correo, y una
contraseña en un buzón institucional compartido no es una contraseña.

Las cuentas se **desactivan**, no se borran. Un docente eliminado dejaría
huérfanas las aplicaciones que creó.

### 3. Frontend

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Queda en `http://localhost:5173`. Vite reenvía `/api` a Flask, así que en
desarrollo no hay que pelearse con CORS.

---

## Probar el motor sin levantar nada

```bash
cd backend
python tests/calibrar.py
```

Corre siete perfiles sintéticos y muestra qué recomienda a cada uno y cuántas
veces aparece cada optativa. Es la forma rápida de ver el efecto de cualquier
ajuste a la matriz de afinidad.

---

## Cómo funcionan las piezas menos obvias

**El autoguardado no tiene botón.** Cada respuesta se escribe como una fila en
`respuesta_fase1/2/3` en el momento en que el estudiante toca la opción. La
llave primaria compuesta `(sesion, reactivo)` hace que volver a contestar
sobrescriba en lugar de duplicar. Si la red falla, `crearCola()` en `api.js`
reintenta sin bloquear al estudiante.

**La fecha límite vive en la tabla `aplicacion`.** El docente la mueve sin
necesidad de un deploy. Al pasarse, las sesiones en progreso se marcan
`expirada` y los endpoints de escritura dejan de aceptar respuestas.

**La matriz de afinidad vive en `peso_academia_optativa`, no en el código.**
`datos.py` es sólo la semilla. Al arrancar, `cargar_pesos_desde_db()` sobrescribe
los valores del motor con los de la base, para que las coordinaciones de academia
puedan ajustarlos sin tocar Python.

**El cálculo es del servidor, nunca del navegador.** El endpoint `/api/catalogo`
manda preguntas y opciones pero no manda los pesos. Si el estudiante pudiera
leerlos desde el bundle, podría contestar para caer donde quisiera.

**El cuestionario no permite regresar.** Elegida una opción, la pantalla avanza
y no hay vuelta atrás. Un toque equivocado queda registrado, y eso pesa sobre
todo en la fase 1, donde el estudiante señala su primera, segunda y tercera
favorita en secuencia; por eso la pantalla de entrada a esa fase lo advierte.
Si al aplicarlo aparecen respuestas claramente erróneas, la salida menos
invasiva es permitir deseleccionar dentro de la misma pregunta, sin rehabilitar
la navegación hacia atrás.

**La sección es cómo se ubica físicamente a un alumno.** La matrícula sirve
para identificarlo y cruzar con Escolar; la sección dice a qué grupo pertenece,
con qué tutor y en qué horario. Por eso el padrón se ordena por sección y luego
por matrícula, y el resumen trae una tabla de avance por sección: es la que dice
a qué grupo hay que ir a insistirle antes de que cierre la fecha.

**El resultado es un bloque, nunca optativas sueltas.** Tres materias sin
relación no hacen a un especialista en nada. El motor sigue calculando el
ranking individual de las 15 optativas —lo necesita para puntuar bloques y es
diagnóstico útil para la coordinación— pero el estudiante recibe un bloque y su
frase de identidad. El bloque se puntúa con `0.6 × promedio + 0.4 × la peor de
las tres`, para que no gane uno con dos materias excelentes y una pésima.

**El resultado se congela al entregar**, con su `version_matriz`. Si el semestre
que entra se recalibra la matriz, el reporte que el estudiante ya vio no cambia
debajo de él.

---

## Endpoints

| Método | Ruta | Quién |
|---|---|---|
| POST | `/api/auth/registro` | público |
| POST | `/api/auth/login` | público |
| GET | `/api/auth/yo` | autenticado |
| PUT | `/api/auth/perfil` | autenticado |
| PUT | `/api/auth/password` | autenticado |
| GET | `/api/catalogo` | estudiante |
| GET | `/api/sesion` | estudiante |
| PUT | `/api/sesion/respuesta` | estudiante |
| POST | `/api/sesion/completar` | estudiante |
| POST | `/api/sesion/elegir-bloque` | estudiante |
| GET | `/api/sesion/resultado` | estudiante |
| GET | `/api/docente/resumen` | docente |
| GET | `/api/docente/padron` | docente |
| GET | `/api/docente/padron.csv` | docente |
| GET | `/api/docente/sin_definir` | docente |
| GET | `/api/docente/concordancia` | docente |
| GET | `/api/docente/oferta` | docente |
| PUT | `/api/docente/oferta` | **admin** |
| PUT | `/api/docente/aplicacion` | **admin** |
| GET | `/api/docente/usuarios` | **admin** |
| POST | `/api/docente/usuarios` | **admin** |
| PUT | `/api/docente/usuarios/:id` | **admin** |

El docente consulta; el administrador cambia el estado del sistema. Separarlos
importa porque un cambio de oferta a media aplicación altera lo que todos los
alumnos ven en su resultado.

---

## Publicarlo en internet

Tres servicios, todos con capa gratuita real y **sin tarjeta de crédito**:

| Pieza | Servicio | Qué da gratis |
|---|---|---|
| Base de datos | **Aiven for MySQL** | 1 GB de almacenamiento, 1 GB de RAM, siempre encendida |
| Backend | **Render** | 750 horas de cómputo al mes, HTTPS, despliegue desde Git |
| Frontend | **Netlify** | Sitio estático ilimitado, HTTPS, dominio propio |

Aiven es la pieza clave: es de los pocos que todavía regala **MySQL** de verdad.
PythonAnywhere lo quitó de su plan gratuito para cuentas nuevas en enero de 2026,
y Render sólo ofrece PostgreSQL y encima expira a los 30 días.

### 1. Base de datos en Aiven

1. Entra a `aiven.io`, crea cuenta y elige *Create service → MySQL → Free plan*.
   Selecciona la región más cercana a México.
2. Cuando el servicio quede en *Running*, abre su pestaña *Overview* y anota
   **Host**, **Port**, **User**, **Password** y **Database name**.
3. Descarga el **CA Certificate** (`ca.pem`) desde esa misma pantalla. Lo vas a
   necesitar: Aiven obliga a TLS con su propia autoridad certificadora, que no
   está en el almacén del sistema.
4. Desde tu máquina, carga el esquema:

   ```bash
   mysql -h <host> -P <puerto> -u avnadmin -p \
         --ssl-ca=ca.pem <base> < db/schema.sql
   ```

### 2. Backend en Render

1. Sube el repositorio a GitHub. Antes verifica con `git status` que
   `backend/.env` **no** aparece; el `.gitignore` ya lo excluye.
2. En Render, *New → Web Service*, conecta el repo.
3. Configura:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60`
   - **Instance Type**: Free
4. En *Environment*, carga:

   ```
   SECRET_KEY=<cadena larga aleatoria>
   JWT_SECRET_KEY=<otra distinta>
   DB_HOST=<host de Aiven>
   DB_PORT=<puerto de Aiven>
   DB_USER=avnadmin
   DB_PASS=<password de Aiven>
   DB_NAME=<base de Aiven>
   DB_SSL_CA_CONTENT=<pega aquí el contenido completo del ca.pem>
   CORS_ORIGINS=https://tu-sitio.netlify.app
   DOMINIO_PERMITIDO=@uv.mx
   ```

   Genera cada llave con `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
   El `ca.pem` se pega tal cual, con sus líneas `BEGIN` y `END`. El certificado
   es público, no es un secreto: lo que se protege es la contraseña.
5. Siembra los catálogos desde la *Shell* del servicio en Render:
   `python seed.py`
6. Prueba `https://tu-backend.onrender.com/api/salud`. Debe devolver `{"ok": true}`.

### 3. Frontend en Netlify

1. *Add new site → Import from Git*, mismo repo.
2. **Base directory** `frontend`, **Build command** `npm run build`,
   **Publish directory** `frontend/dist`.
3. En *Environment variables*:

   ```
   VITE_API_URL=https://tu-backend.onrender.com/api
   ```

   Se lee **al compilar**, no al cargar la página: si la cambias, hay que volver
   a desplegar.
4. El archivo `frontend/public/_redirects` ya está en el repo. Es lo que hace que
   entrar directo a `/panel` no devuelva 404.

### El problema del arranque en frío

El plan gratuito de Render **apaga el servicio tras 15 minutos sin tráfico**, y
despertarlo tarda entre 30 y 60 segundos. El primer alumno del día se queda
mirando una pantalla de carga larguísima.

La interfaz ya lo maneja: a los 4 segundos aparece *«Despertando el servidor…»*
con la explicación. Pero lo que conviene es que no pase.

La solución práctica es mantenerlo despierto durante el periodo de aplicación
con un ping externo. Date de alta en `cron-job.org` o `UptimeRobot` (gratis) y
programa una llamada a `https://tu-backend.onrender.com/api/salud` cada 10
minutos. El plan gratuito da 750 horas al mes y un mes tiene 744, así que un
solo servicio encendido de forma continua cabe dentro de la cuota.

Dicho con honestidad: Render considera esto un rodeo, no una función soportada,
y podría cerrarlo. Si el sistema se vuelve algo que la Facultad usa cada
semestre, los 7 USD al mes del plan de pago son la respuesta limpia.

### Antes de darle la URL a los alumnos

- Cambia las contraseñas de `admin@sioat.local` y `docente@sioat.local`, o
  bórralas y crea las reales con `python cuenta.py crear`. Están escritas en
  este README, o sea que son públicas.
- Pon `DOMINIO_PERMITIDO=@uv.mx` para que sólo se registre gente de la
  Universidad.
- Verifica que `CORS_ORIGINS` sea exactamente la URL de Netlify, sin diagonal
  final. Si no coincide, el navegador bloquea todas las llamadas y la pantalla
  se queda cargando sin ningún mensaje que explique por qué.
- Ajusta la fecha límite desde el panel antes de anunciar nada.
- Prueba el flujo completo con una cuenta de estudiante de mentiras.

### Si alguna de las tres se acaba

Las capas gratuitas cambian seguido. Equivalentes al día de hoy:

| En lugar de | Sirve |
|---|---|
| Aiven MySQL | **TiDB Cloud Starter** (compatible con MySQL, 5 GB, sin tarjeta) |
| Render | **Koyeb** (un servicio web gratis, sin tarjeta) o **Fly.io** (pide tarjeta) |
| Netlify | **Vercel** o **Cloudflare Pages** |

Y si la Facultad tiene servidor propio y prefiere que los datos no salgan de la
Universidad, el despliegue es nginx + gunicorn + MySQL ahí mismo. Conviene
consultarlo con el área de cómputo antes de empezar, porque el trámite suele
tardar más que la instalación.

---

## Lo que falta

1. **Recuperación de contraseña.** No existe todavía.
2. **Alta masiva de alumnos** desde un CSV de Escolar con matrícula y sección,
   para que no tengan que registrarse uno por uno.
3. **Consultar a Secretaría Académica** cuántas optativas se abren realmente por
   periodo y con qué cupo, y cargarlo en la tabla `oferta`. Sin ese dato el
   sistema puede recomendar materias que nadie va a impartir.
4. **Validación retrospectiva** con estudiantes de séptimo y octavo que ya
   eligieron, para recalibrar los pesos con datos reales.
