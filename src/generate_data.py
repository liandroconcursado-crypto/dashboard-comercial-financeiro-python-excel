"""Geração determinística de bases fictícias com problemas de qualidade."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .config import DESPESAS_RAW_PATH, VENDAS_RAW_PATH, ensure_directories


PRODUCT_CATALOG: list[dict[str, Any]] = [
    {"produto": "Notebook Pro 15", "categoria": "Informática", "preco": 4890.00, "custo": 3420.00},
    {"produto": "Notebook Essencial 14", "categoria": "Informática", "preco": 2890.00, "custo": 2020.00},
    {"produto": "Monitor Ultrawide 29", "categoria": "Informática", "preco": 1790.00, "custo": 1160.00},
    {"produto": "Mouse Sem Fio", "categoria": "Acessórios", "preco": 149.90, "custo": 68.00},
    {"produto": "Teclado Mecânico", "categoria": "Acessórios", "preco": 389.90, "custo": 192.00},
    {"produto": "Headset Corporativo", "categoria": "Acessórios", "preco": 329.90, "custo": 158.00},
    {"produto": "Webcam Full HD", "categoria": "Acessórios", "preco": 279.90, "custo": 132.00},
    {"produto": "Cadeira Ergonômica", "categoria": "Móveis", "preco": 1390.00, "custo": 770.00},
    {"produto": "Mesa Ajustável", "categoria": "Móveis", "preco": 1850.00, "custo": 1040.00},
    {"produto": "Gaveteiro Executivo", "categoria": "Móveis", "preco": 690.00, "custo": 365.00},
    {"produto": "Impressora Multifuncional", "categoria": "Impressão", "preco": 1590.00, "custo": 1010.00},
    {"produto": "Toner Preto", "categoria": "Impressão", "preco": 329.00, "custo": 146.00},
    {"produto": "Kit Toner Colorido", "categoria": "Impressão", "preco": 879.00, "custo": 405.00},
    {"produto": "Roteador Empresarial", "categoria": "Conectividade", "preco": 749.00, "custo": 368.00},
    {"produto": "Switch 24 Portas", "categoria": "Conectividade", "preco": 1120.00, "custo": 610.00},
    {"produto": "Access Point Wi-Fi 6", "categoria": "Conectividade", "preco": 890.00, "custo": 478.00},
    {"produto": "Nobreak 1500VA", "categoria": "Energia", "preco": 1190.00, "custo": 675.00},
    {"produto": "Filtro de Linha Premium", "categoria": "Energia", "preco": 119.90, "custo": 51.00},
]

STATE_CITIES = {
    "SP": ["São Paulo", "Campinas", "Santos", "Ribeirão Preto"],
    "RJ": ["Rio de Janeiro", "Niterói", "Petrópolis"],
    "MG": ["Belo Horizonte", "Uberlândia", "Juiz de Fora"],
    "PR": ["Curitiba", "Londrina", "Maringá"],
    "SC": ["Florianópolis", "Joinville", "Blumenau"],
    "RS": ["Porto Alegre", "Caxias do Sul", "Pelotas"],
    "BA": ["Salvador", "Feira de Santana", "Vitória da Conquista"],
    "PE": ["Recife", "Olinda", "Caruaru"],
    "GO": ["Goiânia", "Anápolis", "Aparecida de Goiânia"],
    "DF": ["Brasília"],
}

SELLERS = [
    "Ana Martins",
    "Bruno Costa",
    "Camila Rocha",
    "Diego Lima",
    "Fernanda Alves",
    "Gustavo Ribeiro",
    "Juliana Mendes",
    "Lucas Barros",
]

PAYMENT_METHODS = ["Pix", "Boleto", "Cartão de crédito", "Cartão de débito", "Transferência"]

EXPENSE_CATALOG = {
    "Aluguel": ("Locação do escritório", "Fixa", 6000.0),
    "Salários": ("Folha de pagamento", "Fixa", 12000.0),
    "Marketing": ("Campanhas e conteúdo", "Variável", 2500.0),
    "Logística": ("Fretes e armazenagem", "Variável", 3200.0),
    "Software": ("Licenças e assinaturas", "Fixa", 1200.0),
    "Fornecedores": ("Serviços terceirizados", "Variável", 2200.0),
    "Energia": ("Energia elétrica", "Variável", 900.0),
    "Despesas administrativas": ("Materiais e serviços gerais", "Variável", 1100.0),
}


def _customer_names(count: int = 220) -> list[str]:
    prefixes = ["Alfa", "Aurora", "Central", "Conecta", "Horizonte", "Integra", "Nova", "Ponto", "Prime", "Vértice"]
    suffixes = ["Comercial", "Distribuidora", "Engenharia", "Logística", "Serviços", "Soluções", "Tecnologia", "Varejo"]
    return [f"{prefixes[i % len(prefixes)]} {suffixes[(i * 3) % len(suffixes)]} {i + 1:03d}" for i in range(count)]


def _br_currency(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _inject_sales_quality_issues(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    dirty = df.copy()
    for column in ("preco_unitario", "custo_unitario", "quantidade", "desconto"):
        dirty[column] = dirty[column].astype(object)
    dirty.loc[rng.choice(dirty.index, 16, replace=False), "cliente"] = None
    dirty.loc[rng.choice(dirty.index, 12, replace=False), "vendedor"] = None
    dirty.loc[rng.choice(dirty.index, 18, replace=False), "desconto"] = None

    for idx in rng.choice(dirty.index, 14, replace=False):
        dirty.at[idx, "preco_unitario"] = _br_currency(float(dirty.at[idx, "preco_unitario"]))
    for idx in rng.choice(dirty.index, 10, replace=False):
        dirty.at[idx, "custo_unitario"] = _br_currency(float(dirty.at[idx, "custo_unitario"]))
    for idx in rng.choice(dirty.index, 12, replace=False):
        dirty.at[idx, "quantidade"] = f"{dirty.at[idx, 'quantidade']} unidades"
    for idx in rng.choice(dirty.index, 10, replace=False):
        discount = float(dirty.at[idx, "desconto"] or 0)
        dirty.at[idx, "desconto"] = f"{discount * 100:.0f}%"

    for idx in rng.choice(dirty.index, 18, replace=False):
        dirty.at[idx, "categoria"] = f" {str(dirty.at[idx, 'categoria']).lower()} "
    for idx in rng.choice(dirty.index, 16, replace=False):
        dirty.at[idx, "estado"] = f" {str(dirty.at[idx, 'estado']).lower()} "
    for idx in rng.choice(dirty.index, 14, replace=False):
        value = str(dirty.at[idx, "forma_pagamento"])
        dirty.at[idx, "forma_pagamento"] = value.upper() if idx % 2 else value.replace("Cartão", "Cartao")
    for idx in rng.choice(dirty.index, 14, replace=False):
        dirty.at[idx, "vendedor"] = f" {str(dirty.at[idx, 'vendedor']).upper()} "

    valid_alt_dates = rng.choice(dirty.index, 14, replace=False)
    for idx in valid_alt_dates:
        dirty.at[idx, "data"] = pd.Timestamp(dirty.at[idx, "data"]).strftime("%d/%m/%Y")
    invalid_dates = rng.choice(dirty.index.difference(valid_alt_dates), 7, replace=False)
    dirty.loc[invalid_dates[:4], "data"] = "32/13/2025"
    dirty.loc[invalid_dates[4:], "data"] = None

    duplicates = dirty.sample(24, random_state=731)
    return pd.concat([dirty, duplicates], ignore_index=True)


def _inject_expense_quality_issues(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    dirty = df.copy()
    dirty["valor"] = dirty["valor"].astype(object)
    dirty.loc[rng.choice(dirty.index, 6, replace=False), "descricao"] = None
    for idx in rng.choice(dirty.index, 10, replace=False):
        dirty.at[idx, "categoria"] = f" {str(dirty.at[idx, 'categoria']).lower()} "
    for idx in rng.choice(dirty.index, 8, replace=False):
        dirty.at[idx, "tipo"] = str(dirty.at[idx, "tipo"]).upper().replace("Á", "A")
    for idx in rng.choice(dirty.index, 10, replace=False):
        dirty.at[idx, "valor"] = _br_currency(float(dirty.at[idx, "valor"]))
    valid_alt_dates = rng.choice(dirty.index, 8, replace=False)
    for idx in valid_alt_dates:
        dirty.at[idx, "data"] = pd.Timestamp(dirty.at[idx, "data"]).strftime("%d/%m/%Y")
    invalid_dates = rng.choice(dirty.index.difference(valid_alt_dates), 3, replace=False)
    dirty.loc[invalid_dates, "data"] = ["31/02/2025", None, "data inválida"]
    duplicates = dirty.sample(8, random_state=902)
    return pd.concat([dirty, duplicates], ignore_index=True)


def generate_sales_data(seed: int = 42, target_rows: int = 1800) -> pd.DataFrame:
    """Gera vendas realistas, com múltiplos itens por pedido."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    customers = _customer_names()
    states = list(STATE_CITIES)
    state_weights = np.array([0.30, 0.13, 0.13, 0.09, 0.07, 0.07, 0.07, 0.05, 0.05, 0.04])
    product_weights = np.array([0.05, 0.07, 0.06, 0.10, 0.08, 0.08, 0.07, 0.06, 0.04, 0.04, 0.05, 0.08, 0.04, 0.05, 0.04, 0.04, 0.03, 0.12])
    product_weights /= product_weights.sum()

    rows: list[dict[str, Any]] = []
    order_number = 1
    while len(rows) < target_rows:
        date = pd.Timestamp(rng.choice(dates))
        state = str(rng.choice(states, p=state_weights))
        city = str(rng.choice(STATE_CITIES[state]))
        customer = str(rng.choice(customers))
        seller = str(rng.choice(SELLERS))
        payment = str(rng.choice(PAYMENT_METHODS, p=[0.30, 0.18, 0.30, 0.10, 0.12]))
        item_count = int(rng.choice([1, 2, 3], p=[0.54, 0.35, 0.11]))
        chosen = rng.choice(len(PRODUCT_CATALOG), size=item_count, replace=False, p=product_weights)
        for product_index in chosen:
            product = PRODUCT_CATALOG[int(product_index)]
            seasonal_factor = 1.10 if date.month in (3, 6, 11, 12) else 1.0
            quantity = max(1, int(round(rng.gamma(2.0, 1.4) * seasonal_factor)))
            price = float(product["preco"] * rng.uniform(0.96, 1.05))
            discount = float(rng.choice([0, 0.03, 0.05, 0.08, 0.10, 0.12, 0.15], p=[0.30, 0.08, 0.20, 0.14, 0.15, 0.08, 0.05]))
            cost = float(product["custo"] * rng.uniform(0.97, 1.04))
            rows.append(
                {
                    "data": date.strftime("%Y-%m-%d"),
                    "numero_pedido": f"PED-2025-{order_number:05d}",
                    "cliente": customer,
                    "estado": state,
                    "cidade": city,
                    "vendedor": seller,
                    "produto": product["produto"],
                    "categoria": product["categoria"],
                    "quantidade": quantity,
                    "preco_unitario": round(price, 2),
                    "desconto": discount,
                    "custo_unitario": round(cost, 2),
                    "forma_pagamento": payment,
                }
            )
            if len(rows) >= target_rows:
                break
        order_number += 1
    return _inject_sales_quality_issues(pd.DataFrame(rows), rng)


