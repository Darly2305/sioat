"""
Catálogos del sistema de orientación LGDN 2024.

Todo lo que aquí aparece proviene del plan de estudios 2024:
  - Tabla 14  -> las 15 experiencias educativas optativas del AFT
  - Tabla 22  -> agrupación de EE por academia / área de conocimiento
  - Mapa curricular -> distribución por periodo

Los ÚNICOS valores que no provienen del plan son los de PESOS
(matriz academia x optativa). Esos son criterio de diseño y deben ser
validados por las diez coordinaciones de academia antes de producción.
"""

# --------------------------------------------------------------------------
# Academias (tabla 22)
# --------------------------------------------------------------------------
ACADEMIAS = [
    "ADM",  # Administración
    "CYF",  # Contabilidad y finanzas
    "DER",  # Derecho
    "ECO",  # Economía
    "EMP",  # Emprendimiento e innovación
    "MAT",  # Matemáticas
    "MKT",  # Mercadotecnia
    "TH",   # Talento humano
    "TEC",  # Tecnologías
    "VEI",  # Vinculación e investigación
]

ACADEMIA_NOMBRE = {
    "ADM": "Administración",
    "CYF": "Contabilidad y finanzas",
    "DER": "Derecho",
    "ECO": "Economía",
    "EMP": "Emprendimiento e innovación",
    "MAT": "Matemáticas",
    "MKT": "Mercadotecnia",
    "TH": "Talento humano",
    "TEC": "Tecnologías",
    "VEI": "Vinculación e investigación",
}

# --------------------------------------------------------------------------
# Las 15 optativas del AFT (tabla 14)
# --------------------------------------------------------------------------
OPTATIVAS = {
    "EI":  {"nombre": "Economía internacional",                                  "academia": "ECO", "creditos": 6},
    "GA":  {"nombre": "Gestión aduanal",                                         "academia": "ECO", "creditos": 6},
    "PCE": {"nombre": "Proyectos de comercio exterior",                          "academia": "ECO", "creditos": 7},
    "DS":  {"nombre": "Desarrollo sustentable",                                  "academia": "ECO", "creditos": 6},
    "GEF": {"nombre": "Gestión de empresas familiares",                          "academia": "ADM", "creditos": 6},
    "GC":  {"nombre": "Gestión cultural",                                        "academia": "ADM", "creditos": 6},
    "GP":  {"nombre": "Gestión pública",                                         "academia": "ADM", "creditos": 6},
    "LE":  {"nombre": "Logística empresarial",                                   "academia": "ADM", "creditos": 6},
    "FCD": {"nombre": "Fundamental concepts of directive competences in business","academia": "ADM", "creditos": 6, "idioma": "en"},
    "CE":  {"nombre": "Comercio electrónico",                                    "academia": "MKT", "creditos": 6},
    "CCD": {"nombre": "Creación de contenidos digitales",                        "academia": "MKT", "creditos": 6},
    "CO":  {"nombre": "Comportamiento organizacional",                           "academia": "TH",  "creditos": 6},
    "GCO": {"nombre": "Gestión del conocimiento organizacional",                 "academia": "TH",  "creditos": 6},
    "ES":  {"nombre": "Emprendimiento social",                                   "academia": "EMP", "creditos": 6},
    "SI":  {"nombre": "Seminario de investigación",                              "academia": "VEI", "creditos": 6},
}

