import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Plus, Minus, Check, CircleAlert, GraduationCap, Layers,
  Compass, ClipboardList, CloudOff, Loader2, Lock, LogOut,
} from "lucide-react";
import { api, crearCola } from "../api";
import { useAuth } from "../auth";
import { C, iconoDe } from "../tema";

/* ══════════════════════════════════════════════════════════════════════════
   Cuestionario del estudiante, conectado al API.

   Dos cosas que no son negociables aquí:

   1. El cálculo es del servidor. Esta pantalla no sabe cuánto pesa cada
      respuesta. Si los pesos viajaran al navegador, el estudiante podría
      leerlos desde el bundle y contestar para caer donde quisiera.

   2. Cada respuesta se manda al momento en que se toca. No hay botón de
      guardar ni borrador en memoria: cerrar la pestaña a media pregunta no
      pierde nada, y al volver el servidor dice dónde se quedó.
   ══════════════════════════════════════════════════════════════════════════ */

const ROMANO = { 1: "I", 2: "II", 3: "III", 4: "IV", 5: "V" };
const PASOS = [
  { k: "fav1", prompt: "¿Cuál te gustó más?", badge: "1ª" },
  { k: "fav2", prompt: "¿Y la segunda?", badge: "2ª" },
  { k: "fav3", prompt: "¿La tercera?", badge: "3ª" },
  { k: "rechazada", prompt: "Ahora al revés: ¿cuál te gustó menos?", badge: "menos" },
];

/* ───────────────────────────── piezas ───────────────────────────── */

function Pill({ children, tono = "azul" }) {
  return (
    <span className="inline-flex items-center justify-center rounded-md px-3 py-2 text-[12.5px] font-medium text-white text-center leading-snug"
      style={{ background: tono === "azul" ? C.azul : C.verde }}>{children}</span>
  );
}

function Carta({ children, acento = C.azul, className = "" }) {
  return (
    <div className={"rounded-lg overflow-hidden " + className}
      style={{ background: C.carta, borderLeft: `4px solid ${acento}`,
        boxShadow: "0 1px 2px rgba(15,23,42,.06), 0 1px 3px rgba(15,23,42,.04)" }}>
      {children}
    </div>
  );
}

function Seccion({ icono: Ico, titulo, children }) {
  return (
    <section className="mb-10">
      <div className="flex items-center gap-2.5 mb-4">
        <Ico size={20} strokeWidth={2} color={C.azul} />
        <h2 className="text-[19px] font-semibold" style={{ color: C.azul }}>{titulo}</h2>
      </div>
      {children}
    </section>
  );
}

function Acordeon({ bloque, abierto, onToggle, onElegir, eligiendo }) {
  const Ico = iconoDe(bloque.id);
  return (
    <Carta acento={abierto ? C.verde : C.azul} className="mb-2.5">
      <button onClick={onToggle} className="w-full flex items-center gap-3 px-4 py-3.5 text-left">
        <span className="text-[11px] font-bold tabular-nums shrink-0" style={{ color: C.suave }}>
          {String(bloque.id).padStart(2, "0")}
        </span>
        <Ico size={17} strokeWidth={2} color={abierto ? C.verde : C.azulMed} className="shrink-0" />
        <span className="flex-1 min-w-0">
          <span className="block text-[14.5px] font-semibold leading-tight"
            style={{ color: abierto ? C.verdeOs : C.azulMed }}>{bloque.nombre}</span>
          {!abierto && (
            <span className="block text-[12.5px] mt-0.5 truncate" style={{ color: C.suave }}>
              {bloque.resumen}
            </span>
          )}
        </span>
        {abierto ? <Minus size={17} strokeWidth={2.5} color={C.verde} className="shrink-0" />
                 : <Plus size={17} strokeWidth={2.5} color={C.verde} className="shrink-0" />}
      </button>

      {abierto && (
        <div className="px-4 pb-4 pt-1" style={{ borderTop: `1px solid ${C.borde}` }}>
          <p className="text-[13.5px] leading-relaxed mt-3 mb-4 text-justify" style={{ color: C.texto }}>
            {bloque.perfil}
          </p>
          <p className="text-[12px] font-semibold mb-2" style={{ color: C.azul }}>
            Las tres experiencias educativas
          </p>
          <div className="grid sm:grid-cols-3 gap-2 mb-4">
            {bloque.optativas.map((o, i) => (
              <Pill key={o.clave} tono={i % 2 === 0 ? "azul" : "verde"}>{o.nombre}</Pill>
            ))}
          </div>
          <p className="text-[12px] font-semibold mb-2" style={{ color: C.azul }}>
            Dónde puedes trabajar
          </p>
          <div className="grid sm:grid-cols-3 gap-2">
            {(bloque.salidas || []).map((s, i) => (
              <Pill key={s} tono={i % 2 === 0 ? "verde" : "azul"}>{s}</Pill>
            ))}
          </div>
          {onElegir && (
            <button onClick={onElegir} disabled={eligiendo}
              className="mt-5 w-full rounded-md py-3 text-[14px] font-semibold text-white flex items-center justify-center gap-2 disabled:opacity-60"
              style={{ background: C.verde }}>
              {eligiendo
                ? <><Loader2 size={16} className="animate-spin" /> Registrando…</>
                : <><Check size={17} strokeWidth={2.5} /> Elegir este bloque</>}
            </button>
          )}
        </div>
      )}
    </Carta>
  );
}

