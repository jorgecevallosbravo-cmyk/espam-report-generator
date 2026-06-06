import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from utils import FACILITADOR, UCI_RESPONSIBLE, tex_s, compile_latex
from cycles import NIVEL_MAP


def _stats(df):
    active    = df[df['ESTADO'] != 'RETIRADO']
    total     = len(df)
    passed    = len(df[df['ESTADO'] == 'APROBADO'])
    failed    = len(df[df['ESTADO'] == 'REPROBADO'])
    avg       = round(active['FINAL'].mean(), 2) if not active.empty else 0.0
    pass_rate = round(passed / total * 100, 2) if total > 0 else 0.0

    def scaled(col, scale):
        vals = df[df[col] > 0][col]
        return round(vals.mean() / 10 * scale, 2) if not vals.empty else 0.0

    return {
        'avg': avg, 'pass_rate': pass_rate, 'fail': failed,
        'lo_a': scaled('LO_A', 1.5), 'lo_b': scaled('LO_B', 1.5),
        'lo_c': scaled('LO_C', 2.0), 'lo_d': scaled('LO_D', 2.0),
    }


def _f(v):
    return f"{float(v):.2f}".replace('.', ',')


def generate_informe_final(df: pd.DataFrame, cycle_data: dict,
                           course_code: str, level_digit: str,
                           classroom: str) -> bytes:

    nivel   = NIVEL_MAP.get(str(level_digit), "Unknown")
    periodo = cycle_data['periodo']
    fecha_doc = cycle_data['informe_docente']
    fecha_uci = cycle_data['informe_resp']
    s = _stats(df)
    clean_code = tex_s(course_code.replace('_', '-'))

    qual = (
        f"The group demonstrated strong academic performance, achieving an average "
        f"grade of {_f(s['avg'])} and a {_f(s['pass_rate'])}\\% passing rate. "
        f"While {s['fail']} student(s) failed based on grades, no students failed "
        f"due to attendance; furthermore, no curricular adaptations were necessary. "
        f"Overall, the class successfully met the expected learning outcomes, "
        f"and no immediate improvement plans are required."
    )

    latex = r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc} \usepackage[T1]{fontenc}
