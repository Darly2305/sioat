import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { useAuth } from "./auth";
import { C } from "./tema";
import Login from "./pages/Login";
import Cuestionario from "./pages/Cuestionario";
import Docente from "./pages/Docente";

function Protegida({ children, rol }) {
  const { usuario, cargando } = useAuth();
  if (cargando) return (
    <div className="min-h-screen grid place-items-center" style={{ background: C.fondo }}>
      <Loader2 className="animate-spin" color={C.azul} size={26} />
    </div>
  );
  if (!usuario) return <Navigate to="/entrar" replace />;
  if (rol && usuario.rol !== rol && usuario.rol !== "admin") return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  const { usuario } = useAuth();
  return (
    <Routes>
      <Route path="/entrar" element={usuario ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/" element={
        <Protegida>
          {usuario?.rol === "estudiante" ? <Cuestionario /> : <Navigate to="/panel" replace />}
        </Protegida>} />
      <Route path="/panel" element={<Protegida rol="docente"><Docente /></Protegida>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
