/* En desarrollo Vite reenvía /api a Flask. En producción el backend vive en
   otro dominio, así que la URL entra por variable de entorno al compilar. */
const BASE = import.meta.env.VITE_API_URL || "/api";

let token = null;
export const setToken = t => { token = t; };
export const getToken = () => token;

async function pedir(ruta, { metodo = "GET", cuerpo } = {}) {
  const r = await fetch(BASE + ruta, {
    method: metodo,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(datos.error || "No pudimos conectar. Revisa tu internet.");
  return datos;
}

export const api = {
  registro: d => pedir("/auth/registro", { metodo: "POST", cuerpo: d }),
  login:    d => pedir("/auth/login",    { metodo: "POST", cuerpo: d }),
  yo:       () => pedir("/auth/yo"),
  actualizarPerfil: d => pedir("/auth/perfil",   { metodo: "PUT", cuerpo: d }),
  cambiarPassword:  d => pedir("/auth/password", { metodo: "PUT", cuerpo: d }),

  catalogo: () => pedir("/catalogo"),
  sesion:   () => pedir("/sesion"),
  guardar:  d => pedir("/sesion/respuesta", { metodo: "PUT", cuerpo: d }),
  completar:() => pedir("/sesion/completar", { metodo: "POST" }),
  elegirBloque: id => pedir("/sesion/elegir-bloque", { metodo: "POST", cuerpo: { itinerario: id } }),
  resultado:() => pedir("/sesion/resultado"),

  resumen:      () => pedir("/docente/resumen"),
  padron:       () => pedir("/docente/padron"),
  sinDefinir:   () => pedir("/docente/sin_definir"),
  concordancia: () => pedir("/docente/concordancia"),
  verOferta:    () => pedir("/docente/oferta"),
  guardarOferta: d => pedir("/docente/oferta", { metodo: "PUT", cuerpo: d }),
  guardarAplicacion: d => pedir("/docente/aplicacion", { metodo: "PUT", cuerpo: d }),
  usuarios:      () => pedir("/docente/usuarios"),
  crearUsuario:  d => pedir("/docente/usuarios", { metodo: "POST", cuerpo: d }),
  editarUsuario: (id, d) => pedir(`/docente/usuarios/${id}`, { metodo: "PUT", cuerpo: d }),

  /* El CSV no pasa por pedir(): la respuesta es un archivo, no JSON, y el
     token viaja en cabecera, así que no basta con abrir la URL en otra pestaña. */
  async descargarPadron() {
    const r = await fetch(BASE + "/docente/padron.csv", {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!r.ok) throw new Error("No pudimos generar el archivo.");
    const url = URL.createObjectURL(await r.blob());
    const a = document.createElement("a");
    a.href = url;
    a.download = "padron_sioat.csv";
    a.click();
    URL.revokeObjectURL(url);
  },
};

/* ──────────────────────────────────────────────────────────────────────────
   Cola de autoguardado.

   Cada respuesta se manda sola, pero la red del campus se cae. Si un PUT
   falla, la respuesta se queda en la cola y se reintenta; el estado local
   ya cambió, así que el estudiante no ve nada raro y puede seguir. Si de
   plano no hay red, avisamos en vez de fingir que se guardó.
   ────────────────────────────────────────────────────────────────────────── */
export function crearCola(onEstado) {
  const pendientes = [];
  let corriendo = false;

  async function vaciar() {
    if (corriendo) return;
    corriendo = true;
    while (pendientes.length) {
      const item = pendientes[0];
      try {
        await api.guardar(item);
        pendientes.shift();
        onEstado(pendientes.length ? "guardando" : "guardado");
      } catch {
        onEstado("sin_conexion");
        await new Promise(r => setTimeout(r, 3000));   // reintento con espera
      }
    }
    corriendo = false;
  }

  return {
    encolar(respuesta) {
      pendientes.push(respuesta);
      onEstado("guardando");
      vaciar();
    },
    get pendientes() { return pendientes.length; },
  };
}
