"""Convierte Etapa3_CVRP.md en un proyecto LaTeX (pdfLaTeX) listo para Overleaf."""
import re, shutil, subprocess
from pathlib import Path

DOC = Path(__file__).parent
OUT = DOC / 'latex'
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'resultados').exists())
FIG = ROOT / 'figuras'
LOGO = DOC / 'logo_tec.png'

md = (DOC / 'Etapa3_CVRP.md').read_text()

# ---------------------------------------------------------------- estructura
md = md.split('---', 2)[2]                                   # quita el front matter
md = re.sub(r'^\*\*Diseño de algoritmos.*?\nProfesor:.*?\n', '', md, flags=re.S | re.M)
res = re.search(r'## Resumen\n\n(.+?)\n\n## ', md, flags=re.S)
resumen = res.group(1).strip()
md = md.replace(res.group(0)[:-3], '')
md = re.sub(r'^(#{2,3}) \d+(?:\.\d+)?\.? ', r'\1 ', md, flags=re.M)        # numeración automática
md = md.replace('## Referencias', '## Referencias {-}')
md = md.replace('## Anexo A. Reproducibilidad', '\\appendix\n\n## Reproducibilidad')
# leyendas de tablas: "**Tabla N.** texto" antes de la tabla -> "Table: texto" después
md = re.sub(r'\*\*Tabla \d+\.\*\* ([^\n]+)\n\n((?:\|[^\n]*\n)+)', r'\2\nTable: \1\n', md)
md = re.sub(r'\([^()\s]*/figuras/([^)/]+\.png)\)', r'(figuras/\1)', md)

# ---------------------------------------------------------------- notación
SUP = str.maketrans('⁻⁰¹²³⁴⁵⁶⁷⁸⁹', '-0123456789')


def sci(m):
    base, exp = m.group(1), m.group(2).translate(SUP)
    return f'${base}\\times10^{{{exp}}}$' if base else f'$10^{{{exp}}}$'


def notacion(txt):
    txt = re.sub(r'(\d+(?:\.\d+)?)×10([⁻⁰¹²³⁴⁵⁶⁷⁸⁹]+)', sci, txt)
    txt = re.sub(r'()10([⁻][⁰¹²³⁴⁵⁶⁷⁸⁹]+)', sci, txt)
    txt = re.sub(r'(?<![\w\\$])([A-Za-z])_([A-Za-z0-9]+)(?![\w])', r'$\1_{\2}$', txt)   # p_m, x_ij, v_max
    txt = re.sub(r'C\^nn', r'$C^{nn}$', txt)
    return txt


# protege matemáticas, código, URLs y rutas de figuras
partes = re.split(r'(\$\$.*?\$\$|\$[^$\n]+\$|`[^`]+`|<https?://[^>]+>|https?://\S+|\(figuras/[^)]+\))', md, flags=re.S)
md = ''.join(p if k % 2 else notacion(p) for k, p in enumerate(partes))


def anchos(m):
    filas = [l for l in m.group(0).strip('\n').split('\n')]
    sep = filas[1]
    celdas = [[c.strip() for c in l.strip().strip('|').split('|')] for l in filas if l is not sep]
    limpia = lambda c: re.sub(r'\$[^$]*\$', 'xxxx', re.sub(r'[*`]', '', c))
    L = [max(len(limpia(f[k])) for f in celdas if k < len(f)) for k in range(len(celdas[0]))]
    al = [c.strip() for c in sep.strip().strip('|').split('|')]
    nuevo = []
    L[0] = max(L[0], 16)
    for a, l in zip(al, L):
        d = '-' * max(3, min(l, 45))
        nuevo.append((':' if a.startswith(':') else '') + d + (':' if a.endswith(':') else ''))
    filas[1] = '| ' + ' | '.join(nuevo) + ' |'
    return '\n'.join(filas) + '\n'


md = re.sub(r'(?:^\|.*\n)+', anchos, md, flags=re.M)
(OUT).mkdir(exist_ok=True)
(OUT / 'cuerpo.md').write_text(md)
body = subprocess.run(['pandoc', '-f', 'markdown', '-t', 'latex', '--columns=100', '--wrap=none', '--shift-heading-level-by=-1'],
                      input=md, capture_output=True, text=True, check=True).stdout

# ---------------------------------------------------------------- tablas anchas
def ajustar(m):
    t = m.group(0)
    cab = re.search(r'\\begin\{longtable\}\[\]\{@\{\}(.*?)@\{\}\}', t, flags=re.S).group(1)
    ncol = cab.count('\\real{') or len(re.findall(r'[lrc]', cab))
    if '\\caption' not in t:
        t = t + '\n\\addtocounter{table}{-1}'
    if ncol >= 10:
        return ('\\begin{landscape}\n{\\footnotesize\\setlength{\\tabcolsep}{4pt}\n' + t + '\n}\n\\end{landscape}')
    if ncol >= 6:
        return '{\\small\\setlength{\\tabcolsep}{4pt}\n' + t + '\n}'
    return t


body = re.sub(r'\\begin\{longtable\}.*?\\end\{longtable\}', ajustar, body, flags=re.S)
# referencias con sangría francesa
i = body.find('\\section*{Referencias}')
j = body.find('\\appendix')
ref = body[i:j].replace('\\begin{itemize}', '\\begin{itemize}[label={},leftmargin=1.5em,itemindent=-1.5em]')
body = body[:i] + ref + body[j:]

