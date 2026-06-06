"""
ESPAM MFL Report Generator
Author: Jorge Bienvenido Cevallos Bravo
"""

import io
import zipfile
import streamlit as st
import pandas as pd

from cycles import extract_cycle_from_filename, extract_level_from_filename, \
                   extract_classroom_from_filename, get_cycle
from intake import load_grades, compute_grades, compute_grades_mensual, \
                   get_flagged_students

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ESPAM MFL — Report Generator",
    page_icon="📋",
    layout="centered",
)

# ── Password gate ──────────────────────────────────────────────────────────
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown("## 📋 ESPAM MFL — Report Generator")
    st.markdown("---")
    pwd = st.text_input("Password", type="password", placeholder="Enter password")
    if st.button("Login", type="primary"):
        if pwd.lower() == "portafolio":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()

# ── App header ─────────────────────────────────────────────────────────────
st.markdown("## 📋 ESPAM MFL — Report Generator")
st.markdown("*Jorge Cevallos Bravo · Ciclo 2026*")
st.markdown("---")

# ── STEP 1: Upload grade files ─────────────────────────────────────────────
st.subheader("Step 1 — Upload grade files")
st.caption("Raw Moodle ODS/CSV or clean CSV accepted · Up to 4 files")

uploaded_files = st.file_uploader(
    "Moodle grade files",
    type=["ods", "csv", "xlsx"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if not uploaded_files:
    st.info("Upload your grade file(s) to continue.")
    st.stop()

if len(uploaded_files) > 4:
    st.error("Maximum 4 files allowed.")
    st.stop()

# ── Parse uploaded files ────────────────────────────────────────────────────
courses = []
parse_errors = []

for uf in uploaded_files:
    try:
        df_raw = load_grades(uf, uf.name)
        cycle_code = extract_cycle_from_filename(uf.name)
        cycle_data = get_cycle(cycle_code) if cycle_code else None
        level_digit = extract_level_from_filename(uf.name)
        classroom   = extract_classroom_from_filename(uf.name)

        courses.append({
            "filename":    uf.name,
            "cycle_code":  cycle_code,
            "cycle_data":  cycle_data,
            "level_digit": level_digit,
            "classroom":   classroom,
            "df_raw":      df_raw,
        })
    except Exception as e:
        parse_errors.append(f"{uf.name}: {e}")

for err in parse_errors:
    st.error(f"Could not read file — {err}")

if not courses:
    st.stop()

# ── Show detected metadata ──────────────────────────────────────────────────
for c in courses:
    if not c["cycle_code"]:
        st.warning(f"⚠️ Could not detect cycle code from **{c['filename']}**. "
                   "Dates will not be auto-filled.")
    elif not c["cycle_data"]:
        st.warning(f"⚠️ Cycle **{c['cycle_code']}** not found in the 2026 calendar. "
                   "Dates will not be auto-filled.")

st.success(f"✅ {len(courses)} file(s) loaded successfully.")
st.markdown("---")

# ── STEP 2: Per-course details ──────────────────────────────────────────────
st.subheader("Step 2 — Details per course")

course_inputs = {}

for c in courses:
    code  = c["cycle_code"] or "Unknown"
    cdata = c["cycle_data"] or {}
    fname = c["filename"]

    with st.expander(f"**{code}** — {fname}", expanded=True):

        # ── All 6 reports: dates + horario ───────────────────────────────
        st.markdown("**All 6 reports**")
        col1, col2, col3 = st.columns(3)
        col1.metric("Inicio",      cdata.get("inicio",      "—"))
        col2.metric("Fin / Examen", cdata.get("fin",        "—"))
        col3.metric("Supletorio",  cdata.get("supletorio",  "—"))

        horario = st.text_input(
            "Horario",
            placeholder="e.g. 07h00 - 09h00",
            key=f"horario_{code}",
        )

        st.divider()

        # ── Informe Docente ───────────────────────────────────────────────
        st.markdown("**Informe Docente** *(Logro A & B only)*")

        df_raw = c["df_raw"]
        df_mensual = compute_grades_mensual(df_raw)
        acad_flagged, att_flagged = get_flagged_students(df_raw)

        # Academic strategies
        acad_strategies = {}
        if acad_flagged:
            st.markdown("*Dificultades académicas — add strategy per student:*")
            for name, _ in acad_flagged:
                strat = st.text_input(
                    f"↳ {name}",
                    placeholder="Strategy...",
                    key=f"acad_{code}_{name}",
                )
                acad_strategies[name] = strat
        else:
            st.caption("Dificultades académicas: No flagged students")

        # Attendance strategies
        att_strategies = {}
        if att_flagged:
            st.markdown("*Dificultades de asistencia — add strategy per student:*")
            for name, _ in att_flagged:
                strat = st.text_input(
                    f"↳ {name}",
                    placeholder="Strategy...",
                    key=f"att_{code}_{name}",
                )
                att_strategies[name] = strat
        else:
            st.caption("Dificultades de asistencia: No flagged students")

        # Moodle enrollment
        moodle_ok = st.selectbox(
            "Anexo: Moodle",
            options=["Todos los estudiantes fueron matriculados sin problema",
                     "Algunos estudiantes tuvieron inconvenientes"],
            key=f"moodle_{code}",
        )
        moodle_all   = (moodle_ok.startswith("Todos"))
        moodle_names = ""
        if not moodle_all:
            moodle_names = st.text_input(
                "Names of students with enrollment issues",
                key=f"moodle_names_{code}",
            )

        course_inputs[code] = {
            "horario":          horario,
            "df_mensual":       df_mensual,
            "acad_strategies":  acad_strategies,
            "att_strategies":   att_strategies,
            "moodle_all":       moodle_all,
            "moodle_names":     moodle_names,
        }

st.markdown("---")

# ── STEP 3: Reporte de Tutorías ─────────────────────────────────────────────
st.subheader("Step 3 — Reporte de Tutorías *(all courses)*")

col1, col2 = st.columns(2)
modalidad = col1.selectbox("Modalidad", ["VIRTUAL", "PRESENCIAL"], key="modalidad")
jornada   = col2.selectbox("Jornada",   ["MAÑANA", "TARDE"],       key="jornada")

col3, col4 = st.columns(2)
dias_semana    = col3.text_input("Días de la semana",
                                  value="Lunes, Miércoles, Viernes",
                                  key="dias")
horas_semana   = col4.number_input("Horas semanales", min_value=1,
                                    max_value=10, value=3, key="horas")

observaciones  = st.text_area("Observaciones",
    value="Las sesiones de tutoría se desarrollaron con normalidad, "
          "cumpliendo con los objetivos académicos planteados.",
    height=68, key="obs")

st.markdown("**Mecanismos de evidencias** — Semana 1–4")
col_s1, col_s2, col_s3, col_s4 = st.columns(4)
sem1 = col_s1.file_uploader("Semana 1", type=["png","jpg","jpeg"],
                              key="sem1", label_visibility="visible")
sem2 = col_s2.file_uploader("Semana 2", type=["png","jpg","jpeg"],
                              key="sem2", label_visibility="visible")
sem3 = col_s3.file_uploader("Semana 3", type=["png","jpg","jpeg"],
                              key="sem3", label_visibility="visible")
sem4 = col_s4.file_uploader("Semana 4", type=["png","jpg","jpeg"],
                              key="sem4", label_visibility="visible")

semana_images = []
for s in [sem1, sem2, sem3, sem4]:
    if s:
        semana_images.append((s.name, s.read()))

st.markdown("---")

# ── Readiness check ─────────────────────────────────────────────────────────
missing = []
for c in courses:
    code = c["cycle_code"] or "Unknown"
    if not course_inputs.get(code, {}).get("horario", "").strip():
        missing.append(f"Horario for {code}")

if not semana_images:
    missing.append("At least one Semana photo for Reporte de Tutorías")

if missing:
    st.warning("⚠️ Required before generating:\n" +
               "\n".join(f"- {m}" for m in missing))

# ── GENERATE button ──────────────────────────────────────────────────────────
btn_disabled = bool(missing)
generate = st.button(
    "🗜️  Generate all reports",
    type="primary",
    disabled=btn_disabled,
    use_container_width=True,
)

if btn_disabled:
    st.caption("Complete all required fields above to enable generation.")

if not generate:
    st.stop()

# ── Generation ───────────────────────────────────────────────────────────────
from reports.asistencia      import generate_asistencia
from reports.notas           import generate_notas
from reports.informe_docente import generate_informe_docente
from reports.informe_final   import generate_informe_final
from reports.tutorias        import generate_tutorias

progress = st.progress(0, text="Starting...")
outputs  = {}   # {cycle_code: {report_name: bytes}}

total_steps = len(courses) * 6 + 1
step = 0

# ── Per-course reports ────────────────────────────────────────────────────────
for c in courses:
    code  = c["cycle_code"]
    cdata = c["cycle_data"]
    fname = c["filename"]
    level = c["level_digit"] or "1"
    cls   = c["classroom"]
    inp   = course_inputs[code]
    df_raw     = c["df_raw"]
    df_final   = compute_grades(df_raw)
    df_mensual = inp["df_mensual"]
    horario    = inp["horario"]

    outputs[code] = {}

    # 1. Asistencia Final
    step += 1
    progress.progress(step / total_steps,
                      text=f"{code}: Asistencia Final...")
    try:
        outputs[code]["Asistencia_Final.pdf"] = generate_asistencia(
            df_raw, cdata, horario, code, is_mensual=False)
    except Exception as e:
        st.error(f"{code} Asistencia Final failed: {e}")

    # 2. Asistencia Mensual
    step += 1
    progress.progress(step / total_steps,
                      text=f"{code}: Asistencia Mensual...")
    try:
        outputs[code]["Asistencia_Mensual.pdf"] = generate_asistencia(
            df_raw, cdata, horario, code, is_mensual=True)
    except Exception as e:
        st.error(f"{code} Asistencia Mensual failed: {e}")

    # 3. Notas Final
    step += 1
    progress.progress(step / total_steps, text=f"{code}: Notas Final...")
    try:
        outputs[code]["Notas_Final.pdf"] = generate_notas(
            df_final, cdata, code, level, is_mensual=False)
    except Exception as e:
        st.error(f"{code} Notas Final failed: {e}")

    # 4. Notas Mensual
    step += 1
    progress.progress(step / total_steps, text=f"{code}: Notas Mensual...")
    try:
        outputs[code]["Notas_Mensual.pdf"] = generate_notas(
            df_mensual, cdata, code, level, is_mensual=True)
    except Exception as e:
        st.error(f"{code} Notas Mensual failed: {e}")

    # 5. Informe Docente
    step += 1
    progress.progress(step / total_steps,
                      text=f"{code}: Informe Docente...")
    try:
        outputs[code]["Informe_Docente.pdf"] = generate_informe_docente(
            df_mensual, cdata, code, level, cls,
            inp["acad_strategies"], inp["att_strategies"],
            inp["moodle_all"], inp["moodle_names"],
        )
    except Exception as e:
        st.error(f"{code} Informe Docente failed: {e}")

    # 6. Informe Final del Curso
    step += 1
    progress.progress(step / total_steps,
                      text=f"{code}: Informe Final del Curso...")
    try:
        outputs[code]["Informe_Final_del_Curso.pdf"] = generate_informe_final(
            df_final, cdata, code, level, cls)
    except Exception as e:
        st.error(f"{code} Informe Final failed: {e}")

# ── Reporte de Tutorías ───────────────────────────────────────────────────────
step += 1
progress.progress(step / total_steps, text="Reporte de Tutorías...")

# Determine date range across all courses
all_starts = [c["cycle_data"]["inicio"] for c in courses if c["cycle_data"]]
all_ends   = [c["cycle_data"]["fin"]    for c in courses if c["cycle_data"]]

from datetime import datetime as dt
def _parse(s): return dt.strptime(s, "%d/%m/%Y")

cycle_start = min(all_starts, key=_parse) if all_starts else "01/01/2026"
cycle_end   = max(all_ends,   key=_parse) if all_ends   else "31/12/2026"

all_dfs_meta = [
    (compute_grades_mensual(c["df_raw"]), c["cycle_code"], c["level_digit"] or "1")
    for c in courses if c["cycle_code"]
]

try:
    tutorias_pdf = generate_tutorias(
        all_dfs_meta, cycle_start, cycle_end,
        modalidad, jornada, dias_semana,
        int(horas_semana), observaciones, semana_images,
    )
except Exception as e:
    tutorias_pdf = None
    st.error(f"Reporte de Tutorías failed: {e}")

progress.progress(1.0, text="Done!")

# ── Build ZIPs ────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📥 Download reports")

for code, reports in outputs.items():
    if not reports:
        continue
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for rname, rbytes in reports.items():
            zf.writestr(rname, rbytes)
    zip_buf.seek(0)
    st.download_button(
        label=f"⬇️  ZIP_{code}.zip  ({len(reports)} reports)",
        data=zip_buf.getvalue(),
        file_name=f"ZIP_{code}.zip",
        mime="application/zip",
        use_container_width=True,
    )

if tutorias_pdf:
    st.download_button(
        label="⬇️  Reporte_de_Tutorias.pdf",
        data=tutorias_pdf,
        file_name="Reporte_de_Tutorias.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

st.success("🎉 All reports generated successfully!")
st.caption("Built for ESPAM MFL Centro de Idiomas · Jorge Cevallos Bravo")