# --------------------------------------------------------------------------
# Matriz de afinidad academia x optativa   (0.0 - 1.0)
# Orden de columnas: ADM CYF DER ECO EMP MAT MKT TH TEC VEI
# --------------------------------------------------------------------------
_COLS = ACADEMIAS
_M = {
    "EI":  [0.3, 0.7, 0.5, 1.0, 0.2, 0.5, 0.2, 0.0, 0.1, 0.3],
    "GA":  [0.5, 0.5, 0.8, 1.0, 0.1, 0.4, 0.1, 0.0, 0.3, 0.2],
    "PCE": [0.6, 0.7, 0.5, 1.0, 0.4, 0.5, 0.3, 0.1, 0.2, 0.4],
    "DS":  [0.5, 0.2, 0.5, 1.0, 0.5, 0.2, 0.2, 0.2, 0.2, 0.5],
    "GEF": [1.0, 0.6, 0.4, 0.2, 0.5, 0.2, 0.3, 0.7, 0.1, 0.3],
    "GC":  [1.0, 0.2, 0.2, 0.2, 0.4, 0.1, 0.7, 0.3, 0.2, 0.4],
    "GP":  [1.0, 0.4, 0.8, 0.6, 0.2, 0.2, 0.1, 0.3, 0.2, 0.4],
    "LE":  [1.0, 0.5, 0.2, 0.5, 0.2, 0.8, 0.3, 0.1, 0.7, 0.1],
    "FCD": [1.0, 0.3, 0.2, 0.3, 0.4, 0.2, 0.3, 0.8, 0.2, 0.3],
    "CE":  [0.5, 0.3, 0.3, 0.3, 0.5, 0.3, 1.0, 0.0, 0.9, 0.1],
    "CCD": [0.3, 0.1, 0.1, 0.0, 0.4, 0.1, 1.0, 0.2, 0.6, 0.2],
    "CO":  [0.6, 0.1, 0.2, 0.1, 0.2, 0.2, 0.2, 1.0, 0.1, 0.4],
    "GCO": [0.6, 0.1, 0.1, 0.1, 0.3, 0.2, 0.2, 1.0, 0.6, 0.5],
    "ES":  [0.5, 0.3, 0.3, 0.5, 1.0, 0.1, 0.4, 0.3, 0.2, 0.3],
    "SI":  [0.4, 0.3, 0.2, 0.3, 0.2, 0.6, 0.2, 0.3, 0.3, 1.0],
}
PESOS = {opt: dict(zip(_COLS, fila)) for opt, fila in _M.items()}

# --------------------------------------------------------------------------
# Experiencias educativas de los periodos I a V (fase 1)
# Se excluyen AFBG y Electivas: no aportan señal vocacional.
# --------------------------------------------------------------------------
EE_CURRICULARES = {
    1: [
        ("FADM", "Fundamentos de administración",                  "ADM"),
        ("DIVI", "Diversidad e inclusión",                         "ADM"),
        ("FCON", "Fundamentos de contabilidad",                    "CYF"),
        ("FDER", "Fundamentos de derecho",                         "DER"),
        ("ECON", "Economía",                                       "ECO"),
    ],
    2: [
        ("EEPS", "Entorno económico, político y social de la empresa", "ECO"),
        ("MINV", "Metodología de la investigación",                "VEI"),
        ("MFIN", "Matemáticas financieras",                        "MAT"),
        ("FMKT", "Fundamentos de mercadotecnia",                   "MKT"),
        ("MJUR", "Marco jurídico de los negocios",                 "DER"),
        ("AUTO", "Autoconocimiento y desarrollo personal",         "TH"),
    ],
    3: [
        ("TDOR", "Técnicas para el diseño organizacional",         "ADM"),
        ("ETRS", "Ética y responsabilidad social en las organizaciones", "ADM"),
        ("ACPR", "Análisis de costos y presupuestos",              "CYF"),
        ("DLAB", "Derecho laboral y seguridad social",             "DER"),
        ("ESTA", "Estadística aplicada a los negocios",            "MAT"),
        ("RPUB", "Relaciones públicas",                            "MKT"),
        ("SIOR", "Sistemas de información en las organizaciones",  "TEC"),
    ],
    4: [
        ("CALI", "Calidad en las organizaciones",                  "ADM"),
        ("AEST", "Administración estratégica",                     "ADM"),
        ("EEFI", "Estructura de estados financieros",              "CYF"),
        ("CINN", "Creatividad e innovación",                       "EMP"),
        ("MMTD", "Modelos matemáticos para la toma de decisiones", "MAT"),
        ("GTH",  "Gestión del talento humano",                     "TH"),
    ],
    5: [
        ("GSPR", "Gestión de sistemas productivos",                "ADM"),
        ("FAFI", "Fundamentos de administración financiera",       "CYF"),
        ("MNEG", "Modelos de negocios",                            "EMP"),
        ("IMER", "Investigación de mercados",                      "MKT"),
        ("DPMA", "Desarrollo de productos y marcas",               "MKT"),
        ("DTH",  "Dirección del talento humano",                   "TH"),
    ],
}

