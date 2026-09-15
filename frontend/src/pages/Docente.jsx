import React, { useEffect, useMemo, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import {
  LayoutDashboard, Table2, SlidersHorizontal, TriangleAlert, Download,
  Search, LogOut, Loader2, CalendarClock, Check, Lock, UserCog, KeyRound,
  UserPlus, Users2,
} from "lucide-react";
import { api } from "../api";
import { useAuth } from "../auth";
import { C, iconoDe } from "../tema";

/* Panel de coordinación.

   Tres pestañas. Las dos primeras las ve el docente; la tercera sólo el
   administrador, porque cambiar la oferta a media aplicación altera lo que
   todos los alumnos ven en su resultado.

   La matrícula es la llave en todas las tablas: así funciona todo en la UV y
   es lo que permite cruzar estos listados con los de Escolar sin pelearse con
   nombres escritos de tres formas distintas. */

const VERDE_CLARO = "#86EFAC";
const AZUL_CLARO = "#93C5FD";

function Carta({ children, acento = C.azul, className = "" }) {
  return (
    <div className={"rounded-lg overflow-hidden " + className}
      style={{ background: C.carta, borderLeft: `4px solid ${acento}`,
        boxShadow: "0 1px 2px rgba(15,23,42,.06)" }}>{children}</div>
  );
}

function Titulo({ icono: Ico, children, nota }) {
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2.5 mb-1.5">
        <Ico size={19} strokeWidth={2} color={C.azul} />
        <h2 className="text-[18px] font-semibold" style={{ color: C.azul }}>{children}</h2>
      </div>
      {nota && <p className="text-[13.5px] leading-relaxed" style={{ color: C.suave }}>{nota}</p>}
    </div>
  );
}

function Metrica({ valor, etiqueta, tono = C.azul }) {
  return (
    <div>
      <p className="text-[26px] font-extrabold tabular-nums leading-none" style={{ color: tono }}>
        {valor ?? 0}
      </p>
      <p className="text-[12px] mt-1.5" style={{ color: C.suave }}>{etiqueta}</p>
    </div>
  );
}

function Vacio({ children }) {
  return (
    <Carta acento={C.borde}>
      <p className="p-6 text-[14px] leading-relaxed" style={{ color: C.suave }}>{children}</p>
    </Carta>
  );
}

/* ─────────────────────────── pestaña: resumen ─────────────────────────── */

