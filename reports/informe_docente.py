import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import date
from utils import FACILITADOR, tex_s, compile_latex
from cycles import NIVEL_MAP_ES


def _attendance_codes_mensual(row):
    a, b = row['LO_A'], row['LO_B']
    if a == 0.0 and b == 0.0: return ["I"] * 5
    if a > 0 and b == 0.0:    return ["P"] + ["I"] * 4
    return ["P"] * 5


def generate_informe_docente(
    df: pd.DataFrame,
    cycle_data: dict,
    course_code: str,
    level_digit: str,
    classroom: str,
    academic_strategies: dict,
    attendance_strategies: dict,
    moodle_all_enrolled: bool,
    moodle_missing_names: str = "",
    moodle_img=None,
) -> bytes:

    nivel  = NIVEL_MAP_ES.get(str(level_digit), "Nivel")
    inicio = cycle_data['inicio']
    fin    = cycle_data['fin']
    clean_code = tex_s(course_code.replace('_', '-'))

    # ── Academic difficulty table ─────────────────────────────
    acad_students = df[((df['LO_A'] < 7.0) | (df['LO_B'] < 7.0)) &
                       ~((df['LO_A'] == 0.0) & (df['LO_B'] == 0.0))]
    if acad_students.empty:
        acad_rows = r"N/A & N/A & N/A \\ \hline"
    else:
        acad_rows = "\n".join(
            f"{tex_s(r['FullName'])} & En progreso & "
            f"{tex_s(academic_strategies.get(r['FullName'], 'N/A'))} \\\\ \\hline"
            for _, r in acad_students.iterrows()
        )

    # ── Attendance difficulty table ───────────────────────────
    att_students = df[(df['LO_A'] == 0.0) | (df['LO_B'] == 0.0)]
    if att_students.empty:
        att_rows_diff = r"N/A & N/A & N/A \\ \hline"
    else:
        att_rows_diff = "\n".join(
            f"{tex_s(r['FullName'])} & En progreso & "
            f"{tex_s(attendance_strategies.get(r['FullName'], 'N/A'))} \\\\ \\hline"
            for _, r in att_students.iterrows()
        )

    # ── Moodle text ───────────────────────────────────────────
    if moodle_all_enrolled:
        moodle_tex = "Todo los estudiantes fueron matriculados sin problema."
    else:
        moodle_tex = (f"Los estudiantes {tex_s(moodle_missing_names)} "
                      "tuvieron inconveniente para matricularse en Moodle.")

    # ── Attendance annex rows (simplified P/I per day) ────────
    att_annex_rows = ""
    att_names = set(att_students['FullName'].tolist())
    for i, row in enumerate(df.itertuples(), 1):
        s = "I" if row.FullName in att_names else "P"
        att_annex_rows += (f"{i} & {tex_s(str(row.IDNumber))} & "
                           f"{tex_s(str(row.FullName))} & "
                           f"{s} & {s} & {s} & {s} \\\\ \\hline\n")

    # ── Notes annex rows (LO A & B only) ─────────────────────
    grade_rows = ""
    for i, row in enumerate(df.itertuples(), 1):
        prom = round((row.LO_A + row.LO_B) / 2, 2)
        grade_rows += (f"{i} & {tex_s(str(row.IDNumber))} & "
                       f"{tex_s(str(row.FullName))} & "
                       f"{row.LO_A:.2f} & {row.EQ_A:.2f} & "
                       f"{row.LO_B:.2f} & {row.EQ_B:.2f} & "
                       f"{prom:.2f} \\\\ \\hline\n")

    latex = r"""\documentclass[10pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[letterpaper, portrait, margin=1.5cm]{geometry}
\usepackage{graphicx, array, longtable, colortbl, xcolor, needspace}
\usepackage[scaled]{helvet}
\renewcommand{\familydefault}{\sfdefault}
\definecolor{espamTeal}{RGB}{0, 169, 158}
\begin{document}

\begin{center}
    \includegraphics[height=1.3cm, keepaspectratio]{logo.png} \hfill
    {\small\bfseries\itshape Informe Docente}
\end{center}
\vspace{0.5em}
\begin{center}
    {\normalsize\bfseries Informe correspondiente al periodo del """ + tex_s(inicio) + r""" al """ + tex_s(fin) + r"""}
\end{center}
\vspace{1em}
\noindent\textbf{Nivel/Ciclo:} """ + nivel + r" / " + clean_code + r""" \\
\textbf{Paralelo:} """ + tex_s(classroom) + r""" \\
\textbf{Docente:} """ + tex_s(FACILITADOR) + r"""

\vspace{1.5em}
\noindent 1. \textbf{Resumen de estudiantes con dificultades en el desempe\~no acad\'emico}

\begin{longtable}{|>{\centering\arraybackslash}p{6cm}|p{3.5cm}|p{6.5cm}|}
\hline \textbf{Nombres y Apellidos} & \textbf{Estado} & \textbf{Estrategias} \\ \hline
""" + acad_rows + r"""
\end{longtable}

\vspace{0.5em}
\noindent 2. \textbf{Resumen de estudiantes con dificultades en asistencia (por paralelo), as\'i tambi\'en estudiantes que se retiran en el transcurso del desarrollo del curso.}

\begin{longtable}{|>{\centering\arraybackslash}p{6cm}|p{3.5cm}|p{6.5cm}|}
\hline \textbf{Nombres y Apellidos} & \textbf{Situaci\'on} & \textbf{Estrategias} \\ \hline
""" + att_rows_diff + r"""
\end{longtable}

\Needspace{5cm}
\vspace{4em}
\begin{center}
\rule{8cm}{0.4pt} \\
\vspace{4pt}
\textbf{""" + tex_s(FACILITADOR) + r"""} \\
Docente de la Unidad de Centro de Idiomas
\end{center}

\newpage
\begin{center}
    \includegraphics[height=1.3cm, keepaspectratio]{logo.png} \hfill
    {\small\bfseries\itshape Informe Docente}
\end{center}
\vspace{1em}

\noindent\textbf{Anexos:}

\vspace{0.5em}
\noindent\textbf{ASISTENCIA:}

\vspace{0.3em}
\noindent{\small\itshape (Asistencia correspondiente al periodo mensual hasta la fecha indicada en este reporte).}

\vspace{0.3em}
\setlength{\arrayrulewidth}{0.6pt}
\renewcommand{\arraystretch}{1.5}
{\fontsize{9}{10}\selectfont
\begin{longtable}{|>{\centering\arraybackslash}m{6mm}|>{\centering\arraybackslash}m{26mm}|>{\centering\arraybackslash}m{75mm}|>{\centering\arraybackslash}m{8mm}|>{\centering\arraybackslash}m{8mm}|>{\centering\arraybackslash}m{8mm}|>{\centering\arraybackslash}m{8mm}|}
\hline
\rowcolor{espamTeal}
\centering{\bfseries\color{white}N\textdegree} &
\centering{\bfseries\color{white}C\'edula} &
\centering{\bfseries\color{white}Apellidos y Nombres} &
\centering{\bfseries\color{white}D1} &
\centering{\bfseries\color{white}D2} &
\centering{\bfseries\color{white}D3} &
\centering\arraybackslash{\bfseries\color{white}D4} \\ \hline
""" + att_annex_rows + r"""
\end{longtable}}
\renewcommand{\arraystretch}{1}

\vspace{0.8em}
\noindent\textbf{NOTAS:} {\small\itshape (Logros de Aprendizaje A y B)}

\vspace{0.3em}
\renewcommand{\arraystretch}{1.5}
{\fontsize{9}{10}\selectfont
\begin{longtable}{|>{\centering\arraybackslash}m{6mm}|>{\centering\arraybackslash}m{26mm}|>{\centering\arraybackslash}m{62mm}|>{\centering\arraybackslash}m{10mm}|>{\centering\arraybackslash}m{10mm}|>{\centering\arraybackslash}m{10mm}|>{\centering\arraybackslash}m{10mm}|>{\centering\arraybackslash}m{10mm}|}
\hline
\rowcolor{espamTeal}
\centering{\bfseries\color{white}N\textdegree} &
\centering{\bfseries\color{white}C\'edula} &
\centering{\bfseries\color{white}Apellidos y Nombres} &
\centering{\bfseries\color{white}A} &
\centering{\bfseries\color{white}EQ} &
\centering{\bfseries\color{white}B} &
\centering{\bfseries\color{white}EQ} &
\centering\arraybackslash{\bfseries\color{white}Prom.} \\ \hline
""" + grade_rows + r"""
\end{longtable}}
\renewcommand{\arraystretch}{1}

\newpage
\noindent\textbf{MOODLE:}

\vspace{0.3em}
\noindent """ + moodle_tex + (r"""

\vspace{0.5em}
\noindent\includegraphics[width=0.6\textwidth]{moodle_screenshot.png}
""" if moodle_img else "") + r"""

\end{document}"""

    return compile_latex(latex, 'informe_docente',
                         extra_files={"moodle_screenshot.png": moodle_img[1]} if moodle_img else {})
