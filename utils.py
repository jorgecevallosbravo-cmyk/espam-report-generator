"""Shared utilities for all report generators."""

import os
import base64
import subprocess
import tempfile
import shutil

# Logo path — stored as logo.png in the repo root
def _find_logo():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.png'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logo.png'),
        '/mount/src/espam-report-generator/logo.png',
        os.path.join(os.getcwd(), 'logo.png'),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"logo.png not found. Tried: {candidates}")

LOGO_PATH = _find_logo()

# For WeasyPrint (tutorias) — read logo as base64 data URI
def _get_logo_data_uri():
    with open(LOGO_PATH, 'rb') as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{data}"

FACILITADOR       = "JORGE CEVALLOS BRAVO"
FACILITADOR_SHORT = "Jorge Cevallos Bravo"
COORDINADOR       = "Lic. Carlos Enrique Alcívar Zambrano, Mg."
UCI_RESPONSIBLE   = "Ing. José Rafael Vera Vera, Mg."

MODULO_WORDS = {
    "1": "PRIMERO", "2": "SEGUNDO", "3": "TERCERO", "4": "CUARTO",
    "5": "QUINTO",  "6": "SEXTO",   "7": "SÉPTIMO", "8": "OCTAVO",
}

TEAL  = "#00A99D"
WHITE = "#FFFFFF"


def fmt(v) -> str:
    return f"{float(v):.2f}".replace('.', ',')


def esc_html(text: str) -> str:
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))


def tex_s(text) -> str:
    """Escape special LaTeX characters."""
    if not isinstance(text, str):
        text = str(text)
    conv = {
        '\\': r'\textbackslash{}',
        '&':  r'\&',
        '%':  r'\%',
        '$':  r'\$',
        '#':  r'\#',
        '_':  r'\_',
        '{':  r'\{',
        '}':  r'\}',
    }
    return "".join(conv.get(c, c) for c in text)


def write_logo(directory: str) -> str:
    """Copy logo.png to the given temp directory. Returns 'logo.png'."""
    dest = os.path.join(directory, 'logo.png')
    shutil.copy2(LOGO_PATH, dest)
    return 'logo.png'


