"""Validação, limpeza, padronização e enriquecimento das bases."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import numpy as np
import pandas as pd

from .generate_data import EXPENSE_CATALOG, PAYMENT_METHODS, PRODUCT_CATALOG, SELLERS, STATE_CITIES


SALES_REQUIRED_COLUMNS = {
    "data",
    "numero_pedido",
    "cliente",
    "estado",
    "cidade",
    "vendedor",
    "produto",
    "categoria",
    "quantidade",
    "preco_unitario",
    "desconto",
    "custo_unitario",
    "forma_pagamento",
}

EXPENSE_REQUIRED_COLUMNS = {"data", "categoria", "descricao", "tipo", "valor"}


def _key(value: Any) -> str:
    text = "" if pd.isna(value) else str(value)
    text = " ".join(text.strip().split()).lower()
    return "".join(char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char))


def _canonical_map(values: list[str]) -> dict[str, str]:
    return {_key(value): value for value in values}


PRODUCT_MAP = _canonical_map([item["produto"] for item in PRODUCT_CATALOG])
SALES_CATEGORY_MAP = _canonical_map(sorted({item["categoria"] for item in PRODUCT_CATALOG}))
EXPENSE_CATEGORY_MAP = _canonical_map(list(EXPENSE_CATALOG))
SELLER_MAP = _canonical_map(SELLERS)
PAYMENT_MAP = _canonical_map(PAYMENT_METHODS)
PAYMENT_MAP.update(
    {
        "cartao credito": "Cartão de crédito",
        "credito": "Cartão de crédito",
        "cartao debito": "Cartão de débito",
        "debito": "Cartão de débito",
        "boleto bancario": "Boleto",
        "transferencia bancaria": "Transferência",
    }
)
CITY_MAP = _canonical_map([city for cities in STATE_CITIES.values() for city in cities])


def _normalize_series(series: pd.Series, mapping: dict[str, str], fallback: str) -> pd.Series:
    return series.map(lambda value: mapping.get(_key(value), fallback if not _key(value) else " ".join(str(value).strip().split())))


def parse_number(value: Any, *, percent: bool = False) -> float:
    """Converte números, moedas brasileiras e percentuais em float."""
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        number = float(value)
    else:
        text = str(value).strip()
        is_percent = "%" in text
        text = re.sub(r"[^0-9,.-]", "", text)
        if not text:
            return np.nan
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        number = float(text)
        if is_percent:
            number /= 100
    if percent and abs(number) > 1:
        number /= 100
    return number


def _parse_dates(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, format="mixed", dayfirst=True, errors="coerce")


def clean_sales(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Limpa vendas e retorna a base tratada junto de um resumo de auditoria."""
    missing_columns = SALES_REQUIRED_COLUMNS.difference(df.columns)
    if missing_columns:
        raise ValueError(f"Colunas obrigatórias ausentes em vendas: {sorted(missing_columns)}")

    work = df.copy()
    audit = {"linhas_recebidas": len(work)}
    before = len(work)
    work = work.drop_duplicates().copy()
    audit["duplicatas_removidas"] = before - len(work)

    work["data"] = _parse_dates(work["data"])
    audit["datas_invalidas_removidas"] = int(work["data"].isna().sum())
    work = work.dropna(subset=["data", "numero_pedido"]).copy()

    missing_clients = int(work["cliente"].isna().sum())
    missing_sellers = int(work["vendedor"].isna().sum())
    work["cliente"] = work["cliente"].fillna("Cliente não informado").map(lambda value: " ".join(str(value).strip().split()))
    work["vendedor"] = _normalize_series(work["vendedor"], SELLER_MAP, "Não informado")
    work["produto"] = _normalize_series(work["produto"], PRODUCT_MAP, "Produto não identificado")
    work["categoria"] = _normalize_series(work["categoria"], SALES_CATEGORY_MAP, "Outros")
    work["cidade"] = _normalize_series(work["cidade"], CITY_MAP, "Não informada")
    work["estado"] = work["estado"].fillna("NI").astype(str).str.strip().str.upper()
    work.loc[~work["estado"].isin(STATE_CITIES), "estado"] = "NI"
    work["forma_pagamento"] = _normalize_series(work["forma_pagamento"], PAYMENT_MAP, "Não informada")
    work["numero_pedido"] = work["numero_pedido"].astype(str).str.strip().str.upper()

    for column in ("quantidade", "preco_unitario", "custo_unitario"):
        work[column] = work[column].map(parse_number)
    work["desconto"] = work["desconto"].map(lambda value: parse_number(value, percent=True))

    numeric_missing = int(work[["quantidade", "preco_unitario", "custo_unitario", "desconto"]].isna().sum().sum())
    work["quantidade"] = work["quantidade"].fillna(work["quantidade"].median()).abs().clip(lower=1).round().astype(int)
    for column in ("preco_unitario", "custo_unitario"):
        product_median = work.groupby("produto")[column].transform("median")
        work[column] = work[column].fillna(product_median).fillna(work[column].median()).abs()
    work["desconto"] = work["desconto"].fillna(0).clip(lower=0, upper=0.70)

    work["faturamento_bruto"] = work["quantidade"] * work["preco_unitario"]
    work["valor_desconto"] = work["faturamento_bruto"] * work["desconto"]
    work["faturamento_liquido"] = work["faturamento_bruto"] - work["valor_desconto"]
    work["custo"] = work["quantidade"] * work["custo_unitario"]
    work["lucro_bruto"] = work["faturamento_liquido"] - work["custo"]
    work["margem_percentual"] = np.where(
        work["faturamento_liquido"] > 0,
        work["lucro_bruto"] / work["faturamento_liquido"],
        np.nan,
    )

    currency_columns = [
        "preco_unitario",
        "custo_unitario",
        "faturamento_bruto",
        "valor_desconto",
        "faturamento_liquido",
        "custo",
        "lucro_bruto",
    ]
    work[currency_columns] = work[currency_columns].round(2)
    work["margem_percentual"] = work["margem_percentual"].round(6)
    work = work.drop_duplicates().sort_values(["data", "numero_pedido", "produto"]).reset_index(drop=True)

    audit.update(
        {
            "clientes_preenchidos": missing_clients,
            "vendedores_preenchidos": missing_sellers,
            "valores_numericos_corrigidos": numeric_missing,
            "linhas_finais": len(work),
        }
    )
    errors = validate_sales(work)
    if errors:
        raise ValueError("Falha na validação de vendas: " + "; ".join(errors))
    return work, audit


