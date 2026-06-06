"""
Generates Informe de Notas (Final and Mensual) as PDF bytes.
Replicates the original LaTeX output using WeasyPrint HTML/CSS.
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from weasyprint import HTML
from utils import LOGO_DATA_URI, FACILITADOR, esc_html, fmt
from cycles import NIVEL_MAP
import pandas as pd


CSS = """
@page { size: letter landscape; margin: 1.0cm 1.0cm 1.0cm 1.0cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 7.5pt; margin: 0; }
.inst-header { text-align: center; font-size: 8pt; font-weight: bold;
               margin-bottom: 4pt; }
.meta-row { display: flex; align-items: flex-end;
            justify-content: space-between; margin-bottom: 4pt; }
.meta-left { font-size: 8.5pt; font-weight: bold; line-height: 1.6; }
.meta-right img { height: 1.9cm; }
.notes-table { width: 100%; border-collapse: collapse; font-size: 7pt; }
.notes-table th, .notes-table td {
  border: 0.6pt solid black;
  text-align: center;
  padding: 1pt 1pt;
  vertical-align: middle;
}
.rot { writing-mode: vertical-rl; transform: rotate(180deg);
       white-space: nowrap; font-size: 6.5pt; font-weight: bold;
       padding: 3pt 1pt; height: 28mm; }
