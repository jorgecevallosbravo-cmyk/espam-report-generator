"""
Generates Informe Final del Curso as PDF bytes.
2-page A4 portrait institutional form with 61 numbered rows.
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from weasyprint import HTML
import pandas as pd
from utils import (LOGO_DATA_URI, FACILITADOR, FACILITADOR_SHORT,
                   UCI_RESPONSIBLE, esc_html, fmt)
from cycles import NIVEL_MAP


CSS = """
@page { size: A4 portrait; margin: 1.5cm 1.5cm 1.0cm 1.5cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 8pt;
       margin: 0; color: #000; }
.main-table { width: 100%; border-collapse: collapse; }
.main-table td, .main-table th {
  border: 0.8pt solid black;
  padding: 2pt 3pt;
  vertical-align: middle;
  font-size: 8pt;
}
.row-num { width: 7mm; text-align: center; font-size: 8pt;
           font-family: Helvetica; }
.teal-row td { background: #00A99D; color: white; font-weight: bold;
               font-size: 8pt; }
.logo-cell { text-align: center; }
.logo-cell img { height: 24mm; }
.title-cell { text-align: center; font-size: 11pt; font-weight: bold; }
.label { font-weight: bold; padding-left: 2pt; }
.value { padding-left: 2pt; }
.page-break { page-break-before: always; }
.big-number { font-size: 40pt; font-weight: bold; text-align: center;
              vertical-align: middle; }
.italic-text { font-style: italic; font-size: 8pt; }
.qual-cell { font-size: 7.5pt; padding: 4pt; }
.sig-area { height: 30mm; vertical-align: bottom; font-size: 8pt; }
"""


def _compute_stats(df: pd.DataFrame) -> dict:
    active = df[df['ESTADO'] != 'RETIRADO']
    avg    = round(active['FINAL'].mean(), 2) if not active.empty else 0.0
    total  = len(df)
    passed = len(df[df['ESTADO'] == 'APROBADO'])
    failed = len(df[df['ESTADO'] == 'REPROBADO'])
    pass_rate = round(passed / total * 100, 2) if total > 0 else 0.0

    def scaled_avg(col, scale):
        vals = df[df[col] > 0][col]
        return round(vals.mean() / 10 * scale, 2) if not vals.empty else 0.0

    return {
        'avg': avg, 'pass_rate': pass_rate, 'fail': failed,
        'lo_a': scaled_avg('LO_A', 1.5),
        'lo_b': scaled_avg('LO_B', 1.5),
        'lo_c': scaled_avg('LO_C', 2.0),
        'lo_d': scaled_avg('LO_D', 2.0),
    }


def generate_informe_final(
    df: pd.DataFrame,
    cycle_data: dict,
    course_code: str,
    level_digit: str,
    classroom: str,
) -> bytes:

    nivel   = NIVEL_MAP.get(level_digit, "Unknown")
    periodo = cycle_data['periodo']
    fecha_doc = cycle_data['informe_docente']
    fecha_uci = cycle_data['informe_resp']
    s = _compute_stats(df)

    qual = (
        f"The group demonstrated strong academic performance, achieving an average "
        f"grade of {fmt(s['avg'])} and a {fmt(s['pass_rate'])}% passing rate. "
        f"While {s['fail']} student(s) failed based on grades, no students failed "
        f"due to attendance; furthermore, no curricular adaptations were necessary. "
        f"Overall, the class successfully met the expected learning outcomes, "
        f"and no immediate improvement plans are required."
    )

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>{CSS}</style></head><body>

<!-- PAGE 1 -->
<table class="main-table">
<col style="width:7mm"><col style="width:46mm"><col style="width:41mm">
<col style="width:41mm"><col style="width:41mm">

<tr>
  <td class="row-num">1</td>
  <td colspan="4" class="logo-cell">
    <img src="{LOGO_DATA_URI}" alt="ESPAM Logo">
  </td>
</tr>
<tr>
  <td class="row-num">2</td>
  <td colspan="4" class="title-cell">
    FINAL COURSE REPORT — LANGUAGE CENTER UNIT
  </td>
</tr>
<tr>
  <td class="row-num">3</td>
  <td colspan="4" style="height:7mm"></td>
</tr>
<tr class="teal-row">
  <td class="row-num" style="background:#00A99D;color:white">4</td>
  <td colspan="4">1. GENERAL INFORMATION</td>
</tr>
<tr>
  <td class="row-num">5</td>
  <td class="label">Course code:</td>
  <td colspan="3" class="value">{esc_html(course_code)}</td>
</tr>
<tr>
  <td class="row-num">6</td>
  <td class="label">Level:</td>
  <td colspan="3" class="value">{esc_html(nivel)}</td>
</tr>
<tr>
  <td class="row-num">7</td>
  <td class="label">Program:</td>
  <td colspan="3" class="value">English Language</td>
</tr>
<tr>
  <td class="row-num">8</td>
  <td class="label">Responsible Teacher:</td>
  <td colspan="3" class="value">{FACILITADOR}</td>
</tr>
<tr>
  <td class="row-num">9</td>
  <td class="label">Academic Period:</td>
  <td colspan="3" class="value">{esc_html(periodo)}</td>
</tr>
<tr>
  <td class="row-num">10</td>
  <td class="label">Classroom:</td>
  <td colspan="3" class="value">{esc_html(classroom)}</td>
</tr>
<tr class="teal-row">
  <td class="row-num" style="background:#00A99D;color:white">11</td>
  <td colspan="4">2. COMPLIANCE WITH ACADEMIC PLANNING</td>
</tr>
<tr>
  <td class="row-num">12</td>
  <td class="label">Learning Type</td>
  <td class="label">Planned Hours</td>
  <td class="label">Completed Hours</td>
  <td class="label">Total Hours</td>
</tr>
<tr>
  <td class="row-num">13</td>
  <td>AA (Autonomous Learning)</td>
  <td style="text-align:center">16</td>
  <td style="text-align:center">16</td>
  <td rowspan="3" class="big-number">80</td>
</tr>
<tr>
  <td class="row-num">14</td>
  <td>PECD (Practical Learning)</td>
  <td style="text-align:center">16</td>
  <td style="text-align:center">16</td>
</tr>
<tr>
  <td class="row-num">15</td>
  <td>ACD (Teacher Contact)</td>
  <td style="text-align:center">48</td>
  <td style="text-align:center">48</td>
</tr>
<tr class="teal-row">
  <td class="row-num" style="background:#00A99D;color:white">16</td>
  <td colspan="4">3. ACHIEVEMENT OF LEARNING OUTCOMES</td>
</tr>
<tr>
  <td class="row-num">17</td>
  <td class="label">Unit</td>
  <td class="label">Learning Outcome</td>
  <td class="label">Evidence Used</td>
  <td class="label">Achievement Score</td>
</tr>
<tr>
  <td class="row-num">18</td>
  <td>Unit 1</td><td>Learning Outcome A</td>
  <td>Presentation Video</td>
  <td style="text-align:center">{fmt(s['lo_a'])}</td>
</tr>
<tr>
  <td class="row-num">19</td>
  <td>Unit 2</td><td>Learning Outcome B</td>
  <td>Writing</td>
  <td style="text-align:center">{fmt(s['lo_b'])}</td>
</tr>
<tr>
  <td class="row-num">20</td>
  <td>Unit 3</td><td>Learning Outcome C</td>
  <td>Class Presentation</td>
  <td style="text-align:center">{fmt(s['lo_c'])}</td>
</tr>
<tr>
  <td class="row-num">21</td>
  <td>Unit 4</td><td>Learning Outcome D</td>
  <td>Class Presentation</td>
  <td style="text-align:center">{fmt(s['lo_d'])}</td>
</tr>
<tr class="teal-row">
  <td class="row-num" style="background:#00A99D;color:white">22</td>
  <td colspan="4">4. STUDENT PERFORMANCE ANALYSIS</td>
</tr>
<tr>
  <td class="row-num">23</td>
  <td class="label">Average grade:</td>
  <td>{fmt(s['avg'])}</td>
  <td colspan="2" rowspan="6" class="qual-cell">{esc_html(qual)}</td>
</tr>
<tr>
  <td class="row-num">24</td>
  <td class="label">Passing rate (%):</td>
  <td>{fmt(s['pass_rate'])}</td>
</tr>
<tr>
  <td class="row-num">25</td>
  <td class="label">Failed by attendance:</td><td>0</td>
</tr>
<tr>
  <td class="row-num">26</td>
  <td class="label">Failed by grades:</td><td>{s['fail']}</td>
</tr>
<tr>
  <td class="row-num">27</td>
  <td class="label">Curricular adaptations:</td><td>N/A</td>
</tr>
<tr>
  <td class="row-num">28</td>
  <td class="label">Improvement plans:</td><td>N/A</td>
</tr>
<tr class="teal-row">
  <td class="row-num" style="background:#00A99D;color:white">29</td>
  <td colspan="4">5. COURSE CONTRIBUTION</td>
</tr>
<tr>
  <td class="row-num">30</td>
  <td colspan="4" class="italic-text">
    Throughout this course students demonstrated steady engagement with the content
    and activities. Their participation contributed positively to the overall
    learning environment, particularly through collaborative tasks and consistent
    application of the target language.
  </td>
</tr>
<tr><td class="row-num">31</td><td colspan="4" style="height:5mm"></td></tr>
<tr><td class="row-num">32</td><td colspan="4" style="height:5mm"></td></tr>
<tr class="teal-row">
  <td class="row-num" style="background:#00A99D;color:white">33</td>
  <td colspan="4">6. MAIN DIFFICULTIES</td>
</tr>
<tr>
  <td class="row-num">34</td>
  <td colspan="4" class="italic-text">
    The course presented a moderate level of difficulty, primarily due to occasional
    absences. Although these factors created certain challenges, they did not
    jeopardize students' overall performance.
  </td>
</tr>
<tr><td class="row-num">35</td><td colspan="4" style="height:5mm"></td></tr>
<tr><td class="row-num">36</td><td colspan="4" style="height:5mm"></td></tr>
<tr><td class="row-num">37</td><td colspan="4" style="height:5mm"></td></tr>
</table>

<!-- PAGE 2 -->
<div class="page-break"></div>
<table class="main-table">
<col style="width:7mm"><col style="width:46mm"><col style="width:41mm">
<col style="width:41mm"><col style="width:41mm">

<tr>
  <td class="row-num">A</td><td colspan="4" style="height:5mm"></td>
</tr>
<tr class="teal-row">
  <td class="row-num" style="background:#00A99D;color:white">38</td>
  <td colspan="4">7. SUPPORT OR REINFORCEMENT ACTIONS IMPLEMENTED</td>
</tr>
<tr>
  <td class="row-num">39</td>
  <td colspan="4" class="italic-text">
    Reminders and follow-ups were implemented to mitigate the impact of occasional
    absences, maintaining consistent participation and engagement throughout the course.
  </td>
</tr>
<tr><td class="row-num">40</td><td colspan="4" style="height:5mm"></td></tr>
<tr><td class="row-num">41</td><td colspan="4" style="height:5mm"></td></tr>
<tr><td class="row-num">42</td><td colspan="4" style="height:5mm"></td></tr>
<tr><td class="row-num">43</td><td colspan="4" style="height:5mm"></td></tr>
<tr class="teal-row">
  <td class="row-num" style="background:#00A99D;color:white">44</td>
  <td colspan="4">8. SUGGESTIONS FOR IMPROVEMENT</td>
</tr>
<tr>
  <td class="row-num">45</td>
  <td colspan="4" class="italic-text">
    For future terms, it is recommended to implement more structured attendance
    monitoring to further support continuous learning and engagement.
  </td>
</tr>
<tr><td class="row-num">46</td><td colspan="4" style="height:5mm"></td></tr>
<tr><td class="row-num">47</td><td colspan="4" style="height:5mm"></td></tr>
<tr><td class="row-num">48</td><td colspan="4" style="height:5mm"></td></tr>
<tr><td class="row-num">49</td><td colspan="4" style="height:5mm"></td></tr>
<tr class="teal-row">
  <td class="row-num" style="background:#00A99D;color:white">50</td>
  <td colspan="4">9. GENERAL OBSERVATIONS (teacher's comments)</td>
</tr>
<tr>
  <td class="row-num">51</td>
  <td colspan="4" class="italic-text">
    Overall, students demonstrated commitment and adaptability. Their active
    participation significantly contributed to a positive learning environment.
  </td>
</tr>
<tr><td class="row-num">52</td><td colspan="4" style="height:5mm"></td></tr>
<tr><td class="row-num">53</td><td colspan="4" style="height:5mm"></td></tr>
<tr><td class="row-num">54</td><td colspan="4" style="height:5mm"></td></tr>
<tr class="teal-row">
  <td class="row-num" style="background:#00A99D;color:white">55</td>
  <td colspan="4">10. SIGNATURES</td>
</tr>
<tr>
  <td class="row-num">56</td><td colspan="4" style="height:5mm"></td>
</tr>
<tr>
  <td class="row-num">57</td>
  <td colspan="2" style="font-size:8pt">Teacher:</td>
  <td colspan="2" style="font-size:8pt">Responsable UCI:</td>
</tr>
<tr>
  <td class="row-num">58</td>
  <td colspan="2" style="font-size:8pt">{FACILITADOR}</td>
  <td colspan="2" style="font-size:8pt">{UCI_RESPONSIBLE}</td>
</tr>
<tr>
  <td class="row-num">59</td>
  <td colspan="2" style="font-size:8pt"><b>Date: {esc_html(fecha_doc)}</b></td>
  <td colspan="2" style="font-size:8pt"><b>Date: {esc_html(fecha_uci)}</b></td>
</tr>
<tr>
  <td class="row-num">60</td>
  <td colspan="2" class="sig-area"><i>Signature:</i></td>
  <td colspan="2" class="sig-area"><i>Signature:</i></td>
</tr>
<tr>
  <td class="row-num">61</td><td colspan="4" style="height:5mm"></td>
</tr>
</table>

</body></html>"""

    return HTML(string=html).write_pdf()
