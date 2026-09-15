import React, { createContext, useContext, useEffect, useState } from "react";
import { api, setToken } from "./api";

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

const LLAVE = "sioat_token";

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    const t = sessionStorage.getItem(LLAVE);
    if (!t) { setCargando(false); return; }
    setToken(t);
    api.yo()
      .then(d => setUsuario(d.usuario))
      .catch(() => { sessionStorage.removeItem(LLAVE); setToken(null); })
      .finally(() => setCargando(false));
  }, []);

  const guardarSesion = d => {
    sessionStorage.setItem(LLAVE, d.token);
    setToken(d.token);
    setUsuario(d.usuario);
  };

  const valor = {
    usuario, cargando,
    login:    async d => guardarSesion(await api.login(d)),
    registro: async d => guardarSesion(await api.registro(d)),
    salir: () => { sessionStorage.removeItem(LLAVE); setToken(null); setUsuario(null); },
    refrescar: u => setUsuario(u),
  };
  return <Ctx.Provider value={valor}>{children}</Ctx.Provider>;
}
