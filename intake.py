"""
Smart file ingestion module.
Accepts raw Moodle ODS/CSV exports or clean semicolon-delimited CSVs.
Normalizes everything into a standard DataFrame with columns:
  FullName, LastName, FirstName, IDNumber,
  LO_A, LO_B, LO_C, LO_D, Examen, Supletorio
"""

import re
import io
import pandas as pd


# ── Column detection patterns ──────────────────────────────────────────────

def _clean_col(name: str) -> str:
    """Strip emoji, extra spaces, normalize for matching."""
    cleaned = re.sub(r'[^\x00-\x7F]', '', str(name)).strip().lower()
    return cleaned


def _find_col(columns, *patterns):
    """Find first column matching any of the given patterns (case-insensitive)."""
    for col in columns:
        c = _clean_col(col)
        for p in patterns:
            if p.lower() in c:
                return col
    return None


def _to_float(val) -> float:
    if pd.isna(val):
        return 0.0
    s = str(val).strip()
    if s in ('-', '', 'N/A', 'n/a'):
        return 0.0
    s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0


# ── Main ingestion function ────────────────────────────────────────────────

def load_grades(file_obj, filename: str) -> pd.DataFrame:
    """
    Load and normalize a grades file.
    Returns a clean DataFrame regardless of input format.
    """
    fname = filename.lower()

    # ── Read raw file ───────────────────────────────────────────────────
    if fname.endswith('.ods'):
        raw = pd.read_excel(file_obj, engine='odf', header=0, dtype=str)
    elif fname.endswith('.xlsx') or fname.endswith('.xls'):
        raw = pd.read_excel(file_obj, header=0, dtype=str)
    else:
        # CSV: try semicolon first (clean format), then comma (Moodle export)
        content = file_obj.read()
        if isinstance(content, bytes):
            content = content.decode('latin-1')
        if ';' in content.split('\n')[0]:
            raw = pd.read_csv(io.StringIO(content), sep=';', dtype=str)
        else:
            raw = pd.read_csv(io.StringIO(content), sep=',', dtype=str)

    # Drop fully empty rows
    raw.dropna(how='all', inplace=True)
    raw.reset_index(drop=True, inplace=True)

    cols = list(raw.columns)

    # ── Detect name columns ──────────────────────────────────────────────
    col_first = _find_col(cols, 'first name', 'firstname', 'nombre')
    col_last  = _find_col(cols, 'last name',  'lastname',  'apellido')
    col_full  = _find_col(cols, 'full name',  'fullname')
    col_id    = _find_col(cols, 'id number',  'idnumber',  'cedula',
                          'id_number', 'documento', 'número de cédula')

    # ── Detect grade columns ─────────────────────────────────────────────
    col_a = _find_col(cols, 'learning outcome a', 'resultado de aprendizaje a',
                      'logro a', 'outcome a')
    col_b = _find_col(cols, 'learning outcome b', 'resultado de aprendizaje b',
                      'logro b', 'outcome b')
    col_c = _find_col(cols, 'learning outcome c', 'resultado de aprendizaje c',
                      'logro c', 'outcome c')
    col_d = _find_col(cols, 'learning outcome d', 'resultado de aprendizaje d',
                      'logro d', 'outcome d')
    col_ex  = _find_col(cols, 'examen', 'exam', '📝 examen', 'integrative')
    col_sup = _find_col(cols, 'supletorio', 'make-up', 'recuperacion',
                        'recuperación', 'integrative outcome')

    # ── Build normalized DataFrame ───────────────────────────────────────
    df = pd.DataFrame()

    if col_first and col_last:
        df['LastName']  = raw[col_last].fillna('').str.strip().str.upper()
        df['FirstName'] = raw[col_first].fillna('').str.strip().str.upper()
        df['FullName']  = (df['LastName'] + ' ' + df['FirstName']).str.strip()
    elif col_full:
        df['FullName']  = raw[col_full].fillna('').str.strip().str.upper()
        df['LastName']  = df['FullName']
        df['FirstName'] = ''
    else:
        raise ValueError("Could not detect name columns in the uploaded file.")

    df['IDNumber']  = raw[col_id].fillna('S/N').str.strip() if col_id else 'S/N'

    df['LO_A']      = raw[col_a].apply(_to_float)  if col_a  else 0.0
    df['LO_B']      = raw[col_b].apply(_to_float)  if col_b  else 0.0
    df['LO_C']      = raw[col_c].apply(_to_float)  if col_c  else 0.0
    df['LO_D']      = raw[col_d].apply(_to_float)  if col_d  else 0.0
    df['Examen']    = raw[col_ex].apply(_to_float)  if col_ex  else 0.0
    df['Supletorio']= raw[col_sup].apply(_to_float) if col_sup else 0.0

    # Drop rows with no name
    df = df[df['FullName'].str.len() > 2].copy()
    df.sort_values('FullName', inplace=True, ignore_index=True)

    return df


