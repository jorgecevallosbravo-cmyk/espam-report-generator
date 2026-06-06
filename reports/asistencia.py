"""
Generates Informe de Asistencia (Final and Mensual) as PDF bytes.
Replicates the original LaTeX output using WeasyPrint HTML/CSS.
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import random
from datetime import date, timedelta
from weasyprint import HTML
from utils import LOGO_DATA_URI, FACILITADOR, esc_html

MONTH_MAP = {
    1:"JAN",2:"FEB",3:"MAR",4:"APR",5:"MAY",6:"JUN",
    7:"JUL",8:"AUG",9:"SEP",10:"OCT",11:"NOV",12:"DEC"
}

NUM_DATES    = 13
NUM_MENSUAL  = 5   # Only first 5 sessions filled for monthly report


def _parse_date(s: str) -> date:
    d, m, y = s.strip().split("/")
    return date(int(y), int(m), int(d))


def _get_class_dates(inicio: str, fin: str):
    start = _parse_date(inicio)
    end   = _parse_date(fin)
    span  = (end - start).days
    weekdays = {0, 2, 4} if span <= 40 else {1, 3}
    dates = []
    cur = start
    while len(dates) < NUM_DATES:
        if cur.weekday() in weekdays:
            dates.append(cur)
        cur += timedelta(days=1)
        if cur > end + timedelta(days=400):
            break
    return dates


def _attendance_codes_final(row, grade_cols):
    a, b, c, d = [row[col] for col in grade_cols[:4]]
    exam = row[grade_cols[4]] if len(grade_cols) >= 5 else 0.0
    total = a + b + c + d + exam
    if total == 0.0:
        return ["I"] * NUM_DATES
    elif a > 0 and b == 0 and c == 0 and d == 0 and exam == 0.0:
        return ["P"] * 3 + ["I"] * 10
    else:
        return ["P"] * NUM_DATES


def _attendance_codes_mensual(row):
    a, b = row['LO_A'], row['LO_B']
    if a == 0.0 and b == 0.0:
        return ["I"] * NUM_MENSUAL
    elif a > 0 and b == 0.0:
        return ["P"] + ["I"] * (NUM_MENSUAL - 1)
    else:
        return ["P"] * NUM_MENSUAL


def _add_random_absences(df, codes_col):
    eligible = df[df[codes_col].apply(lambda c: c.count("P") >= 2)].index.tolist()
    if not eligible:
        return df
    chosen = random.sample(eligible, round(len(eligible) * 0.40))
    for idx in chosen:
        codes = df.at[idx, codes_col][:]
        p_pos = [i for i, c in enumerate(codes) if c == "P"]
        for pos in random.sample(p_pos, random.randint(1, min(2, len(p_pos)))):
            codes[pos] = "I"
        df.at[idx, codes_col] = codes
    return df


def _cell_color(code):
    return {
        "P": "#F5E7CB",
        "I": "#FC935A",
        "J": "#FED363",
        "T": "#B4D23C",
    }.get(code, "#FFFFFF")


def _build_table_html(df, class_dates, horario, course_code, fecha_examen,
                      fecha_supletorio, num_populated, is_mensual):
    """Build the main student attendance table HTML."""

    # Header row 1 — date labels
    date_headers = ""
    for d in class_dates:
        date_headers += f'<th class="date-h">{str(d.day).zfill(2)}</th>'

    # Header row 0 — month labels
    month_headers = ""
    for d in class_dates:
        month_headers += f'<th class="month-h">{MONTH_MAP[d.month]}</th>'

    # Student rows
    rows_html = ""
    for i, row in df.iterrows():
        is_even = (i % 2 == 0)
        row_bg  = "#DBF0F6" if is_even else "#FFFFFF"
        name    = esc_html(str(row['FullName']))
        id_num  = esc_html(str(row['IDNumber']))
        codes   = row['Codes']

        p_count = codes.count("P")
        i_count = codes.count("I")

        att_cells = ""
        for j, code in enumerate(codes):
            bg = _cell_color(code)
            att_cells += f'<td style="background:{bg};text-align:center;font-size:7pt;">{code}</td>'

        if is_mensual:
            for _ in range(NUM_DATES - num_populated):
                att_cells += f'<td style="background:{row_bg}"></td>'

        rows_html += f"""
        <tr style="background:{row_bg}">
          <td style="text-align:center">{i+1}</td>
          <td style="text-align:center;font-size:7pt">{id_num}</td>
          <td style="font-size:7.5pt">{name}</td>
          {att_cells}
          <td style="text-align:center">0</td>
          <td style="text-align:center">0</td>
          <td style="text-align:center;background:#FC935A">{i_count}</td>
          <td style="text-align:center;background:#F5E7CB">{p_count}</td>
          <td style="text-align:center">{i_count}</td>
        </tr>"""

    return date_headers, month_headers, rows_html


CSS = """
@page { size: letter landscape; margin: 0.5cm 0.5cm 0.5cm 0.5cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 8pt; margin: 0; }
.main-header { background: #00A99D; color: white; display: flex;
               align-items: center; padding: 4mm 3mm; margin-bottom: 2pt; }
