import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import base64
import random
from datetime import datetime, timedelta
from weasyprint import HTML
from utils import (FACILITADOR_SHORT, COORDINADOR, esc_html,
                   TOPIC_DATABASE, MODULO_WORDS, write_logo)

# We need LOGO_DATA_URI for WeasyPrint HTML
from utils import _get_logo_data_uri
LOGO_DATA_URI = _get_logo_data_uri()


def _b64_image(file_bytes: bytes, mime: str = "image/png") -> str:
    data = base64.b64encode(file_bytes).decode()
    return f"data:{mime};base64,{data}"


def _detect_mime(filename: str) -> str:
    fn = filename.lower()
    if fn.endswith('.jpg') or fn.endswith('.jpeg'):
        return "image/jpeg"
    return "image/png"


CSS = """
@page { size: A4 landscape; margin: 0.5cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 8.5pt;
       color: #333; margin: 0; }
table { width: 100%; border-collapse: collapse; }
th, td { border: 1pt solid #000; padding: 3pt 4pt; text-align: left;
         font-size: 8.5pt; }
tr { page-break-inside: avoid; }
.header-table td:first-child { border-right: none; padding: 6pt; }
.header-table td:last-child  { border-left: none; width: 28%;
                                text-align: center; }
.info-box { border: 1pt solid #000; border-top: none; padding: 5pt 6pt;
            font-size: 8.5pt; line-height: 1.5; margin-bottom: 0; }
.data-table th { background: #F2F2F2; text-align: center; font-weight: bold;
                 padding: 6pt; }
.obs-box { border: 1pt solid #000; padding: 6pt; margin-top: 4pt;
           min-height: 18pt; font-size: 8.5pt; }
.sig-table { border: none; margin-top: 20pt; }
.sig-table td { border: none; text-align: center; width: 50%; padding-top: 30pt; }
.sig-line { display: inline-block; width: 220pt;
            border-top: 1pt solid black; padding-top: 3pt; font-size: 8pt; }
.page-break { page-break-before: always; }
.evidence-header { text-align: center; font-size: 12pt; font-weight: bold;
                   margin-bottom: 10pt; border-bottom: 2pt solid #000;
                   padding-bottom: 4pt; }
.semana-label { font-weight: bold; font-size: 9pt; margin-top: 12pt;
                margin-bottom: 4pt; }
.semana-img { max-width: 70%; max-height: 150pt; display: block;
              margin: 0 auto 12pt auto; border: 0.5pt solid #ccc; }
"""


def _build_sessions(all_dfs_meta, inicio, fin, dias_semana, jornada):
    start_dt = datetime.strptime(inicio, "%d/%m/%Y")
    end_dt   = datetime.strptime(fin,    "%d/%m/%Y")

    day_map = {"Lunes":0,"Martes":1,"Miércoles":2,"Jueves":3,
               "Viernes":4,"Sábado":5,"Domingo":6}
    target_days = [day_map.get(d.strip()) for d in dias_semana.split(',')
                   if d.strip() in day_map]
    if not target_days:
        target_days = [0, 2, 4]

    time_in  = "08:00" if jornada == "MAÑANA" else "14:00"
    time_out = "09:00" if jornada == "MAÑANA" else "15:00"

    pools = []
    for df, code, level_digit in all_dfs_meta:
        digit  = str(level_digit)
        modulo = MODULO_WORDS.get(digit, "PRIMERO")
        topics = TOPIC_DATABASE.get(digit, ["English Practice"])
        eligible = df[df['LO_A'] > 0]['FullName'].tolist()
        pools.append({"code": code, "modulo": modulo,
                      "names": eligible, "topics": topics})

    sessions = []
    curr, pool_idx = start_dt, 0
    while curr <= end_dt:
        if curr.weekday() in target_days:
            p = pools[pool_idx % len(pools)]
            student = p['names'].pop(0) if p['names'] else "ESTUDIANTE TUTORADO"
            sessions.append({
                "fecha":      curr.strftime("%d/%m/%Y"),
                "estudiante": student,
                "modulo":     p["modulo"],
                "codigo":     p["code"],
                "tema":       random.choice(p["topics"]),
                "entrada":    time_in,
                "salida":     time_out,
            })
            pool_idx += 1
        curr += timedelta(days=1)
    return sessions


