"""Dashboard interativo do projeto demonstrativo."""

from __future__ import annotations

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from src.charts import format_brl
from src.config import DESPESAS_CLEAN_PATH, VENDAS_CLEAN_PATH
from src.metrics import build_analysis


st.set_page_config(
    page_title="Dashboard comercial e financeiro",
    page_icon=":material/monitoring:",
    layout="wide",
)


@st.cache_data(show_spinner="Carregando bases tratadas...")
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega os CSVs tratados; o cache é invalidado quando o arquivo muda."""
    sales = pd.read_csv(VENDAS_CLEAN_PATH, encoding="utf-8-sig", parse_dates=["data"])
    expenses = pd.read_csv(DESPESAS_CLEAN_PATH, encoding="utf-8-sig", parse_dates=["data"])
    return sales, expenses


def filter_sales(
    sales: pd.DataFrame,
    period: tuple[date, date] | list[date],
    categories: list[str],
    sellers: list[str],
    states: list[str],
) -> pd.DataFrame:
    """Aplica os filtros globais à base comercial."""
    filtered = sales.copy()
    if len(period) == 2:
        start, end = pd.Timestamp(period[0]), pd.Timestamp(period[1])
        filtered = filtered[filtered["data"].between(start, end)]
    if categories:
        filtered = filtered[filtered["categoria"].isin(categories)]
    if sellers:
        filtered = filtered[filtered["vendedor"].isin(sellers)]
    if states:
        filtered = filtered[filtered["estado"].isin(states)]
    return filtered


def filter_expenses(expenses: pd.DataFrame, period: tuple[date, date] | list[date]) -> pd.DataFrame:
    """Filtra despesas apenas pelo período, pois não há dimensão comercial nelas."""
    if len(period) != 2:
        return expenses
    start, end = pd.Timestamp(period[0]), pd.Timestamp(period[1])
    return expenses[expenses["data"].between(start, end)].copy()


def pct_br(value: float) -> str:
    return f"{value:.1%}".replace(".", ",")


def money_tooltip(field: str, title: str) -> alt.Tooltip:
    return alt.Tooltip(f"{field}:Q", title=title, format=",.2f")


if not VENDAS_CLEAN_PATH.exists() or not DESPESAS_CLEAN_PATH.exists():
    st.error("As bases tratadas ainda não existem. Execute `python -m src.main` antes de abrir o dashboard.", icon=":material/error:")
    st.stop()

sales, expenses = load_data()
min_date = sales["data"].min().date()
max_date = sales["data"].max().date()

with st.sidebar:
    st.header("Filtros", icon=":material/filter_list:")
    period = st.date_input(
        "Período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY",
        key="periodo",
    )
    categories = st.multiselect(
        "Categoria",
        sorted(sales["categoria"].dropna().unique()),
        placeholder="Todas as categorias",
        key="categorias",
        wrap=True,
    )
    sellers = st.multiselect(
        "Vendedor",
        sorted(sales["vendedor"].dropna().unique()),
        placeholder="Todos os vendedores",
        key="vendedores",
        wrap=True,
    )
    states = st.multiselect(
        "Estado",
        sorted(sales["estado"].dropna().unique()),
        placeholder="Todos os estados",
        key="estados",
        wrap=True,
    )
    st.caption("Todos os dados são fictícios e foram gerados exclusivamente para demonstração.")

filtered_sales = filter_sales(sales, period, categories, sellers, states)
filtered_expenses = filter_expenses(expenses, period)

st.title("Dashboard comercial e financeiro", icon=":material/monitoring:")
st.caption("Indicadores de vendas, rentabilidade e despesas | projeto demonstrativo")

if filtered_sales.empty:
    st.warning("Nenhuma venda encontrada para os filtros selecionados.", icon=":material/warning:")
    st.stop()

analysis = build_analysis(filtered_sales, filtered_expenses)
kpis = analysis["kpis"]
monthly = analysis["mensal"]
growth = kpis["crescimento_mensal"]

with st.container(horizontal=True):
    st.metric(
        "Faturamento líquido",
        format_brl(kpis["faturamento_liquido"], compact=True),
        pct_br(growth) if pd.notna(growth) else None,
        delta_description="último mês",
        icon=":material/payments:",
        border=True,
        chart_data=monthly["faturamento_liquido"].tolist(),
        chart_type="line",
    )
    st.metric(
        "Lucro bruto",
        format_brl(kpis["lucro_bruto"], compact=True),
        icon=":material/trending_up:",
        border=True,
        chart_data=monthly["lucro_bruto"].tolist(),
        chart_type="area",
        delta_color="green",
    )
    st.metric("Margem bruta", pct_br(kpis["margem_media"]), icon=":material/percent:", border=True)
    st.metric(
        "Despesas",
        format_brl(kpis["despesas_totais"], compact=True),
        icon=":material/receipt_long:",
        border=True,
        chart_data=monthly["despesas"].tolist(),
        chart_type="bar",
        delta_color="orange",
    )
    st.metric("Pedidos", f"{kpis['numero_pedidos']:,}".replace(",", "."), icon=":material/shopping_cart:", border=True)
    st.metric("Ticket médio", format_brl(kpis["ticket_medio"]), icon=":material/confirmation_number:", border=True)

if categories or sellers or states:
    st.caption("As despesas são filtradas somente pelo período, pois a base de despesas não possui categoria de produto, vendedor ou estado.")

monthly_long = monthly[["mes_data", "faturamento_liquido", "lucro_bruto"]].melt(
    id_vars="mes_data", var_name="indicador", value_name="valor"
)
monthly_long["indicador"] = monthly_long["indicador"].map(
    {"faturamento_liquido": "Faturamento líquido", "lucro_bruto": "Lucro bruto"}
)
trend_chart = (
    alt.Chart(monthly_long)
    .mark_line(point=True, strokeWidth=2.5)
    .encode(
        x=alt.X("mes_data:T", title=None, axis=alt.Axis(format="%b/%y")),
        y=alt.Y("valor:Q", title="R$", scale=alt.Scale(zero=False)),
        color=alt.Color("indicador:N", title=None, legend=alt.Legend(orient="bottom")),
        tooltip=[alt.Tooltip("mes_data:T", title="Mês", format="%m/%Y"), alt.Tooltip("indicador:N", title="Indicador"), money_tooltip("valor", "Valor (R$)")],
    )
    .properties(height=320)
)

category_data = analysis["rankings"]["categorias"].sort_values("faturamento_liquido")
category_chart = (
    alt.Chart(category_data)
    .mark_bar(cornerRadiusEnd=4)
    .encode(
        x=alt.X("faturamento_liquido:Q", title="Faturamento líquido (R$)"),
        y=alt.Y("categoria:N", title=None, sort=None),
        color=alt.Color("categoria:N", legend=None),
        tooltip=[alt.Tooltip("categoria:N", title="Categoria"), money_tooltip("faturamento_liquido", "Faturamento (R$)")],
    )
    .properties(height=320)
)

row_one = st.columns(2)
with row_one[0].container(border=True, height="stretch"):
    st.subheader("Evolução mensal", icon=":material/query_stats:")
    st.altair_chart(trend_chart, width="stretch")
with row_one[1].container(border=True, height="stretch"):
    st.subheader("Vendas por categoria", icon=":material/category:")
    st.altair_chart(category_chart, width="stretch")

seller_data = analysis["rankings"]["vendedores"].sort_values("faturamento_liquido")
seller_chart = (
    alt.Chart(seller_data)
    .mark_bar(cornerRadiusEnd=4, color="#34D399")
    .encode(
        x=alt.X("faturamento_liquido:Q", title="Faturamento líquido (R$)"),
        y=alt.Y("vendedor:N", title=None, sort=None),
        tooltip=[alt.Tooltip("vendedor:N", title="Vendedor"), money_tooltip("faturamento_liquido", "Faturamento (R$)"), alt.Tooltip("pedidos:Q", title="Pedidos")],
    )
    .properties(height=300)
)

product_data = analysis["rankings"]["produtos"].head(10).sort_values("unidades_vendidas")
product_chart = (
    alt.Chart(product_data)
    .mark_bar(cornerRadiusEnd=4, color="#FB923C")
    .encode(
        x=alt.X("unidades_vendidas:Q", title="Unidades vendidas"),
        y=alt.Y("produto:N", title=None, sort=None),
        tooltip=[alt.Tooltip("produto:N", title="Produto"), alt.Tooltip("unidades_vendidas:Q", title="Unidades", format=",.0f"), money_tooltip("faturamento_liquido", "Faturamento (R$)")],
    )
    .properties(height=300)
)

row_two = st.columns(2)
with row_two[0].container(border=True, height="stretch"):
    st.subheader("Vendas por vendedor", icon=":material/groups:")
    st.altair_chart(seller_chart, width="stretch")
with row_two[1].container(border=True, height="stretch"):
    st.subheader("Top 10 produtos", icon=":material/inventory_2:")
    st.altair_chart(product_chart, width="stretch")

state_data = analysis["rankings"]["estados"].sort_values("faturamento_liquido")
state_chart = (
    alt.Chart(state_data)
    .mark_bar(cornerRadiusEnd=4, color="#22D3EE")
    .encode(
        x=alt.X("faturamento_liquido:Q", title="Faturamento líquido (R$)"),
        y=alt.Y("estado:N", title=None, sort=None),
        tooltip=[alt.Tooltip("estado:N", title="Estado"), money_tooltip("faturamento_liquido", "Faturamento (R$)"), alt.Tooltip("pedidos:Q", title="Pedidos")],
    )
    .properties(height=280)
)

cash = analysis["fluxo_caixa"][["mes_data", "entradas", "saidas_totais", "saldo_mensal"]].melt(
    id_vars="mes_data", var_name="movimento", value_name="valor"
)
cash["movimento"] = cash["movimento"].map({"entradas": "Entradas", "saidas_totais": "Saídas totais", "saldo_mensal": "Saldo mensal"})
cash_chart = (
    alt.Chart(cash)
    .mark_line(point=True, strokeWidth=2.2)
    .encode(
        x=alt.X("mes_data:T", title=None, axis=alt.Axis(format="%b/%y")),
        y=alt.Y("valor:Q", title="R$"),
        color=alt.Color("movimento:N", title=None, legend=alt.Legend(orient="bottom")),
        tooltip=[alt.Tooltip("mes_data:T", title="Mês", format="%m/%Y"), alt.Tooltip("movimento:N", title="Movimento"), money_tooltip("valor", "Valor (R$)")],
    )
    .properties(height=280)
)

row_three = st.columns(2)
with row_three[0].container(border=True, height="stretch"):
    st.subheader("Distribuição regional", icon=":material/public:")
    st.altair_chart(state_chart, width="stretch")
with row_three[1].container(border=True, height="stretch"):
    st.subheader("Fluxo mensal simplificado", icon=":material/account_balance_wallet:")
    st.altair_chart(cash_chart, width="stretch")

with st.expander("Ver resumo mensal e dados filtrados", icon=":material/table_chart:"):
    summary_view = monthly.rename(
        columns={
            "mes_label": "Mês",
            "faturamento_liquido": "Faturamento líquido",
            "lucro_bruto": "Lucro bruto",
            "despesas": "Despesas",
            "resultado_operacional": "Resultado operacional",
            "margem_percentual": "Margem bruta",
            "pedidos": "Pedidos",
        }
    )[["Mês", "Faturamento líquido", "Lucro bruto", "Despesas", "Resultado operacional", "Margem bruta", "Pedidos"]]
    st.dataframe(
        summary_view,
        hide_index=True,
        column_config={
            "Faturamento líquido": st.column_config.NumberColumn(format="R$ %.2f"),
            "Lucro bruto": st.column_config.NumberColumn(format="R$ %.2f"),
            "Despesas": st.column_config.NumberColumn(format="R$ %.2f"),
            "Resultado operacional": st.column_config.NumberColumn(format="R$ %.2f"),
            "Margem bruta": st.column_config.NumberColumn(format="percent"),
            "Pedidos": st.column_config.NumberColumn(format="%,d"),
        },
    )
    st.caption(f"{len(filtered_sales):,} linhas de vendas na seleção atual.".replace(",", "."))

st.caption("DRE e fluxo são gerenciais e simplificados, produzidos exclusivamente para demonstração. Não constituem contabilidade fiscal oficial.")
