import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from utils import FACILITADOR, tex_s, compile_latex
from cycles import NIVEL_MAP

TEMPLATE_HEADER = r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc} \usepackage[T1]{fontenc}
\usepackage[letterpaper, landscape, margin=1.0cm, top=1.2cm]{geometry}
\usepackage{graphicx, array, longtable, colortbl, xcolor, rotating, needspace}
\usepackage[scaled]{helvet}
\renewcommand{\familydefault}{\sfdefault}
\newcommand{\arialbold}{\fontfamily{phv}\selectfont\bfseries\fontsize{11}{13}\selectfont}
\newcolumntype{W}[1]{>{\centering\arraybackslash}m{#1}}
\newcolumntype{P}[1]{>{\columncolor{promlac}}W{#1}}
\newcolumntype{Q}[1]{>{\columncolor{promlac}}W{#1}}
\definecolor{row_red}{RGB}{217, 149, 148}
\definecolor{row_green}{RGB}{234, 242, 221}
\definecolor{row_blue}{RGB}{146, 205, 219}
\definecolor{row_lime}{RGB}{146, 209, 79}
\definecolor{row_peach}{RGB}{252, 233, 218}
\definecolor{row_cyan}{RGB}{1, 176, 241}
\definecolor{promlac}{HTML}{F8F4A8}
\newcommand{\headerstyle}[1]{{\fontsize{10}{11}\selectfont\bfseries\fontfamily{phv}\selectfont #1}}
\newcommand{\vtwo}[2]{\rotatebox{90}{\begin{tabular}[c]{@{}c@{}}\fontsize{9}{9.5}\selectfont\bfseries\fontfamily{phv}\selectfont #1 \\[0.6em] \fontsize{9}{9.5}\selectfont\bfseries\fontfamily{phv}\selectfont #2 \end{tabular}}}
\newcommand{\vone}[1]{\rotatebox{90}{\fontsize{9}{9.5}\selectfont\bfseries\fontfamily{phv}\selectfont #1}}
\begin{document}
\pagestyle{empty}
\begin{center}
    {\fontfamily{phv}\selectfont\fontsize{8}{8}\selectfont\bfseries \textbf{ESCUELA SUPERIOR POLIT\'ECNICA AGROPECUARIA DE MANAB\'I ``MANUEL F\'ELIX L\'OPEZ''} \par}
    \vspace{5.0pt}
    {\fontfamily{phv}\selectfont\fontsize{8}{8}\selectfont\bfseries \textbf{UNIDAD DE CENTRO DE IDIOMAS} \par}
\end{center}
\vspace{0.2em}
\noindent\begin{minipage}[b]{8.5cm}
    \fontfamily{phv}\selectfont\bfseries\fontsize{9.5}{12.5}\selectfont
    NIVEL: %%NIVEL%% \\
    CICLO: %%CICLO%% \\
    FACILITADOR (A): %%FACILITADOR%% \\
    FECHA: %%FECHA%%
\end{minipage}\hfill
\begin{minipage}[b]{16.5cm} \raggedleft \includegraphics[height=1.95cm, keepaspectratio]{logo.png} \end{minipage}
\vspace{0.15em}
\scriptsize \setlength{\tabcolsep}{0pt} \renewcommand{\arraystretch}{0} \setlength{\arrayrulewidth}{0.75pt}
\begin{longtable}{|W{7mm}|W{23mm}|W{67mm}|>{\columncolor{row_red}}W{8mm}|>{\columncolor{row_red}}W{8mm}|>{\columncolor{row_green}}W{8mm}|>{\columncolor{row_green}}W{8mm}|>{\columncolor{row_blue}}W{8mm}|>{\columncolor{row_blue}}W{8mm}|>{\columncolor{row_lime}}W{8mm}|>{\columncolor{row_lime}}W{8mm}|P{8mm}|Q{8mm}|>{\columncolor{row_peach}}W{9mm}|>{\columncolor{row_cyan}}W{8mm}|>{\columncolor{row_cyan}}W{8mm}|>{\columncolor{row_peach}}W{9mm}|>{\columncolor{row_cyan}}W{8mm}|>{\columncolor{row_cyan}}W{8mm}|>{\columncolor{row_peach}}W{9mm}|W{20mm}|}
\hline \rule{0pt}{28mm} \centering\raisebox{11mm}{\headerstyle{N\textdegree}} & \headerstyle{N\'UMERO DE C\'EDULA} & \headerstyle{ALUMNOS} & \vtwo{RESULTADO DE}{APRENDIZAJE A} & \vone{EQ} & \vtwo{RESULTADO DE}{APRENDIZAJE B} & \vone{EQ} & \vtwo{RESULTADO DE}{APRENDIZAJE C} & \vone{EQ} & \vtwo{RESULTADO DE}{APRENDIZAJE D} & \vone{EQ} & \vtwo{PROMEDIO}{LOGROS A \& C} & \vone{EQ} & \vone{SUBTOTAL} & \vone{EXAMEN} & \vone{EQ} & \vtwo{SUBTOTAL +}{EXAMEN} & \vone{SUPLETORIO} & \vone{EQ} & \vtwo{NOTA}{FINAL} & \headerstyle{ESTADO} \tabularnewline \hline
"""


def _f(v):
    return f"{float(v):.2f}".replace('.', ',')


def _make_student_row(i, id_num, full_name, r):
    return (
        fr"""\rule[-1.5mm]{{0pt}}{{4.5mm}} \raisebox{{0mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {i}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {id_num}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont \raggedright {full_name}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['LO_A'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['EQ_A'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['LO_B'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['EQ_B'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['LO_C'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['EQ_C'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['LO_D'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['EQ_D'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['PROM_AC'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['EQ_PROM_AC'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['SUBTOTAL'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['Examen'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['EQ_EX'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['SUB_EX'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['Supletorio'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['EQ_SUP'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {_f(r['FINAL'])}}} & """
        fr"""\raisebox{{-1.5mm}}{{\fontsize{{8.2}}{{10}}\selectfont\fontfamily{{phv}}\selectfont {tex_s(str(r['ESTADO']))}}} \\ \hline""" + "\n"
    )


def generate_notas(df: pd.DataFrame, cycle_data: dict,
                   course_code: str, level_digit: str,
                   is_mensual: bool = False) -> bytes:

    nivel = NIVEL_MAP.get(str(level_digit), "Unknown")
    if is_mensual:
        from datetime import datetime, timedelta
        inicio_dt = datetime.strptime(cycle_data['inicio'], "%d/%m/%Y")
        fecha = (inicio_dt + timedelta(weeks=3)).strftime("%d/%m/%Y")
    else:
        fecha = cycle_data['informe_docente']

    rows_list = []
    for i, (_, row) in enumerate(df.iterrows(), 1):
        rows_list.append(_make_student_row(
            i,
            tex_s(str(row['IDNumber'])),
            tex_s(str(row['FullName'])),
            row,
        ))
    if len(rows_list) >= 2:
        rows_list[-2] = "\\nopagebreak[4]
" + rows_list[-2]
        rows_list[-1] = "\\nopagebreak[4]
" + rows_list[-1]
    rows_latex = "".join(rows_list)

    # Averages row
    ca = ['LO_A','EQ_A','LO_B','EQ_B','LO_C','EQ_C','LO_D','EQ_D',
          'PROM_AC','EQ_PROM_AC','SUBTOTAL','Examen','EQ_EX','SUB_EX',
          'Supletorio','EQ_SUP','FINAL']
    p_vals = [
        df[df[c] > 0][c].mean() if not df[df[c] > 0].empty else 0.0
        for c in ca
    ]
    avg_row = (
        r"\noalign{\smallskip} \multicolumn{1}{c}{} & \multicolumn{1}{c}{} & "
        r"\multicolumn{1}{c}{\raisebox{-1.2mm}{\fontfamily{phv}\selectfont\bfseries PROMEDIOS}} & "
        + " & ".join(
            fr"\multicolumn{{1}}{{c}}{{\raisebox{{-1.2mm}}{{\fontfamily{{phv}}\selectfont {_f(v)}}}}}"
            for v in p_vals
        )
        + r" & \multicolumn{1}{c}{} \\ \end{longtable}"
    )

    sig = (r"\Needspace{5cm} \vspace{1.9cm} \begin{center} \begin{minipage}{8cm} \centering "
           r"\rule{6cm}{0.4pt} \\ \vspace{4pt} {\arialbold DOCENTE} "
           r"\end{minipage} \end{center} \end{document}")

    clean_code = tex_s(course_code.replace('_', '-').replace(' ', '-'))
    tex = (TEMPLATE_HEADER
           .replace("%%NIVEL%%",      nivel)
           .replace("%%CICLO%%",      clean_code)
           .replace("%%FACILITADOR%%", FACILITADOR)
           .replace("%%FECHA%%",      fecha)
           + rows_latex + avg_row + sig)

    return compile_latex(tex, 'notas')