function Resumen({ datos }) {
  const { avance, metodo, bloques, optativas, academias, secciones, bloques_vacios } = datos;
  const hayDatos = bloques.length > 0;

  const datosMetodo = metodo.map(m => ({
    name: m.metodo, value: Number(m.alumnos),
  }));

  const datosBloques = bloques.slice(0, 13).map(b => ({
    nombre: b.nombre.length > 26 ? b.nombre.slice(0, 25) + "…" : b.nombre,
    Diagnóstico: Number(b.por_cuestionario),
    Elección: Number(b.eligieron_directo),
  }));

  const datosOptativas = optativas.map(o => ({
    nombre: o.nombre.length > 26 ? o.nombre.slice(0, 25) + "…" : o.nombre,
    Alumnos: Number(o.alumnos),
  }));

  return (
    <>
      {avance && (
        <Carta acento={C.verde} className="mb-8">
          <div className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <CalendarClock size={17} color={C.verde} strokeWidth={2} />
              <span className="text-[13px] font-semibold" style={{ color: C.verdeOs }}>
                {avance.nombre} · cierra el {new Date(avance.fecha_limite)
                  .toLocaleDateString("es-MX", { day: "numeric", month: "long", year: "numeric" })}
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-5">
              <Metrica valor={avance.sesiones} etiqueta="Alumnos registrados" />
              <Metrica valor={avance.completadas} etiqueta="Terminaron" tono={C.verdeOs} />
              <Metrica valor={avance.en_progreso} etiqueta="A medias" />
              <Metrica valor={avance.eleccion_directa} etiqueta="Eligieron directo" />
              <Metrica valor={`${avance.pct_completado ?? 0}%`} etiqueta="Avance" tono={C.verdeOs} />
            </div>
          </div>
        </Carta>
      )}

      {secciones && secciones.length > 0 && (
        <div className="mb-9">
          <Titulo icono={Users2} nota="A qué grupo hay que ir a insistirle antes de que cierre la fecha.">
            Avance por sección
          </Titulo>
          <Carta>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead>
                  <tr style={{ background: C.azulSuave }}>
                    {["Sección", "Alumnos", "Terminaron", "A medias", "Eligieron directo", "Avance"]
                      .map((h, i) => (
                      <th key={h} className={"px-4 py-2.5 font-semibold whitespace-nowrap " + (i ? "text-right" : "text-left")}
                        style={{ color: C.azul }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {secciones.map((s2, i) => (
                    <tr key={s2.seccion} style={{ background: i % 2 ? "#FAFCFE" : C.carta }}>
                      <td className="px-4 py-2.5 font-semibold" style={{ color: C.azul }}>{s2.seccion}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums" style={{ color: C.texto }}>{s2.alumnos}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums" style={{ color: C.verdeOs }}>{s2.terminaron}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums" style={{ color: C.suave }}>{s2.a_medias}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums" style={{ color: C.suave }}>{s2.eleccion_directa}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums font-semibold"
                        style={{ color: (s2.pct ?? 0) < 50 ? C.ambar : C.verdeOs }}>{s2.pct ?? 0}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Carta>
        </div>
      )}

      {!hayDatos ? (
        <Vacio>
          Nadie ha terminado todavía. Cuando los primeros alumnos entreguen, aquí van a
          aparecer la demanda por bloque, por optativa y el reparto entre los que
          eligieron directo y los que pasaron por el diagnóstico.
        </Vacio>
      ) : (
        <>
          <div className="grid lg:grid-cols-2 gap-6 mb-9">
            <div>
              <Titulo icono={LayoutDashboard} nota="Si casi todos eligen directo, el catálogo se explica solo y el diagnóstico sobra. Si es al revés, los bloques no se entienden sin ayuda.">
                Cómo llegaron a su bloque
              </Titulo>
              <Carta>
                <div className="p-4" style={{ height: 260 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={datosMetodo} dataKey="value" nameKey="name"
                        innerRadius={58} outerRadius={90} paddingAngle={2}>
                        {datosMetodo.map((d, i) => (
                          <Cell key={i} fill={i === 0 ? C.azul : C.verde} />
                        ))}
                      </Pie>
                      <Tooltip formatter={v => `${v} alumnos`} />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: 12.5 }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </Carta>
            </div>

            <div>
              <Titulo icono={LayoutDashboard} nota="Suma de los alumnos de cada bloque que contiene esa academia.">
                Demanda por academia
              </Titulo>
              <Carta>
                <div className="p-4" style={{ height: 260 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={academias} layout="vertical"
                      margin={{ left: 4, right: 16, top: 4, bottom: 4 }}>
                      <CartesianGrid horizontal={false} stroke={C.borde} />
                      <XAxis type="number" tick={{ fontSize: 11, fill: C.suave }} allowDecimals={false} />
                      <YAxis type="category" dataKey="academia" width={118}
                        tick={{ fontSize: 11, fill: C.suave }} />
                      <Tooltip formatter={v => `${v} alumnos`} cursor={{ fill: C.azulSuave }} />
                      <Bar dataKey="alumnos" fill={C.azulMed} radius={[0, 3, 3, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Carta>
            </div>
          </div>

          <div className="mb-9">
            <Titulo icono={LayoutDashboard} nota="Cada barra separa a quienes llegaron por diagnóstico de quienes lo eligieron ellos mismos.">
              Alumnos por bloque
            </Titulo>
            <Carta>
              <div className="p-4" style={{ height: 30 * datosBloques.length + 60 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={datosBloques} layout="vertical"
                    margin={{ left: 4, right: 16, top: 4, bottom: 4 }}>
                    <CartesianGrid horizontal={false} stroke={C.borde} />
                    <XAxis type="number" tick={{ fontSize: 11, fill: C.suave }} allowDecimals={false} />
                    <YAxis type="category" dataKey="nombre" width={185}
                      tick={{ fontSize: 11, fill: C.suave }} />
                    <Tooltip cursor={{ fill: C.azulSuave }} />
                    <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="Diagnóstico" stackId="a" fill={C.azul} />
                    <Bar dataKey="Elección" stackId="a" fill={C.verde} radius={[0, 3, 3, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Carta>
          </div>

          <div className="mb-9">
            <Titulo icono={Table2} nota="La matrícula real de cada optativa: cuántos alumnos quedaron en un bloque que la incluye. Los grupos salen de dividir entre el cupo.">
              Demanda por optativa
            </Titulo>
            <Carta>
              <div className="p-4" style={{ height: 30 * datosOptativas.length + 50 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={datosOptativas} layout="vertical"
                    margin={{ left: 4, right: 16, top: 4, bottom: 4 }}>
                    <CartesianGrid horizontal={false} stroke={C.borde} />
                    <XAxis type="number" tick={{ fontSize: 11, fill: C.suave }} allowDecimals={false} />
                    <YAxis type="category" dataKey="nombre" width={185}
                      tick={{ fontSize: 11, fill: C.suave }} />
                    <Tooltip formatter={v => `${v} alumnos`} cursor={{ fill: C.azulSuave }} />
                    <Bar dataKey="Alumnos" fill={C.verde} radius={[0, 3, 3, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Carta>
          </div>

          <div className="mb-9">
            <Titulo icono={Table2}>Cuántos grupos abrir</Titulo>
            <Carta>
              <div className="overflow-x-auto">
                <table className="w-full text-[13px]">
                  <thead>
                    <tr style={{ background: C.azulSuave }}>
                      {["Optativa", "Academia", "Alumnos", "Cupo", "Grupos", "Estado"].map((h, i) => (
                        <th key={h} className={"px-4 py-2.5 font-semibold whitespace-nowrap " + (i > 1 ? "text-right" : "text-left")}
                          style={{ color: C.azul }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {optativas.map((o, i) => (
                      <tr key={o.clave} style={{ background: i % 2 ? "#FAFCFE" : C.carta }}>
                        <td className="px-4 py-2.5" style={{ color: C.texto }}>{o.nombre}</td>
                        <td className="px-4 py-2.5" style={{ color: C.suave }}>{o.academia}</td>
                        <td className="px-4 py-2.5 text-right tabular-nums font-semibold"
                          style={{ color: C.texto }}>{o.alumnos}</td>
                        <td className="px-4 py-2.5 text-right tabular-nums" style={{ color: C.suave }}>
                          {o.cupo ?? "—"}
                        </td>
                        <td className="px-4 py-2.5 text-right tabular-nums font-semibold"
                          style={{ color: o.grupos_necesarios > 1 ? C.ambar : C.suave }}>
                          {o.grupos_necesarios}
                        </td>
                        <td className="px-4 py-2.5 text-right">
                          <span className="rounded px-2 py-0.5 text-[11.5px] font-medium"
                            style={{ background: o.se_abre ? "#DCFCE7" : "#F1F5F9",
                              color: o.se_abre ? C.verdeOs : C.suave }}>
                            {o.se_abre ? "Se abre" : "Cerrada"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Carta>
            {optativas.some(o => o.cupo == null) && (
              <p className="mt-3 text-[12.5px] leading-relaxed" style={{ color: C.ambar }}>
                Hay optativas sin cupo registrado. Mientras no lo cargues en la pestaña de
                Oferta, la columna de grupos asume que con uno alcanza.
              </p>
            )}
          </div>

          {bloques_vacios.length > 0 && (
            <Carta acento={C.suave}>
              <div className="p-5">
                <p className="text-[13px] font-semibold mb-1.5" style={{ color: C.texto }}>
                  Bloques sin un solo alumno ({bloques_vacios.length})
                </p>
                <p className="text-[13px] leading-relaxed" style={{ color: C.suave }}>
                  {bloques_vacios.map(v => v.nombre).join(" · ")}
                </p>
              </div>
            </Carta>
          )}
        </>
      )}
    </>
  );
}

/* ─────────────────────────── pestaña: padrón ─────────────────────────── */

function Padron({ alumnos, sinDefinir, onDescargar }) {
  const [busca, setBusca] = useState("");
  const [orden, setOrden] = useState({ campo: "matricula", asc: true });
  const [filtro, setFiltro] = useState("todos");
  const [seccion, setSeccion] = useState("todas");

  const secciones = useMemo(
    () => [...new Set(alumnos.map(a => a.seccion).filter(Boolean))].sort(),
    [alumnos]);

  const lista = useMemo(() => {
    let l = alumnos;
    if (seccion !== "todas") l = l.filter(a => (a.seccion || "") === seccion);
    if (filtro === "diagnostico") l = l.filter(a => a.metodo === "Examen diagnóstico");
    if (filtro === "eleccion") l = l.filter(a => a.metodo === "Elección del alumno");
    if (filtro === "pendientes") l = l.filter(a => a.estado !== "completada");
    const q = busca.trim().toLowerCase();
    if (q) l = l.filter(a =>
      (a.matricula || "").toLowerCase().includes(q) ||
      (a.nombre || "").toLowerCase().includes(q) ||
      (a.seccion || "").toLowerCase().includes(q) ||
      (a.bloque || "").toLowerCase().includes(q));
    return [...l].sort((x, y) => {
      const a = (x[orden.campo] ?? "").toString(), b = (y[orden.campo] ?? "").toString();
      return orden.asc ? a.localeCompare(b, "es") : b.localeCompare(a, "es");
    });
  }, [alumnos, busca, orden, filtro, seccion]);

  const ordenar = campo => setOrden(o =>
    o.campo === campo ? { campo, asc: !o.asc } : { campo, asc: true });

  const COLS = [
    ["matricula", "Matrícula"], ["seccion", "Sección"], ["nombre", "Nombre"],
    ["metodo", "Método"], ["bloque", "Área terminal"], ["estado", "Estado"],
  ];

  return (
    <>
      <Titulo icono={Table2} nota="Quién obtuvo qué área terminal y por qué vía. La matrícula es la llave: ordena y busca por ella para cruzar con los listados de Escolar.">
        Padrón de alumnos
      </Titulo>

      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={15} color={C.suave}
            className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input value={busca} onChange={e => setBusca(e.target.value)}
            placeholder="Buscar por matrícula, sección, nombre o bloque"
            className="w-full rounded-md py-2.5 pl-9 pr-3 text-[13.5px]"
            style={{ background: C.carta, border: `1px solid ${C.borde}`, color: C.texto }} />
        </div>
        {secciones.length > 0 && (
          <select value={seccion} onChange={e => setSeccion(e.target.value)}
            className="rounded-md px-3 py-2.5 text-[13px]"
            style={{ background: C.carta, border: `1px solid ${C.borde}`, color: C.texto }}>
            <option value="todas">Todas las secciones</option>
            {secciones.map(x => <option key={x} value={x}>Sección {x}</option>)}
          </select>
        )}
        <div className="flex gap-1.5">
          {[["todos", "Todos"], ["diagnostico", "Diagnóstico"],
            ["eleccion", "Elección"], ["pendientes", "Pendientes"]].map(([k, t]) => (
            <button key={k} onClick={() => setFiltro(k)}
              className="rounded-md px-3 py-2 text-[12.5px] font-medium"
              style={{ background: filtro === k ? C.azul : C.carta,
                color: filtro === k ? "#FFF" : C.suave,
                border: `1px solid ${filtro === k ? C.azul : C.borde}` }}>{t}</button>
          ))}
        </div>
        <button onClick={onDescargar}
          className="flex items-center gap-2 rounded-md px-4 py-2.5 text-[13px] font-semibold text-white"
          style={{ background: C.verde }}>
          <Download size={15} /> CSV
        </button>
      </div>

      {lista.length === 0 ? (
        <Vacio>No hay alumnos que coincidan con ese filtro.</Vacio>
      ) : (
        <Carta className="mb-9">
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr style={{ background: C.azulSuave }}>
                  {COLS.map(([campo, label]) => (
                    <th key={campo} onClick={() => ordenar(campo)}
                      className="px-4 py-2.5 text-left font-semibold whitespace-nowrap cursor-pointer select-none"
                      style={{ color: C.azul }}>
                      {label}{orden.campo === campo ? (orden.asc ? " ↑" : " ↓") : ""}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {lista.map((a, i) => {
                  const Ico = a.bloque_id ? iconoDe(a.bloque_id) : null;
                  return (
                    <tr key={a.matricula || i} style={{ background: i % 2 ? "#FAFCFE" : C.carta }}>
                      <td className="px-4 py-2.5 tabular-nums font-semibold whitespace-nowrap"
                        style={{ color: C.azul }}>{a.matricula || "—"}</td>
                      <td className="px-4 py-2.5 tabular-nums" style={{ color: C.suave }}>
                        {a.seccion || "—"}</td>
                      <td className="px-4 py-2.5" style={{ color: C.texto }}>{a.nombre}</td>
                      <td className="px-4 py-2.5 whitespace-nowrap">
                        <span className="rounded px-2 py-0.5 text-[11.5px] font-medium"
                          style={{ background: a.metodo === "Elección del alumno" ? "#DCFCE7" : C.azulSuave,
                            color: a.metodo === "Elección del alumno" ? C.verdeOs : C.azulMed }}>
                          {a.metodo}
                        </span>
                      </td>
                      <td className="px-4 py-2.5" style={{ color: C.texto }}>
                        {a.bloque ? (
                          <span className="flex items-center gap-2">
                            {Ico && <Ico size={14} color={C.suave} strokeWidth={2} />}
                            {a.bloque}
                          </span>
                        ) : a.perfil_plano ? (
                          <span style={{ color: C.ambar }}>Sin definir</span>
                        ) : (
                          <span style={{ color: C.suave }}>—</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap" style={{ color: C.suave }}>
                        {a.estado === "completada" ? "Terminó"
                          : a.estado === "expirada" ? "Venció" : "A medias"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Carta>
      )}

      {sinDefinir.length > 0 && (
        <>
          <Titulo icono={TriangleAlert} nota="Terminaron pero ningún bloque se despegó de los demás. El sistema no les asignó nada a propósito: a estos hay que hablarles, no mandarles un correo automático.">
            Necesitan tutoría
          </Titulo>
          <Carta acento={C.ambar}>
            <div className="p-4 flex flex-col gap-2">
              {sinDefinir.map(a => (
                <div key={a.matricula} className="flex flex-wrap items-center gap-3 text-[13px]">
                  <span className="w-24 tabular-nums font-semibold" style={{ color: C.azul }}>
                    {a.matricula}
                  </span>
                  <span className="w-16 tabular-nums" style={{ color: C.suave }}>
                    {a.seccion ? `Secc. ${a.seccion}` : "—"}
                  </span>
                  <span className="flex-1 min-w-[140px]" style={{ color: C.texto }}>{a.nombre}</span>
                  <span style={{ color: C.suave }}>{a.correo}</span>
                </div>
              ))}
            </div>
          </Carta>
        </>
      )}
    </>
  );
}

/* ─────────────────────────── pestaña: oferta ─────────────────────────── */

function OfertaTab({ esAdmin }) {
  const [filas, setFilas] = useState(null);
  const [guardando, setGuardando] = useState(false);
  const [aviso, setAviso] = useState("");

  useEffect(() => { api.verOferta().then(d => setFilas(d.optativas)); }, []);

  const cambiar = (clave, campo, valor) =>
    setFilas(f => f.map(o => o.clave === clave ? { ...o, [campo]: valor } : o));

  const guardar = async () => {
    setGuardando(true); setAviso("");
    try {
      await api.guardarOferta({ optativas: filas.map(o => ({
        clave: o.clave, se_abre: !!o.se_abre, cupo: o.cupo ? Number(o.cupo) : null })) });
      setAviso("Guardado.");
    } catch (e) { setAviso(e.message); }
    finally { setGuardando(false); }
  };

  if (!filas) return <Loader2 className="animate-spin" color={C.azul} size={22} />;

  return (
    <>
      <Titulo icono={SlidersHorizontal} nota="Qué optativas se abren y con qué cupo. El resultado del estudiante se filtra contra esto, así que un cambio a media aplicación altera lo que todos ven.">
        Oferta del periodo
      </Titulo>

      {!esAdmin && (
        <Carta acento={C.suave} className="mb-5">
          <p className="p-4 text-[13px] flex items-center gap-2" style={{ color: C.suave }}>
            <Lock size={15} /> Sólo lectura. Para cambiar la oferta se necesitan permisos de administrador.
          </p>
        </Carta>
      )}

      <Carta className="mb-5">
        <div className="overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead>
              <tr style={{ background: C.azulSuave }}>
                {["Optativa", "Academia", "¿Se abre?", "Cupo por grupo"].map((h, i) => (
                  <th key={h} className={"px-4 py-2.5 font-semibold whitespace-nowrap " + (i > 1 ? "text-right" : "text-left")}
                    style={{ color: C.azul }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filas.map((o, i) => (
                <tr key={o.clave} style={{ background: i % 2 ? "#FAFCFE" : C.carta }}>
                  <td className="px-4 py-2.5" style={{ color: C.texto }}>{o.nombre}</td>
                  <td className="px-4 py-2.5" style={{ color: C.suave }}>{o.academia}</td>
                  <td className="px-4 py-2 text-right">
                    <button disabled={!esAdmin}
                      onClick={() => cambiar(o.clave, "se_abre", o.se_abre ? 0 : 1)}
                      className="rounded px-3 py-1.5 text-[12px] font-medium disabled:opacity-70"
                      style={{ background: o.se_abre ? "#DCFCE7" : "#F1F5F9",
                        color: o.se_abre ? C.verdeOs : C.suave }}>
                      {o.se_abre ? "Se abre" : "Cerrada"}
                    </button>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <input type="number" min="1" disabled={!esAdmin}
                      value={o.cupo ?? ""} placeholder="—"
                      onChange={e => cambiar(o.clave, "cupo", e.target.value)}
                      className="w-20 rounded-md px-2 py-1.5 text-right text-[13px] tabular-nums disabled:opacity-70"
                      style={{ background: C.carta, border: `1px solid ${C.borde}`, color: C.texto }} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Carta>

      {esAdmin && (
        <div className="flex items-center gap-4">
          <button onClick={guardar} disabled={guardando}
            className="flex items-center gap-2 rounded-md px-6 py-2.5 text-[14px] font-semibold text-white disabled:opacity-60"
            style={{ background: C.azul }}>
            {guardando ? <><Loader2 size={15} className="animate-spin" /> Guardando…</>
                       : <><Check size={16} /> Guardar oferta</>}
          </button>
          {aviso && <span className="text-[13px]" style={{ color: C.verdeOs }}>{aviso}</span>}
        </div>
      )}
    </>
  );
}


/* ─────────────────────────── pestaña: cuentas ─────────────────────────── */

function campoEstilo() {
  return { background: C.carta, border: `1px solid ${C.borde}`, color: C.texto };
}

function MiCuenta({ usuario, onActualizar }) {
  const [perfil, setPerfil] = useState({ nombre: usuario.nombre, correo: usuario.correo });
  const [pw, setPw] = useState({ actual: "", nueva: "", repetir: "" });
  const [aviso, setAviso] = useState({ perfil: "", pw: "" });
  const [ocupado, setOcupado] = useState("");

  const guardarPerfil = async () => {
    setOcupado("perfil"); setAviso(a => ({ ...a, perfil: "" }));
    try {
      const r = await api.actualizarPerfil(perfil);
      onActualizar(r.usuario);
      setAviso(a => ({ ...a, perfil: "Datos actualizados." }));
    } catch (e) { setAviso(a => ({ ...a, perfil: e.message })); }
    finally { setOcupado(""); }
  };

  const guardarPw = async () => {
    if (pw.nueva !== pw.repetir) {
      return setAviso(a => ({ ...a, pw: "La nueva contraseña no coincide con la repetición." }));
    }
    setOcupado("pw"); setAviso(a => ({ ...a, pw: "" }));
    try {
      await api.cambiarPassword({ actual: pw.actual, nueva: pw.nueva });
      setPw({ actual: "", nueva: "", repetir: "" });
      setAviso(a => ({ ...a, pw: "Contraseña cambiada." }));
    } catch (e) { setAviso(a => ({ ...a, pw: e.message })); }
    finally { setOcupado(""); }
  };

  const inp = "w-full rounded-md px-3 py-2.5 text-[13.5px]";

  return (
    <div className="grid lg:grid-cols-2 gap-6 mb-10">
      <div>
        <Titulo icono={UserCog}>Mis datos</Titulo>
        <Carta>
          <div className="p-5 flex flex-col gap-3">
            <input className={inp} style={campoEstilo()} value={perfil.nombre}
              onChange={e => setPerfil({ ...perfil, nombre: e.target.value })} placeholder="Nombre completo" />
            <input className={inp} style={campoEstilo()} type="email" value={perfil.correo}
              onChange={e => setPerfil({ ...perfil, correo: e.target.value })} placeholder="Correo" />
            <div className="flex items-center gap-3">
              <button onClick={guardarPerfil} disabled={ocupado === "perfil"}
                className="rounded-md px-5 py-2.5 text-[13.5px] font-semibold text-white disabled:opacity-60"
                style={{ background: C.azul }}>
                {ocupado === "perfil" ? "Guardando…" : "Guardar"}
              </button>
              {aviso.perfil && <span className="text-[12.5px]" style={{ color: C.verdeOs }}>{aviso.perfil}</span>}
            </div>
          </div>
        </Carta>
      </div>

      <div>
        <Titulo icono={KeyRound} nota="Pide la actual a propósito: si dejas la sesión abierta en un laboratorio, que nadie pueda dejarte fuera.">
          Cambiar mi contraseña
        </Titulo>
        <Carta>
          <div className="p-5 flex flex-col gap-3">
            <input className={inp} style={campoEstilo()} type="password" autoComplete="current-password"
              value={pw.actual} onChange={e => setPw({ ...pw, actual: e.target.value })}
              placeholder="Contraseña actual" />
            <input className={inp} style={campoEstilo()} type="password" autoComplete="new-password"
              value={pw.nueva} onChange={e => setPw({ ...pw, nueva: e.target.value })}
              placeholder="Nueva contraseña (mínimo 8)" />
            <input className={inp} style={campoEstilo()} type="password" autoComplete="new-password"
              value={pw.repetir} onChange={e => setPw({ ...pw, repetir: e.target.value })}
              placeholder="Repite la nueva" />
            <div className="flex items-center gap-3">
              <button onClick={guardarPw} disabled={ocupado === "pw" || !pw.actual || !pw.nueva}
                className="rounded-md px-5 py-2.5 text-[13.5px] font-semibold text-white disabled:opacity-60"
                style={{ background: C.azul }}>
                {ocupado === "pw" ? "Cambiando…" : "Cambiar contraseña"}
              </button>
              {aviso.pw && <span className="text-[12.5px]" style={{ color: C.verdeOs }}>{aviso.pw}</span>}
            </div>
          </div>
        </Carta>
      </div>
    </div>
  );
}

function Cuentas({ usuario, onActualizar }) {
  const esAdmin = usuario.rol === "admin";
  const [lista, setLista] = useState(null);
  const [nuevo, setNuevo] = useState({ nombre: "", correo: "", rol: "docente", password: "" });
  const [aviso, setAviso] = useState("");
  const [abrirAlta, setAbrirAlta] = useState(false);

  const recargar = () => api.usuarios().then(d => setLista(d.usuarios)).catch(e => setAviso(e.message));
  useEffect(() => { if (esAdmin) recargar(); }, [esAdmin]);

  const crear = async () => {
    setAviso("");
    try {
      await api.crearUsuario(nuevo);
      setNuevo({ nombre: "", correo: "", rol: "docente", password: "" });
      setAbrirAlta(false);
      recargar();
    } catch (e) { setAviso(e.message); }
  };

  const editar = async (id, cambio) => {
    setAviso("");
    try { await api.editarUsuario(id, cambio); recargar(); }
    catch (e) { setAviso(e.message); }
  };

  const restablecer = async u => {
    const p = window.prompt(`Contraseña nueva para ${u.correo} (mínimo 8 caracteres).\nEntrégasela en persona, no por correo.`);
    if (p) editar(u.id, { password: p });
  };

  const inp = "rounded-md px-3 py-2.5 text-[13.5px]";

  return (
    <>
      <MiCuenta usuario={usuario} onActualizar={onActualizar} />

      {!esAdmin ? (
        <Carta acento={C.suave}>
          <p className="p-5 text-[13.5px] flex items-center gap-2" style={{ color: C.suave }}>
            <Lock size={15} /> La administración de cuentas es exclusiva del administrador.
          </p>
        </Carta>
      ) : (
        <>
          <Titulo icono={Users2} nota="Cuentas de docente y administrador. Los estudiantes no aparecen aquí: para eso está el padrón.">
            Cuentas del sistema
          </Titulo>

          {aviso && (
            <Carta acento={C.ambar} className="mb-4">
              <p className="p-4 text-[13px]" style={{ color: C.texto }}>{aviso}</p>
            </Carta>
          )}

          {!lista ? <Loader2 className="animate-spin" color={C.azul} size={22} /> : (
            <Carta className="mb-5">
              <div className="overflow-x-auto">
                <table className="w-full text-[13px]">
                  <thead>
                    <tr style={{ background: C.azulSuave }}>
                      {["Nombre", "Correo", "Rol", "Estado", ""].map((h, i) => (
                        <th key={i} className={"px-4 py-2.5 font-semibold whitespace-nowrap " + (i > 2 ? "text-right" : "text-left")}
                          style={{ color: C.azul }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {lista.map((u, i) => (
                      <tr key={u.id} style={{ background: i % 2 ? "#FAFCFE" : C.carta }}>
                        <td className="px-4 py-2.5" style={{ color: C.texto }}>
                          {u.nombre}{u.id === usuario.id && <span style={{ color: C.suave }}> (tú)</span>}
                        </td>
                        <td className="px-4 py-2.5" style={{ color: C.suave }}>{u.correo}</td>
                        <td className="px-4 py-2">
                          <select value={u.rol} disabled={u.id === usuario.id}
                            onChange={e => editar(u.id, { rol: e.target.value })}
                            className="rounded px-2 py-1 text-[12.5px] disabled:opacity-60"
                            style={campoEstilo()}>
                            <option value="docente">Docente</option>
                            <option value="admin">Administrador</option>
                          </select>
                        </td>
                        <td className="px-4 py-2 text-right">
                          <button disabled={u.id === usuario.id}
                            onClick={() => editar(u.id, { activo: !u.activo })}
                            className="rounded px-3 py-1.5 text-[12px] font-medium disabled:opacity-60"
                            style={{ background: u.activo ? "#DCFCE7" : "#F1F5F9",
                              color: u.activo ? C.verdeOs : C.suave }}>
                            {u.activo ? "Activa" : "Desactivada"}
                          </button>
                        </td>
                        <td className="px-4 py-2 text-right">
                          <button onClick={() => restablecer(u)}
                            className="text-[12.5px] font-medium" style={{ color: C.azulMed }}>
                            Restablecer contraseña
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Carta>
          )}

          {!abrirAlta ? (
            <button onClick={() => setAbrirAlta(true)}
              className="flex items-center gap-2 rounded-md px-5 py-2.5 text-[13.5px] font-semibold"
              style={{ background: C.carta, color: C.azul, border: `1.5px solid ${C.azul}` }}>
              <UserPlus size={16} /> Dar de alta una cuenta
            </button>
          ) : (
            <Carta acento={C.verde}>
              <div className="p-5">
                <p className="text-[13px] font-semibold mb-3" style={{ color: C.texto }}>Nueva cuenta</p>
                <div className="grid sm:grid-cols-2 gap-3 mb-3">
                  <input className={inp} style={campoEstilo()} placeholder="Nombre completo"
                    value={nuevo.nombre} onChange={e => setNuevo({ ...nuevo, nombre: e.target.value })} />
                  <input className={inp} style={campoEstilo()} type="email" placeholder="Correo"
                    value={nuevo.correo} onChange={e => setNuevo({ ...nuevo, correo: e.target.value })} />
                  <select className={inp} style={campoEstilo()} value={nuevo.rol}
                    onChange={e => setNuevo({ ...nuevo, rol: e.target.value })}>
                    <option value="docente">Docente</option>
                    <option value="admin">Administrador</option>
                  </select>
                  <input className={inp} style={campoEstilo()} type="text" placeholder="Contraseña inicial"
                    value={nuevo.password} onChange={e => setNuevo({ ...nuevo, password: e.target.value })} />
                </div>
                <p className="text-[12.5px] mb-4" style={{ color: C.suave }}>
                  Entrega la contraseña en persona. El sistema no manda correos, y una contraseña
                  en un buzón compartido no es una contraseña.
                </p>
                <div className="flex gap-3">
                  <button onClick={crear}
                    className="rounded-md px-5 py-2.5 text-[13.5px] font-semibold text-white"
                    style={{ background: C.verde }}>Crear cuenta</button>
                  <button onClick={() => setAbrirAlta(false)}
                    className="rounded-md px-5 py-2.5 text-[13.5px] font-semibold"
                    style={{ color: C.suave }}>Cancelar</button>
                </div>
              </div>
            </Carta>
          )}
        </>
      )}
    </>
  );
}

/* ─────────────────────────────── panel ─────────────────────────────── */

export default function Docente() {
  const { usuario, salir, refrescar } = useAuth();
  const [tab, setTab] = useState("resumen");
  const [resumen, setResumen] = useState(null);
  const [alumnos, setAlumnos] = useState(null);
  const [sinDefinir, setSinDefinir] = useState([]);
  const [error, setError] = useState("");

  const esAdmin = usuario?.rol === "admin";

  useEffect(() => {
    Promise.all([api.resumen(), api.padron(), api.sinDefinir()])
      .then(([r, p, s]) => { setResumen(r); setAlumnos(p.alumnos); setSinDefinir(s.alumnos); })
      .catch(e => setError(e.message));
  }, []);

  const TABS = [
    { k: "resumen", t: "Resumen", i: LayoutDashboard },
    { k: "padron", t: "Padrón", i: Table2 },
    { k: "oferta", t: "Oferta", i: SlidersHorizontal },
    { k: "cuenta", t: "Cuenta", i: UserCog },
  ];

  return (
    <div className="min-h-screen" style={{ background: C.fondo }}>
      <header style={{ background: C.carta, borderBottom: `1px solid ${C.borde}` }}>
        <div className="mx-auto w-full max-w-[1040px] px-5 md:px-8">
          <div className="flex items-start justify-between gap-6 pt-8 pb-5">
            <div>
              <h1 className="text-[27px] font-extrabold leading-tight" style={{ color: C.azul }}>
                Qué optativas abrir
              </h1>
              <p className="text-[13.5px] mt-1" style={{ color: C.suave }}>
                {usuario?.nombre} · {esAdmin ? "Administrador" : "Docente"}
              </p>
            </div>
            <button onClick={salir}
              className="flex items-center gap-2 rounded-md px-5 py-2.5 text-[14px] font-semibold shrink-0"
              style={{ background: C.carta, color: C.azul, border: `1.5px solid ${C.azul}` }}>
              <LogOut size={16} strokeWidth={2.2} /> Salir
            </button>
          </div>

          <nav className="flex gap-1 -mb-px">
            {TABS.map(({ k, t, i: Ico }) => (
              <button key={k} onClick={() => setTab(k)}
                className="flex items-center gap-2 px-4 py-3 text-[14px] font-semibold"
                style={{ color: tab === k ? C.azul : C.suave,
                  borderBottom: `2.5px solid ${tab === k ? C.verde : "transparent"}` }}>
                <Ico size={16} strokeWidth={2} /> {t}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1040px] px-5 md:px-8 py-9">
        {error && (
          <Carta acento={C.ambar} className="mb-6">
            <p className="p-5 text-[14px]" style={{ color: C.texto }}>{error}</p>
          </Carta>
        )}

        {!resumen && !error && (
          <div className="grid place-items-center py-20">
            <Loader2 className="animate-spin" color={C.azul} size={26} />
          </div>
        )}

        {resumen && tab === "resumen" && <Resumen datos={resumen} />}
        {resumen && tab === "padron" && alumnos && (
          <Padron alumnos={alumnos} sinDefinir={sinDefinir}
            onDescargar={() => api.descargarPadron().catch(e => setError(e.message))} />
        )}
        {tab === "oferta" && <OfertaTab esAdmin={esAdmin} />}
        {tab === "cuenta" && usuario && <Cuentas usuario={usuario} onActualizar={refrescar} />}
      </main>
    </div>
  );
}
