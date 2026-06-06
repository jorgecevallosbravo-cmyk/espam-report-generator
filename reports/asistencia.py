import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import date, timedelta
import pandas as pd
from utils import FACILITADOR, tex_s, compile_latex

MONTH_MAP = {1:"JAN",2:"FEB",3:"MAR",4:"APR",5:"MAY",6:"JUN",
             7:"JUL",8:"AUG",9:"SEP",10:"OCT",11:"NOV",12:"DEC"}
NUM_DATES    = 13
NUM_MENSUAL  = 5

TEMPLATE = r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[letterpaper, landscape, margin=0.5cm, top=1cm]{geometry}
\usepackage[table]{xcolor}
\usepackage{array}
\usepackage{longtable}
\usepackage{multirow}
\usepackage{graphicx}
\usepackage{needspace}
\usepackage[scaled]{helvet}
\renewcommand{\familydefault}{\sfdefault}
\definecolor{espamTeal}{RGB}{0, 169, 158}
\definecolor{colorT}{RGB}{180, 210, 60}
\definecolor{colorJ}{RGB}{254, 211, 99}
\definecolor{colorI}{RGB}{252, 147, 90}
\definecolor{colorP}{RGB}{245, 227, 203}
\definecolor{colorAusente}{RGB}{219, 238, 244}
\newcommand{\datarow}{\rule[-%%OFFSET%%]{0pt}{%%HEIGHT%%}}
\setlength{\extrarowheight}{0pt}
\setlength{\parskip}{0pt}
\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1}
\begin{document}
\pagestyle{empty}
\begin{center}
\begin{tabular}{@{} m{110mm} @{} m{154mm} @{}}
    \rowcolor{espamTeal}
    \rule[-4mm]{0pt}{14mm}
    {\fontsize{22}{18}\selectfont\bfseries\color{white} REGISTRO DE ASISTENCIA} &
    \rule[-4mm]{0pt}{14mm}
    {\fontsize{22}{18}\selectfont\bfseries\color{white} %%COURSE_CODE%%} \\