def clean_expenses(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Limpa despesas e retorna a base tratada junto de um resumo de auditoria."""
    missing_columns = EXPENSE_REQUIRED_COLUMNS.difference(df.columns)
    if missing_columns:
        raise ValueError(f"Colunas obrigatórias ausentes em despesas: {sorted(missing_columns)}")

    work = df.copy()
    audit = {"linhas_recebidas": len(work)}
    before = len(work)
    work = work.drop_duplicates().copy()
    audit["duplicatas_removidas"] = before - len(work)
    work["data"] = _parse_dates(work["data"])
    audit["datas_invalidas_removidas"] = int(work["data"].isna().sum())
    work = work.dropna(subset=["data"]).copy()

    missing_descriptions = int(work["descricao"].isna().sum())
    work["categoria"] = _normalize_series(work["categoria"], EXPENSE_CATEGORY_MAP, "Despesas administrativas")
    work["descricao"] = work["descricao"].fillna("Despesa sem descrição").map(lambda value: " ".join(str(value).strip().split()))
    work["tipo"] = work["tipo"].map(lambda value: "Fixa" if _key(value) == "fixa" else "Variável")
    work["valor"] = work["valor"].map(parse_number)
    missing_values = int(work["valor"].isna().sum())
    category_median = work.groupby("categoria")["valor"].transform("median")
    work["valor"] = work["valor"].fillna(category_median).fillna(work["valor"].median()).abs().round(2)
    work = work.drop_duplicates().sort_values(["data", "categoria"]).reset_index(drop=True)

    audit.update(
        {
            "descricoes_preenchidas": missing_descriptions,
            "valores_numericos_corrigidos": missing_values,
            "linhas_finais": len(work),
        }
    )
    errors = validate_expenses(work)
    if errors:
        raise ValueError("Falha na validação de despesas: " + "; ".join(errors))
    return work, audit


def validate_sales(df: pd.DataFrame) -> list[str]:
    """Retorna uma lista vazia quando a base de vendas está consistente."""
    errors: list[str] = []
    expected = SALES_REQUIRED_COLUMNS | {
        "faturamento_bruto",
        "valor_desconto",
        "faturamento_liquido",
        "custo",
        "lucro_bruto",
        "margem_percentual",
    }
    if missing := expected.difference(df.columns):
        errors.append(f"campos ausentes: {sorted(missing)}")
        return errors
    if df[list(expected)].isna().any().any():
        errors.append("há valores ausentes em campos obrigatórios")
    if df.duplicated().any():
        errors.append("há linhas duplicadas")
    if (df["quantidade"] <= 0).any() or (df["preco_unitario"] <= 0).any() or (df["custo_unitario"] <= 0).any():
        errors.append("há quantidades, preços ou custos não positivos")
    if not df["desconto"].between(0, 0.70).all():
        errors.append("há descontos fora do intervalo permitido")
    if not np.allclose(df["faturamento_bruto"], df["quantidade"] * df["preco_unitario"], atol=0.02):
        errors.append("faturamento bruto inconsistente")
    if not np.allclose(df["faturamento_liquido"], df["faturamento_bruto"] - df["valor_desconto"], atol=0.02):
        errors.append("faturamento líquido inconsistente")
    if not np.allclose(df["lucro_bruto"], df["faturamento_liquido"] - df["custo"], atol=0.02):
        errors.append("lucro bruto inconsistente")
    return errors


def validate_expenses(df: pd.DataFrame) -> list[str]:
    """Retorna uma lista vazia quando a base de despesas está consistente."""
    errors: list[str] = []
    if missing := EXPENSE_REQUIRED_COLUMNS.difference(df.columns):
        errors.append(f"campos ausentes: {sorted(missing)}")
        return errors
    if df[list(EXPENSE_REQUIRED_COLUMNS)].isna().any().any():
        errors.append("há valores ausentes em campos obrigatórios")
    if df.duplicated().any():
        errors.append("há linhas duplicadas")
    if (df["valor"] <= 0).any():
        errors.append("há despesas não positivas")
    return errors
