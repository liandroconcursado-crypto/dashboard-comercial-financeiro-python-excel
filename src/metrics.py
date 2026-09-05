"""Indicadores comerciais, análise temporal e demonstrativos gerenciais."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


MONTH_NAMES = {
    1: "Jan",
    2: "Fev",
    3: "Mar",
    4: "Abr",
    5: "Mai",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Set",
    10: "Out",
    11: "Nov",
    12: "Dez",
}


def calculate_monthly_summary(vendas: pd.DataFrame, despesas: pd.DataFrame) -> pd.DataFrame:
    """Consolida vendas, custos e despesas em frequência mensal."""
    sales = vendas.copy()
    expenses = despesas.copy()
    sales["mes"] = sales["data"].dt.to_period("M")
    expenses["mes"] = expenses["data"].dt.to_period("M")

    sales_monthly = sales.groupby("mes", observed=True).agg(
        faturamento_bruto=("faturamento_bruto", "sum"),
        descontos=("valor_desconto", "sum"),
        faturamento_liquido=("faturamento_liquido", "sum"),
        custo=("custo", "sum"),
        lucro_bruto=("lucro_bruto", "sum"),
        pedidos=("numero_pedido", "nunique"),
        unidades_vendidas=("quantidade", "sum"),
    )
    expense_monthly = expenses.groupby("mes", observed=True).agg(despesas=("valor", "sum"))

    start = min(sales["mes"].min(), expenses["mes"].min())
    end = max(sales["mes"].max(), expenses["mes"].max())
    full_index = pd.period_range(start, end, freq="M")
    monthly = sales_monthly.join(expense_monthly, how="outer").reindex(full_index, fill_value=0)
    monthly.index.name = "mes"
    monthly["resultado_operacional"] = monthly["lucro_bruto"] - monthly["despesas"]
    monthly["margem_percentual"] = np.where(
        monthly["faturamento_liquido"] > 0,
        monthly["lucro_bruto"] / monthly["faturamento_liquido"],
        np.nan,
    )
    monthly["ticket_medio"] = np.where(
        monthly["pedidos"] > 0,
        monthly["faturamento_liquido"] / monthly["pedidos"],
        np.nan,
    )
    monthly["crescimento_mensal"] = monthly["faturamento_liquido"].pct_change(fill_method=None)
    monthly = monthly.reset_index()
    monthly["mes_data"] = monthly["mes"].dt.to_timestamp()
    monthly["mes_label"] = monthly["mes"].map(lambda period: f"{MONTH_NAMES[period.month]}/{str(period.year)[2:]}")
    columns = [
        "mes_data",
        "mes_label",
        "faturamento_bruto",
        "descontos",
        "faturamento_liquido",
        "custo",
        "lucro_bruto",
        "despesas",
        "resultado_operacional",
        "margem_percentual",
        "pedidos",
        "ticket_medio",
        "unidades_vendidas",
        "crescimento_mensal",
    ]
    monthly = monthly[columns]
    money_columns = [
        "faturamento_bruto",
        "descontos",
        "faturamento_liquido",
        "custo",
        "lucro_bruto",
        "despesas",
        "resultado_operacional",
        "ticket_medio",
    ]
    monthly[money_columns] = monthly[money_columns].round(2)
    return monthly


def calculate_rankings(vendas: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Cria rankings comerciais utilizados no Excel, imagens e aplicativo."""
    products = (
        vendas.groupby("produto", as_index=False)
        .agg(unidades_vendidas=("quantidade", "sum"), faturamento_liquido=("faturamento_liquido", "sum"))
        .sort_values(["unidades_vendidas", "faturamento_liquido"], ascending=False)
        .reset_index(drop=True)
    )
    categories = (
        vendas.groupby("categoria", as_index=False)
        .agg(faturamento_liquido=("faturamento_liquido", "sum"), lucro_bruto=("lucro_bruto", "sum"))
        .sort_values("faturamento_liquido", ascending=False)
        .reset_index(drop=True)
    )
    sellers = (
        vendas.groupby("vendedor", as_index=False)
        .agg(faturamento_liquido=("faturamento_liquido", "sum"), pedidos=("numero_pedido", "nunique"))
        .sort_values("faturamento_liquido", ascending=False)
        .reset_index(drop=True)
    )
    states = (
        vendas.groupby("estado", as_index=False)
        .agg(faturamento_liquido=("faturamento_liquido", "sum"), pedidos=("numero_pedido", "nunique"))
        .sort_values("faturamento_liquido", ascending=False)
        .reset_index(drop=True)
    )
    products["faturamento_liquido"] = products["faturamento_liquido"].round(2)
    categories[["faturamento_liquido", "lucro_bruto"]] = categories[["faturamento_liquido", "lucro_bruto"]].round(2)
    sellers["faturamento_liquido"] = sellers["faturamento_liquido"].round(2)
    states["faturamento_liquido"] = states["faturamento_liquido"].round(2)
    return {"produtos": products, "categorias": categories, "vendedores": sellers, "estados": states}


