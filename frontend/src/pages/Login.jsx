import React, { useState } from "react";
import { GraduationCap, Loader2, CircleAlert } from "lucide-react";
import { useAuth } from "../auth";
import { C } from "../tema";

/* Cada campo lleva etiqueta propia arriba, no sólo placeholder: en cuanto el
   alumno escribe, el placeholder desaparece y ya no hay forma de saber qué
   pedía ese recuadro. */
function Campo({ etiqueta, ancho = "", ...props }) {
  return (
    <label className={"flex flex-col gap-1.5 " + ancho}>
      <span className="text-[12.5px] font-semibold" style={{ color: C.azul }}>{etiqueta}</span>
      <input
        className="w-full rounded-lg px-3.5 py-2.5 text-[15px] outline-none"
        style={{ background: C.carta, border: `1px solid ${C.borde}`, color: C.texto }}
        onFocus={e => (e.target.style.borderColor = C.verde)}
        onBlur={e => (e.target.style.borderColor = C.borde)}
        {...props}
      />
    </label>
  );
}

export default function Login() {
  const { login, registro } = useAuth();
  const [modo, setModo] = useState("entrar");
  const [f, setF] = useState({ nombre: "", matricula: "", seccion: "", correo: "", password: "" });
  const [error, setError] = useState("");
  const [ocupado, setOcupado] = useState(false);

  const cambiar = k => e => setF({ ...f, [k]: e.target.value });
  const esRegistro = modo === "registro";

  const enviar = async e => {
    e.preventDefault();
    setError(""); setOcupado(true);
    try {
      if (esRegistro) await registro(f);
      else await login({ correo: f.correo, password: f.password });
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2" style={{ background: C.fondo }}>

      {/* lado izquierdo: el porqué, no el formulario */}
      <div className="hidden lg:flex flex-col justify-center px-14 xl:px-20"
        style={{ background: C.azul }}>
        <div className="flex items-center gap-2 mb-6">
          <GraduationCap size={19} color="#86EFAC" strokeWidth={2} />
          <span className="text-[12.5px] font-semibold" style={{ color: "#86EFAC" }}>
            Gestión y Dirección de Negocios · FCA · UV
          </span>
        </div>
        <h1 className="text-white font-extrabold leading-[1.08] tracking-[-0.02em]"
          style={{ fontSize: "clamp(34px,3.8vw,50px)" }}>
          Elige el área terminal<br />en la que te vas<br />a especializar.
        </h1>
        <p className="mt-7 max-w-[430px] text-[15.5px] leading-relaxed" style={{ color: "#BFDBFE" }}>
          En sexto, séptimo y octavo cursas tres experiencias educativas optativas.
          No se eligen sueltas: forman un bloque. Ese bloque es lo primero que un
          empleador lee en tu kardex.
        </p>
        <p className="mt-4 max-w-[430px] text-[14px] leading-relaxed" style={{ color: "#93C5FD" }}>
          Doce minutos. Puedes salirte cuando quieras: al volver sigues donde te quedaste.
        </p>
      </div>

      {/* lado derecho: el formulario */}
      <div className="flex items-center justify-center px-6 py-14">
        <form onSubmit={enviar} className="w-full max-w-[420px]">

          <div className="lg:hidden flex items-center gap-2 mb-5">
            <GraduationCap size={18} color={C.verde} strokeWidth={2} />
            <span className="text-[12px] font-semibold" style={{ color: C.verde }}>
              LGDN · FCA · UV
            </span>
          </div>

          <h2 className="text-[29px] font-extrabold leading-tight mb-1.5" style={{ color: C.azul }}>
            {esRegistro ? "Crea tu cuenta" : "Entra a tu cuenta"}
          </h2>
          <p className="text-[14px] mb-7" style={{ color: C.suave }}>
            {esRegistro
              ? "Con tu correo institucional y los datos de tu grupo."
              : "Con el correo y la contraseña que registraste."}
          </p>

          <div className="flex flex-col gap-4">
            {esRegistro && (
              <>
                <Campo etiqueta="Nombre completo" value={f.nombre} onChange={cambiar("nombre")}
                  autoComplete="name" required />
                {/* grid en vez de flex: las columnas quedan fijas y ninguna
                    clase de ancho pelea con otra */}
                <div className="grid grid-cols-[1fr_7rem] gap-3">
                  <Campo etiqueta="Matrícula" value={f.matricula} onChange={cambiar("matricula")}
                    placeholder="S21016023" required />
                  <Campo etiqueta="Sección" value={f.seccion} onChange={cambiar("seccion")}
                    placeholder="01" />
                </div>
              </>
            )}

            <Campo etiqueta="Correo" type="email" value={f.correo} onChange={cambiar("correo")}
              autoComplete="email" placeholder="zs21016023@estudiantes.uv.mx" required />

            <Campo etiqueta="Contraseña" type="password" value={f.password}
              onChange={cambiar("password")} required
              autoComplete={esRegistro ? "new-password" : "current-password"} />
          </div>

          {esRegistro && (
            <p className="mt-3 text-[12.5px] leading-relaxed" style={{ color: C.suave }}>
              La contraseña necesita mínimo 8 caracteres. La sección es la de tu grupo;
              si no la sabes, déjala en blanco y tu tutor la completa después.
            </p>
          )}

          {error && (
            <div className="mt-5 flex gap-2.5 rounded-lg px-4 py-3"
              style={{ background: "#FEF2F2", borderLeft: "4px solid #B91C1C" }}>
              <CircleAlert size={17} color="#B91C1C" strokeWidth={2} className="shrink-0 mt-0.5" />
              <p className="text-[13.5px] leading-relaxed" style={{ color: "#7F1D1D" }}>{error}</p>
            </div>
          )}

          <button type="submit" disabled={ocupado}
            className="mt-6 w-full rounded-lg py-3.5 text-[15px] font-semibold text-white flex items-center justify-center gap-2 disabled:opacity-60"
            style={{ background: C.azul }}>
            {ocupado
              ? <><Loader2 size={17} className="animate-spin" /> Un momento…</>
              : esRegistro ? "Crear cuenta" : "Entrar"}
          </button>

          <button type="button"
            onClick={() => { setModo(esRegistro ? "entrar" : "registro"); setError(""); }}
            className="mt-5 w-full text-[13.5px] font-semibold" style={{ color: C.verde }}>
            {esRegistro ? "Ya tengo cuenta" : "No tengo cuenta todavía"}
          </button>
        </form>
      </div>
    </div>
  );
}
