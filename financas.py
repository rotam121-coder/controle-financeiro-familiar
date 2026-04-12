import calendar
import os
import re
from datetime import date, datetime
from uuid import uuid4

import altair as alt
import firebase_admin
import pandas as pd
import streamlit as st
from dateutil.relativedelta import relativedelta
from firebase_admin import credentials, firestore


st.set_page_config(
    page_title="Controle Financeiro Familiar",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)


COLECAO = "lancamentos"
COLECAO_RECORRENTES = "lancamentos_recorrentes"
RESPONSAVEIS = ["Luiz", "Maria"]
CATEGORIAS = [
    "Alimentação",
    "Casa",
    "Carro",
    "Combustível",
    "Educação",
    "Entretenimento",
    "Saúde",
    "Gaby",
    "Alanna",
    "Outros",
]
PAGAMENTOS = ["Dinheiro", "Pix", "Débito", "Crédito"]
TIPOS_CARTAO_CREDITO = [
    "Amazon",
    "Banco do Brasil",
    "Itaú Platinum",
    "Itaú Laranja",
    "Renner",
    "C&A",
    "Mercado Livre",
]
TIPOS = ["Unico", "Parcelado", "Recorrente"]
CORES = ["#2F7D4A", "#5A9C70", "#86B79A", "#ADCBB1", "#CFE0CB", "#6B8F61", "#B18D57"]


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #F4F7F2;
            --card: #FFFFFF;
            --card-soft: #FAFCF9;
            --surface: #F6FAF5;
            --ink: #111827;
            --muted: #5C6B5F;
            --muted-strong: #37463A;
            --line: #D9E3D6;
            --line-strong: #C5D2C3;
            --primary: #2F7D4A;
            --primary-strong: #25653B;
            --primary-soft: #EAF4ED;
            --hover: #EEF5EF;
            --success: #25653B;
            --success-soft: #EDF7F0;
            --warning-soft: #F7F3E8;
            --danger-soft: #FBEEEB;
            --shadow-sm: 0 8px 20px rgba(17, 24, 39, 0.04);
            --shadow-md: 0 16px 28px rgba(17, 24, 39, 0.08);
        }
        html, body, [class*="css"] { font-family: Inter, "Segoe UI", sans-serif; }
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            color: var(--ink);
            background:
                radial-gradient(circle at top left, rgba(47, 125, 74, 0.10), transparent 26%),
                radial-gradient(circle at top right, rgba(132, 183, 154, 0.08), transparent 22%),
                linear-gradient(180deg, #FBFCFA 0%, var(--bg) 100%);
        }
        [data-testid="stHeader"] {
            background: rgba(244, 247, 242, 0.88);
            border-bottom: 1px solid rgba(217, 227, 214, 0.8);
            backdrop-filter: blur(8px);
        }
        .block-container {
            max-width: 1120px;
            padding-top: 1.2rem;
            padding-bottom: 3.8rem;
        }
        h1, h2, h3, h4, h5, h6, p, span, label, li, small { color: var(--ink) !important; }
        .stMarkdown p { line-height: 1.5; }
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] span,
        .field-label,
        .section-title {
            color: var(--ink) !important;
            font-weight: 650 !important;
            letter-spacing: -0.01em;
        }
        .stTextInput, .stDateInput, .stSelectbox, .stNumberInput, .stSegmentedControl {
            margin-bottom: 0.75rem;
        }
        [data-baseweb="input"] > div,
        [data-baseweb="base-input"],
        [data-baseweb="select"] > div,
        .stTextInput > div > div,
        .stDateInput > div > div,
        .stNumberInput > div > div {
            min-height: 54px !important;
            background: var(--card) !important;
            border: 1px solid rgba(197, 210, 195, 0.82) !important;
            border-radius: 11px !important;
            box-shadow: none !important;
            transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
        }
        [data-baseweb="input"] input,
        [data-baseweb="select"] input,
        .stTextInput input,
        .stDateInput input,
        .stNumberInput input,
        textarea {
            background: transparent !important;
            color: var(--ink) !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }
        input::placeholder, textarea::placeholder {
            color: #98A2B3 !important;
            opacity: 1 !important;
        }
        [data-baseweb="input"] > div:focus-within,
        [data-baseweb="select"] > div:focus-within,
        [data-baseweb="base-input"]:focus-within,
        .stTextInput > div > div:focus-within,
        .stDateInput > div > div:focus-within,
        .stNumberInput > div > div:focus-within {
            border-color: rgba(47, 125, 74, 0.58) !important;
            box-shadow: 0 0 0 2px rgba(47, 125, 74, 0.10) !important;
            background: #FFFFFF !important;
        }
        .stSelectbox [data-baseweb="select"] > div > div,
        .stSelectbox [data-baseweb="select"] input,
        .stSelectbox [data-baseweb="select"] span {
            color: var(--ink) !important;
        }
        [data-baseweb="select"] svg,
        [data-testid="stDateInput"] svg {
            color: var(--muted-strong) !important;
        }
        div[data-baseweb="popover"] {
            z-index: 999999 !important;
        }
        div[data-baseweb="popover"] > div,
        div[data-baseweb="menu"] {
            background: var(--card) !important;
            border: 1px solid rgba(197, 210, 195, 0.9) !important;
            border-radius: 11px !important;
            box-shadow: 0 12px 24px rgba(17, 24, 39, 0.08) !important;
            overflow: hidden !important;
            max-height: min(340px, calc(100vh - 4.5rem)) !important;
            max-width: min(440px, calc(100vw - 1rem)) !important;
        }
        div[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"],
        div[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"] > div,
        div[data-baseweb="menu"] [data-testid="stSelectboxVirtualDropdown"],
        div[data-baseweb="menu"] [data-testid="stSelectboxVirtualDropdown"] > div {
            background: var(--card) !important;
            max-height: min(280px, calc(100vh - 7rem)) !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }
        div[data-baseweb="popover"] ul,
        div[data-baseweb="popover"] [role="listbox"],
        div[data-baseweb="menu"] ul,
        div[data-baseweb="menu"] [role="listbox"],
        div[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"],
        div[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"] > div,
        div[data-baseweb="menu"] [data-testid="stSelectboxVirtualDropdown"],
        div[data-baseweb="menu"] [data-testid="stSelectboxVirtualDropdown"] > div {
            background: var(--card) !important;
            color: var(--ink) !important;
            max-height: min(280px, calc(100vh - 7rem)) !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            display: block !important;
            padding: 0.3rem !important;
            scrollbar-gutter: stable both-edges !important;
            scrollbar-width: auto !important;
            scrollbar-color: #9FB6A2 #EEF5EF !important;
            overscroll-behavior: contain !important;
            -webkit-overflow-scrolling: touch !important;
        }
        div[data-baseweb="popover"] li,
        div[data-baseweb="popover"] [role="option"],
        div[data-baseweb="menu"] li,
        div[data-baseweb="menu"] [role="option"] {
            min-height: 42px !important;
            color: var(--ink) !important;
            border-radius: 10px !important;
            padding: 0.65rem 0.75rem !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            background: transparent !important;
        }
        div[data-baseweb="popover"] li *,
        div[data-baseweb="popover"] [role="option"] *,
        div[data-baseweb="menu"] li *,
        div[data-baseweb="menu"] [role="option"] * {
            color: var(--ink) !important;
        }
        div[data-baseweb="popover"] li:hover,
        div[data-baseweb="popover"] [role="option"]:hover,
        div[data-baseweb="menu"] li:hover,
        div[data-baseweb="menu"] [role="option"]:hover {
            background: var(--surface) !important;
        }
        div[data-baseweb="popover"] [aria-selected="true"],
        div[data-baseweb="popover"] li[aria-selected="true"],
        div[data-baseweb="menu"] [aria-selected="true"],
        div[data-baseweb="menu"] li[aria-selected="true"] {
            background: var(--primary-soft) !important;
            color: var(--ink) !important;
            font-weight: 700 !important;
        }
        div[data-baseweb="popover"] [role="listbox"]::-webkit-scrollbar,
        div[data-baseweb="popover"] ul::-webkit-scrollbar,
        div[data-baseweb="menu"] ul::-webkit-scrollbar,
        div[data-baseweb="menu"] [role="listbox"]::-webkit-scrollbar,
        div[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"]::-webkit-scrollbar,
        div[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"] > div::-webkit-scrollbar,
        div[data-baseweb="menu"] [data-testid="stSelectboxVirtualDropdown"]::-webkit-scrollbar,
        div[data-baseweb="menu"] [data-testid="stSelectboxVirtualDropdown"] > div::-webkit-scrollbar {
            width: 13px;
        }
        div[data-baseweb="popover"] [role="listbox"]::-webkit-scrollbar-track,
        div[data-baseweb="popover"] ul::-webkit-scrollbar-track,
        div[data-baseweb="menu"] ul::-webkit-scrollbar-track,
        div[data-baseweb="menu"] [role="listbox"]::-webkit-scrollbar-track,
        div[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"]::-webkit-scrollbar-track,
        div[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"] > div::-webkit-scrollbar-track,
        div[data-baseweb="menu"] [data-testid="stSelectboxVirtualDropdown"]::-webkit-scrollbar-track,
        div[data-baseweb="menu"] [data-testid="stSelectboxVirtualDropdown"] > div::-webkit-scrollbar-track {
            background: #EDF4EE;
            border-radius: 999px;
        }
        div[data-baseweb="popover"] [role="listbox"]::-webkit-scrollbar-thumb,
        div[data-baseweb="popover"] ul::-webkit-scrollbar-thumb,
        div[data-baseweb="menu"] ul::-webkit-scrollbar-thumb,
        div[data-baseweb="menu"] [role="listbox"]::-webkit-scrollbar-thumb,
        div[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"]::-webkit-scrollbar-thumb,
        div[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"] > div::-webkit-scrollbar-thumb,
        div[data-baseweb="menu"] [data-testid="stSelectboxVirtualDropdown"]::-webkit-scrollbar-thumb,
        div[data-baseweb="menu"] [data-testid="stSelectboxVirtualDropdown"] > div::-webkit-scrollbar-thumb {
            background: #9FB6A2;
            border-radius: 999px;
            border: 2px solid #EDF4EE;
        }
        div[data-baseweb="popover"] [role="listbox"]::-webkit-scrollbar-thumb:hover,
        div[data-baseweb="popover"] ul::-webkit-scrollbar-thumb:hover,
        div[data-baseweb="menu"] ul::-webkit-scrollbar-thumb:hover,
        div[data-baseweb="menu"] [role="listbox"]::-webkit-scrollbar-thumb:hover,
        div[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"]::-webkit-scrollbar-thumb:hover,
        div[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"] > div::-webkit-scrollbar-thumb:hover,
        div[data-baseweb="menu"] [data-testid="stSelectboxVirtualDropdown"]::-webkit-scrollbar-thumb:hover,
        div[data-baseweb="menu"] [data-testid="stSelectboxVirtualDropdown"] > div::-webkit-scrollbar-thumb:hover {
            background: #728C76;
        }
        [data-baseweb="button-group"] {
            width: 100%;
            background: var(--card) !important;
            border: 1px solid var(--line) !important;
            border-radius: 12px !important;
            padding: 0.22rem !important;
            gap: 0.22rem !important;
            box-shadow: none !important;
        }
        [data-baseweb="button-group"] button,
        [data-baseweb="button-group"] [role="radio"] {
            min-height: 42px !important;
            border: none !important;
            border-radius: 10px !important;
            background: transparent !important;
            color: var(--muted-strong) !important;
            box-shadow: none !important;
            font-weight: 650 !important;
        }
        [data-baseweb="button-group"] button:hover,
        [data-baseweb="button-group"] [role="radio"]:hover {
            background: var(--surface) !important;
            color: var(--ink) !important;
        }
        [data-baseweb="button-group"] [aria-selected="true"],
        [data-baseweb="button-group"] [aria-pressed="true"],
        [data-baseweb="button-group"] [aria-checked="true"] {
            background: linear-gradient(135deg, var(--primary), var(--primary-strong)) !important;
            color: #FFFFFF !important;
            box-shadow: 0 8px 18px rgba(37, 101, 59, 0.18) !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.35rem;
            flex-wrap: wrap;
            margin-bottom: 1.2rem;
            padding: 0.28rem;
            width: fit-content;
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid var(--line);
            border-radius: 16px;
            box-shadow: var(--shadow-sm);
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            color: var(--muted-strong);
            border: none !important;
            border-radius: 12px;
            min-height: 44px;
            padding: 0.5rem 1.05rem;
            font-weight: 650;
            transition: background-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background: var(--surface) !important;
            color: var(--ink) !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--primary), var(--primary-strong)) !important;
            color: #FFFFFF !important;
            box-shadow: 0 10px 22px rgba(37, 101, 59, 0.18) !important;
        }
        .stButton > button {
            width: 100%;
            min-height: 52px;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--primary), var(--primary-strong));
            color: #FFF !important;
            font-size: 1rem;
            font-weight: 700;
            box-shadow: 0 10px 20px rgba(37, 101, 59, 0.18);
            transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 24px rgba(37, 101, 59, 0.2);
            filter: brightness(1.02);
        }
        .stButton > button:focus {
            box-shadow: 0 0 0 3px rgba(47, 125, 74, 0.14);
        }
        .hero, .panel, .metric-card, .note {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid rgba(197, 210, 195, 0.78);
            border-radius: 14px;
            box-shadow: var(--shadow-sm);
        }
        .hero {
            padding: 1.45rem 1.6rem;
            margin-bottom: 1.15rem;
            background: linear-gradient(135deg, rgba(47, 125, 74, 0.12), rgba(134, 183, 154, 0.08));
        }
        .panel { padding: 1.25rem 1.35rem; margin-bottom: 1rem; }
        .section-title {
            font-size: 1.08rem;
            margin-bottom: 0.2rem;
        }
        .eyebrow {
            color: var(--primary-strong) !important;
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.5rem;
        }
        .hero-text, .subtitle, .metric-sub, .note span, .stCaptionContainer {
            color: var(--muted) !important;
        }
        .field-label {
            margin-bottom: 0.35rem;
            color: var(--ink);
            font-weight: 650;
        }
        .metric-card { padding: 1rem 1.05rem; }
        .metric-card.accent { background: linear-gradient(180deg, rgba(234, 244, 237, 0.96), rgba(255, 255, 255, 0.98)); }
        .metric-card.success { background: linear-gradient(180deg, rgba(237, 247, 240, 0.94), rgba(255, 255, 255, 0.98)); }
        .metric-card.danger { background: linear-gradient(180deg, rgba(254, 243, 242, 0.92), rgba(255, 255, 255, 0.98)); }
        .metric-label {
            display: block;
            color: var(--muted) !important;
            font-size: 0.9rem;
            font-weight: 650;
            margin-bottom: 0.45rem;
        }
        .metric-value {
            display: block;
            color: var(--ink) !important;
            font-size: clamp(1.45rem, 2.5vw, 1.95rem);
            font-weight: 800;
            line-height: 1.05;
        }
        .metric-sub { display: block; margin-top: 0.5rem; font-size: 0.88rem; }
        .note { padding: 0.95rem 1rem; margin-bottom: 1rem; }
        .note.warning { background: var(--warning-soft); }
        .note.success { background: var(--success-soft); }
        .note.danger { background: var(--danger-soft); }
        [data-testid="stDataFrame"] {
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid var(--line);
            background: var(--card);
        }
        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.9rem;
                padding-right: 0.9rem;
                padding-top: 1rem;
            }
            div[data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
            .hero, .panel, .metric-card, .note {
                border-radius: 14px;
            }
            .stTabs [data-baseweb="tab-list"] {
                width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def normalize_payment_method(payment_method: str | None) -> str:
    normalized = (payment_method or "").strip()
    payment_aliases = {
        "Debito": PAGAMENTOS[2],
        PAGAMENTOS[2]: PAGAMENTOS[2],
        "Credito": PAGAMENTOS[3],
        PAGAMENTOS[3]: PAGAMENTOS[3],
    }
    if normalized in payment_aliases:
        return payment_aliases[normalized]
    if normalized in PAGAMENTOS:
        return normalized
    return PAGAMENTOS[0]


def form_state_defaults() -> dict:
    return {
        "data_input": date.today(),
        "descricao_input": "",
        "responsavel_input": RESPONSAVEIS[0],
        "categoria_input": CATEGORIAS[0],
        "pagamento_input": PAGAMENTOS[1],
        "cartao_credito_input": TIPOS_CARTAO_CREDITO[0],
        "tipo_input": TIPOS[0],
        "parcelas_input": 2,
        "valor_atm_widget": "",
        "valor_atm_digits": "",
        "valor_atm_display": "",
        "valor_atm_valor": 0.0,
        "valor_atm_valido": True,
        "valor_atm_sync_pending": False,
    }


def apply_pending_form_reset() -> None:
    if not st.session_state.get("pending_form_reset", False):
        return

    for key, value in form_state_defaults().items():
        st.session_state[key] = value

    st.session_state["pending_form_reset"] = False


def init_state() -> None:
    defaults = {
        **form_state_defaults(),
        "pending_form_reset": False,
        "form_feedback_message": "",
        "receitas_mensais": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    apply_pending_form_reset()
    st.session_state["pagamento_input"] = normalize_payment_method(st.session_state.get("pagamento_input"))


def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def decimal_brl(value: float) -> str:
    return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def resolve_credit_card(item: dict | pd.Series | None) -> str:
    if item is None:
        return ""
    return str(item.get("cartao") or item.get("cartao_credito") or "").strip()


def queue_form_reset(success_message: str) -> None:
    st.session_state["pending_form_reset"] = True
    st.session_state["form_feedback_message"] = success_message


def format_date_br(value: str | date | datetime | pd.Timestamp | None) -> str:
    if value is None or value == "":
        return ""
    if pd.isna(value):
        return ""

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().strftime("%d/%m/%Y")
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")

    text = str(value).strip()
    if not text:
        return ""

    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, pattern).strftime("%d/%m/%Y")
        except ValueError:
            continue

    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return text
    return parsed.strftime("%d/%m/%Y")


def format_atm_digits(digits: str) -> str:
    if not digits:
        return ""
    return decimal_brl(int(digits) / 100)


def prepare_atm_widget_state(key: str) -> None:
    widget_key = f"{key}_widget"
    display_key = f"{key}_display"
    sync_key = f"{key}_sync_pending"

    if st.session_state.get(sync_key, False) or widget_key not in st.session_state:
        st.session_state[widget_key] = st.session_state.get(display_key, "")
        st.session_state[sync_key] = False


def reconcile_atm_input(key: str, raw_value: str) -> tuple[float, bool]:
    digits_key = f"{key}_digits"
    display_key = f"{key}_display"
    value_key = f"{key}_valor"
    valid_key = f"{key}_valido"
    sync_key = f"{key}_sync_pending"

    previous_display = str(st.session_state.get(display_key, ""))
    previous_digits = str(st.session_state.get(digits_key, ""))
    current_input = str(raw_value or "")
    current_digits = re.sub(r"\D", "", current_input)

    if not current_input.strip():
        new_digits = ""
    elif len(current_input) < len(previous_display) and previous_display.startswith(current_input):
        new_digits = previous_digits[:-1]
    else:
        new_digits = current_digits.lstrip("0")

    display_value = format_atm_digits(new_digits)
    numeric_value = (int(new_digits) / 100) if new_digits else 0.0

    st.session_state[digits_key] = new_digits
    st.session_state[display_key] = display_value
    st.session_state[value_key] = numeric_value
    st.session_state[valid_key] = True

    needs_sync = current_input != display_value
    if needs_sync:
        st.session_state[sync_key] = True

    return numeric_value, needs_sync


def month_label(month_key: str) -> str:
    year, month = month_key.split("-")
    return f"{month}/{year}"


def month_to_date(month_key: str) -> date:
    return datetime.strptime(f"{month_key}-01", "%Y-%m-%d").date()


def date_to_month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def current_month_key() -> str:
    return date_to_month_key(date.today())


def shift_month_key(month_key: str, months: int) -> str:
    return date_to_month_key(month_to_date(month_key) + relativedelta(months=months))


def iter_month_keys(start_month: str, end_month: str):
    cursor = month_to_date(start_month)
    limit = month_to_date(end_month)
    while cursor <= limit:
        yield date_to_month_key(cursor)
        cursor += relativedelta(months=1)


def scheduled_date_for_month(month_key: str, reference_day: int) -> str:
    month_date = month_to_date(month_key)
    last_day = calendar.monthrange(month_date.year, month_date.month)[1]
    day = min(reference_day, last_day)
    return month_date.replace(day=day).strftime("%Y-%m-%d")


def resolve_projection_horizon(lancamentos: list[dict], recorrentes: list[dict]) -> str:
    meses = [current_month_key()]
    meses.extend(item["competencia"] for item in lancamentos if item.get("competencia"))
    meses.extend(item["competencia_inicio"] for item in recorrentes if item.get("competencia_inicio"))
    meses.extend(item["competencia_fim"] for item in recorrentes if item.get("competencia_fim"))
    return max(meses)


def metric_card(column, title: str, value: str, subtitle: str, tone: str = "") -> None:
    column.markdown(
        f"""
        <div class="metric-card {tone}">
            <span class="metric-label">{title}</span>
            <span class="metric-value">{value}</span>
            <span class="metric-sub">{subtitle}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def note(title: str, body: str, tone: str = "") -> None:
    st.markdown(
        f"""
        <div class="note {tone}">
            <strong>{title}</strong><br/>
            <span>{body}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def atm_input(key: str) -> float:
    widget_key = f"{key}_widget"
    prepare_atm_widget_state(key)
    raw_value = st.text_input(
        "Valor",
        key=widget_key,
        placeholder="0,00",
        label_visibility="collapsed",
    )
    value, needs_sync = reconcile_atm_input(key, raw_value)
    if needs_sync:
        return value
    return value


def get_firebase_credentials():
    if "firebase_service_account" in st.secrets:
        data = dict(st.secrets["firebase_service_account"])
        if "private_key" in data:
            data["private_key"] = data["private_key"].replace("\\n", "\n")
        return credentials.Certificate(data)
    if "firebase" in st.secrets:
        data = dict(st.secrets["firebase"])
        if "private_key" in data:
            data["private_key"] = data["private_key"].replace("\\n", "\n")
        return credentials.Certificate(data)
    json_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if json_path and os.path.exists(json_path):
        return credentials.Certificate(json_path)

    local_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".firebase", "chave.json")
    if os.path.exists(local_json):
        return credentials.Certificate(local_json)

    raise RuntimeError(
        "Credenciais do Firebase nao encontradas. Configure st.secrets['firebase_service_account'], "
        "FIREBASE_SERVICE_ACCOUNT_PATH ou coloque o JSON em .firebase/chave.json."
    )


def initialize_firebase_app() -> None:
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(get_firebase_credentials())


@st.cache_resource(show_spinner=False)
def get_firestore():
    initialize_firebase_app()
    return firestore.client()


def is_credit_payment(payment_method: str) -> bool:
    return normalize_payment_method(payment_method) == PAGAMENTOS[3]


def normalize_payment_display(forma_pagamento: str, cartao_credito: str) -> str:
    payment_label = normalize_payment_method(forma_pagamento)
    if is_credit_payment(payment_label) and cartao_credito:
        return f"{payment_label} - {cartao_credito}"
    return payment_label


def salvar_lancamento_firestore(lancamento: dict) -> None:
    if not lancamento.get("descricao"):
        raise ValueError("Descricao e obrigatoria para salvar o lancamento.")

    record_id = lancamento.get("id") or uuid4().hex
    group_id = lancamento.get("grupo_id") or record_id

    try:
        valor = float(lancamento.get("valor", 0.0))
    except (TypeError, ValueError):
        raise ValueError("Valor deve ser um numero valido.")

    if valor <= 0:
        raise ValueError("Valor deve ser maior que zero.")

    data_value = lancamento.get("data")
    if isinstance(data_value, (date, datetime)):
        data_value = data_value.strftime("%Y-%m-%d")

    payment_method = normalize_payment_method(lancamento.get("forma_pagamento", PAGAMENTOS[0]))
    credit_card = resolve_credit_card(lancamento) if is_credit_payment(payment_method) else ""

    record = {
        "id": record_id,
        "grupo_id": group_id,
        "data_compra": data_value,
        "competencia": date_to_month_key(datetime.strptime(data_value, "%Y-%m-%d").date()) if data_value else "",
        "descricao": lancamento["descricao"].strip(),
        "valor": valor,
        "categoria": lancamento.get("categoria", "Outros"),
        "responsavel": lancamento.get("responsavel", RESPONSAVEIS[0]),
        "forma_pagamento": payment_method,
        "cartao": credit_card,
        "cartao_credito": credit_card,
        "tipo": lancamento.get("tipo", "Unico"),
        "parcelas_totais": 1,
        "parcela_atual": 1,
        "parcela_label": "",
        "valor_total_compra": valor,
        "origem": "manual",
        "criado_em": firestore.SERVER_TIMESTAMP,
    }

    db = get_firestore()
    db.collection(COLECAO).document(record["id"]).set(record)
    clear_firestore_caches()


def normalize(item: dict) -> dict:
    total_installments = int(item.get("parcelas_totais", 1) or 1)
    current_installment = int(item.get("parcela_atual", 1) or 1)
    amount = float(item.get("valor", 0.0) or 0.0)
    kind = item.get("tipo", "Unico")
    payment_method = normalize_payment_method(item.get("forma_pagamento", PAGAMENTOS[0]))
    credit_card = resolve_credit_card(item) if is_credit_payment(payment_method) else ""
    return {
        "id": item.get("id", ""),
        "grupo_id": item.get("grupo_id", ""),
        "data_compra": item.get("data_compra", ""),
        "competencia": item.get("competencia", ""),
        "descricao": item.get("descricao", ""),
        "valor": amount,
        "categoria": item.get("categoria", "Outros"),
        "responsavel": item.get("responsavel", RESPONSAVEIS[0]),
        "forma_pagamento": payment_method,
        "cartao": credit_card,
        "cartao_credito": credit_card,
        "tipo": kind,
        "parcelas_totais": total_installments,
        "parcela_atual": current_installment,
        "parcela_label": item.get("parcela_label", f"{current_installment}/{total_installments}" if kind == "Parcelado" else ""),
        "valor_total_compra": float(item.get("valor_total_compra", amount) or amount),
        "recorrente_id": item.get("recorrente_id", ""),
        "origem": item.get("origem", "manual"),
    }


def normalize_recurring(item: dict) -> dict:
    amount = float(item.get("valor", 0.0) or 0.0)
    start_date = item.get("data_inicio", "")
    reference_day = int(item.get("dia_referencia", 1) or 1)
    active = bool(item.get("ativo", True))
    start_month = item.get("competencia_inicio", "")
    payment_method = normalize_payment_method(item.get("forma_pagamento", PAGAMENTOS[0]))
    credit_card = resolve_credit_card(item) if is_credit_payment(payment_method) else ""

    if not start_month and start_date:
        start_month = date_to_month_key(datetime.strptime(start_date, "%Y-%m-%d").date())

    return {
        "id": item.get("id", ""),
        "grupo_id": item.get("grupo_id", item.get("id", "")),
        "data_inicio": start_date,
        "dia_referencia": reference_day,
        "competencia_inicio": start_month,
        "competencia_fim": item.get("competencia_fim", ""),
        "descricao": item.get("descricao", ""),
        "valor": amount,
        "categoria": item.get("categoria", "Outros"),
        "responsavel": item.get("responsavel", RESPONSAVEIS[0]),
        "forma_pagamento": payment_method,
        "cartao": credit_card,
        "cartao_credito": credit_card,
        "tipo": "Recorrente",
        "ativo": active,
        "desativado_em": item.get("desativado_em"),
    }


@st.cache_data(show_spinner=False)
def carregar_dados_firestore() -> list[dict]:
    return []
    


@st.cache_data(show_spinner=False)
def carregar_recorrentes_firestore() -> list[dict]:
    docs = get_firestore().collection(COLECAO_RECORRENTES).stream()
    data = []
    for doc in docs:
        row = doc.to_dict()
        row["id"] = doc.id
        data.append(normalize_recurring(row))
    data.sort(key=lambda row: (row["ativo"] is False, row["descricao"], row["id"]))
    return data


def clear_firestore_caches() -> None:
    carregar_dados_firestore.clear()
    carregar_recorrentes_firestore.clear()


def salvar_dados_firestore(records: list[dict]) -> None:
    db = get_firestore()
    batch = db.batch()
    for record in records:
        ref = db.collection(COLECAO).document(record["id"])
        batch.set(ref, {**record, "criado_em": firestore.SERVER_TIMESTAMP})
    batch.commit()
    clear_firestore_caches()


def salvar_recorrente_firestore(record: dict) -> None:
    db = get_firestore()
    ref = db.collection(COLECAO_RECORRENTES).document(record["id"])
    ref.set({**record, "criado_em": firestore.SERVER_TIMESTAMP})
    clear_firestore_caches()


def desativar_recorrente_firestore(recorrente_id: str, stop_month: str | None = None) -> None:
    db = get_firestore()
    final_month = stop_month or current_month_key()
    db.collection(COLECAO_RECORRENTES).document(recorrente_id).update(
        {
            "ativo": False,
            "competencia_fim": final_month,
            "desativado_em": firestore.SERVER_TIMESTAMP,
        }
    )
    clear_firestore_caches()


def load_data_safe() -> tuple[list[dict], list[dict], str | None]:
    try:
        return carregar_dados_firestore(), carregar_recorrentes_firestore(), None
    except Exception as error:
        return [], [], str(error)


def build_recurring_record(
    purchase_date: date,
    description: str,
    total_value: float,
    category: str,
    owner: str,
    payment_method: str,
    credit_card: str = "",
) -> dict:
    recurring_id = uuid4().hex
    payment_method = normalize_payment_method(payment_method)
    credit_card = credit_card if is_credit_payment(payment_method) else ""
    first_month = purchase_date + relativedelta(months=1) if is_credit_payment(payment_method) else purchase_date
    return {
        "id": recurring_id,
        "grupo_id": recurring_id,
        "data_inicio": purchase_date.strftime("%Y-%m-%d"),
        "dia_referencia": purchase_date.day,
        "competencia_inicio": date_to_month_key(first_month),
        "competencia_fim": "",
        "descricao": description.strip(),
        "valor": round(total_value, 2),
        "categoria": category,
        "responsavel": owner,
        "forma_pagamento": payment_method,
        "cartao": credit_card,
        "cartao_credito": credit_card if is_credit_payment(payment_method) else "",
        "tipo": "Recorrente",
        "ativo": True,
        "desativado_em": None,
    }


def build_installments(
    purchase_date: date,
    description: str,
    total_value: float,
    category: str,
    owner: str,
    payment_method: str,
    credit_card: str,
    kind: str,
    installments: int,
) -> list[dict]:
    effective_installments = installments if kind == "Parcelado" else 1
    group_id = uuid4().hex
    payment_method = normalize_payment_method(payment_method)
    credit_card = credit_card if is_credit_payment(payment_method) else ""
    base_month = purchase_date + relativedelta(months=1) if is_credit_payment(payment_method) else purchase_date
    base_amount = round(total_value / effective_installments, 2)
    paid_so_far = 0.0
    records = []

    for index in range(effective_installments):
        if index == effective_installments - 1:
            installment_value = round(total_value - paid_so_far, 2)
        else:
            installment_value = base_amount
            paid_so_far = round(paid_so_far + installment_value, 2)

        installment_number = index + 1
        records.append(
            {
                "id": f"{group_id}-{installment_number:02d}",
                "grupo_id": group_id,
                "data_compra": purchase_date.strftime("%Y-%m-%d"),
                "competencia": (base_month + relativedelta(months=index)).strftime("%Y-%m"),
                "descricao": description.strip(),
                "valor": installment_value,
                "categoria": category,
                "responsavel": owner,
                "forma_pagamento": payment_method,
                "cartao": credit_card,
                "cartao_credito": credit_card if is_credit_payment(payment_method) else "",
                "tipo": kind,
                "parcelas_totais": effective_installments,
                "parcela_atual": installment_number,
                "parcela_label": f"{installment_number}/{effective_installments}" if effective_installments > 1 else "",
                "valor_total_compra": round(total_value, 2),
                "origem": "manual",
            }
        )

    return records


def expand_recurring_records(recorrentes: list[dict], horizon_month: str) -> list[dict]:
    records = []

    for recorrente in recorrentes:
        start_month = recorrente.get("competencia_inicio", "")
        if not start_month:
            continue

        end_month = recorrente.get("competencia_fim") or horizon_month
        final_month = min(end_month, horizon_month)
        if final_month < start_month:
            continue

        reference_day = int(recorrente.get("dia_referencia", 1) or 1)
        payment_method = normalize_payment_method(recorrente.get("forma_pagamento", PAGAMENTOS[0]))
        credit_card = resolve_credit_card(recorrente) if is_credit_payment(payment_method) else ""
        for month_key in iter_month_keys(start_month, final_month):
            records.append(
                {
                    "id": f"rec-{recorrente['id']}-{month_key}",
                    "grupo_id": recorrente.get("grupo_id", recorrente["id"]),
                    "data_compra": scheduled_date_for_month(month_key, reference_day),
                    "competencia": month_key,
                    "descricao": recorrente["descricao"],
                    "valor": float(recorrente["valor"]),
                    "categoria": recorrente["categoria"],
                    "responsavel": recorrente["responsavel"],
                    "forma_pagamento": payment_method,
                    "cartao": credit_card,
                    "cartao_credito": credit_card,
                    "tipo": "Recorrente",
                    "parcelas_totais": 1,
                    "parcela_atual": 1,
                    "parcela_label": "",
                    "valor_total_compra": float(recorrente["valor"]),
                    "recorrente_id": recorrente["id"],
                    "origem": "recorrente",
                }
            )

    return records


def prepare_df(data: list[dict]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame(
            columns=[
                "id",
                "grupo_id",
                "data_compra",
                "competencia",
                "descricao",
                "valor",
                "categoria",
                "responsavel",
                "forma_pagamento",
                "cartao",
                "cartao_credito",
                "tipo",
                "parcelas_totais",
                "parcela_atual",
                "parcela_label",
                "valor_total_compra",
                "recorrente_id",
                "origem",
                "mes_ref",
            ]
        )

    df = pd.DataFrame(data)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
    df["descricao"] = df["descricao"].fillna("")
    df["categoria"] = df["categoria"].fillna("Outros")
    df["responsavel"] = df["responsavel"].fillna(RESPONSAVEIS[0])
    df["tipo"] = df["tipo"].fillna("Unico")
    df["forma_pagamento"] = df["forma_pagamento"].fillna(PAGAMENTOS[0]).apply(normalize_payment_method)
    if "cartao" not in df.columns:
        df["cartao"] = ""
    else:
        df["cartao"] = df["cartao"].fillna("")
    if "cartao_credito" not in df.columns:
        df["cartao_credito"] = df["cartao"]
    else:
        df["cartao_credito"] = df["cartao_credito"].fillna("")
        df["cartao_credito"] = df["cartao_credito"].where(df["cartao_credito"] != "", df["cartao"])
        df["cartao"] = df["cartao"].where(df["cartao"] != "", df["cartao_credito"])
    if "recorrente_id" not in df.columns:
        df["recorrente_id"] = ""
    else:
        df["recorrente_id"] = df["recorrente_id"].fillna("")
    if "origem" not in df.columns:
        df["origem"] = "manual"
    else:
        df["origem"] = df["origem"].fillna("manual")
    df["mes_ref"] = pd.to_datetime(df["competencia"] + "-01", errors="coerce")
    return df.sort_values(["mes_ref", "descricao", "parcela_atual"], ascending=[False, True, True])


def pie_by_category(df_month: pd.DataFrame) -> None:
    grouped = df_month.groupby("categoria", as_index=False)["valor"].sum().sort_values("valor", ascending=False)
    if grouped.empty:
        st.info("Sem dados por categoria neste mes.")
        return

    chart = (
        alt.Chart(grouped)
        .mark_arc(innerRadius=62)
        .encode(
            theta=alt.Theta("valor:Q", title="Valor"),
            color=alt.Color("categoria:N", title="Categoria", scale=alt.Scale(range=CORES)),
            tooltip=[
                alt.Tooltip("categoria:N", title="Categoria"),
                alt.Tooltip("valor:Q", title="Valor", format=",.2f"),
            ],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)


def bar_by_owner(df_month: pd.DataFrame) -> None:
    grouped = df_month.groupby("responsavel", as_index=False)["valor"].sum().sort_values("valor", ascending=False)
    if grouped.empty:
        st.info("Sem dados por responsavel neste mes.")
        return

    chart = (
        alt.Chart(grouped)
        .mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10)
        .encode(
            x=alt.X("responsavel:N", title="Responsavel"),
            y=alt.Y("valor:Q", title="Valor gasto"),
            color=alt.Color("responsavel:N", legend=None, scale=alt.Scale(range=["#2F7D4A", "#86B79A"])),
            tooltip=[
                alt.Tooltip("responsavel:N", title="Responsavel"),
                alt.Tooltip("valor:Q", title="Valor", format=",.2f"),
            ],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)


def monthly_evolution(df: pd.DataFrame) -> None:
    grouped = df.groupby("mes_ref", as_index=False)["valor"].sum().sort_values("mes_ref")
    if grouped.empty:
        st.info("Sem historico suficiente para a evolucao mensal.")
        return

    chart = (
        alt.Chart(grouped)
        .mark_line(point=alt.OverlayMarkDef(size=85, filled=True, color="#2F7D4A"), strokeWidth=3)
        .encode(
            x=alt.X("mes_ref:T", title="Mes", axis=alt.Axis(format="%m/%Y")),
            y=alt.Y("valor:Q", title="Gasto total"),
            tooltip=[
                alt.Tooltip("mes_ref:T", title="Mes", format="%m/%Y"),
                alt.Tooltip("valor:Q", title="Valor", format=",.2f"),
            ],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)


def firebase_help(error: str) -> None:
    note("Firebase pendente", "A interface esta pronta, mas a conexao com o Firestore ainda nao foi configurada.", "warning")
    st.error(f"Detalhe da conexao: {error}")
    with st.expander("Exemplo de configuracao no Streamlit"):
        st.code(
            """
[firebase_service_account]
type = "service_account"
project_id = "seu-projeto"
private_key_id = "sua-chave"
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "firebase-adminsdk@seu-projeto.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
            """.strip(),
            language="toml",
        )
        st.caption("Tambem funciona com a variavel FIREBASE_SERVICE_ACCOUNT_PATH apontando para o JSON da conta de servico.")


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>Controle Financeiro Familiar</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_form_tab(firestore_error: str | None) -> None:
    st.markdown(
        """
        <div class="panel">
            <div class="section-title">Novo lançamento</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    feedback_message = st.session_state.get("form_feedback_message", "")
    if feedback_message:
        st.success(feedback_message)
        st.session_state["form_feedback_message"] = ""

    left, right = st.columns(2, gap="medium")

    with left:
        st.date_input("Data da compra", key="data_input", format="DD/MM/YYYY")
        st.text_input("Descrição", key="descricao_input", placeholder="Ex.: supermercado, farmácia, gasolina")
        st.markdown('<div class="field-label">Valor</div>', unsafe_allow_html=True)
        value = atm_input("valor_atm")
        st.selectbox("Responsável", RESPONSAVEIS, key="responsavel_input")

    with right:
        st.selectbox("Categoria", CATEGORIAS, key="categoria_input")
        st.selectbox("Forma de pagamento", PAGAMENTOS, key="pagamento_input")
        if is_credit_payment(st.session_state["pagamento_input"]):
            st.selectbox("Cartão de crédito", TIPOS_CARTAO_CREDITO, key="cartao_credito_input")
        st.segmented_control(
            "Tipo de lançamento",
            TIPOS,
            key="tipo_input",
            selection_mode="single",
            width="stretch",
        )
        installments = 1
        if st.session_state["tipo_input"] == "Parcelado":
            installments = int(
                st.number_input(
                    "Quantidade de parcelas",
                    min_value=2,
                    max_value=48,
                    step=1,
                    key="parcelas_input",
                )
            )
            st.caption("Compras no cartão de crédito entram automaticamente na competência do mês seguinte.")
        elif st.session_state["tipo_input"] == "Recorrente":
            st.caption("O valor será repetido automaticamente nas competências seguintes, respeitando a regra do meio de pagamento, até ser desativado.")

    if st.button("Salvar lançamento", disabled=firestore_error is not None):
        description = str(st.session_state.get("descricao_input", "")).strip()
        value = float(st.session_state.get("valor_atm_valor", value))
        kind = st.session_state.get("tipo_input", TIPOS[0])
        installments = int(st.session_state.get("parcelas_input", 2) or 2) if kind == "Parcelado" else 1

        if not description or value <= 0:
            st.error("Preencha a descrição e informe um valor válido antes de salvar.")
            return

        try:
            purchase_date = st.session_state.get("data_input", date.today())
            payment_method = normalize_payment_method(st.session_state.get("pagamento_input", PAGAMENTOS[0]))
            credit_card = st.session_state["cartao_credito_input"] if is_credit_payment(payment_method) else ""
            success_message = ""

            if kind == "Recorrente":
                recurring_record = build_recurring_record(
                    purchase_date=purchase_date,
                    description=description,
                    total_value=float(value),
                    category=st.session_state["categoria_input"],
                    owner=st.session_state["responsavel_input"],
                    payment_method=payment_method,
                    credit_card=credit_card,
                )
                salvar_recorrente_firestore(recurring_record)
                success_message = "Lançamento recorrente salvo. Ele será somado automaticamente nos próximos meses até ser desativado."
            elif kind == "Parcelado":
                records = build_installments(
                    purchase_date=purchase_date,
                    description=description,
                    total_value=float(value),
                    category=st.session_state["categoria_input"],
                    owner=st.session_state["responsavel_input"],
                    payment_method=payment_method,
                    credit_card=credit_card,
                    kind=kind,
                    installments=installments,
                )
                salvar_dados_firestore(records)
                success_message = "Lançamento parcelado salvo no Firestore com sucesso."
            else:
                salvar_lancamento_firestore(
                    {
                        "data": purchase_date,
                        "descricao": description,
                        "valor": float(value),
                        "categoria": st.session_state["categoria_input"],
                        "responsavel": st.session_state["responsavel_input"],
                        "forma_pagamento": payment_method,
                        "cartao": credit_card,
                        "cartao_credito": credit_card,
                        "tipo": kind,
                    }
                )
                success_message = "Lançamento único salvo no Firestore com sucesso."
            queue_form_reset(success_message)
            st.rerun()
        except Exception as error:
            st.error(f"Não foi possível salvar no Firestore: {error}")

    if firestore_error:
        st.caption("O botão de salvar será habilitado assim que as credenciais do Firebase forem configuradas.")


def render_dashboard_tab(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Nenhum lancamento encontrado no Firestore ainda.")
        return

    months = sorted(df["competencia"].dropna().unique(), reverse=True)
    selected_month = st.selectbox("Mes de analise", months, format_func=month_label)
    df_month = df[df["competencia"] == selected_month].copy()

    initial_income = float(st.session_state["receitas_mensais"].get(selected_month, 0.0))
    income = st.number_input(
        "Receita do mes",
        min_value=0.0,
        value=initial_income,
        step=100.0,
        key=f"receita_{selected_month}",
    )
    st.session_state["receitas_mensais"][selected_month] = income

    spent = float(df_month["valor"].sum())
    balance = income - spent
    average_ticket = float(df_month["valor"].mean()) if not df_month.empty else 0.0

    col1, col2, col3 = st.columns(3, gap="large")
    metric_card(col1, "Gasto do mes", brl(spent), f"Competencia {month_label(selected_month)}", "accent")
    metric_card(col2, "Receita informada", brl(income), "Valor mantido em session_state", "success")
    metric_card(col3, "Saldo projetado", brl(balance), f"Ticket medio {brl(average_ticket)}", "success" if balance >= 0 else "danger")

    if income > 0 and spent >= income * 0.8:
        percent = (spent / income) * 100
        note("Alerta de gasto alto", f"Os gastos do mes consumiram {percent:.1f}% da receita informada.", "warning")

    biggest = df_month.sort_values("valor", ascending=False).head(1)
    if not biggest.empty and float(biggest.iloc[0]["valor"]) >= max(average_ticket * 2, 300):
        row = biggest.iloc[0]
        note("Maior lancamento do mes", f"{row['descricao']} em {row['categoria']} somou {brl(float(row['valor']))}.", "danger")

    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        st.markdown("### Pizza por categoria")
        pie_by_category(df_month)
    with chart_right:
        st.markdown("### Gastos por responsavel")
        bar_by_owner(df_month)

    st.markdown("### Evolucao mensal")
    monthly_evolution(df)

    st.markdown("### Ultimos lancamentos do mes")
    df_month = df_month.copy()
    df_month["pagamento_exibido"] = df_month.apply(
        lambda row: normalize_payment_display(row["forma_pagamento"], resolve_credit_card(row)),
        axis=1,
    )
    table = (
        df_month.sort_values(["data_compra", "parcela_atual"], ascending=[False, True])
        .loc[:, ["data_compra", "descricao", "categoria", "responsavel", "tipo", "pagamento_exibido", "parcela_label", "valor"]]
        .rename(
            columns={
                "data_compra": "Data",
                "descricao": "Descricao",
                "categoria": "Categoria",
                "responsavel": "Responsavel",
                "tipo": "Tipo",
                "pagamento_exibido": "Pagamento",
                "parcela_label": "Parcela",
                "valor": "Valor",
            }
        )
    )
    table["Data"] = table["Data"].map(format_date_br)
    table["Valor"] = table["Valor"].map(brl)
    st.dataframe(table, use_container_width=True, hide_index=True)


def render_installments_tab(df: pd.DataFrame) -> None:
    installments = df[df["tipo"] == "Parcelado"].copy()
    if installments.empty:
        st.info("Nenhuma compra parcelada encontrada.")
        return

    st.markdown("### Compras parceladas")
    st.caption("Cada parcela fica registrada na competencia correta para nao distorcer o dashboard mensal.")

    installments["pagamento_exibido"] = installments.apply(
        lambda row: normalize_payment_display(row["forma_pagamento"], resolve_credit_card(row)),
        axis=1,
    )
    summary = (
        installments.groupby(
            ["grupo_id", "descricao", "categoria", "responsavel", "pagamento_exibido", "parcelas_totais"],
            as_index=False,
        )
        .agg(
            valor_total_compra=("valor_total_compra", "max"),
            parcelas_registradas=("parcela_atual", "max"),
            primeira_competencia=("competencia", "min"),
            ultima_competencia=("competencia", "max"),
        )
        .sort_values(["ultima_competencia", "descricao"], ascending=[False, True])
    )

    summary["primeira_competencia"] = summary["primeira_competencia"].map(month_label)
    summary["ultima_competencia"] = summary["ultima_competencia"].map(month_label)
    summary["valor_total_compra"] = summary["valor_total_compra"].map(brl)
    summary = summary.rename(
        columns={
            "descricao": "Descricao",
            "categoria": "Categoria",
            "responsavel": "Responsavel",
            "pagamento_exibido": "Pagamento",
            "parcelas_totais": "Parcelas",
            "parcelas_registradas": "Ultima parcela",
            "primeira_competencia": "Primeira competencia",
            "ultima_competencia": "Ultima competencia",
            "valor_total_compra": "Valor total",
        }
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)


def render_recurring_tab(recorrentes: list[dict], firestore_error: str | None) -> None:
    st.markdown("### Lancamentos recorrentes")
    st.caption("Ao desativar um recorrente, ele para de ser somado a partir dos proximos meses e o mes atual e preservado.")

    if firestore_error:
        st.info("Configure o Firebase para gerenciar os recorrentes por aqui.")
        return

    if not recorrentes:
        st.info("Nenhum lancamento recorrente cadastrado ainda.")
        return

    ativos = [item for item in recorrentes if item.get("ativo", True)]
    inativos = [item for item in recorrentes if not item.get("ativo", True)]

    col1, col2, col3 = st.columns(3, gap="large")
    metric_card(col1, "Recorrentes ativos", str(len(ativos)), "Lancamentos somados automaticamente", "accent")
    metric_card(col2, "Total mensal ativo", brl(sum(float(item["valor"]) for item in ativos)), "Soma fixa dos recorrentes ativos", "success")
    metric_card(col3, "Recorrentes desativados", str(len(inativos)), "Historico mantido para auditoria", "danger" if inativos else "")

    if ativos:
        st.markdown("#### Ativos")
        for recorrente in ativos:
            start_label = month_label(recorrente["competencia_inicio"]) if recorrente.get("competencia_inicio") else "-"
            payment_label = normalize_payment_display(recorrente["forma_pagamento"], resolve_credit_card(recorrente))
            info = (
                f"{recorrente['categoria']} &bull; {recorrente['responsavel']} &bull; {payment_label}<br/>"
                f"Início em {start_label} &bull; Valor mensal {brl(float(recorrente['valor']))}"
            )

            card_col, action_col = st.columns([4.5, 1.2], gap="medium")
            card_col.markdown(
                f"""
                <div class="panel" style="margin-bottom:0.85rem;">
                    <div class="section-title">{recorrente['descricao']}</div>
                    <div class="subtitle">{info}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if action_col.button("Desativar", key=f"desativar_recorrente_{recorrente['id']}"):
                try:
                    desativar_recorrente_firestore(recorrente["id"])
                    st.success("Recorrente desativado para os proximos meses.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Nao foi possivel desativar o recorrente: {error}")

    if inativos:
        st.markdown("#### Desativados")
        inactive_df = pd.DataFrame(inativos)
        inactive_df["valor"] = inactive_df["valor"].map(brl)
        inactive_df["pagamento_exibido"] = inactive_df.apply(
            lambda row: normalize_payment_display(row["forma_pagamento"], resolve_credit_card(row)),
            axis=1,
        )
        inactive_df["competencia_inicio"] = inactive_df["competencia_inicio"].apply(
            lambda value: month_label(value) if value else "-"
        )
        inactive_df["competencia_fim"] = inactive_df["competencia_fim"].replace("", pd.NA).fillna("-")
        inactive_df["competencia_fim"] = inactive_df["competencia_fim"].apply(
            lambda value: month_label(value) if value != "-" else value
        )
        inactive_df = inactive_df.loc[
            :,
            ["descricao", "categoria", "responsavel", "pagamento_exibido", "competencia_inicio", "competencia_fim", "valor"],
        ].rename(
            columns={
                "descricao": "Descricao",
                "categoria": "Categoria",
                "responsavel": "Responsavel",
                "pagamento_exibido": "Pagamento",
                "competencia_inicio": "Inicio",
                "competencia_fim": "Encerrado em",
                "valor": "Valor mensal",
            }
        )
        st.dataframe(inactive_df, use_container_width=True, hide_index=True)


def main() -> None:
    inject_css()
    init_state()
    render_header()

    data, recorrentes, firestore_error = [], [], None
    projection_horizon = resolve_projection_horizon(data, recorrentes)
    expanded_data = data + expand_recurring_records(recorrentes, projection_horizon)
    df = prepare_df(expanded_data)

    if firestore_error:
        firebase_help(firestore_error)

    tab1, tab2, tab3, tab4 = st.tabs(["Lançar", "Painel", "Parcelados", "Recorrentes"])

    with tab1:
        render_form_tab(firestore_error)

    with tab2:
        if firestore_error and df.empty:
            st.info("Configure o Firebase para carregar o dashboard diretamente do Firestore.")
        render_dashboard_tab(df)

    with tab3:
        if firestore_error and df.empty:
            st.info("As compras parceladas aparecerao aqui assim que o Firestore estiver configurado.")
        render_installments_tab(df)

    with tab4:
        render_recurring_tab(recorrentes, firestore_error)


if __name__ == "__main__":
    main()