.hdr-num  { background: white; }
.hdr-doc  { background: white; }
.hdr-name { background: white; }
.col-a    { background: #D99594; }
.col-b    { background: #EAF1DA; }
.col-c    { background: #92CDDB; }
.col-d    { background: #92D150; }
.col-prom { background: #F9F1A5; }
.col-peach{ background: #FCE8D5; }
.col-cyan { background: #01B0F1; }
.col-white{ background: #FFFFFF; }
.promedios-row td { font-weight: bold; background: #F0F0F0; font-size: 7pt; }
.name-cell { text-align: left; padding-left: 3pt; font-size: 7.5pt; }
.sig-block { margin-top: 1.5cm; text-align: center; }
.sig-line  { display: inline-block; width: 6cm;
             border-top: 0.5pt solid black; padding-top: 3pt; font-size: 8pt; }
"""


def _rotated(line1, line2=None):
    if line2:
        return f'<div class="rot">{esc_html(line1)}<br>{esc_html(line2)}</div>'
    return f'<div class="rot">{esc_html(line1)}</div>'


def generate_notas(df: pd.DataFrame, cycle_data: dict,
                   course_code: str, level_digit: str,
                   is_mensual: bool = False) -> bytes:
    """
    Generate grade report PDF.
    df: normalized + computed DataFrame from intake.py
    cycle_data: dict from cycles.py
    course_code: e.g. 'E406-F-C14NM'
    level_digit: '1'-'8'
    is_mensual: True for monthly (LO A&B only), False for final
    """
    nivel  = NIVEL_MAP.get(level_digit, "Unknown")
    fecha  = cycle_data['fin']

    # Build header row
    header_row = f"""
    <tr>
      <th class="hdr-num" rowspan="2" style="width:7mm"><div class="rot">N°</div></th>
      <th class="hdr-doc" rowspan="2" style="width:23mm"><div class="rot">NÚMERO DE CÉDULA</div></th>
      <th class="hdr-name" rowspan="2" style="width:65mm">ALUMNOS</th>
      <th class="col-a">{_rotated("RESULTADO DE","APRENDIZAJE A")}</th>
      <th class="col-a">{_rotated("EQ")}</th>
      <th class="col-b">{_rotated("RESULTADO DE","APRENDIZAJE B")}</th>
      <th class="col-b">{_rotated("EQ")}</th>
      <th class="col-c">{_rotated("RESULTADO DE","APRENDIZAJE C")}</th>
      <th class="col-c">{_rotated("EQ")}</th>
      <th class="col-d">{_rotated("RESULTADO DE","APRENDIZAJE D")}</th>
      <th class="col-d">{_rotated("EQ")}</th>
      <th class="col-prom">{_rotated("PROMEDIO","LOGROS A & C")}</th>
      <th class="col-prom">{_rotated("EQ")}</th>
      <th class="col-peach">{_rotated("SUBTOTAL")}</th>
      <th class="col-cyan">{_rotated("EXAMEN")}</th>
      <th class="col-cyan">{_rotated("EQ")}</th>
      <th class="col-peach">{_rotated("SUBTOTAL +","EXAMEN")}</th>
      <th class="col-cyan">{_rotated("SUPLETORIO")}</th>
      <th class="col-cyan">{_rotated("EQ")}</th>
      <th class="col-peach">{_rotated("NOTA","FINAL")}</th>
      <th class="col-white" style="width:20mm">ESTADO</th>
    </tr>"""

    # Build student rows
    student_rows = ""
    for i, row in df.iterrows():
        name    = esc_html(str(row['FullName']))
        id_num  = esc_html(str(row['IDNumber']))
        estado  = esc_html(str(row['ESTADO']))

        if is_mensual:
            lo_c = lo_d = prom_ac = eq_prom_ac = 0.0
            examen = eq_ex = sub_ex = sup = eq_sup = 0.0
        else:
            lo_c     = row['LO_C']
            lo_d     = row['LO_D']
            prom_ac  = row['PROM_AC']
            eq_prom_ac = row['EQ_PROM_AC']
            examen   = row['Examen']
            eq_ex    = row['EQ_EX']
            sub_ex   = row['SUB_EX']
            sup      = row['Supletorio']
            eq_sup   = row['EQ_SUP']

        student_rows += f"""
        <tr>
          <td>{i+1}</td>
          <td style="font-size:7pt">{id_num}</td>
          <td class="name-cell">{name}</td>
          <td class="col-a">{fmt(row['LO_A'])}</td>
          <td class="col-a">{fmt(row['EQ_A'])}</td>
          <td class="col-b">{fmt(row['LO_B'])}</td>
          <td class="col-b">{fmt(row['EQ_B'])}</td>
          <td class="col-c">{fmt(lo_c)}</td>
          <td class="col-c">{fmt(row['EQ_C'])}</td>
          <td class="col-d">{fmt(lo_d)}</td>
          <td class="col-d">{fmt(row['EQ_D'])}</td>
          <td class="col-prom">{fmt(prom_ac)}</td>
          <td class="col-prom">{fmt(eq_prom_ac)}</td>
          <td class="col-peach">{fmt(row['SUBTOTAL'])}</td>
          <td class="col-cyan">{fmt(examen)}</td>
          <td class="col-cyan">{fmt(eq_ex)}</td>
          <td class="col-peach">{fmt(sub_ex)}</td>
          <td class="col-cyan">{fmt(sup)}</td>
          <td class="col-cyan">{fmt(eq_sup)}</td>
          <td class="col-peach"><b>{fmt(row['FINAL'])}</b></td>
          <td style="font-size:7pt">{estado}</td>
        </tr>"""

    # Averages row
    def col_avg(col):
        vals = df[df[col] > 0][col]
        return fmt(vals.mean()) if not vals.empty else fmt(0)

    if is_mensual:
        avg_row = f"""
        <tr class="promedios-row">
          <td></td><td></td>
          <td style="text-align:right;padding-right:4pt">PROMEDIOS</td>
          <td>{col_avg('LO_A')}</td><td>{col_avg('EQ_A')}</td>
          <td>{col_avg('LO_B')}</td><td>{col_avg('EQ_B')}</td>
          <td>0,00</td><td>0,00</td>
          <td>0,00</td><td>0,00</td>
          <td>0,00</td><td>0,00</td>
          <td>{col_avg('SUBTOTAL')}</td>
          <td>0,00</td><td>0,00</td>
          <td>{col_avg('SUB_EX')}</td>
          <td>0,00</td><td>0,00</td>
          <td>{col_avg('FINAL')}</td>
          <td></td>
        </tr>"""
    else:
        avg_row = f"""
        <tr class="promedios-row">
          <td></td><td></td>
          <td style="text-align:right;padding-right:4pt">PROMEDIOS</td>
          <td>{col_avg('LO_A')}</td><td>{col_avg('EQ_A')}</td>
          <td>{col_avg('LO_B')}</td><td>{col_avg('EQ_B')}</td>
          <td>{col_avg('LO_C')}</td><td>{col_avg('EQ_C')}</td>
          <td>{col_avg('LO_D')}</td><td>{col_avg('EQ_D')}</td>
          <td>{col_avg('PROM_AC')}</td><td>{col_avg('EQ_PROM_AC')}</td>
          <td>{col_avg('SUBTOTAL')}</td>
          <td>{col_avg('Examen')}</td><td>{col_avg('EQ_EX')}</td>
          <td>{col_avg('SUB_EX')}</td>
          <td>{col_avg('Supletorio')}</td><td>{col_avg('EQ_SUP')}</td>
          <td>{col_avg('FINAL')}</td>
          <td></td>
        </tr>"""

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>{CSS}</style></head><body>

<div class="inst-header">
  ESCUELA SUPERIOR POLITÉCNICA AGROPECUARIA DE MANABÍ "MANUEL FÉLIX LÓPEZ"<br>
  UNIDAD DE CENTRO DE IDIOMAS
</div>

<div class="meta-row">
  <div class="meta-left">
    NIVEL: {esc_html(nivel)}<br>
    CICLO: {esc_html(course_code)}<br>
    FACILITADOR (A): {FACILITADOR}<br>
    FECHA: {esc_html(fecha)}
  </div>
  <div class="meta-right">
    <img src="{LOGO_DATA_URI}" alt="ESPAM Logo">
  </div>
</div>

<table class="notes-table">
<thead>
  {header_row}
</thead>
<tbody>
  {student_rows}
  {avg_row}
</tbody>
</table>

<div class="sig-block">
  <span class="sig-line">DOCENTE</span>
</div>

</body></html>"""

    return HTML(string=html).write_pdf()