# Puntos por posición. El periodo I no tiene fav3 (solo hay 5 EE elegibles).
PUNTOS = {"fav1": 10, "fav2": 6, "fav3": 3, "rechazada": -4}
PERIODOS_SIN_FAV3 = {1}


def _calcular_maximos():
    """Máximo alcanzable por academia: se le asignan las posiciones más altas
    disponibles en cada periodo donde aparece. Sin esto, Administración (7 EE)
    aplastaría a Tecnologías (1 EE) y el instrumento mediría el plan de
    estudios en lugar de al estudiante."""
    maximos = {a: 0 for a in ACADEMIAS}
    for periodo, ees in EE_CURRICULARES.items():
        ranuras = [10, 6] if periodo in PERIODOS_SIN_FAV3 else [10, 6, 3]
        for acad in ACADEMIAS:
            n = sum(1 for _, _, a in ees if a == acad)
            maximos[acad] += sum(ranuras[: min(n, len(ranuras))])
    return maximos


MAX_ACADEMIA = _calcular_maximos()

# --------------------------------------------------------------------------
# Fase 2 — 15 reactivos situacionales.
# Cada optativa aparece exactamente 4 veces -> máximo idéntico (12 pts).
# --------------------------------------------------------------------------
PUNTOS_REACTIVO = 3
MAX_FASE2 = 12

