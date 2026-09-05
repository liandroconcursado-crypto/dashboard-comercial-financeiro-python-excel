"""Ponto de entrada do pipeline completo."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .charts import generate_portfolio_images
from .cleaning import clean_expenses, clean_sales
from .config import (
    DESPESAS_CLEAN_PATH,
    DESPESAS_RAW_PATH,
    REPORT_OUTPUT_PATH,
    VENDAS_CLEAN_PATH,
    VENDAS_RAW_PATH,
    ensure_directories,
)
from .excel_report import create_excel_report, validate_workbook
from .generate_data import generate_raw_datasets
from .metrics import build_analysis
from .report import generate_executive_report


logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
LOGGER = logging.getLogger(__name__)


def _save_clean_data(vendas: pd.DataFrame, despesas: pd.DataFrame) -> None:
    vendas.to_csv(VENDAS_CLEAN_PATH, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    despesas.to_csv(DESPESAS_CLEAN_PATH, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")


def _validate_outputs(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise FileNotFoundError("Saídas ausentes ou vazias: " + ", ".join(missing))


def run_pipeline(seed: int = 42) -> dict[str, Any]:
    """Executa geração, limpeza, análise e criação de todas as entregas."""
    ensure_directories()
    LOGGER.info("1/7 Gerando bases brutas fictícias")
    generate_raw_datasets(seed=seed)

    LOGGER.info("2/7 Validando e limpando dados")
    sales_raw = pd.read_csv(VENDAS_RAW_PATH, encoding="utf-8-sig")
    expenses_raw = pd.read_csv(DESPESAS_RAW_PATH, encoding="utf-8-sig")
    sales_clean, sales_audit = clean_sales(sales_raw)
    expenses_clean, expenses_audit = clean_expenses(expenses_raw)
    _save_clean_data(sales_clean, expenses_clean)

    LOGGER.info("3/7 Calculando indicadores e análises mensais")
    analysis = build_analysis(sales_clean, expenses_clean)

    LOGGER.info("4/7 Gerando imagens de portfólio")
    portfolio_paths = generate_portfolio_images(analysis)

    LOGGER.info("5/7 Criando planilha Excel")
    excel_path = create_excel_report(sales_clean, expenses_clean, analysis)

    LOGGER.info("6/7 Criando relatório executivo")
    audits = {"vendas": sales_audit, "despesas": expenses_audit}
    report_path = generate_executive_report(analysis, audits, REPORT_OUTPUT_PATH)

    LOGGER.info("7/7 Validando arquivos gerados")
    workbook_validation = validate_workbook(excel_path)
    required_paths = [
        VENDAS_RAW_PATH,
        DESPESAS_RAW_PATH,
        VENDAS_CLEAN_PATH,
        DESPESAS_CLEAN_PATH,
        excel_path,
        report_path,
        *portfolio_paths,
    ]
    _validate_outputs(required_paths)
    manifest = {
        "dados": {
            "vendas_brutas": len(sales_raw),
            "vendas_tratadas": len(sales_clean),
            "despesas_brutas": len(expenses_raw),
            "despesas_tratadas": len(expenses_clean),
        },
        "auditoria": audits,
        "excel": workbook_validation,
        "arquivos": [str(path) for path in required_paths],
    }
    LOGGER.info("Pipeline concluído com sucesso")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


if __name__ == "__main__":
    run_pipeline()
