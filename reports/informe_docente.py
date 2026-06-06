"""
Generates Informe Docente as PDF bytes.
Based exclusively on Logro A & B.
Page 1: Main report with difficulty tables.
Page 2: Annexes — Asistencia Mensual table + Notas Mensual table + Moodle text.
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from weasyprint import HTML
import pandas as pd
from utils import LOGO_DATA_URI, FACILITADOR, FACILITADOR_SHORT, esc_html, fmt
from cycles import NIVEL_MAP_ES


CSS = """
@page {
  size: letter portrait;
  margin: 1.5cm 1.5cm 1.5cm 1.5cm;
}
body { font-family: Helvetica, Arial, sans-serif; font-size: 9.5pt;
       margin: 0; color: #000; }
.header { text-align: center; margin-bottom: 8pt; }
.header-logo { height: 1.3cm; margin-bottom: 4pt; }
.header-inst { font-size: 8pt; font-weight: bold; }
.report-title { font-size: 10pt; font-weight: bold; text-align: right;
                font-style: italic; border-bottom: 1pt solid #000;
                padding-bottom: 2pt; margin-bottom: 8pt; }
.period-title { font-size: 10pt; font-weight: bold; text-align: center;
                margin-bottom: 10pt; }
.meta { font-size: 9pt; margin-bottom: 10pt; line-height: 1.8; }
.section-title { font-size: 9.5pt; font-weight: bold; margin-bottom: 5pt;
                 margin-top: 8pt; }
.diff-table { width: 100%; border-collapse: collapse;
              font-size: 8.5pt; margin-bottom: 8pt; }
.diff-table th { border: 0.8pt solid black; padding: 4pt 6pt;
                 text-align: center; font-weight: bold; background: #F0F0F0; }
.diff-table td { border: 0.8pt solid black; padding: 4pt 6pt;
                 text-align: center; }
.sig-section { margin-top: 2.5cm; }
.sig-line { display: inline-block; width: 8cm;
            border-top: 0.8pt solid black; padding-top: 3pt;
            font-size: 8.5pt; font-weight: bold; }
/* Page break */
.page-break { page-break-before: always; }
/* Annexes */
.annex-title { font-size: 11pt; font-weight: bold; margin-bottom: 6pt;
               margin-top: 8pt; }
.annex-sub   { font-size: 9pt; font-style: italic; margin-bottom: 6pt; }
/* Attendance annex table */
.att-annex { width: 100%; border-collapse: collapse; font-size: 7.5pt; }
.att-annex th { background: #00A99D; color: white; border: 0.5pt solid black;
                padding: 2pt 3pt; text-align: center; font-size: 7pt; }
.att-annex td { border: 0.5pt solid black; padding: 2pt 3pt;
                text-align: center; font-size: 7pt; }
.att-P { background: #F5E7CB; }
.att-I { background: #FC935A; }
/* Notes annex table */
.notes-annex { width: 100%; border-collapse: collapse; font-size: 7pt; }
.notes-annex th { background: #00A99D; color: white; border: 0.5pt solid black;
                  padding: 2pt 3pt; text-align: center; }
.notes-annex td { border: 0.5pt solid black; padding: 2pt 3pt;
                  text-align: center; }
.col-a { background: #D99594; }
.col-b { background: #EAF1DA; }
.moodle-section { margin-top: 10pt; font-size: 9pt; }
"""


def _build_att_annex(df: pd.DataFrame, cycle_data: dict) -> str:
    """Build the asistencia annex table (from Mensual data)."""
    from reports.asistencia import (
        _get_class_dates, _attendance_codes_mensual,
        _add_random_absences, _cell_color, NUM_MENSUAL, NUM_DATES
    )

    class_dates = _get_class_dates(cycle_data['inicio'], cycle_data['fin'])
    df = df.copy()
    df['Codes'] = df.apply(_attendance_codes_mensual, axis=1)
    df = _add_random_absences(df, 'Codes')

    date_headers = "".join(
        f'<th>{str(d.day).zfill(2)}/{d.month:02d}</th>'
        for d in class_dates[:NUM_MENSUAL]
    )

    rows = ""
    for i, row in df.iterrows():
        bg = "#F0F8FF" if i % 2 == 0 else "#FFFFFF"
        name   = esc_html(str(row['FullName']))
        id_num = esc_html(str(row['IDNumber']))
        codes  = row['Codes']

        att_cells = ""
        for code in codes:
            cell_bg = _cell_color(code)
            att_cells += f'<td style="background:{cell_bg}">{code}</td>'

        rows += f"""
        <tr style="background:{bg}">
          <td>{i+1}</td><td style="font-size:6.5pt">{id_num}</td>
          <td style="text-align:left;padding-left:3pt;font-size:7pt">{name}</td>
          {att_cells}
          <td>{codes.count("I")}</td>
          <td>{codes.count("P")}</td>
        </tr>"""

    return f"""
    <table class="att-annex">
      <thead>
        <tr>
          <th>N°</th><th>CÉDULA</th><th>APELLIDOS Y NOMBRES</th>
          {date_headers}
          <th>I</th><th>P</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>"""


def _build_notes_annex(df: pd.DataFrame) -> str:
    """Build the notas annex table (LO A & B only)."""
    rows = ""
    for i, row in df.iterrows():
        bg = "#F0F8FF" if i % 2 == 0 else "#FFFFFF"
        name   = esc_html(str(row['FullName']))
        id_num = esc_html(str(row['IDNumber']))
        avg_ab = round((row['LO_A'] + row['LO_B']) / 2, 2)

        rows += f"""
        <tr style="background:{bg}">
          <td>{i+1}</td>
          <td style="font-size:6.5pt">{id_num}</td>
          <td style="text-align:left;padding-left:3pt;font-size:7pt">{name}</td>
          <td class="col-a">{fmt(row['LO_A'])}</td>
          <td class="col-a">{fmt(row['EQ_A'])}</td>
          <td class="col-b">{fmt(row['LO_B'])}</td>
          <td class="col-b">{fmt(row['EQ_B'])}</td>
          <td><b>{fmt(avg_ab)}</b></td>
        </tr>"""

    return f"""
    <table class="notes-annex">
      <thead>
        <tr>
          <th>N°</th><th>CÉDULA</th><th>ESTUDIANTE</th>
          <th class="col-a">LO A</th><th class="col-a">EQ</th>
          <th class="col-b">LO B</th><th class="col-b">EQ</th>
          <th>PROM. A&amp;B</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>"""


def generate_informe_docente(
    df: pd.DataFrame,
    cycle_data: dict,
    course_code: str,
    level_digit: str,
    classroom: str,
    academic_strategies: dict,   # {student_name: strategy_text}
    attendance_strategies: dict, # {student_name: strategy_text}
    moodle_all_enrolled: bool,
    moodle_missing_names: str = "",
) -> bytes:
    """
    Generate Informe Docente PDF.
    df: normalized + mensual-computed DataFrame
    academic_strategies / attendance_strategies: {name: strategy}
    """
    nivel  = NIVEL_MAP_ES.get(level_digit, "Nivel")
    inicio = cycle_data['inicio']
    fin    = cycle_data['fin']

    # ── Academic difficulty table ────────────────────────────────────────
    acad_rows = ""
    acad_students = [r for r in df.itertuples()
                     if (r.LO_A < 7.0 or r.LO_B < 7.0)
                     and not (r.LO_A == 0.0 and r.LO_B == 0.0)]
    if not acad_students:
        acad_rows = "<tr><td>N/A</td><td>N/A</td><td>N/A</td></tr>"
    else:
        for r in acad_students:
            strat = esc_html(academic_strategies.get(r.FullName, "En progreso"))
            acad_rows += f"""
            <tr>
              <td style="text-align:left;padding-left:4pt">{esc_html(r.FullName)}</td>
              <td>En progreso</td>
              <td style="text-align:left;padding-left:4pt">{strat}</td>
            </tr>"""

    # ── Attendance difficulty table ──────────────────────────────────────
    att_students = [r for r in df.itertuples()
                    if r.LO_A == 0.0 or r.LO_B == 0.0]
    att_rows = ""
    if not att_students:
        att_rows = "<tr><td>N/A</td><td>N/A</td><td>N/A</td></tr>"
    else:
        for r in att_students:
            strat = esc_html(attendance_strategies.get(r.FullName, "En progreso"))
            att_rows += f"""
            <tr>
              <td style="text-align:left;padding-left:4pt">{esc_html(r.FullName)}</td>
              <td>En progreso</td>
              <td style="text-align:left;padding-left:4pt">{strat}</td>
            </tr>"""

    # ── Moodle text ──────────────────────────────────────────────────────
    if moodle_all_enrolled:
        moodle_text = ("Todos los estudiantes fueron matriculados en Moodle "
                       "y las dificultades pudieron solucionarse a tiempo.")
    else:
        moodle_text = (f"Los estudiantes {esc_html(moodle_missing_names)} "
                       "tuvieron inconveniente para matricularse en Moodle.")

    # ── Annexes ──────────────────────────────────────────────────────────
    att_annex_html   = _build_att_annex(df, cycle_data)
    notes_annex_html = _build_notes_annex(df)

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>{CSS}</style></head><body>

<!-- PAGE 1 -->
<div style="display:flex;justify-content:space-between;align-items:center;
            border-bottom:1pt solid black;padding-bottom:4pt;margin-bottom:6pt">
  <img src="{LOGO_DATA_URI}" class="header-logo" alt="ESPAM Logo">
  <div class="report-title" style="border:none">Informe Docente</div>
</div>

<div class="period-title">
  Informe correspondiente al periodo del {esc_html(inicio)} al {esc_html(fin)}
</div>

<div class="meta">
  Nivel/Ciclo: {esc_html(course_code)}<br>
  Paralelo: {esc_html(classroom)}<br>
  Docente: {FACILITADOR_SHORT}
</div>

<div class="section-title">
  1. Resumen de estudiantes con dificultades en el desempeño académico
</div>
<table class="diff-table">
  <thead>
    <tr>
      <th style="width:40%">Nombres y apellidos del estudiante</th>
      <th style="width:25%">Desempeño académico del estudiante en el nivel/ciclo</th>
      <th style="width:35%">Estrategias (realizadas a la fecha y en progreso)</th>
    </tr>
  </thead>
  <tbody>{acad_rows}</tbody>
</table>

<div class="section-title">
  2. Resumen de estudiantes con dificultades en asistencia (por paralelo),
  así también estudiantes que se retiran en el transcurso del desarrollo del curso.
</div>
<table class="diff-table">
  <thead>
    <tr>
      <th style="width:40%">Nombres y apellidos del estudiante</th>
      <th style="width:25%">Situación del estudiante respecto a la asistencia</th>
      <th style="width:35%">Estrategias (realizadas a la fecha y en progreso)</th>
    </tr>
  </thead>
  <tbody>{att_rows}</tbody>
</table>

<div class="sig-section">
  <span class="sig-line">
    {FACILITADOR}<br>
    <span style="font-weight:normal">Docente de la Unidad de Centro de Idiomas</span>
  </span>
</div>

<!-- PAGE 2 — ANNEXES -->
<div class="page-break"></div>

<div style="display:flex;justify-content:space-between;align-items:center;
            border-bottom:1pt solid black;padding-bottom:4pt;margin-bottom:6pt">
  <img src="{LOGO_DATA_URI}" class="header-logo" alt="ESPAM Logo">
  <div class="report-title" style="border:none">Informe Docente</div>
</div>

<div style="font-weight:bold;font-size:10pt;margin-bottom:8pt">Anexos:</div>

<div class="annex-title">ASISTENCIA:</div>
<div class="annex-sub">
  (Asistencia correspondiente al periodo mensual hasta la fecha indicada en este reporte).
</div>
{att_annex_html}

<div class="annex-title" style="margin-top:12pt">NOTAS:</div>
<div class="annex-sub">(Logros de Aprendizaje A y B)</div>
{notes_annex_html}

<div class="annex-title" style="margin-top:12pt">MOODLE:</div>
<div class="moodle-section">{esc_html(moodle_text)}</div>

</body></html>"""

    return HTML(string=html).write_pdf()