.main-header .title { font-size: 18pt; font-weight: bold; flex: 1; }
.main-header .code  { font-size: 18pt; font-weight: bold; }
.meta-table { width: 100%; border-collapse: collapse; margin-bottom: 2pt; font-size: 8pt; }
.meta-table td { padding: 1pt 3pt; }
.logo-cell { text-align: right; }
.logo-cell img { height: 11mm; }
.color-key { font-size: 7pt; }
.color-key span { display: inline-block; width: 8pt; height: 8pt;
                  vertical-align: middle; margin: 0 1pt; }
.att-table { width: 100%; border-collapse: collapse; font-size: 8pt; }
.att-table th, .att-table td {
  border: 0.6pt solid black; padding: 1pt 2pt; white-space: nowrap; }
.teal-hdr { background: #00A99D; color: white; font-weight: bold;
            text-align: center; font-size: 7.5pt; }
.month-h  { background: #00A99D; color: white; font-size: 6pt;
            text-align: center; padding: 1pt; }
.date-h   { background: #00A99D; color: white; font-size: 7pt;
            text-align: center; width: 9mm; }
.totals-h { background: #00A99D; color: white; font-size: 7pt; text-align: center; }
.footer   { margin-top: 4pt; font-size: 8pt; }
"""


def generate_asistencia(df, cycle_data: dict, horario: str,
                        course_code: str, is_mensual: bool = False) -> bytes:
    """
    Generate attendance PDF.
    df: normalized DataFrame from intake.py
    cycle_data: dict from cycles.py
    horario: e.g. '07h00 - 09h00'
    course_code: e.g. 'E406-F-C14NM'
    is_mensual: True for monthly report, False for final
    """
    import pandas as pd

    inicio        = cycle_data['inicio']
    fin           = cycle_data['fin']
    fecha_examen  = cycle_data['examen']
    fecha_sup     = cycle_data['supletorio']

    class_dates   = _get_class_dates(inicio, fin)
    num_populated = NUM_MENSUAL if is_mensual else NUM_DATES

    # Build attendance codes
    df = df.copy()
    if is_mensual:
        df['Codes'] = df.apply(_attendance_codes_mensual, axis=1)
    else:
        grade_cols = ['LO_A', 'LO_B', 'LO_C', 'LO_D', 'Examen']
        df['Codes'] = df.apply(
            lambda r: _attendance_codes_final(r, grade_cols), axis=1)

    df = _add_random_absences(df, 'Codes')

    date_headers, month_headers, rows_html = _build_table_html(
        df, class_dates, horario, course_code,
        fecha_examen, fecha_sup, num_populated, is_mensual
    )

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>{CSS}</style></head><body>

<div class="main-header">
  <div class="title">REGISTRO DE ASISTENCIA</div>
  <div class="code">{esc_html(course_code)}</div>
</div>

<table class="meta-table">
<tr>
  <td><b>IDIOMA:</b> Inglés</td>
  <td rowspan="3" class="color-key">
    <b>CLAVE DE COLOR</b><br>
    <span style="background:#B4D23C"></span>T Tarde &nbsp;
    <span style="background:#FC935A"></span>I Injustificado<br>
    <span style="background:#FED363"></span>J Justificado &nbsp;
    <span style="background:#F5E7CB"></span>P Presente
  </td>
  <td rowspan="3" class="logo-cell">
    <img src="{LOGO_DATA_URI}" alt="ESPAM Logo">
  </td>
</tr>
<tr><td><b>HORARIO:</b> {esc_html(horario)}</td></tr>
<tr><td><b>DOCENTE:</b> {FACILITADOR}</td></tr>
</table>

<table class="att-table">
<thead>
  <tr>
    <th class="teal-hdr" rowspan="2" style="width:6mm">N°</th>
    <th class="teal-hdr" rowspan="2" style="width:22mm">DOCUMENTO</th>
    <th class="teal-hdr" rowspan="2" style="width:55mm">ALUMNOS</th>
    {month_headers}
    <th class="totals-h" colspan="5">Totales</th>
  </tr>
  <tr>
    {date_headers}
    <th class="totals-h" style="background:#B4D23C;color:black">T</th>
    <th class="totals-h" style="background:#FED363;color:black">J</th>
    <th class="totals-h" style="background:#FC935A;color:black">I</th>
    <th class="totals-h" style="background:#F5E7CB;color:black">P</th>
    <th class="totals-h">Total</th>
  </tr>
</thead>
<tbody>
  {rows_html}
</tbody>
</table>

<div class="footer">
  <b>EXAMEN FINAL:</b> {esc_html(fecha_examen)} &nbsp;&nbsp;&nbsp;
  <b>SUPLETORIO:</b> {esc_html(fecha_sup)}
  <span style="float:right;margin-right:20mm">DOCENTE</span>
</div>

</body></html>"""

    return HTML(string=html).write_pdf()