def generate_tutorias(
    all_dfs_meta: list,
    cycle_start: str,
    cycle_end: str,
    modalidad: str,
    jornada: str,
    dias_semana: str,
    horas_semanales: int,
    observaciones: str,
    semana_images: list,
) -> bytes:

    sessions = _build_sessions(
        all_dfs_meta, cycle_start, cycle_end, dias_semana, jornada)

    unique_ciclos = ", ".join(sorted(set(m[1] for m in all_dfs_meta)))

    session_rows = ""
    if sessions:
        for s in sessions:
            session_rows += f"""
            <tr>
              <td style="text-align:center">{esc_html(s['fecha'])}</td>
              <td>{esc_html(s['estudiante'])}</td>
              <td style="text-align:center">{esc_html(s['modulo'])}</td>
              <td style="text-align:center;font-size:7.5pt">{esc_html(s['codigo'])}</td>
              <td style="font-size:7.5pt">{esc_html(s['tema'])}</td>
              <td style="text-align:center">{s['entrada']}</td>
              <td style="text-align:center">{s['salida']}</td>
            </tr>"""
    else:
        session_rows = '<tr><td colspan="7" style="text-align:center">No sessions generated.</td></tr>'

    evidence_html = ""
    labels = ["SEMANA 1", "SEMANA 2", "SEMANA 3", "SEMANA 4"]
    for i, (fname, fdata) in enumerate(semana_images[:4]):
        mime    = _detect_mime(fname)
        img_uri = _b64_image(fdata, mime)
        label   = labels[i]
        evidence_html += f"""
        <div class="semana-label">{label}:</div>
        <img src="{img_uri}" class="semana-img" alt="{label}">"""

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>{CSS}</style></head><body>

<table class="header-table">
<tr>
  <td>
    <div style="font-size:10.5pt;font-weight:bold;margin-bottom:4pt">CONTROL DE TUTOR&Iacute;AS ACAD&Eacute;MICAS</div>
    <div style="font-weight:bold;margin-bottom:3pt">UNIDAD ACAD&Eacute;MICA: JEFATURA DEL CENTRO DE IDIOMAS</div>
    <div style="font-weight:bold">PERIODO ACAD&Eacute;MICO: {esc_html(cycle_start)} - {esc_html(cycle_end)}</div>
  </td>
  <td>
    <img src="{LOGO_DATA_URI}" style="height:50pt" alt="ESPAM Logo">
  </td>
</tr>
</table>

<div class="info-box">
  <b>TUTOR:</b> {FACILITADOR_SHORT} &nbsp;|&nbsp;
  <b>MESES:</b> {esc_html(cycle_start)} - {esc_html(cycle_end)} &nbsp;|&nbsp;
  <b>CICLOS:</b> {esc_html(unique_ciclos)} &nbsp;|&nbsp;<br>
  <b>MODALIDAD:</b> {esc_html(modalidad)} &nbsp;|&nbsp;
  <b>HORAS SEMANALES:</b> {horas_semanales}
</div>

<table class="data-table">
<thead>
  <tr>
    <th rowspan="2" style="width:8%">FECHA</th>
    <th rowspan="2" style="width:22%">APELLIDOS Y NOMBRES</th>
    <th rowspan="2" style="width:8%">M&Oacute;DULO</th>
    <th rowspan="2" style="width:12%">C&Oacute;DIGO</th>
    <th rowspan="2" style="width:38%">TEMA</th>
    <th colspan="2" style="width:12%">HORA</th>
  </tr>
  <tr><th>ENTRADA</th><th>SALIDA</th></tr>
</thead>
<tbody>{session_rows}</tbody>
</table>

<div style="margin-top:6pt;font-size:8.5pt">
  <b>TOTAL DE ESTUDIANTES TUTORADOS:</b> {len(sessions)}<br style="line-height:3pt">
  <b>TOTAL DE HORAS EMPLEADAS:</b> {len(sessions)}
</div>

<div class="obs-box">
  <b>OBSERVACIONES:</b> {esc_html(observaciones)}
</div>

<table class="sig-table">
<tr>
  <td><span class="sig-line">{FACILITADOR_SHORT}<br><span style="display:block;margin-top:3pt"></span><b>DOCENTE TUTOR</b></span></td>
  <td><span class="sig-line">{esc_html(COORDINADOR)}<br><span style="display:block;margin-top:3pt"></span><b>COORDINADOR ACAD&Eacute;MICO</b></span></td>
</tr>
</table>

<div style="margin-top:8pt;font-size:8pt">
  <b>MECANISMOS DE EVIDENCIAS:</b> Videos, Capturas de pantalla, Fotos,
  listas de estudiantes con firmas u otros (especificar).
</div>

<div class="page-break"></div>
<div class="evidence-header">MECANISMOS DE EVIDENCIAS</div>
{evidence_html}

</body></html>"""

    return HTML(string=html).write_pdf()