REACTIVOS = [
    (1, "Imagina que tu equipo asesorará a una empresa local real. ¿De qué área preferirías encargarte?", [
        ("a", "Revisar los requisitos y trámites legales para que el producto pueda exportarse", "GA"),
        ("b", "Diseñar la cadena de suministro para que el producto llegue al cliente final a tiempo", "LE"),
        ("c", "Crear la identidad visual de la marca y la estrategia para contar su historia en redes", "CCD"),
        ("d", "Coordinar al equipo de trabajo, distribuir las tareas y mediar si surgen conflictos", "CO"),
    ]),
    (2, "Tienes la oportunidad de tomar un taller intensivo de fin de semana. ¿Qué tema elegirías?", [
        ("a", "Análisis de tratados comerciales y su impacto en el tipo de cambio", "EI"),
        ("b", "Estrategias para pronosticar ventas y optimizar el control de inventarios", "LE"),
        ("c", "Creación de tiendas virtuales y configuración de pasarelas de pago", "CE"),
        ("d", "Metodologías para realizar entrevistas a profundidad y analizar datos cualitativos", "SI"),
    ]),
    (3, "Estás escuchando las noticias. ¿Qué titular captaría inmediatamente tu atención?", [
        ("a", "«México firma un nuevo tratado comercial que abrirá mercados internacionales»", "EI"),
        ("b", "«El detrás de escena de la campaña publicitaria que se volvió viral en redes»", "CCD"),
        ("c", "«Nuevo programa municipal para transformar el manejo de residuos sólidos»", "DS"),
        ("d", "«La estrategia de una empresa que mejoró su ambiente laboral y retuvo a su talento»", "CO"),
    ]),
    (4, "Un negocio está estancado y te contratan para encontrar el problema. ¿Qué analizas primero?", [
        ("a", "Mido la eficiencia de sus procesos, el nivel de inventarios y los tiempos de entrega", "LE"),
        ("b", "Evalúo su presencia en internet y su estrategia de ventas en línea", "CE"),
        ("c", "Entrevisto a los empleados para entender cómo se comunican y colaboran entre áreas", "CO"),
        ("d", "Reviso la estructura de poder: quién toma las decisiones y si hay reglas claras escritas", "GEF"),
    ]),
    (5, "Te ofrecen opciones para realizar tus prácticas profesionales con las mismas condiciones. ¿Cuál prefieres?", [
        ("a", "En una agencia aduanal, revisando pedimentos y documentación de comercio", "GA"),
        ("b", "En un ayuntamiento, gestionando proyectos públicos y licitaciones", "GP"),
        ("c", "En una fundación ambiental, midiendo el impacto de sus iniciativas sustentables", "DS"),
        ("d", "En un departamento de Recursos Humanos, aplicando encuestas de clima laboral y capacitación", "CO"),
    ]),
    (6, "Tienes que presentar una propuesta ante un cliente importante. ¿Cómo prefieres hacerlo?", [
        ("a", "Apoyándote en un diseño visual muy atractivo y contando una historia que conecte", "CCD"),
        ("b", "Destacando cómo el proyecto generará un beneficio social o ambiental a la comunidad", "ES"),
        ("c", "Adaptando tu discurso en tiempo real según las reacciones y el lenguaje corporal de los asistentes", "FCD"),
        ("d", "Mostrando datos duros, un diagnóstico riguroso y recomendaciones muy puntuales", "SI"),
    ]),
    (7, "Al revisar los resultados de fin de año de una empresa, ¿qué logro te parecería más satisfactorio?", [
        ("a", "«Las exportaciones de la empresa crecieron un 12% este año»", "PCE"),
        ("b", "«Logramos reducir el tiempo de entrega al cliente de cinco días a solo dos»", "LE"),
        ("c", "«Las ventas a través de nuestra plataforma digital ya representan el 40% de los ingresos»", "CE"),
        ("d", "«El museo que asesoramos aumentó sus visitas de 200 a 2,000 personas al mes»", "GC"),
    ]),
    (8, "Si pudieras liderar un proyecto para resolver un reto en tu estado, ¿cuál elegirías?", [
        ("a", "Ayudar a que las pequeñas y medianas empresas locales logren exportar sus productos", "PCE"),
        ("b", "Impulsar proyectos para que el patrimonio cultural y turístico de la región sea reconocido", "GC"),
        ("c", "Diseñar estrategias económicas que generen riqueza sin destruir el medio ambiente", "DS"),
        ("d", "Crear mecanismos para que los negocios familiares sobrevivan al cambio de generación", "GEF"),
    ]),
    (9, "Recibes un presupuesto libre para fortalecer internamente a una empresa. ¿En qué invertirías?", [
        ("a", "En implementar sistemas tecnológicos para documentar el conocimiento y que la información no se pierda", "GCO"),
        ("b", "En desarrollar un programa de responsabilidad que beneficie directamente a la comunidad local", "ES"),
        ("c", "En un plan de formación directiva para preparar a quienes liderarán la organización en el futuro", "FCD"),
        ("d", "En reestructurar el gobierno corporativo y definir un plan de sucesión claro", "GEF"),
    ]),
    (10, "En tu día a día académico o laboral, ¿qué actividad fluye de manera más natural para ti?", [
        ("a", "Trabajar siguiendo normativas, leyes y formatos exactos sin margen de error", "GA"),
        ("b", "Diseñar mensajes creativos combinando imágenes, palabras y formatos digitales", "CCD"),
        ("c", "Escuchar distintas posturas, mediar en discusiones y convencer a un grupo", "FCD"),
        ("d", "Investigar a fondo un tema, contrastar diversas fuentes y redactar conclusiones sustentadas", "SI"),
    ]),
    (11, "Si proyectas tu carrera a diez años, ¿qué escenario te entusiasma más?", [
        ("a", "Viajando para negociar y cerrar acuerdos con clientes internacionales", "EI"),
        ("b", "Dirigiendo el crecimiento de tu propia marca o tienda de comercio electrónico", "CE"),
        ("c", "Liderando una iniciativa que transformó positivamente la realidad de tu comunidad", "ES"),
        ("d", "Ocupando un cargo directivo diseñando políticas y proyectos en el gobierno", "GP"),
    ]),
    (12, "Si tuvieras que intervenir en un negocio familiar, tuyo o de alguien cercano, ¿cuál sería tu prioridad?", [
        ("a", "Preparar el producto para cruzar fronteras y venderlo en otros países", "PCE"),
        ("b", "Transformarlo para que, además de ganar dinero, tenga un propósito social o ambiental claro", "ES"),
        ("c", "Poner orden institucional definiendo roles, reglas y cómo se pasará el mando a la siguiente generación", "GEF"),
        ("d", "Crear manuales y sistemas para que la operación no dependa exclusivamente del fundador", "GCO"),
    ]),
    (13, "Ganas un pase con todos los gastos pagados para un congreso profesional. ¿Cuál eliges?", [
        ("a", "Una gran feria internacional de comercio y exportadores", "EI"),
        ("b", "Un foro global sobre ciudades sostenibles y economía verde", "DS"),
        ("c", "Un festival enfocado en la promoción de proyectos culturales y turísticos", "GC"),
        ("d", "Un encuentro sobre innovación y modernización en la gestión del sector público", "GP"),
    ]),
    (14, "Una empresa te contrata para resolver un único gran problema. ¿Cuál elegirías?", [
        ("a", "«Ayúdanos a cumplir los requisitos y la logística para empezar a exportar nuestros productos»", "PCE"),
        ("b", "«Ayúdanos a documentar los procesos clave antes de que nuestro personal más experimentado se jubile»", "GCO"),
        ("c", "«Ayúdanos a desarrollar las habilidades gerenciales de quienes tomarán el control directivo en cinco años»", "FCD"),
        ("d", "«Ayúdanos a investigar de forma metódica qué es lo que realmente valoran y opinan nuestros clientes»", "SI"),
    ]),
    (15, "Independientemente del puesto, ¿en qué tipo de entorno organizacional te visualizas trabajando mejor?", [
        ("a", "En un espacio creativo y de promoción, como un museo, un festival o una fundación cultural", "GC"),
        ("b", "En una dependencia gubernamental u organismo público, enfocado en la administración", "GP"),
        ("c", "En un corporativo estructurado con procesos maduros y oficinas en varios países", "GCO"),
        ("d", "En una agencia aduanal o en una empresa comercializadora enfocada en el mercado internacional", "GA"),
    ]),
]