\end{tabular}
\vspace{3pt}
\begin{flushleft}
\begin{tabular}{@{} m{19mm} m{42mm} m{30.1mm} m{5.2mm} m{14.62mm} m{5.2mm} m{8.mm} m{155mm} @{}}
    \rule{0pt}{-2mm}
    {\fontsize{10}{10}\selectfont\bfseries IDIOMA:} &
    \rule{-4pt}{-2mm}
    {\fontsize{10}{10}\selectfont Ingl\'es} &
    \multirow{3}{35mm}[-2.3mm]{\raggedleft \fontsize{9}{9}\selectfont\bfseries CLAVE DE COLOR \hspace{4mm}} &
    & & & &
    \multirow{3.5}{103.48mm}{\raggedleft \includegraphics[height=10.8mm, keepaspectratio]{logo.png} \hspace*{80mm}} \\
    \rule{0pt}{-2mm}
    {\fontsize{10}{10}\selectfont\bfseries HORARIO:} &
    {\fontsize{10}{10}\selectfont %%HORARIO%%} &
    &
    \cellcolor{colorT} \centering \fontsize{10}{10}\selectfont T &
    {\fontsize{8.5}{8.5}\selectfont Tarde} &
    \cellcolor{colorI} \centering \fontsize{10}{10}\selectfont I &
    {\fontsize{8.5}{8.5}\selectfont Injustificado} & \\
    \rule{0pt}{-2mm}
    {\fontsize{10}{10}\selectfont\bfseries DOCENTE:} &
    {\fontsize{10}{10}\selectfont %%DOCENTE%%} &
    &
    \cellcolor{colorJ} \centering \fontsize{10}{10}\selectfont J &
    {\fontsize{8.5}{8.5}\selectfont Justificado} &
    \cellcolor{colorP} \centering \fontsize{10}{10}\selectfont P &
    {\fontsize{8.5}{8.5}\selectfont Presente} & \\
\end{tabular}
\end{flushleft}
\vspace{-12pt}
\arrayrulecolor{black}
\setlength{\arrayrulewidth}{0.8pt}
\begin{longtable}{@{} | >{\centering\arraybackslash\fontsize{9}{9}\selectfont}m{3mm} | >{\centering\arraybackslash\fontsize{9}{9}\selectfont}m{20mm} | >{\centering\arraybackslash\fontsize{8.5}{8.5}\selectfont}m{65mm} | *{13}{>{\centering\arraybackslash\fontsize{9}{9}\selectfont}m{5mm} |} *{4}{>{\centering\arraybackslash\fontsize{9}{9}\selectfont}m{2.5mm} |} >{\centering\arraybackslash\fontsize{9}{9}\selectfont}m{10mm} | @{}}
%%STUDENT_ROWS%%
\end{longtable}
\end{center}
\end{document}"""


def _parse_date(s):
    d, m, y = s.strip().split("/")
    return date(int(y), int(m), int(d))


def _get_class_dates(inicio, fin):
    start = _parse_date(inicio)
    end   = _parse_date(fin)
    span  = (end - start).days
    weekdays = {0, 2, 4} if span <= 40 else {1, 3}
    dates, cur = [], start
    while len(dates) < NUM_DATES:
        if cur.weekday() in weekdays:
            dates.append(cur)
        cur += timedelta(days=1)
        if cur > end + timedelta(days=400):
            break
    return dates


def _make_row(row_num, name, doc, codes, is_mensual=False):
    is_even = (row_num % 2 == 0)
    z = r"\cellcolor{colorAusente}" if is_even else ""
    att_cells = ""
    for c in codes:
        if c == "P":   att_cells += r"\cellcolor{colorP}P&"
        elif c == "I": att_cells += r"\cellcolor{colorI}I&"
        else:          att_cells += "&"
    if is_mensual:
        for _ in range(NUM_DATES - NUM_MENSUAL):
            att_cells += f"{z}&"
    p = codes.count("P")
    i = codes.count("I")
    return (f"\\datarow {z}{row_num}&{z}{doc}&{z}{name}&"
            f"{att_cells}{z}0&{z}0&{z}{i}&{z}{p}&{z}{i}\\\\\\hline\n")


def generate_asistencia(df: pd.DataFrame, cycle_data: dict,
                        horario: str, course_code: str,
                        is_mensual: bool = False) -> bytes:
    inicio = cycle_data['inicio']
    fin    = cycle_data['fin']
    fecha_examen = cycle_data['examen']
    fecha_sup    = cycle_data['supletorio']
    class_dates  = _get_class_dates(inicio, fin)

    df = df.copy()

    # Attendance codes
    if is_mensual:
        def codes_m(row):
            a, b = row['LO_A'], row['LO_B']
            if a == 0.0 and b == 0.0: return ["I"] * NUM_MENSUAL
            if a > 0 and b == 0.0:    return ["P"] + ["I"] * (NUM_MENSUAL - 1)
            return ["P"] * NUM_MENSUAL
        df['Codes'] = df.apply(codes_m, axis=1)
    else:
        def codes_f(row):
            a, b, c, d = row['LO_A'], row['LO_B'], row['LO_C'], row['LO_D']
            ex = row['Examen']
            if a + b + c + d + ex == 0.0: return ["I"] * NUM_DATES
            if a > 0 and b == 0 and c == 0 and d == 0 and ex == 0.0:
                return ["P"] * 3 + ["I"] * 10
            return ["P"] * NUM_DATES
        df['Codes'] = df.apply(codes_f, axis=1)

    # Random absences for 40% of eligible students
    eligible = df[df['Codes'].apply(lambda c: c.count("P") >= 2)].index.tolist()
    if eligible:
        chosen = random.sample(eligible, round(len(eligible) * 0.40))
        for idx in chosen:
            codes = df.at[idx, 'Codes'][:]
            p_pos = [i for i, c in enumerate(codes) if c == "P"]
            for pos in random.sample(p_pos, random.randint(1, min(2, len(p_pos)))):
                codes[pos] = "I"
            df.at[idx, 'Codes'] = codes

    # Build LaTeX rows
    rows_latex = []
    for i, row in enumerate(df.itertuples()):
        rows_latex.append(_make_row(
            i + 1,
            tex_s(str(row.FullName)),
            tex_s(str(row.IDNumber)),
            row.Codes,
            is_mensual,
        ))

    if len(rows_latex) >= 2:
        rows_latex[-2] = "\\nopagebreak[4]\n" + rows_latex[-2]
        rows_latex[-1] = "\\nopagebreak[4]\n" + rows_latex[-1]

    # Headers
    day_cells = "".join(str(d.day).zfill(2) + "&" for d in class_dates)
    month_placeholders = "".join(f"%%M{i}%%&" for i in range(1, 14))
    lt_header = (
        "\\hline\n"
        "\\rowcolor{espamTeal}\\multicolumn{3}{|c|}{\\rule{0pt}{4mm}\\fontsize{10}{10}\\selectfont\\bfseries FECHAS} & "
        f"{month_placeholders} "
        "\\multicolumn{5}{c|}{\\fontsize{10}{10}\\selectfont\\bfseries Totales} \\\\ \\hline\n"
        "\\cellcolor{espamTeal}{\\fontsize{9}{9}\\selectfont\\bfseries N\\textdegree}&"
        "\\cellcolor{espamTeal}{\\fontsize{9}{9}\\selectfont\\bfseries DOCUMENTO}&"
        "\\cellcolor{espamTeal}{\\fontsize{9}{9}\\selectfont\\bfseries ALUMNOS}&"
        f"{day_cells}"
        "\\cellcolor{colorT}{\\fontsize{9}{9}\\selectfont\\bfseries T}&"
        "\\cellcolor{colorJ}{\\fontsize{9}{9}\\selectfont\\bfseries J}&"
        "\\cellcolor{colorI}{\\fontsize{9}{9}\\selectfont\\bfseries I}&"
        "\\cellcolor{colorP}{\\fontsize{9}{9}\\selectfont\\bfseries P}&"
        "\\cellcolor{colorAusente}{\\fontsize{9}{9}\\selectfont\\bfseries Total}\\\\\\hline\n"
        "\\endhead\n"
    )

    # Footer row inside longtable
    footer_row = (
        r"\noalign{\vspace{1.5cm}}" + "\n"
        r"\multicolumn{21}{@{}l@{}}{"
        r"{\fontsize{9}{9}\selectfont\bfseries EXAMEN FINAL:} \hspace{2mm}"
        r"{\fontsize{9}{9}\selectfont %%EXAMEN_FINAL%%}"
        r"\hspace{20mm}"
        r"{\fontsize{9}{9}\selectfont\bfseries SUPLETORIO:} \hspace{1mm}"
        r"{\fontsize{9}{9}\selectfont %%SUPLETORIO%%}"
        r"\hfill"
        r"{\fontsize{9}{9}\selectfont DOCENTE}"
        r"} \\" + "\n"
    )

    clean_code = course_code.replace('_', '-').replace(' ', '-')
    tex = (TEMPLATE
           .replace("%%COURSE_CODE%%", tex_s(clean_code))
           .replace("%%HORARIO%%",     tex_s(horario))
           .replace("%%DOCENTE%%",     FACILITADOR)
           .replace("%%EXAMEN_FINAL%%", tex_s(fecha_examen))
           .replace("%%SUPLETORIO%%",   tex_s(fecha_sup))
           .replace("%%STUDENT_ROWS%%", lt_header + "".join(rows_latex) + footer_row)
           .replace("%%HEIGHT%%",       "5mm")
           .replace("%%OFFSET%%",       "1.5mm"))

    for i, d in enumerate(class_dates, start=1):
        tex = tex.replace(f"%%M{i}%%", MONTH_MAP[d.month])

    return compile_latex(tex, 'asistencia')
