"""
Corre perfiles sintéticos contra el motor para ver si discrimina.
Lo que buscamos: que ninguna optativa gane siempre ni pierda siempre,
y que perfiles distintos produzcan recomendaciones distintas.
"""
import sys, os
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.motor import datos as D
from app.motor.puntuacion import Respuestas, calcular, explicar

EE_POR_ACAD = {}
for per, ees in D.EE_CURRICULARES.items():
    for clave, nom, acad in ees:
        EE_POR_ACAD.setdefault((per, acad), []).append(clave)


def fase1_sintetica(prioridad, rechazo):
    """Arma una fase 1 donde el alumno elige, en cada periodo, las materias
    de las academias en `prioridad` (en orden) y rechaza la de `rechazo`."""
    out = {}
    for per, ees in D.EE_CURRICULARES.items():
        disponibles = [c for c, _, _ in ees]
        acad_de = {c: a for c, _, a in ees}
        elegidas = []
        for acad in prioridad:
            for c in disponibles:
                if acad_de[c] == acad and c not in elegidas:
                    elegidas.append(c)
                    break
        for c in disponibles:
            if c not in elegidas:
                elegidas.append(c)
        n = 2 if per in D.PERIODOS_SIN_FAV3 else 3
        sel = {}
        for i, pos in enumerate(["fav1", "fav2", "fav3"][:n]):
            sel[pos] = elegidas[i]
        rech = next((c for c in reversed(elegidas)
                     if acad_de[c] == rechazo and c not in sel.values()), None)
        sel["rechazada"] = rech or elegidas[-1]
        out[per] = sel
    return out


def fase2_sintetica(preferidas):
    """En cada reactivo elige la opción cuya optativa esté más arriba en
    `preferidas`; si ninguna aparece, elige la primera."""
    resp = {}
    for num, _, ops in D.REACTIVOS:
        mejor, mejor_rank = ops[0][0], 999
        for letra, _, opt in ops:
            if opt in preferidas and preferidas.index(opt) < mejor_rank:
                mejor, mejor_rank = letra, preferidas.index(opt)
        resp[num] = mejor
    return resp


PERFILES = {
    "Le gustan los números y el dinero": dict(
        prioridad=["MAT", "CYF", "ECO"], rechazo="MKT",
        prefiere=["LE", "SI", "EI", "PCE"], ctx={1: "b", 2: "a", 3: "a", 4: "b", 5: "a"}),
    "Le gustan las redes y el diseño": dict(
        prioridad=["MKT", "TEC", "EMP"], rechazo="MAT",
        prefiere=["CCD", "CE", "GC", "ES"], ctx={1: "b", 2: "b", 3: "b", 4: "b", 5: "c"}),
    "Le gusta la gente y el trato": dict(
        prioridad=["TH", "ADM", "VEI"], rechazo="MAT",
        prefiere=["CO", "FCD", "GCO", "GEF"], ctx={1: "a", 2: "b", 3: "c", 4: "a", 5: "c"}),
    "Le gustan las leyes y lo público": dict(
        prioridad=["DER", "ADM", "ECO"], rechazo="MKT",
        prefiere=["GP", "GA", "DS", "SI"], ctx={1: "c", 2: "a", 3: "a", 4: "b", 5: "b"}),
    "Quiere emprender con causa": dict(
        prioridad=["EMP", "ECO", "ADM"], rechazo="CYF",
        prefiere=["ES", "DS", "CE", "GC"], ctx={1: "b", 2: "a", 3: "c", 4: "a", 5: "b"}),
    "Le gusta operar y organizar": dict(
        prioridad=["ADM", "MAT", "TEC"], rechazo="VEI",
        prefiere=["LE", "GCO", "GA", "GEF"], ctx={1: "b", 2: "a", 3: "b", 4: "b", 5: "a"}),
    "No tiene preferencia clara": dict(
        prioridad=["ADM", "MKT", "TH"], rechazo="DER",
        prefiere=[], ctx={1: "b", 2: "a", 3: "c", 4: "b", 5: "c"}),
}

ganadores, top3_global = Counter(), Counter()
print("=" * 78)
for nombre, p in PERFILES.items():
    r = Respuestas(
        fase1=fase1_sintetica(p["prioridad"], p["rechazo"]),
        fase2=fase2_sintetica(p["prefiere"]),
        fase3=p["ctx"],
    )
    res = calcular(r)
    ganadores[res.bloques[0].id] += 1
    for b in res.bloques[:3]:
        top3_global[b.id] += 1

    print(f"\n▸ {nombre}")
    g = res.bloques[0]
    print(f"    → un {g.frase}")
    print(f"      {g.nombre}  (índice {g.indice:.0f}, media {g.media:.1f}, peor {g.peor:.1f})")
    print(f"      {' · '.join(D.OPTATIVAS[o]['nombre'][:26] for o in g.optativas)}")
    for b in res.alternativos:
        print(f"      luego: {b.nombre[:48]:<50} {b.indice:>5.0f}")
    if g.alerta_debil:
        print(f"    ⚠ materia floja: {D.OPTATIVAS[g.optativa_debil]['nombre']} (lugar {g.pos_debil}/15)")
    if res.empate_tecnico:
        print("    ⚠ empate técnico entre el 1º y el 2º")
    if res.perfil_plano:
        print("    ⚠ perfil plano: no hay inclinación clara")
    print(f"    porque: {explicar(r, res, 2)[0]}")

print("\n" + "=" * 78)
print("COBERTURA — cuántas veces cada bloque quedó en el top 3 de los 7 perfiles\n")
for b in D.ITINERARIOS:
    n = top3_global[b["id"]]
    print(f"  {b['id']:>2}. {b['nombre'][:46]:<48} {n}  {'█'*n if n else '·'}")

nunca = [b['nombre'] for b in D.ITINERARIOS if top3_global[b['id']] == 0]
print(f"\n  Bloques que nunca aparecieron: {len(nunca)}")
for n in nunca:
    print(f"    - {n}")
print(f"  Primeros lugares distintos: {len(ganadores)} de {len(PERFILES)} perfiles")