def calculate_kpis(vendas: pd.DataFrame, despesas: pd.DataFrame, monthly: pd.DataFrame | None = None) -> dict[str, Any]:
    """Calcula os KPIs solicitados em uma única base de definição."""
    monthly = calculate_monthly_summary(vendas, despesas) if monthly is None else monthly
    rankings = calculate_rankings(vendas)
    gross_revenue = float(vendas["faturamento_bruto"].sum())
    net_revenue = float(vendas["faturamento_liquido"].sum())
    gross_profit = float(vendas["lucro_bruto"].sum())
    total_expenses = float(despesas["valor"].sum())
    orders = int(vendas["numero_pedido"].nunique())
    monthly_growth = monthly["crescimento_mensal"].dropna()
    return {
        "faturamento_total": round(gross_revenue, 2),
        "descontos_totais": round(float(vendas["valor_desconto"].sum()), 2),
        "faturamento_liquido": round(net_revenue, 2),
        "custo_total": round(float(vendas["custo"].sum()), 2),
        "lucro_bruto": round(gross_profit, 2),
        "margem_media": gross_profit / net_revenue if net_revenue else np.nan,
        "despesas_totais": round(total_expenses, 2),
        "resultado_operacional": round(gross_profit - total_expenses, 2),
        "numero_pedidos": orders,
        "ticket_medio": round(net_revenue / orders, 2) if orders else np.nan,
        "unidades_vendidas": int(vendas["quantidade"].sum()),
        "crescimento_mensal": float(monthly_growth.iloc[-1]) if not monthly_growth.empty else np.nan,
        "produto_mais_vendido": str(rankings["produtos"].iloc[0]["produto"]),
        "categoria_maior_faturamento": str(rankings["categorias"].iloc[0]["categoria"]),
        "melhor_vendedor": str(rankings["vendedores"].iloc[0]["vendedor"]),
        "estado_maior_faturamento": str(rankings["estados"].iloc[0]["estado"]),
    }


def build_dre(monthly: pd.DataFrame) -> pd.DataFrame:
    """Monta a DRE gerencial simplificada por mês."""
    return pd.DataFrame(
        {
            "mes_data": monthly["mes_data"],
            "mes_label": monthly["mes_label"],
            "receita_bruta": monthly["faturamento_bruto"],
            "descontos": monthly["descontos"],
            "receita_liquida": monthly["faturamento_liquido"],
            "custo_mercadorias": monthly["custo"],
            "lucro_bruto": monthly["lucro_bruto"],
            "despesas_operacionais": monthly["despesas"],
            "resultado_operacional": monthly["resultado_operacional"],
        }
    )


def build_cash_flow(monthly: pd.DataFrame) -> pd.DataFrame:
    """Monta um fluxo mensal simplificado, sem caráter contábil oficial."""
    cash = pd.DataFrame(
        {
            "mes_data": monthly["mes_data"],
            "mes_label": monthly["mes_label"],
            "entradas": monthly["faturamento_liquido"],
            "saidas_cmv": monthly["custo"],
            "saidas_despesas": monthly["despesas"],
        }
    )
    cash["saidas_totais"] = cash["saidas_cmv"] + cash["saidas_despesas"]
    cash["saldo_mensal"] = cash["entradas"] - cash["saidas_totais"]
    cash["saldo_acumulado"] = cash["saldo_mensal"].cumsum()
    money_columns = ["entradas", "saidas_cmv", "saidas_despesas", "saidas_totais", "saldo_mensal", "saldo_acumulado"]
    cash[money_columns] = cash[money_columns].round(2)
    return cash


def build_analysis(vendas: pd.DataFrame, despesas: pd.DataFrame) -> dict[str, Any]:
    """Retorna todo o conjunto analítico consumido pelas saídas."""
    monthly = calculate_monthly_summary(vendas, despesas)
    return {
        "mensal": monthly,
        "rankings": calculate_rankings(vendas),
        "kpis": calculate_kpis(vendas, despesas, monthly),
        "dre": build_dre(monthly),
        "fluxo_caixa": build_cash_flow(monthly),
    }