def compile_latex(tex_content: str, job_name: str = 'output', extra_files: dict = {}) -> bytes:
    """Compile LaTeX string with pdflatex. Returns PDF bytes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        write_logo(tmpdir)
        for fname, fbytes in extra_files.items():
            with open(os.path.join(tmpdir, fname), 'wb') as f:
                f.write(fbytes)
        tex_path = os.path.join(tmpdir, f'{job_name}.tex')
        pdf_path = os.path.join(tmpdir, f'{job_name}.pdf')

        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(tex_content)

        for _ in range(2):
            subprocess.run(
                ['pdflatex', '-interaction=batchmode',
                 '-halt-on-error', f'{job_name}.tex'],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )

        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                return f.read()
        else:
            log_path = os.path.join(tmpdir, f'{job_name}.log')
            log = open(log_path).read()[-3000:] if os.path.exists(log_path) else 'No log'
            raise RuntimeError(f'pdflatex failed:\n{log}')


# ── Topic database ─────────────────────────────────────────────────────────

TOPIC_DATABASE = {
    "1": [
        "Possessive adjectives; the verb be; affirmative statements: Introducing yourself and friends",
        "Articles a, an, and the; this/these, it/they; plurals; prepositions of place: Naming objects",
        "The verb be: affirmative and negative statements, yes/no questions: Talking about cities and countries",
        "Possessives; present continuous statements; conjunctions and, but, so: Describing clothing and colors",
        "Time expressions; present continuous Wh-questions: Asking for and telling time",
        "Simple present statements; time expressions: Talking about daily and weekly routines",
        "Simple present short answers; there is, there are: Describing houses and apartments",
        "Simple present Wh-questions; placement of adjectives: Asking for information about work",
    ],
    "2": [
        "Count and noncount nouns; adverbs of frequency: Talking about food likes and dislikes",
        "Simple present Wh-questions; can for ability: Asking about free-time activities and talents",
        "The future with be going to; future time expressions: Talking about plans and birthdays",
        "Have + noun; feel + adjective; imperatives: Describing health problems and giving advice",
        "Prepositions of place; giving directions with imperatives: Asking for and giving directions",
        "Simple past statements with regular and irregular verbs: Asking about weekend activities",
        "Statements and questions with the past of be; Wh-questions with did: School experiences",
        "Prepositional phrases; subject and object pronouns; invitations: Making and declining invitations",
    ],
    "3": [
        "Wh-questions and statements with be; subject pronouns; possessive adjectives: Introducing oneself",
        "Simple present Wh-questions; time expressions: Describing work and school schedules",
        "Demonstratives; comparisons with adjectives: Talking about prices and preferences",
        "Yes/no and Wh-questions with do; modal verb would: Talking about likes and dislikes",
        "Present continuous; quantifiers: Talking about families and family members",
        "Adverbs of frequency; questions how often, how long: Talking about routines and sports",
        "Simple past yes/no and Wh-questions: Talking about past events and vacations",
        "There is/there are; prepositions of place; count and noncount nouns: Describing neighborhoods",
    ],
    "4": [
        "Questions for describing people; modifiers with participles: Describing people's appearance",
        "Present perfect yes/no and Wh-questions; already and yet; for and since: Past experiences",
        "Adverbs before adjectives; modal verbs can and should: Asking about and describing cities",
        "Adjective + infinitive; modal verbs could and should; requests with may: Health problems",
        "So, too, neither, and either; modal verbs would and will: Ordering a meal",
        "Comparative and superlative forms; questions how far, how big: Describing countries",
        "Future with present continuous and be going to; messages with tell and ask: Making plans",
        "Describing changes with present tense, past tense, present perfect: Exchanging personal information",
    ],
    "5": [
        "Past tense; used to for habitual actions: Introducing yourself and remembering your childhood",
        "Expressions of quantity with count and noncount nouns: Transportation problems and city services",
        "Evaluations and comparisons with adjectives; wish: Describing lifestyle changes",
        "Simple past vs. present perfect; sequence adverbs: Talking about food and giving instructions",
        "Future with be going to and will; modals for necessity and suggestion: Vacation planning",
        "Two-part verbs; will for responding to requests: Making and declining requests, apologizing",
        "Infinitives and gerunds for uses and purposes; imperatives for suggestions: Technology",
        "Relative clauses of time; adverbial clauses of time: Describing holidays and special events",
    ],
    "6": [
        "Time contrasts; conditional sentences with if clauses: Talking about change and consequences",
        "Gerunds; short responses; clauses with because: Describing abilities, skills, and job preferences",
        "Passive with by (simple past); passive without by (simple present): Landmarks and monuments",
        "Past continuous vs. simple past; present perfect continuous: Describing recent past events",
        "Participles as adjectives; relative pronouns for people and things: Movies and books",
        "Modals and adverbs: might, may, could, must; permission and prohibition: Interpreting body language",
        "Unreal conditional sentences with if clauses; past modals: Speculating about past and future events",
        "Reported speech: requests and statements: Reporting what people said; making polite requests",
    ],
    "7": [
        "Relative pronouns as subjects and objects; it clauses with when: Describing personalities",
        "Gerund phrases as subjects and objects; comparisons with adjectives: Talking about careers",
        "Requests with modals, if clauses, and gerunds; indirect requests: Making direct and indirect requests",
        "Past continuous vs. simple past; past perfect: Narrating a story and describing past events",
        "Noun phrases containing relative clauses; expectations: Moving abroad and cultural expectations",
        "Describing problems with past participles; need + gerund: Making complaints and describing problems",
        "Passive in the present continuous and present perfect: Identifying problems and finding solutions",
        "Would rather and would prefer; by + gerund to describe how to do things: Learning methods",
    ],
    "8": [
        "Get or have something done; making suggestions with modals: Asking for and giving advice",
        "Referring to time in the past with adverbs and prepositions; future perfect: Historic events",
        "Time clauses; expressing regret with should have + past participle: Describing milestones and regrets",
        "Describing purpose with infinitive clauses; giving reasons with because, since, due to: Job interviews",
        "Past modals for degrees of certainty: must have, may have, might have: Drawing conclusions",
        "The passive to describe process; defining and non-defining relative clauses: Careers in media",
        "Giving recommendations with passive modals; tag questions for opinions: Controversial topics",
        "Accomplishments with simple past and present perfect; goals with future perfect: Inspirational sayings",
    ],
}