REACTIVOS_VERSION_BREVE = [1, 3, 5, 7, 9, 11, 13, 15]

# --------------------------------------------------------------------------
# Fase 3 — contexto y viabilidad. Ajuste acotado a ±10 puntos porcentuales.
# --------------------------------------------------------------------------
TOPE_FASE3 = 10.0

PREGUNTAS_CONTEXTO = [
    (1, "¿Cómo describirías tu nivel de inglés hoy?",
     [("a", "Puedo seguir una clase completa en inglés", {}),
      ("b", "Entiendo lo básico pero me cuesta", {"FCD": -5}),
      ("c", "Muy poco", {"FCD": -5})],
     "Fundamental concepts of directive competences se imparte en inglés."),
    (2, "¿Podrías hacer prácticas o servicio social fuera de Xalapa (puerto, zona industrial)?",
     [("a", "Sí, sin problema", {}),
      ("b", "Difícilmente", {"GA": -5, "PCE": -5, "LE": -5})],
     "Las mejores prácticas de estas optativas están en la región Veracruz."),
    (3, "¿Piensas titularte por tesis o trabajo de investigación?",
     [("a", "Sí, o lo estoy considerando", {"SI": 5}),
      ("b", "No, prefiero otra modalidad", {}),
      ("c", "Todavía no lo sé", {})],
     "Seminario de investigación es la única optativa que prepara directamente esa modalidad."),
    (4, "¿Tienes acceso a una empresa familiar o a un negocio propio?",
     [("a", "Sí", {"GEF": 5}),
      ("b", "No", {})],
     "Puedes usar ese negocio como caso a lo largo de todo el itinerario."),
    (5, "Hoy, ¿qué pesa más para ti?",
     [("a", "El ingreso inicial", {}),
      ("b", "El propósito del trabajo", {"ES": 5, "DS": 5}),
      ("c", "Están parejos", {})],
     "Los perfiles de impacto suelen tener curvas salariales más lentas al inicio."),
]