function Opcion({ letra, texto, elegida, onClick, badge }) {
  return (
    <button onClick={onClick} className="w-full text-left rounded-lg overflow-hidden"
      style={{ background: C.carta, borderLeft: `4px solid ${elegida ? C.verde : C.azul}`,
        boxShadow: "0 1px 2px rgba(15,23,42,.06)" }}>
      <div className="flex items-center gap-3.5 px-4 py-3.5">
        <span className="shrink-0 grid place-items-center rounded-md text-[12px] font-bold"
          style={{ width: 26, height: 26, background: elegida ? C.verde : C.azulSuave,
            color: elegida ? "#FFF" : C.azulMed }}>{letra}</span>
        <span className="flex-1 text-[14.5px] leading-snug" style={{ color: C.texto }}>{texto}</span>
        {badge && (
          <span className="shrink-0 rounded-md px-2 py-1 text-[10.5px] font-semibold text-white"
            style={{ background: badge === "menos" ? C.suave : C.azul }}>{badge}</span>
        )}
      </div>
    </button>
  );
}

function Transicion({ antetitulo, titulo, texto, onSeguir, icono: Ico }) {
  return (
    <div className="w-full max-w-[620px]">
      <div className="flex items-center gap-2 mb-3">
        <Ico size={18} color={C.verde} strokeWidth={2} />
        <span className="text-[12.5px] font-semibold" style={{ color: C.verde }}>{antetitulo}</span>
      </div>
      <h2 className="text-[30px] sm:text-[36px] font-bold leading-[1.15] mb-4" style={{ color: C.azul }}>
        {titulo}
      </h2>
      <p className="text-[15px] leading-relaxed mb-8" style={{ color: C.texto }}>{texto}</p>
      <button onClick={onSeguir} className="rounded-md px-7 py-3 text-[14.5px] font-semibold text-white"
        style={{ background: C.azul }}>Continuar</button>
    </div>
  );
}

function Aviso({ children, tono = C.ambar }) {
  return (
    <Carta acento={tono} className="mb-6">
      <div className="p-5 flex gap-3">
        <CircleAlert size={19} color={tono} strokeWidth={2} className="shrink-0 mt-0.5" />
        <p className="text-[13.5px] leading-relaxed" style={{ color: C.texto }}>{children}</p>
      </div>
    </Carta>
  );
}

function Estado({ valor }) {
  if (valor === "guardado") return (
    <span className="flex items-center gap-1.5"><Check size={13} color={C.verde} strokeWidth={3} /> Guardado</span>
  );
  if (valor === "guardando") return (
    <span className="flex items-center gap-1.5"><Loader2 size={13} className="animate-spin" /> Guardando…</span>
  );
  if (valor === "sin_conexion") return (
    <span className="flex items-center gap-1.5" style={{ color: C.ambar }}>
      <CloudOff size={13} /> Sin conexión, reintentando
    </span>
  );
  return null;
}

/* ───────────────────────────── pantalla ───────────────────────────── */