# ---------------------------------------------------------------- caracteres Unicode para pdfLaTeX
UNI = {'±': r'\ensuremath{\pm}', '²': r'\textsuperscript{2}', '³': r'\textsuperscript{3}', '·': r'\ensuremath{\cdot}',
       '×': r'\ensuremath{\times}', 'Σ': r'\ensuremath{\Sigma}', 'α': r'\ensuremath{\alpha}', 'β': r'\ensuremath{\beta}',
       'ρ': r'\ensuremath{\rho}', 'τ': r'\ensuremath{\tau}', 'η': r'\ensuremath{\eta}', 'φ': r'\ensuremath{\phi}',
       'ε': r'\ensuremath{\varepsilon}', 'Ω': r'\ensuremath{\Omega}', '→': r'\ensuremath{\rightarrow}',
       '∈': r'\ensuremath{\in}', '−': r'\ensuremath{-}', '⌈': r'\ensuremath{\lceil}', '⌉': r'\ensuremath{\rceil}',
       '≤': r'\ensuremath{\le}', '≥': r'\ensuremath{\ge}', '≈': r'\ensuremath{\approx}',
       '₀': r'\textsubscript{0}', '₁': r'\textsubscript{1}', '₂': r'\textsubscript{2}', '₃': r'\textsubscript{3}',
       'ᵢ': r'\textsubscript{i}', '⁻': r'\textsuperscript{-}', '⁶': r'\textsuperscript{6}'}
usados = sorted({c for c in body + resumen if ord(c) > 255 or c in '±²³·×'})
faltan = [c for c in usados if c not in UNI and c not in '–—“”‘’…¿¡']
assert not faltan, f'caracteres sin mapear: {faltan}'
mapas = '\n'.join(f'\\newunicodechar{{{c}}}{{{UNI[c]}}}' for c in usados if c in UNI)

resumen_tex = subprocess.run(['pandoc', '-f', 'markdown', '-t', 'latex', '--wrap=none'],
                             input=notacion(resumen), capture_output=True, text=True, check=True).stdout

preambulo = r"""\documentclass[11pt,letterpaper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[spanish,es-nodecimaldot,es-tabla,es-noshorthands]{babel}
\usepackage[top=2.4cm,bottom=2.4cm,left=2.3cm,right=2.3cm]{geometry}
\usepackage{amsmath,amssymb,graphicx,booktabs,longtable,array,float,xcolor,fancyhdr,titlesec,caption,enumitem,microtype,pdflscape,newunicodechar,calc}
\usepackage[hidelinks]{hyperref}
\usepackage{xurl}
\definecolor{azul}{HTML}{164769}
\hypersetup{colorlinks=true,linkcolor=azul,urlcolor=azul,citecolor=azul,pdftitle={CVRP de logística urbana: Etapa 3},pdfauthor={Equipo MA2015}}
\titleformat{\section}{\Large\bfseries\color{azul}}{\thesection.}{0.6em}{}
\titleformat{\subsection}{\large\bfseries\color{azul}}{\thesubsection}{0.6em}{}
\setlength{\parindent}{0pt}\setlength{\parskip}{6pt}
\setlength{\emergencystretch}{2em}
\renewcommand{\arraystretch}{1.15}
\floatplacement{figure}{H}
\setkeys{Gin}{keepaspectratio}
\captionsetup{font=small,labelfont=bf}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small Diseño de algoritmos matemáticos bioinspirados}
\fancyhead[R]{\small CVRP $\cdot$ Etapa 3}
\fancyfoot[C]{\thepage}\setlength{\headheight}{14pt}
\renewcommand{\headrulewidth}{0.3pt}
\fancypagestyle{lscape}{\fancyhf{}\fancyfoot[C]{\thepage}\renewcommand{\headrulewidth}{0pt}}
""" + mapas + r"""

\begin{document}
\begin{titlepage}
  \centering
  \includegraphics[width=0.5\textwidth]{figuras/logo_tec.png}\par
  \vspace{2cm}
  {\LARGE\bfseries Entregable 3: comparación de métodos en instancias de referencia\par}
  \vspace{0.5cm}
  {\large Modelo matemático, Clarke--Wright + 2-opt, algoritmo genético y colonia de hormigas para el CVRP\par}
  \vspace{2cm}
  {\large
  Leonardo Orozco -- A00843030\\[2pt]
  Pablo Alonso Robles Nava -- A00573454\\[2pt]
  Sebastián Alberto Chávez Rodríguez -- A01199298\\[2pt]
  Jacqueline Peña San Juan -- A00842524\\[2pt]
  Natalia Ixchel Reynoso Ramírez -- A01352603\par}
  \vspace{1.5cm}
  {\large Profesor: Fernando Elizalde\par}
  \vspace{0.3cm}
  {\large Diseño de algoritmos matemáticos bioinspirados (MA2015) -- Gpo.\ 201\par}
  \vspace{0.3cm}
  {\normalsize Repositorio: \url{https://github.com/Leo-issacs/cvrp-logistica-urbana}\par}
  \vfill
  {\large 26 de octubre de 2026\par}
\end{titlepage}

\begin{abstract}
""" + resumen_tex + r"""\end{abstract}

\tableofcontents
\newpage

"""
tex = preambulo + body + '\n\\end{document}\n'
(OUT / 'main.tex').write_text(tex)
(OUT / 'figuras').mkdir(exist_ok=True)
for f in FIG.glob('*.png'):
    shutil.copy(f, OUT / 'figuras' / f.name)
shutil.copy(LOGO, OUT / 'figuras' / 'logo_tec.png')
(OUT / 'cuerpo.md').unlink()
print('latex ok')
