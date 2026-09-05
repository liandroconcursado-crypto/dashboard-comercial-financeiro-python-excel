"""Caminhos e identidade visual compartilhados pelo projeto."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
PORTFOLIO_DIR = BASE_DIR / "portfolio"

VENDAS_RAW_PATH = DATA_DIR / "vendas_raw.csv"
DESPESAS_RAW_PATH = DATA_DIR / "despesas_raw.csv"
VENDAS_CLEAN_PATH = DATA_DIR / "vendas_clean.csv"
DESPESAS_CLEAN_PATH = DATA_DIR / "despesas_clean.csv"
EXCEL_OUTPUT_PATH = OUTPUT_DIR / "Dashboard_Comercial_Financeiro.xlsx"
REPORT_OUTPUT_PATH = OUTPUT_DIR / "relatorio_executivo.md"

FONT_FAMILY = "Arial"
COLORS = {
    "navy": "0B172A",
    "navy_light": "13263E",
    "cyan": "22D3EE",
    "blue": "38BDF8",
    "green": "34D399",
    "orange": "FB923C",
    "red": "FB7185",
    "yellow": "FACC15",
    "white": "F8FAFC",
    "muted": "A8B3C5",
    "grid": "334155",
    "light_bg": "F1F5F9",
    "dark_text": "1E293B",
}


def ensure_directories() -> None:
    """Cria as pastas de trabalho geradas pelo pipeline."""
    for directory in (DATA_DIR, OUTPUT_DIR, PORTFOLIO_DIR):
        directory.mkdir(parents=True, exist_ok=True)