# --------------------------------------------------------------------------
# Los 13 bloques de área terminal.
#
# Un bloque = 3 optativas reales, cerradas. El estudiante NO elige optativas
# sueltas: tres materias sin relación no hacen a un especialista en nada.
# Regla de diseño: dos bloques comparten como máximo una optativa.
#
# El 13 es posterior a los otros doce. Existe para rescatar Gestión de empresas
# familiares, que sólo vivía en el bloque 8: si ese bloque no juntaba alumnos,
# esa optativa nunca se abría. Sus tres EE ya se ofertan para los bloques 2, 3,
# 7, 8, 9, 10 y 12, así que no cuesta un solo grupo nuevo.
# --------------------------------------------------------------------------
ITINERARIOS = [
    dict(id=1, nombre="Comercio Exterior e Internacionalización",
         nombre_en="Global Trade & Expansion",
         frase="gestor especializado en comercio exterior",
         resumen="Llevar un producto mexicano a mercados extranjeros.",
         opts=["EI", "GA", "PCE"],
         perfil="Dominas la normativa aduanera, los tratados comerciales y las variables macroeconómicas que hacen viable una exportación. Sabes si un producto puede salir del país y cuánto cuesta que salga.",
         salidas=["Analista en agencia aduanal", "Coordinador de exportaciones", "Asesor en cámaras de comercio"]),
    dict(id=2, nombre="Logística, Aduanas y Distribución",
         nombre_en="Supply Chain & Distribution",
         frase="gestor especializado en logística y distribución",
         resumen="Mover mercancía de la planta al cliente, incluso cruzando frontera.",
         opts=["LE", "GA", "CE"],
         perfil="Diseñas y optimizas el flujo físico completo: almacenes, rutas, inventarios, cruce aduanal y entrega de última milla del canal digital.",
         salidas=["Gerente de operaciones", "Supply Chain Analyst", "Responsable de fulfillment"]),
    dict(id=3, nombre="Emprendimiento y Comercio Digital",
         nombre_en="Digital Venture Builder",
         frase="gestor especializado en comercio digital",
         resumen="Montar y sostener un negocio propio en línea.",
         opts=["CE", "CCD", "ES"],
         perfil="Construyes producto, narrativa y canal de venta en entornos digitales, con un modelo que se sostiene sin depender de inversión externa.",
         salidas=["Fundador de marca o tienda en línea", "Growth o e-commerce manager", "Consultor de digitalización"]),
    dict(id=4, nombre="Industrias Creativas, Culturales y Turismo",
         nombre_en="Creative & Cultural Producer",
         frase="gestor especializado en industrias creativas y culturales",
         resumen="Profesionalizar festivales, museos y proyectos turísticos.",
         opts=["GC", "CCD", "GP"],
         perfil="Administras proyectos artísticos y patrimoniales, que en México casi siempre operan con presupuesto público y alianzas mixtas, y sabes comunicarlos.",
         salidas=["Director de proyectos turísticos", "Productor de eventos y festivales", "Gestor cultural institucional"]),
    dict(id=5, nombre="Sostenibilidad y Desarrollo Regional",
         nombre_en="Sustainable Development Specialist",
         frase="gestor especializado en sostenibilidad y desarrollo regional",
         resumen="Formular y evaluar proyectos de desarrollo con criterio ambiental.",
         opts=["DS", "GP", "SI"],
         perfil="Formulas proyectos de desarrollo con criterios ambientales, sociales y de gasto público, y sustentas sus resultados con evidencia, no con intenciones.",
         salidas=["Director de desarrollo económico municipal", "Gestor de proyectos regionales", "Evaluador de programas públicos"]),
    dict(id=6, nombre="Liderazgo de Organizaciones de Impacto",
         nombre_en="Impact Organization Lead",
         frase="gestor especializado en organizaciones de impacto",
         resumen="Dirigir empresas sociales y áreas de sostenibilidad corporativa.",
         opts=["ES", "DS", "FCD"],
         perfil="Diriges organizaciones que persiguen rentabilidad e impacto a la vez, con la competencia lingüística y directiva que exigen los organismos internacionales.",
         salidas=["Gerente de sustentabilidad o ESG", "Director de proyectos en ONG", "Fundador de empresa social"]),
    dict(id=7, nombre="Talento, Cultura y Conocimiento Organizacional",
         nombre_en="People, Culture & Knowledge",
         frase="gestor especializado en talento y cultura organizacional",
         resumen="Diagnosticar la cultura de una organización y desarrollar a su gente.",
         opts=["CO", "GCO", "FCD"],
         perfil="Diagnosticas motivación, grupos y conflicto; conviertes la experiencia individual en capacidad institucional; desarrollas a quienes van a dirigir.",
         salidas=["Business Partner de Recursos Humanos", "Especialista en desarrollo organizacional", "Consultor en gestión del cambio"]),
    dict(id=8, nombre="Empresas Familiares y Sucesión",
         nombre_en="Family Business Succession Lead",
         frase="gestor especializado en empresas familiares",
         resumen="Profesionalizar el negocio familiar y su transición generacional.",
         opts=["GEF", "CO", "SI"],
         perfil="Diagnosticas con método el tipo de empresa que domina el tejido económico veracruzano, ordenas su gobierno corporativo y medias la sucesión.",
         salidas=["Sucesor profesionalizado", "Consultor en protocolos familiares", "Director general de MiPyME"]),
    dict(id=9, nombre="Mejora de Operaciones y Consultoría de Procesos",
         nombre_en="Process & Operations Consultant",
         frase="gestor especializado en mejora de operaciones",
         resumen="Medir una operación, rediseñarla y documentarla.",
         opts=["SI", "LE", "GCO"],
         perfil="Mides una operación con método, la rediseñas y documentas el conocimiento para que la mejora no dependa de quién esté ese día.",
         salidas=["Analista de mejora continua", "Consultor de procesos", "Coordinador de calidad"]),
    dict(id=10, nombre="Dirección de Negocios Globales",
         nombre_en="Global Business Management",
         frase="gestor especializado en negocios globales",
         resumen="Operar y dirigir en inglés en corporativos internacionales.",
         opts=["FCD", "EI", "CE"],
         perfil="Te mueves en entornos corporativos multinacionales con la comprensión macroeconómica y digital que exige el comercio transfronterizo.",
         salidas=["Analista en corporativo multinacional", "Key account manager internacional", "Consultor en expansión transfronteriza"]),
    dict(id=11, nombre="Emprendimiento Social y Comunitario",
         nombre_en="Community Venture Builder",
         frase="gestor especializado en emprendimiento social",
         resumen="Crear y sostener cooperativas y colectivos.",
         opts=["ES", "GC", "CO"],
         perfil="Levantas organizaciones de base comunitaria y cultural, donde el reto no es el capital sino la dinámica del grupo humano que las sostiene.",
         salidas=["Fundador de cooperativa o colectivo", "Coordinador de proyectos comunitarios", "Gestor de economía social"]),
    dict(id=12, nombre="Comunicación de Sostenibilidad y Reputación",
         nombre_en="Sustainability Communications",
         frase="gestor especializado en comunicación de sostenibilidad",
         resumen="Traducir el desempeño ambiental y social en información creíble.",
         opts=["CCD", "GCO", "DS"],
         perfil="Conviertes el desempeño ambiental y social de una organización en información verificable para clientes, inversionistas y reguladores.",
         salidas=["Especialista en reporte ESG", "Comunicación corporativa", "Consultor en comunicación de impacto"]),
    dict(id=13, nombre="Digitalización de Empresas Familiares",
         nombre_en="Family Business Digitalization",
         frase="gestor especializado en digitalización de empresas familiares",
         resumen="Llevar al negocio familiar de la libreta al sistema y a la venta en línea.",
         opts=["GEF", "CE", "GCO"],
         perfil="Entiendes la dinámica familia-negocio y la usas para digitalizar sin romper: canal de venta en línea, procesos documentados y conocimiento que deja de vivir en la cabeza del fundador.",
         salidas=["Consultor de digitalización para MiPyMEs", "Responsable de transformación digital", "Sucesor a cargo del canal en línea"]),
]

# Puntuación del bloque. NO es el promedio simple: castiga a su miembro más
# débil. Con bloques cerrados el estudiante SÍ va a cursar las tres, así que un
# bloque con dos materias excelentes y una pésima no puede ganarle a uno parejo.
PESO_MEDIA_BLOQUE = 0.6
PESO_PEOR_BLOQUE = 0.4

# Si la materia floja del bloque ganador quedó de este lugar en adelante en el
# ranking individual, el reporte lo advierte en vez de esconderlo.
UMBRAL_MATERIA_DEBIL = 10

PESO_FASE1 = 0.45
PESO_FASE2 = 0.45