# ── Grade calculations ─────────────────────────────────────────────────────

def compute_grades(df: pd.DataFrame) -> pd.DataFrame:
    """Add all calculated grade columns to the DataFrame."""
    df = df.copy()

    df['EQ_A']      = (df['LO_A'] * 0.15).round(2)
    df['EQ_B']      = (df['LO_B'] * 0.15).round(2)
    df['EQ_C']      = (df['LO_C'] * 0.20).round(2)
    df['EQ_D']      = (df['LO_D'] * 0.20).round(2)
    df['PROM_AC']   = ((df['LO_A'] + df['LO_C']) / 2).round(2)
    df['EQ_PROM_AC']= (df['PROM_AC'] * 0.30).round(2)
    df['SUBTOTAL']  = (df['EQ_A'] + df['EQ_B'] + df['EQ_C'] + df['EQ_D']).round(2)
    df['EQ_EX']     = (df['Examen'] * 0.30).round(2)
    df['SUB_EX']    = (df['SUBTOTAL'] + df['EQ_EX']).round(2)
    df['EQ_SUP']    = (df['Supletorio'] * 0.30).round(2)
    df['FINAL']     = df.apply(
        lambda r: round(r['SUBTOTAL'] + r['EQ_SUP'], 2)
        if r['Supletorio'] > 0 else r['SUB_EX'], axis=1
    )

    def status(r):
        total = r['LO_A'] + r['LO_B'] + r['LO_C'] + r['LO_D']
        if total == 0.0:
            return 'RETIRADO'
        return 'APROBADO' if r['FINAL'] >= 7.0 else 'REPROBADO'

    df['ESTADO'] = df.apply(status, axis=1)
    return df


def compute_grades_mensual(df: pd.DataFrame) -> pd.DataFrame:
    """Compute grades using only LO_A and LO_B (monthly/partial report)."""
    df = df.copy()
    df['LO_C'] = 0.0
    df['LO_D'] = 0.0
    df['Examen'] = 0.0
    df['Supletorio'] = 0.0

    df['EQ_A']       = (df['LO_A'] * 0.15).round(2)
    df['EQ_B']       = (df['LO_B'] * 0.15).round(2)
    df['EQ_C']       = 0.0
    df['EQ_D']       = 0.0
    df['PROM_AC']    = 0.0
    df['EQ_PROM_AC'] = 0.0
    df['SUBTOTAL']   = (df['EQ_A'] + df['EQ_B']).round(2)
    df['EQ_EX']      = 0.0
    df['SUB_EX']     = df['SUBTOTAL']
    df['EQ_SUP']     = 0.0
    df['FINAL']      = df['SUBTOTAL']

    def status(r):
        if r['LO_A'] == 0.0 and r['LO_B'] == 0.0:
            return 'RETIRADO'
        return 'APROBADO' if r['FINAL'] >= 7.0 else 'REPROBADO'

    df['ESTADO'] = df.apply(status, axis=1)
    return df


def get_flagged_students(df: pd.DataFrame):
    """
    Returns two lists of (FullName, IDNumber) tuples:
      - academic: LO_A or LO_B below 7.0 (and not zero/withdrawn)
      - attendance: LO_A == 0 or LO_B == 0
    Based only on Logro A & B per Informe Docente rules.
    """
    academic = []
    attendance = []

    for _, row in df.iterrows():
        a, b = row['LO_A'], row['LO_B']
        name = row['FullName']
        id_  = row['IDNumber']

        if a == 0.0 or b == 0.0:
            attendance.append((name, id_))
        elif a < 7.0 or b < 7.0:
            academic.append((name, id_))

    return academic, attendance
