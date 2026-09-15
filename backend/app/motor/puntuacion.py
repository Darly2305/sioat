"""
Motor de puntuación. Sin dependencias de Flask ni de la base de datos:
recibe respuestas, devuelve el ranking de los 13 bloques de área terminal.

Cambio de fondo respecto a la v2: el resultado que se entrega al estudiante es
un BLOQUE, no optativas sueltas. El ranking individual de las 15 optativas se
sigue calculando —se necesita para puntuar bloques y es diagnóstico valioso
para la coordinación— pero es interno.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import datos as D


@dataclass
class Respuestas:
    """Lo que el estudiante ha contestado hasta ahora. Todo es opcional: el
    motor puntúa un cuestionario incompleto, que es lo que permite guardar
    progreso y mostrar avances parciales."""
    fase1: Dict[int, Dict[str, str]] = field(default_factory=dict)
    fase2: Dict[int, str] = field(default_factory=dict)
    fase3: Dict[int, str] = field(default_factory=dict)


@dataclass
class Optativa:
    clave: str
    nombre: str
    academia: str
    f1: float
    f2: float
    ajuste_f3: float
    afinidad: float
    posicion: int


@dataclass
class Bloque:
    id: int
    nombre: str
    frase: str
    resumen: str
    perfil: str
    salidas: List[str]
    optativas: List[str]
    media: float
    peor: float
    score: float
    indice: float          # 0-100, relativo a los 13 del propio estudiante
    posicion: int
    optativa_debil: str    # la de menor afinidad dentro del bloque
    pos_debil: int         # su lugar en el ranking individual de 15
    alerta_debil: bool     # ¿hay que advertirlo en el reporte?


@dataclass
class Resultado:
    bloques: List[Bloque]
    optativas: List[Optativa]
    perfil_academias: Dict[str, float]
    recomendado: Optional[Bloque]
    alternativos: List[Bloque]
    empate_tecnico: bool
    perfil_plano: bool
    advertencias: List[str]
    completitud: Dict[str, float]


# ---------------------------------------------------------------- fase 1
def perfil_academias(fase1: Dict[int, Dict[str, str]]) -> Dict[str, float]:
    """Puntos por academia, normalizados contra el máximo alcanzable de cada
    una. Sin normalizar, Administración (7 EE entre I y V) aplastaría a
    Tecnologías (1 EE) y mediríamos el plan de estudios, no al estudiante."""
    ee_academia = {c: a for ees in D.EE_CURRICULARES.values() for c, _, a in ees}
    crudos = {a: 0 for a in D.ACADEMIAS}
    for periodo, sel in fase1.items():
        for posicion, clave_ee in sel.items():
            if not clave_ee or posicion not in D.PUNTOS:
                continue
            if periodo in D.PERIODOS_SIN_FAV3 and posicion == "fav3":
                continue
            acad = ee_academia.get(clave_ee)
            if acad:
                crudos[acad] += D.PUNTOS[posicion]
    return {a: max(0.0, crudos[a]) / D.MAX_ACADEMIA[a] for a in D.ACADEMIAS}


def _f1_optativa(clave: str, perfil: Dict[str, float]) -> float:
    pesos = D.PESOS[clave]
    return sum(perfil[a] * pesos[a] for a in D.ACADEMIAS) / sum(pesos.values())


# ---------------------------------------------------------------- fases 2 y 3
def puntos_fase2(fase2: Dict[int, str]) -> Dict[str, int]:
    idx = {n: {l: o for l, _, o in ops} for n, _, ops in D.REACTIVOS}
    pts = {k: 0 for k in D.OPTATIVAS}
    for numero, letra in fase2.items():
        opt = idx.get(numero, {}).get(letra)
        if opt:
            pts[opt] += D.PUNTOS_REACTIVO
    return pts


def ajustes_fase3(fase3: Dict[int, str]):
    idx = {n: {l: aj for l, _, aj in ops} for n, _, ops, _ in D.PREGUNTAS_CONTEXTO}
    notas = {n: t for n, _, _, t in D.PREGUNTAS_CONTEXTO}
    ajustes = {k: 0.0 for k in D.OPTATIVAS}
    advertencias: List[str] = []
    for numero, letra in fase3.items():
        aj = idx.get(numero, {}).get(letra)
        if aj:
            for opt, delta in aj.items():
                ajustes[opt] += delta
            advertencias.append(notas[numero])
    t = D.TOPE_FASE3
    return {k: max(-t, min(t, v)) for k, v in ajustes.items()}, advertencias


# ---------------------------------------------------------------- motor
def calcular(resp: Respuestas) -> Resultado:
    perfil = perfil_academias(resp.fase1)
    pts2 = puntos_fase2(resp.fase2)
    aj3, advertencias = ajustes_fase3(resp.fase3)

    filas = []
    for clave, meta in D.OPTATIVAS.items():
        f1 = _f1_optativa(clave, perfil)
        f2 = pts2[clave] / D.MAX_FASE2
        filas.append(Optativa(
            clave=clave, nombre=meta["nombre"], academia=meta["academia"],
            f1=round(f1, 4), f2=round(f2, 4), ajuste_f3=aj3[clave],
            afinidad=round((D.PESO_FASE1 * f1 + D.PESO_FASE2 * f2) * 100 + aj3[clave], 2),
            posicion=0))
    filas.sort(key=lambda r: r.afinidad, reverse=True)
    for i, f in enumerate(filas, start=1):
        f.posicion = i

    por_clave = {f.clave: f for f in filas}
    lugar = {f.clave: f.posicion for f in filas}

    bloques = []
    for b in D.ITINERARIOS:
        vals = [por_clave[o].afinidad for o in b["opts"]]
        media = sum(vals) / len(vals)
        peor = min(vals)
        debil = b["opts"][vals.index(peor)]
        bloques.append(Bloque(
            id=b["id"], nombre=b["nombre"], frase=b["frase"], resumen=b["resumen"],
            perfil=b["perfil"], salidas=b["salidas"], optativas=b["opts"],
            media=round(media, 2), peor=round(peor, 2),
            score=round(D.PESO_MEDIA_BLOQUE * media + D.PESO_PEOR_BLOQUE * peor, 2),
            indice=0.0, posicion=0,
            optativa_debil=debil, pos_debil=lugar[debil],
            alerta_debil=lugar[debil] >= D.UMBRAL_MATERIA_DEBIL))

    bloques.sort(key=lambda b: b.score, reverse=True)
    hi, lo = bloques[0].score, bloques[-1].score
    rango = (hi - lo) or 1.0
    for i, b in enumerate(bloques, start=1):
        b.posicion = i
        b.indice = round((b.score - lo) / rango * 100, 1)

    # Dispersión: si los 13 quedan casi iguales, el estudiante contestó al azar
    # o de verdad no tiene inclinación. En los dos casos, no fingir certeza.
    media_g = sum(b.score for b in bloques) / len(bloques)
    sd = (sum((b.score - media_g) ** 2 for b in bloques) / len(bloques)) ** 0.5
    plano = sd < 2.5
    empate = (bloques[0].score - bloques[1].score) < 3.0

    return Resultado(
        bloques=bloques, optativas=filas,
        perfil_academias={a: round(v, 3) for a, v in perfil.items()},
        recomendado=None if plano else bloques[0],
        alternativos=bloques[1:3],
        empate_tecnico=empate, perfil_plano=plano, advertencias=advertencias,
        completitud={
            "fase1": len(resp.fase1) / len(D.EE_CURRICULARES),
            "fase2": len(resp.fase2) / len(D.REACTIVOS),
            "fase3": len(resp.fase3) / len(D.PREGUNTAS_CONTEXTO),
        })


def explicar(resp: Respuestas, res: Resultado, n: int = 3) -> List[str]:
    """Las n respuestas que más empujaron al bloque ganador. El reporte nunca
    entrega un veredicto sin mostrar de dónde salió."""
    if not res.bloques:
        return []
    ganador = res.bloques[0]
    pesos = {a: sum(D.PESOS[o][a] for o in ganador.optativas) / 3 for a in D.ACADEMIAS}
    ee_meta = {c: (nom, ac) for ees in D.EE_CURRICULARES.values() for c, nom, ac in ees}
    contribuciones = []

    for periodo, sel in resp.fase1.items():
        for posicion, clave_ee in sel.items():
            if posicion == "rechazada" or clave_ee not in ee_meta:
                continue
            nom, acad = ee_meta[clave_ee]
            contribuciones.append((D.PUNTOS[posicion] * pesos[acad],
                                   f"elegiste «{nom}» entre tus favoritas del periodo {periodo}"))

    idx = {num: {l: (txt, o) for l, txt, o in ops} for num, _, ops in D.REACTIVOS}
    for numero, letra in resp.fase2.items():
        par = idx.get(numero, {}).get(letra)
        if par and par[1] in ganador.optativas:
            contribuciones.append((float(D.PUNTOS_REACTIVO), f"respondiste «{par[0]}»"))

    contribuciones.sort(reverse=True, key=lambda x: x[0])
    return [t for _, t in contribuciones[:n]]
