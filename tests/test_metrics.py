"""Testes dos cálculos e reconciliações gerenciais."""

import numpy as np

from src.metrics import build_analysis


def test_sales_calculations_reconcile(clean_datasets):
    sales, _, _, _ = clean_datasets
    assert np.allclose(sales["faturamento_bruto"], sales["quantidade"] * sales["preco_unitario"], atol=0.02)
    assert np.allclose(sales["faturamento_liquido"], sales["faturamento_bruto"] - sales["valor_desconto"], atol=0.02)
    assert np.allclose(sales["lucro_bruto"], sales["faturamento_liquido"] - sales["custo"], atol=0.02)


def test_kpis_and_monthly_totals_are_consistent(clean_datasets):
    sales, expenses, _, _ = clean_datasets
    analysis = build_analysis(sales, expenses)
    kpis = analysis["kpis"]
    monthly = analysis["mensal"]
    assert np.isclose(kpis["faturamento_total"], sales["faturamento_bruto"].sum(), atol=0.02)
    assert np.isclose(kpis["faturamento_liquido"], monthly["faturamento_liquido"].sum(), atol=0.02)
    assert np.isclose(kpis["lucro_bruto"], monthly["lucro_bruto"].sum(), atol=0.02)
    assert np.isclose(kpis["despesas_totais"], expenses["valor"].sum(), atol=0.02)
    assert np.isclose(kpis["resultado_operacional"], kpis["lucro_bruto"] - kpis["despesas_totais"], atol=0.02)
    assert kpis["numero_pedidos"] == sales["numero_pedido"].nunique()
    assert kpis["unidades_vendidas"] == int(sales["quantidade"].sum())


def test_dre_and_cash_flow_reconcile(clean_datasets):
    sales, expenses, _, _ = clean_datasets
    analysis = build_analysis(sales, expenses)
    dre = analysis["dre"]
    cash = analysis["fluxo_caixa"]
    assert np.allclose(dre["receita_liquida"], dre["receita_bruta"] - dre["descontos"], atol=0.02)
    assert np.allclose(dre["lucro_bruto"], dre["receita_liquida"] - dre["custo_mercadorias"], atol=0.02)
    assert np.allclose(dre["resultado_operacional"], dre["lucro_bruto"] - dre["despesas_operacionais"], atol=0.02)
    assert np.allclose(cash["saldo_mensal"], cash["entradas"] - cash["saidas_totais"], atol=0.02)
    assert np.isclose(cash["saldo_acumulado"].iloc[-1], cash["saldo_mensal"].sum(), atol=0.02)