export default function Cuestionario() {
  const { usuario, salir } = useAuth();
  const [cat, setCat] = useState(null);
  const [ses, setSes] = useState(null);
  const [resp, setResp] = useState({ fase1: {}, fase2: {}, fase3: {} });
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [lento, setLento] = useState(false);

  const [vista, setVista] = useState("portada");
  const [abierto, setAbierto] = useState(null);
  const [idxP, setIdxP] = useState(1), [pasoF1, setPasoF1] = useState(0);
  const [idxR, setIdxR] = useState(0), [idxC, setIdxC] = useState(0);
  const [guardado, setGuardado] = useState(null);
  const [eligiendo, setEligiendo] = useState(false);
  const [fade, setFade] = useState(false);

  const cola = useMemo(() => crearCola(setGuardado), []);
  const ir = fn => { setFade(true); setTimeout(() => { fn(); setFade(false); window.scrollTo(0, 0); }, 150); };

  /* Dónde retomar. Se deduce de las respuestas guardadas y no de paso_actual:
     si el último PUT se perdió por red, las respuestas siguen siendo la verdad. */
  const ubicar = (c, r) => {
    for (const p of [1, 2, 3, 4, 5]) {
      const pasos = p === 1 ? PASOS.filter(x => x.k !== "fav3") : PASOS;
      const dadas = r.fase1[p] || {};
      const falta = pasos.findIndex(x => !dadas[x.k]);
      if (falta !== -1) { setVista("f1"); setIdxP(p); setPasoF1(falta); return; }
    }
    const rFalta = c.reactivos.findIndex(x => r.fase2[x.numero] === undefined);
    if (rFalta !== -1) { setVista("f2"); setIdxR(rFalta); return; }
    const cFalta = c.contexto.findIndex(x => r.fase3[x.numero] === undefined);
    if (cFalta !== -1) { setVista("f3"); setIdxC(cFalta); return; }
    setVista("t3");
  };

  /* ── carga inicial: catálogo + progreso guardado ──
     En hospedaje gratuito el servidor se duerme tras unos minutos sin uso y
     tarda hasta un minuto en despertar. Si a los 4 segundos no ha respondido,
     se avisa: una pantalla en blanco larga se lee como que la app está rota. */
  useEffect(() => {
    const t = setTimeout(() => setLento(true), 4000);
    Promise.all([api.catalogo(), api.sesion()])
      .then(([c, s]) => {
        setCat(c);
        setSes(s.sesion);
        setResp(s.respuestas);
        if (s.sesion.estado === "completada") {
          return api.resultado().then(r => { setResultado(r); setVista("resultado"); });
        }
        if (s.sesion.paso_actual !== "fase0") ubicar(c, s.respuestas);
      })
      .catch(e => setError(e.message))
      .finally(() => { clearTimeout(t); setCargando(false); });
    return () => clearTimeout(t);
  }, []);

  const vencida = cat?.aplicacion?.vencida;
  const bloqueado = vencida || ses?.estado === "expirada";

  /* Guardado optimista: el estado local cambia ya, la cola reintenta si la red
     falla. El estudiante nunca espera a que el servidor responda. */
  const guardar = useCallback(payload => {
    if (!bloqueado) cola.encolar(payload);
  }, [cola, bloqueado]);

  const pasosDe = p => (p === 1 ? PASOS.filter(x => x.k !== "fav3") : PASOS);
  const sel = resp.fase1[idxP] || {};

  const entregar = async () => {
    setCargando(true);
    try {
      await api.completar();
      setResultado(await api.resultado());
      ir(() => setVista("resultado"));
    } catch (e) { setError(e.message); }
    finally { setCargando(false); }
  };

  const elegirF1 = ee => {
    if (Object.values(sel).includes(ee) || bloqueado) return;
    const pasos = pasosDe(idxP), paso = pasos[pasoF1];
    setResp(r => ({ ...r, fase1: { ...r.fase1, [idxP]: { ...(r.fase1[idxP] || {}), [paso.k]: ee } } }));
    guardar({ fase: "fase1", periodo: idxP, posicion: paso.k, ee, paso_actual: `f1-p${idxP}` });
    if (pasoF1 < pasos.length - 1) setPasoF1(pasoF1 + 1);
    else if (idxP < 5) ir(() => { setIdxP(idxP + 1); setPasoF1(0); });
    else ir(() => setVista("t2"));
  };

  const elegirF2 = op => {
    if (bloqueado) return;
    const n = cat.reactivos[idxR].numero;
    setResp(r => ({ ...r, fase2: { ...r.fase2, [n]: op.id } }));
    guardar({ fase: "fase2", reactivo: n, opcion: op.id, paso_actual: `f2-r${n}` });
    if (idxR < cat.reactivos.length - 1) ir(() => setIdxR(idxR + 1));
    else ir(() => setVista("t3"));
  };

  const elegirF3 = op => {
    if (bloqueado) return;
    const n = cat.contexto[idxC].numero;
    setResp(r => ({ ...r, fase3: { ...r.fase3, [n]: op.id } }));
    guardar({ fase: "fase3", pregunta: n, opcion: op.id, paso_actual: `f3-${n}` });
    if (idxC < cat.contexto.length - 1) ir(() => setIdxC(idxC + 1));
    else entregar();
  };

  const elegirDirecto = async id => {
    setEligiendo(true);
    try {
      await api.elegirBloque(id);
      setResultado(await api.resultado());
      ir(() => setVista("resultado"));
    } catch (e) { setError(e.message); }
    finally { setEligiendo(false); }
  };

  const responderFase0 = (yaDecidio, destino) => {
    guardar({ fase: "fase0", ya_decidio: yaDecidio,
              paso_actual: destino === "elegir" ? "fase0" : "f1-p1" });
    ir(() => { setVista(destino); setAbierto(null); });
  };

  useEffect(() => {
    const k = e => {
      const i = "abcdefg".indexOf(e.key.toLowerCase());
      const d = parseInt(e.key, 10) - 1;
      const j = i >= 0 ? i : (d >= 0 && d < 7 ? d : -1);
      if (j < 0 || !cat) return;
      if (vista === "f1" && j < cat.periodos[idxP].length) elegirF1(cat.periodos[idxP][j].clave);
      else if (vista === "f2" && j < cat.reactivos[idxR].opciones.length) elegirF2(cat.reactivos[idxR].opciones[j]);
      else if (vista === "f3" && j < cat.contexto[idxC].opciones.length) elegirF3(cat.contexto[idxC].opciones[j]);
    };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  });

  const prog = vista === "f1" ? 0.15 + 0.25 * (((idxP - 1) + pasoF1 / pasosDe(idxP).length) / 5)
    : vista === "f2" ? 0.40 + 0.40 * (idxR / (cat?.reactivos.length || 15))
    : vista === "f3" ? 0.80 + 0.20 * (idxC / (cat?.contexto.length || 5))
    : vista === "resultado" ? 1
    : (vista === "catalogo" || vista === "elegir") ? 0.08 : 0;

  const pantalla = "min-h-screen w-full flex flex-col items-center justify-center px-5 py-20";

  if (cargando && !cat) return (
    <div className="min-h-screen grid place-items-center px-6" style={{ background: C.fondo }}>
      <div className="text-center max-w-[380px]">
        <Loader2 className="animate-spin mx-auto" color={C.azul} size={26} />
        {lento && (
          <>
            <p className="mt-5 text-[14.5px] font-semibold" style={{ color: C.azul }}>
              Despertando el servidor…
            </p>
            <p className="mt-2 text-[13.5px] leading-relaxed" style={{ color: C.suave }}>
              La primera visita del día puede tardar hasta un minuto. Las siguientes
              son inmediatas. No cierres la pestaña.
            </p>
          </>
        )}
      </div>
    </div>
  );

  if (error && !cat) return (
    <div className="min-h-screen grid place-items-center px-6" style={{ background: C.fondo }}>
      <div className="max-w-[420px] w-full">
        <Aviso>{error}</Aviso>
        <button onClick={() => window.location.reload()}
          className="rounded-md px-5 py-2.5 text-[14px] font-semibold text-white" style={{ background: C.azul }}>
          Reintentar
        </button>
      </div>
    </div>
  );

  return (
    <div style={{ background: C.fondo, minHeight: "100vh" }}>
      <div className="fixed top-0 left-0 right-0 h-1 z-30" style={{ background: C.borde }}>
        <div className="h-full" style={{ width: `${prog * 100}%`, background: C.verde,
          transition: "width .4s cubic-bezier(.22,1,.36,1)" }} />
      </div>

      <div className="fixed top-4 right-4 z-30 flex items-center gap-3">
        <span className="text-[12px]" style={{ color: C.suave }}><Estado valor={guardado} /></span>
        <button onClick={salir}
          className="flex items-center gap-2 rounded-md px-4 py-2.5 text-[13.5px] font-semibold"
          style={{ background: C.carta, color: C.azul, border: `1.5px solid ${C.azul}`,
            boxShadow: "0 1px 3px rgba(15,23,42,.08)" }}>
          <LogOut size={15} strokeWidth={2.2} /> Salir
        </button>
      </div>

      <div style={{ opacity: fade ? 0 : 1, transition: "opacity .15s" }}>

        {/* portada */}
        {vista === "portada" && (
          <div className={pantalla}>
            <div className="w-full max-w-[660px]">
              <div className="flex items-center gap-2 mb-4">
                <GraduationCap size={19} color={C.verde} strokeWidth={2} />
                <span className="text-[12.5px] font-semibold" style={{ color: C.verde }}>
                  Gestión y Dirección de Negocios · FCA · UV
                </span>
              </div>
              <h1 className="text-[36px] sm:text-[46px] font-extrabold leading-[1.08] mb-5" style={{ color: C.azul }}>
                Hola {usuario?.nombre?.split(" ")[0]}.<br />Elige el área terminal<br />en la que te vas a especializar.
              </h1>
              <p className="text-[16px] leading-relaxed mb-4" style={{ color: C.texto }}>
                En sexto, séptimo y octavo cursas tres experiencias educativas optativas.
                No se eligen sueltas: forman un bloque. Ese bloque es lo que te vuelve
                especialista en algo concreto y es lo primero que un empleador lee en tu currículum.
              </p>
              <p className="text-[14.5px] leading-relaxed mb-8" style={{ color: C.suave }}>
                Primero vas a ver los bloques. Si ya sabes cuál quieres, lo eliges y terminas.
                Si no, contestarás un breve un cuestionario de unos doce minutos. 
              </p>

              {bloqueado ? (
                <Aviso tono={C.suave}>
                  <span className="flex items-center gap-2 font-semibold mb-1">
                    <Lock size={15} /> La fecha límite ya pasó
                  </span>
                  Este periodo cerró el {new Date(cat.aplicacion.fecha_limite)
                    .toLocaleDateString("es-MX", { day: "numeric", month: "long", year: "numeric" })}.
                  Habla con tu tutor para registrar tu bloque.
                </Aviso>
              ) : (
                <>
                  <button onClick={() => ir(() => setVista("catalogo"))}
                    className="rounded-md px-8 py-3.5 text-[15px] font-semibold text-white"
                    style={{ background: C.azul }}>
                    Ver los bloques
                  </button>
                  <p className="mt-4 text-[12.5px]" style={{ color: C.suave }}>
                    Tienes hasta el {new Date(cat.aplicacion.fecha_limite)
                      .toLocaleDateString("es-MX", { day: "numeric", month: "long" })}.
                  </p>
                </>
              )}
            </div>
          </div>
        )}

        {/* catálogo */}
        {vista === "catalogo" && (
          <div className="min-h-screen w-full px-5 py-16">
            <div className="w-full max-w-[780px] mx-auto">
              <Seccion icono={Layers} titulo={`Los ${cat.itinerarios.length} bloques de área terminal`}>
                <p className="text-[14px] leading-relaxed mb-5" style={{ color: C.texto }}>
                  Toca cualquiera para conocerlo.
                </p>
                {cat.itinerarios.map(b => (
                  <Acordeon key={b.id} bloque={b} abierto={abierto === b.id}
                    onToggle={() => setAbierto(abierto === b.id ? null : b.id)} />
                ))}
              </Seccion>
              <button onClick={() => ir(() => setVista("decision"))}
                className="rounded-md px-8 py-3.5 text-[15px] font-semibold text-white" style={{ background: C.azul }}>
                Ya los revisé
              </button>
            </div>
          </div>
        )}

        {/* decisión */}
        {vista === "decision" && (
          <div className={pantalla}>
            <div className="w-full max-w-[620px]">
              <div className="flex items-center gap-2 mb-3">
                <Compass size={18} color={C.verde} strokeWidth={2} />
                <span className="text-[12.5px] font-semibold" style={{ color: C.verde }}>Punto de partida</span>
              </div>
              <h2 className="text-[30px] sm:text-[34px] font-bold leading-tight mb-6" style={{ color: C.azul }}>
                Después de leerlos, ¿ya sabes cuál quieres?. 
              </h2>
              <p className="text-[30px] sm:text-[34px] font-bold leading-tight mb-6" style={{ color: C.azul }}>
                
              </p>
              <div className="flex flex-col gap-2.5">
                <Opcion letra="A" texto="Sí, ya sé cuál quiero" onClick={() => responderFase0(true, "elegir")} />
                <Opcion letra="B" texto="Dudo entre dos o tres" onClick={() => responderFase0(false, "t1")} />
                <Opcion letra="C" texto="No tengo idea" onClick={() => responderFase0(false, "t1")} />
              </div>
              <p className="mt-6 text-[13px] leading-relaxed" style={{ color: C.suave }}>
                Si seleccionas la opción A, registras tu bloque y terminas la actividad. Si eliges la opción B o C, realizarás un cuestionario que te sugerirá un bloque. 
                Recuerda responder con calma y honestamente.
              </p>
            </div>
          </div>
        )}

        {/* elección directa */}
        {vista === "elegir" && (
          <div className="min-h-screen w-full px-5 py-16">
            <div className="w-full max-w-[780px] mx-auto">
              <Seccion icono={Check} titulo="Elige tu bloque">
                <p className="text-[14px] leading-relaxed mb-5" style={{ color: C.texto }}>
                  Ábrelo, revísalo una última vez y confirma. Puedes cambiarlo con tu tutor
                  antes de la fecha de inscripción.
                </p>
                {error && <Aviso>{error}</Aviso>}
                {cat.itinerarios.map(b => (
                  <Acordeon key={b.id} bloque={b} abierto={abierto === b.id} eligiendo={eligiendo}
                    onToggle={() => setAbierto(abierto === b.id ? null : b.id)}
                    onElegir={() => elegirDirecto(b.id)} />
                ))}
              </Seccion>
            </div>
          </div>
        )}

        {/* transiciones */}
        {vista === "t1" && (
          <div className={pantalla}>
            <Transicion icono={ClipboardList} antetitulo="Parte 1 de 3"
              titulo="Empecemos por lo que ya cursaste"
              texto="De cada periodo, del primero al quinto, vas a escoger las Experiencias que más te gustaron y la que menos. Toma en cuenta que lo importante no es tu calificación, sino las experiencias educativas que te resultaron interesantes, ya que de ello depende la mitad de este diagnóstico. Responde con calma y contesta todas las preguntas"
              onSeguir={() => ir(() => setVista("f1"))} />
          </div>
        )}
        {vista === "t2" && (
          <div className={pantalla}>
            <Transicion icono={Compass} antetitulo="Parte 2 de 3"
              titulo="Ahora, cómo trabajas"
              texto={`${cat.reactivos.length} situaciones con cuatro alternativas distintas. No hay respuesta correcta y ninguna opción es mejor que otra: Elige la que se adapta más a ti.`}
              onSeguir={() => ir(() => setVista("f2"))} />
          </div>
        )}
        {vista === "t3" && (
          <div className={pantalla}>
            <Transicion icono={CircleAlert} antetitulo="Parte 3 de 3"
              titulo="Cinco preguntas de contexto"
              texto="Estas no miden gustos. Sirven para no recomendarte algo que no puedas cursar, como un bloque en inglés si todavía no lo dominas, o prácticas en el puerto si no puedes salir de Xalapa."
              onSeguir={() => ir(() => setVista("f3"))} />
          </div>
        )}

        {/* fase 1 */}
        {vista === "f1" && cat.periodos[idxP] && (() => {
          const pasos = pasosDe(idxP), paso = pasos[pasoF1];
          return (
            <div className={pantalla}>
              <div className="w-full max-w-[620px]">
                <p className="text-[12.5px] font-semibold mb-2" style={{ color: C.verde }}>
                  Periodo {ROMANO[idxP]} · paso {pasoF1 + 1} de {pasos.length}
                </p>
                <h2 className="text-[26px] sm:text-[31px] font-bold leading-tight mb-7" style={{ color: C.azul }}>
                  {paso.prompt}
                </h2>
                <div className="flex flex-col gap-2.5">
                  {cat.periodos[idxP].map((ee, i) => {
                    const pos = Object.entries(sel).find(([, v]) => v === ee.clave)?.[0];
                    return <Opcion key={ee.clave} letra={"ABCDEFG"[i]} texto={ee.nombre}
                      onClick={() => elegirF1(ee.clave)}
                      badge={pos ? PASOS.find(x => x.k === pos).badge : null} />;
                  })}
                </div>
                <p className="mt-5 text-[13px]" style={{ color: C.suave }}>
                  {paso.k === "rechazada"
                    ? "Esta también cuenta: saber qué no te late acota tanto como saber qué sí."
                    : "Piensa en la clase, no en la calificación."}
                </p>
              </div>
            </div>
          );
        })()}

        {/* fase 2 */}
        {vista === "f2" && cat.reactivos[idxR] && (
          <div className={pantalla}>
            <div className="w-full max-w-[620px]">
              <p className="text-[12.5px] font-semibold mb-2" style={{ color: C.verde }}>
                Situación {idxR + 1} de {cat.reactivos.length}
              </p>
              <h2 className="text-[25px] sm:text-[30px] font-bold leading-tight mb-7" style={{ color: C.azul }}>
                {cat.reactivos[idxR].enunciado}
              </h2>
              <div className="flex flex-col gap-2.5">
                {cat.reactivos[idxR].opciones.map((op, i) => (
                  <Opcion key={op.id} letra={"ABCD"[i]} texto={op.texto}
                    elegida={resp.fase2[cat.reactivos[idxR].numero] === op.id}
                    onClick={() => elegirF2(op)} />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* fase 3 */}
        {vista === "f3" && cat.contexto[idxC] && (
          <div className={pantalla}>
            <div className="w-full max-w-[620px]">
              <p className="text-[12.5px] font-semibold mb-2" style={{ color: C.verde }}>
                Contexto {idxC + 1} de {cat.contexto.length}
              </p>
              <h2 className="text-[25px] sm:text-[30px] font-bold leading-tight mb-7" style={{ color: C.azul }}>
                {cat.contexto[idxC].enunciado}
              </h2>
              <div className="flex flex-col gap-2.5">
                {cat.contexto[idxC].opciones.map((op, i) => (
                  <Opcion key={op.id} letra={"ABC"[i]} texto={op.texto}
                    elegida={resp.fase3[cat.contexto[idxC].numero] === op.id}
                    onClick={() => elegirF3(op)} />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* resultado */}
        {vista === "resultado" && resultado && (() => {
          const directo = resultado.origen === "eleccion_directa";
          const g = directo ? resultado.bloque : resultado.recomendado;
          const Ico = g ? iconoDe(g.id) : Layers;
          return (
            <div className="min-h-screen w-full px-5 py-16">
              <div className="w-full max-w-[720px] mx-auto">
                <div className="flex items-center gap-2 mb-3">
                  <Check size={18} color={C.verde} strokeWidth={2.5} />
                  <span className="text-[12.5px] font-semibold" style={{ color: C.verde }}>
                    {directo ? "Registrado" : "Tu resultado"}
                  </span>
                </div>

                {!g ? (
                  <>
                    <h1 className="text-[28px] sm:text-[34px] font-extrabold leading-[1.14] mb-4" style={{ color: C.azul }}>
                      Tus respuestas no marcan una inclinación clara todavía.
                    </h1>
                    <p className="text-[15px] leading-relaxed mb-8" style={{ color: C.texto }}>
                      Ningún bloque se despegó de los demás. Eso pasa y no está mal, pero conviene
                      que lo platiques con tu tutor antes de inscribir. Abajo está el orden que sí salió.
                    </p>
                  </>
                ) : (
                  <>
                    <h2 className="text-[17px] font-medium mb-2" style={{ color: C.suave }}>
                      {directo ? "Al terminar vas a ser" : "Según tus respuestas, deberías ser"}
                    </h2>
                    <h1 className="text-[30px] sm:text-[40px] font-extrabold leading-[1.1] mb-6" style={{ color: C.azul }}>
                      un {g.frase}.
                    </h1>
                    <Carta acento={C.verde} className="mb-6">
                      <div className="p-5">
                        <div className="flex items-center gap-2.5 mb-3">
                          <Ico size={19} color={C.verde} strokeWidth={2} />
                          <h3 className="text-[16px] font-bold" style={{ color: C.verdeOs }}>{g.nombre}</h3>
                        </div>
                        <p className="text-[13.5px] leading-relaxed mb-4 text-justify" style={{ color: C.texto }}>
                          {g.perfil}
                        </p>
                        <div className="grid sm:grid-cols-3 gap-2 mb-4">
                          {g.optativas.map((o, i) => (
                            <Pill key={o.clave} tono={i % 2 === 0 ? "azul" : "verde"}>{o.nombre}</Pill>
                          ))}
                        </div>
                        <div className="grid sm:grid-cols-3 gap-2">
                          {(g.salidas || []).map((s, i) => (
                            <Pill key={s} tono={i % 2 === 0 ? "verde" : "azul"}>{s}</Pill>
                          ))}
                        </div>
                      </div>
                    </Carta>
                  </>
                )}

                {resultado.alerta_debil && (
                  <Aviso>
                    Este bloque te queda bien salvo por <strong>{resultado.alerta_debil.nombre}</strong>,
                    que en tu orden individual quedó en el lugar {resultado.alerta_debil.posicion} de 15.
                    Vas a tener que cursarla igual: los bloques no se desarman. Tenlo presente
                    antes de confirmar.
                  </Aviso>
                )}

                {resultado.empate_tecnico && (
                  <Aviso>
                    El primero y el segundo quedaron casi empatados. Léelos otra vez con calma y
                    decide con tu tutor: aquí el sistema no tiene una respuesta mejor que la tuya.
                  </Aviso>
                )}

                {!directo && resultado.explicacion?.razones?.length > 0 && (
                  <Seccion icono={ClipboardList} titulo="Por qué salió este">
                    <Carta>
                      <div className="p-5">
                        <ul className="flex flex-col gap-2">
                          {resultado.explicacion.razones.map((r, i) => (
                            <li key={i} className="text-[13.5px] leading-relaxed flex gap-2" style={{ color: C.texto }}>
                              <span style={{ color: C.verde }}>—</span>{r}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </Carta>
                  </Seccion>
                )}

                {!directo && resultado.alternativos?.length > 0 && (
                  <Seccion icono={Layers} titulo="Las otras dos que más te acomodan">
                    {resultado.alternativos.map(b => {
                      const I = iconoDe(b.id);
                      return (
                        <Carta key={b.id} className="mb-2.5">
                          <div className="px-4 py-3.5 flex items-center gap-3">
                            <I size={17} color={C.azulMed} strokeWidth={2} className="shrink-0" />
                            <span className="flex-1 min-w-0">
                              <span className="block text-[14px] font-semibold" style={{ color: C.azulMed }}>
                                {b.nombre}
                              </span>
                              <span className="block text-[12.5px] mt-0.5" style={{ color: C.suave }}>
                                {b.resumen}
                              </span>
                            </span>
                            <span className="text-[13px] font-bold tabular-nums shrink-0" style={{ color: C.verde }}>
                              {Math.round(b.indice)}
                            </span>
                          </div>
                        </Carta>
                      );
                    })}
                  </Seccion>
                )}

                {!directo && resultado.ranking && (
                  <Seccion icono={Layers} titulo="Todos, en tu orden">
                    <Carta>
                      <div className="p-4 flex flex-col gap-2.5">
                        {resultado.ranking.map((b, i) => (
                          <div key={b.id} className="flex items-center gap-3">
                            <span className="w-5 text-right text-[11px] font-bold tabular-nums" style={{ color: C.suave }}>
                              {i + 1}
                            </span>
                            <span className="w-[44%] truncate text-[12.5px]" style={{ color: i < 3 ? C.texto : C.suave }}>
                              {b.nombre}
                            </span>
                            <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: C.borde }}>
                              <div className="h-full rounded-full" style={{ width: `${b.indice}%`,
                                background: i === 0 ? C.verde : i < 3 ? C.azulMed : "#CBD5E1" }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </Carta>
                  </Seccion>
                )}

                <p className="text-[13px] leading-relaxed" style={{ color: C.suave }}>
                  La jefatura de carrera ya tiene tu registro. Se usará como guía para la apertura de las experiencias educativas optativas que se ofertarán en tus próximos periodos escolares. Gracias
                </p>
              </div>
            </div>
          );
        })()}
      </div>
    </div>
  );
}