def generate_expense_data(seed: int = 84, target_rows: int = 360) -> pd.DataFrame:
    """Gera despesas operacionais ao longo de doze meses."""
    rng = np.random.default_rng(seed)
    categories = list(EXPENSE_CATALOG)
    dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    rows: list[dict[str, Any]] = []
    for _ in range(target_rows):
        category = str(rng.choice(categories, p=[0.05, 0.12, 0.15, 0.20, 0.10, 0.15, 0.10, 0.13]))
        description, expense_type, base_value = EXPENSE_CATALOG[category]
        date = pd.Timestamp(rng.choice(dates))
        month_factor = 1.18 if date.month in (11, 12) and category in ("Marketing", "Logística") else 1.0
        value = float(max(120.0, rng.normal(base_value, base_value * 0.18) * month_factor))
        rows.append(
            {
                "data": date.strftime("%Y-%m-%d"),
                "categoria": category,
                "descricao": description,
                "tipo": expense_type,
                "valor": round(value, 2),
            }
        )
    return _inject_expense_quality_issues(pd.DataFrame(rows), rng)


def generate_raw_datasets(seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Gera e grava as duas bases brutas em CSV."""
    ensure_directories()
    sales = generate_sales_data(seed=seed)
    expenses = generate_expense_data(seed=seed + 42)
    sales.to_csv(VENDAS_RAW_PATH, index=False, encoding="utf-8-sig")
    expenses.to_csv(DESPESAS_RAW_PATH, index=False, encoding="utf-8-sig")
    return sales, expenses


if __name__ == "__main__":
    vendas, despesas = generate_raw_datasets()
    print(f"Vendas brutas: {len(vendas):,} linhas")
    print(f"Despesas brutas: {len(despesas):,} linhas")