\usepackage[a4paper, margin=1.5cm, top=1.5cm, bottom=1cm]{geometry}
\usepackage{array, multirow, graphicx, hhline}
\usepackage[scaled]{helvet}
\usepackage[table]{xcolor}
\renewcommand{\familydefault}{\sfdefault}
\definecolor{rowteal}{HTML}{00A99D}
\setlength{\arrayrulewidth}{0.8pt}
\begin{document}
\setlength{\tabcolsep}{0pt}
\begin{tabular}{| p{4.23mm} | p{46.92mm} | p{40.92mm} | p{40.92mm} | p{41.28mm} |}
\hline \rule{0pt}{2.5mm} & \centering\tiny A & \centering\tiny B & \centering\tiny C & \centering\tiny D \tabularnewline \hline
\rule{0pt}{24mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 1 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\centering \includegraphics[height=24mm, keepaspectratio]{logo.png}} \tabularnewline \hline
\rule{0pt}{4.95mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 2 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\centering \fontfamily{phv}\fontsize{10}{12}\selectfont\bfseries FINAL COURSE REPORT -- LANGUAGE CENTER UNIT} \tabularnewline \hline
\rule{0pt}{2.85mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 3 & \multicolumn{4}{@{}p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}@{}|}{\begin{tabular}{p{42.51mm}|p{42.51mm}|p{42.51mm}|p{42.51mm}} \rule{0pt}{2.85mm} & & & \tabularnewline \end{tabular}} \tabularnewline \hhline{|-|-|-|-|-|}
\multicolumn{1}{|>{\columncolor{rowteal}[0.2pt][0pt]}p{4.23mm}|}{\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 4} & \multicolumn{4}{>{\columncolor{rowteal}[0pt][3pt]}p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries 1. GENERAL INFORMATION} \tabularnewline \hhline{|-|-|-|-|-|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 5 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Course code:} & \multicolumn{3}{p{\dimexpr 122.41mm + 2\arrayrulewidth \relax}|}{\hspace{0.375mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + clean_code + r"""} \tabularnewline \hline
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 6 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Level:} & \multicolumn{3}{p{\dimexpr 122.41mm + 2\arrayrulewidth \relax}|}{\hspace{0.375mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + nivel + r"""} \tabularnewline \hline
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 7 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Program:} & \multicolumn{3}{p{\dimexpr 122.41mm + 2\arrayrulewidth \relax}|}{\hspace{0.375mm}\fontfamily{phv}\fontsize{8}{10}\selectfont English Language} \tabularnewline \hline
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 8 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Responsible Teacher:} & \multicolumn{3}{p{\dimexpr 122.41mm + 2\arrayrulewidth \relax}|}{\hspace{0.375mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + tex_s(FACILITADOR) + r"""} \tabularnewline \hline
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 9 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Academic Period:} & \multicolumn{3}{p{\dimexpr 122.41mm + 2\arrayrulewidth \relax}|}{\hspace{0.375mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + tex_s(periodo) + r"""} \tabularnewline \hline
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 10 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Classroom:} & \multicolumn{3}{p{\dimexpr 122.41mm + 2\arrayrulewidth \relax}|}{\hspace{0.375mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + tex_s(classroom) + r"""} \tabularnewline \hline
\multicolumn{1}{|>{\columncolor{rowteal}[0.2pt][0pt]}p{4.23mm}|}{\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 11} & \multicolumn{4}{>{\columncolor{rowteal}[0pt][3pt]}p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries 2. COMPLIANCE WITH ACADEMIC PLANNING} \tabularnewline \hhline{|-|-|-|-|-|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 12 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries Learning Type} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries Planned Hours} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries Completed Hours} & \multicolumn{1}{p{41.28mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries Total Hours} \tabularnewline \hline
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 13 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{7.5}{9}\selectfont AA (Autonomous Learning)} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont 16} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont 16} & \multirow{3}{=}{\centering\fontfamily{phv}\fontsize{50}{60}\selectfont\bfseries 80} \tabularnewline \hhline{|-|-|-|-|~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 14 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{7.5}{9}\selectfont PECD (Practical Learning)} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont 16} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont 16} & \tabularnewline \hhline{|-|-|-|-|~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 15 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{7.5}{9}\selectfont ACD (Teacher Contact)} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont 48} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont 48} & \tabularnewline \hline
\multicolumn{1}{|>{\columncolor{rowteal}[0.2pt][0pt]}p{4.23mm}|}{\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 16} & \multicolumn{4}{>{\columncolor{rowteal}[0pt][3pt]}p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries 3. ACHIEVEMENT OF LEARNING OUTCOMES} \tabularnewline \hhline{|-|-|-|-|-|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 17 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries Unit} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries Learning Outcome} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries Evidence Used} & \multicolumn{1}{p{41.28mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries Achievement Score} \tabularnewline \hline
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 18 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Unit 1} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Learning Outcome A} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Presentation Video} & \multicolumn{1}{p{41.28mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + _f(s['lo_a']) + r"""} \tabularnewline \hline
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 19 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Unit 2} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Learning Outcome B} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Writing} & \multicolumn{1}{p{41.28mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + _f(s['lo_b']) + r"""} \tabularnewline \hline
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 20 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Unit 3} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Learning Outcome C} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Class Presentation} & \multicolumn{1}{p{41.28mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + _f(s['lo_c']) + r"""} \tabularnewline \hline
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 21 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Unit 4} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Learning Outcome D} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Class Presentation} & \multicolumn{1}{p{41.28mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + _f(s['lo_d']) + r"""} \tabularnewline \hline
\multicolumn{1}{|>{\columncolor{rowteal}[0.2pt][0pt]}p{4.23mm}|}{\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 22} & \multicolumn{4}{>{\columncolor{rowteal}[0pt][3pt]}p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries 4. STUDENT PERFORMANCE ANALYSIS} \tabularnewline \hhline{|-|-|-|-|-|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 23 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Average grade:} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + _f(s['avg']) + r"""} & \multicolumn{2}{p{82.2mm}|}{\multirow{6}{=}{\centering\begin{minipage}{78mm}\vspace{2mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Qualitative analysis: """ + qual + r"""\vspace{2mm}\end{minipage}}} \tabularnewline \hhline{|-|-|-|~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 24 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Passing rate (\%):} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + _f(s['pass_rate']) + r"""} & \multicolumn{2}{l|}{} \tabularnewline \hhline{|-|-|-|~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 25 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Failed by attendance:} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont 0} & \multicolumn{2}{l|}{} \tabularnewline \hhline{|-|-|-|~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 26 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Failed by grades:} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + str(s['fail']) + r"""} & \multicolumn{2}{l|}{} \tabularnewline \hhline{|-|-|-|~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 27 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Curricular adaptations:} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont N/A} & \multicolumn{2}{l|}{} \tabularnewline \hhline{|-|-|-|~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 28 & \multicolumn{1}{p{47.63mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Improvement plans:} & \multicolumn{1}{p{40.92mm}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont N/A} & \multicolumn{2}{l|}{} \tabularnewline \hline
\multicolumn{1}{|>{\columncolor{rowteal}[0.2pt][0pt]}p{4.23mm}|}{\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 29} & \multicolumn{4}{>{\columncolor{rowteal}[0pt][3pt]}p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries 5. COURSE CONTRIBUTION} \tabularnewline \hhline{|-|-|-|-|-|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 30 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\multirow{3}{=}{\centering\begin{minipage}{164mm}\vspace{2mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\itshape Throughout this Course students demonstrated steady engagement with the content and activities. Their participation contributed positively to the overall learning environment, particularly through collaborative tasks and consistent application of the target language.\vspace{2mm}\end{minipage}}} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 31 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 32 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hline
\multicolumn{1}{|>{\columncolor{rowteal}[0.2pt][0pt]}p{4.23mm}|}{\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 33} & \multicolumn{4}{>{\columncolor{rowteal}[0pt][3pt]}p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries 6. MAIN DIFFICULTIES} \tabularnewline \hhline{|-|-|-|-|-|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 34 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\multirow{4}{=}{\centering\begin{minipage}{164mm}\vspace{2mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\itshape The course presented a moderate level of difficulty, primarily due to occasional absences. Although these factors created certain challenges, they did not jeopardize students' overall performance.\vspace{2mm}\end{minipage}}} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 35 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 36 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 37 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hline
\end{tabular}

\newpage
\begin{tabular}{| p{4.23mm} | p{46.92mm} | p{40.92mm} | p{40.92mm} | p{41.28mm} |}
\hline \rule{0pt}{2.5mm} & \centering\tiny A & \centering\tiny B & \centering\tiny C & \centering\tiny D \tabularnewline \hline
\multicolumn{1}{|>{\columncolor{rowteal}[0.2pt][0pt]}p{4.23mm}|}{\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 38} & \multicolumn{4}{>{\columncolor{rowteal}[0pt][9.0pt]}p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries 7. SUPPORT OR REINFORCEMENT ACTIONS IMPLEMENTED} \tabularnewline \hhline{|-|-|-|-|-|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 39 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\multirow{5}{=}{\centering\begin{minipage}{164mm}\vspace{2mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\itshape Reminders and follow-ups were implemented to mitigate the impact of occasional absences, maintaining consistent participation and engagement throughout the course.\vspace{2mm}\end{minipage}}} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 40 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 41 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 42 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 43 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hline
\multicolumn{1}{|>{\columncolor{rowteal}[0.2pt][0pt]}p{4.23mm}|}{\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 44} & \multicolumn{4}{>{\columncolor{rowteal}[0pt][9.0pt]}p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries 8. SUGGESTIONS FOR IMPROVEMENT} \tabularnewline \hhline{|-|-|-|-|-|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 45 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\multirow{5}{=}{\centering\begin{minipage}{164mm}\vspace{2mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\itshape For future terms, it is recommended to implement more structured attendance monitoring to further support continuous learning and engagement.\vspace{2mm}\end{minipage}}} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 46 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 47 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 48 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 49 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hline
\multicolumn{1}{|>{\columncolor{rowteal}[0.2pt][0pt]}p{4.23mm}|}{\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 50} & \multicolumn{4}{>{\columncolor{rowteal}[0pt][9.0pt]}p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries 9. GENERAL OBSERVATIONS (teacher's comments)} \tabularnewline \hhline{|-|-|-|-|-|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 51 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\multirow{4}{=}{\centering\begin{minipage}{164mm}\vspace{2mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\itshape Overall, students demonstrated commitment and adaptability. Their active participation significantly contributed to a positive learning environment.\vspace{2mm}\end{minipage}}} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 52 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 53 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hhline{|-|~~~~|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 54 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hline
\multicolumn{1}{|>{\columncolor{rowteal}[0.2pt][0pt]}p{4.23mm}|}{\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 55} & \multicolumn{4}{>{\columncolor{rowteal}[0pt][9.0pt]}p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries 10. SIGNATURES} \tabularnewline \hhline{|-|-|-|-|-|}
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 56 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 57 & \multicolumn{2}{p{\dimexpr 87.84mm + \arrayrulewidth \relax}}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Teacher:} & \multicolumn{2}{p{\dimexpr 82.2mm + 2\arrayrulewidth \relax}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont Responsable UCI:} \tabularnewline
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 58 & \multicolumn{2}{p{\dimexpr 87.84mm + \arrayrulewidth \relax}}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + tex_s(FACILITADOR) + r"""} & \multicolumn{2}{p{\dimexpr 82.2mm + 2\arrayrulewidth \relax}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont """ + tex_s(UCI_RESPONSIBLE) + r"""} \tabularnewline
\rule{0pt}{4.94mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 59 & \multicolumn{2}{p{\dimexpr 87.84mm + \arrayrulewidth}}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries Date: """ + tex_s(fecha_doc) + r"""} & \multicolumn{2}{p{\dimexpr 82.2mm + 2\arrayrulewidth}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries Date: """ + tex_s(fecha_uci) + r"""} \tabularnewline \hline
\rule{0pt}{30mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 60 & \multicolumn{2}{p{\dimexpr 85.02mm + 1.5\arrayrulewidth \relax}}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries\itshape Signature:} & \multicolumn{2}{p{\dimexpr 85.02mm + 1.5\arrayrulewidth \relax}|}{\hspace{1mm}\fontfamily{phv}\fontsize{8}{10}\selectfont\bfseries\itshape Signature:} \tabularnewline \hline
\rule{0pt}{3mm}\centering\fontfamily{phv}\fontsize{10}{12}\selectfont 61 & \multicolumn{4}{p{\dimexpr 170.04mm + 3\arrayrulewidth \relax}|}{} \tabularnewline \hline
\end{tabular}
\end{document}"""

    return compile_latex(latex, 'informe_final')
