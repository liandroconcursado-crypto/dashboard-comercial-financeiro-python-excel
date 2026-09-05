"""Relatório executivo em Markdown gerado a partir dos resultados."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .charts import format_brl


def _pct(value: float) -> str:
    return f"{value:.1%}".replace(".", ",")


def generate_executive_report(
    analysis: dict[str, Any],
    audits: dict[str, dict[str, int]],
    output_path: Path,
) -> Path:
    """Escreve um resumo executivo sem atribuir causalidade aos dados."""
    kpis = analysis["kpis"]
    monthly: pd.DataFrame = analysis["mensal"]
    best_revenue = monthly.loc[monthly["faturamento_liquido"].idxmax()]
    best_result = monthly.loc[monthly["resultado_operacional"].idxmax()]
    worst_result = monthly.loc[monthly["resultado_operacional"].idxmin()]
    growth = monthly["crescimento_mensal"].dropna()
    positive_months = int((monthly["resultado_operacional"] > 0).sum())

    observations = [
        f"O faturamento líquido acumulado foi de **{format_brl(kpis['faturamento_liquido'])}**.",
        f"O lucro bruto atingiu **{format_brl(kpis['lucro_bruto'])}**, com margem bruta consolidada de **{_pct(kpis['margem_media'])}**.",
        f"As despesas operacionais totalizaram **{format_brl(kpis['despesas_totais'])}** e o resultado operacional simplificado foi de **{format_brl(kpis['resultado_operacional'])}**.",
        f"O maior faturamento mensal ocorreu em **{best_revenue['mes_label']}**, com **{format_brl(best_revenue['faturamento_liquido'])}**.",
        f"O maior resultado operacional mensal ocorreu em **{best_result['mes_label']}**; o menor, em **{worst_result['mes_label']}**.",
        f"Houve resultado operacional positivo em **{positive_months} de {len(monthly)} meses**.",
    ]
    if not growth.empty:
        observations.append(f"A variação do último mês em relação ao anterior foi de **{_pct(float(growth.iloc[-1]))}**.")

    report = f"""# Relatório executivo — Dashboard Comercial e Financeiro

> Todos os dados utilizados são fictícios e foram gerados exclusivamente para demonstração.

## Resumo dos resultados

Este relatório consolida a operação simulada de janeiro a dezembro de 2025. Os valores foram produzidos por um pipeline automatizado de geração, validação, limpeza, transformação e análise de dados.

## Principais indicadores

| Indicador | Resultado |
|---|---:|
| Faturamento bruto | {format_brl(kpis['faturamento_total'])} |
| Descontos concedidos | {format_brl(kpis['descontos_totais'])} |
| Faturamento líquido | {format_brl(kpis['faturamento_liquido'])} |
| Lucro bruto | {format_brl(kpis['lucro_bruto'])} |
| Margem bruta | {_pct(kpis['margem_media'])} |
| Despesas operacionais | {format_brl(kpis['despesas_totais'])} |
| Resultado operacional simplificado | {format_brl(kpis['resultado_operacional'])} |
| Pedidos | {kpis['numero_pedidos']:,} |
| Ticket médio | {format_brl(kpis['ticket_medio'])} |
| Unidades vendidas | {kpis['unidades_vendidas']:,} |

## Destaques observados nos dados

{chr(10).join(f'- {item}' for item in observations)}

- O produto com mais unidades vendidas foi **{kpis['produto_mais_vendido']}**.
- A categoria com maior faturamento líquido foi **{kpis['categoria_maior_faturamento']}**.
- O vendedor com maior faturamento líquido foi **{kpis['melhor_vendedor']}**.
- O estado com maior faturamento líquido foi **{kpis['estado_maior_faturamento']}**.

## Tendências observadas

- A série mensal apresenta variação de faturamento ao longo do ano; os valores exatos estão na planilha e no dashboard.
- A comparação entre lucro bruto e despesas mostra em quais meses a operação simulada gerou resultado operacional positivo ou negativo.
- A concentração por categoria, vendedor, produto e estado está documentada nos rankings e gráficos, sem atribuição automática de causa.

## Exemplos de interpretações gerenciais

As interpretações abaixo são hipóteses de trabalho, não conclusões causais:

- Investigar os meses com menor resultado operacional para separar efeito de volume, mix de produtos, descontos, custos e despesas.
- Verificar se a concentração nas categorias e regiões líderes representa oportunidade de expansão ou dependência comercial.
- Comparar vendedores com carteiras e regiões semelhantes antes de definir metas ou ações de capacitação.
- Avaliar a evolução do ticket médio em conjunto com unidades, margem e descontos para evitar decisões baseadas apenas em faturamento.

## Qualidade e tratamento dos dados

| Base | Linhas recebidas | Duplicatas removidas | Datas inválidas removidas | Linhas finais |
|---|---:|---:|---:|---:|
| Vendas | {audits['vendas']['linhas_recebidas']} | {audits['vendas']['duplicatas_removidas']} | {audits['vendas']['datas_invalidas_removidas']} | {audits['vendas']['linhas_finais']} |
| Despesas | {audits['despesas']['linhas_recebidas']} | {audits['despesas']['duplicatas_removidas']} | {audits['despesas']['datas_invalidas_removidas']} | {audits['despesas']['linhas_finais']} |

O tratamento também padronizou textos, converteu moedas e percentuais, corrigiu tipos numéricos e preencheu ausências não críticas com regras explícitas.

## Limitação conceitual

A DRE apresentada é uma **DRE gerencial simplificada para fins demonstrativos**. Ela não inclui tributos, regime de competência completo, depreciação, resultado financeiro ou outras exigências de contabilidade fiscal. O fluxo de caixa também é uma visão simplificada baseada em entradas de receita líquida e saídas de CMV e despesas operacionais.
"""
    report = report.replace(f"{kpis['numero_pedidos']:,}", f"{kpis['numero_pedidos']:,}".replace(",", "."))
    report = report.replace(f"{kpis['unidades_vendidas']:,}", f"{kpis['unidades_vendidas']:,}".replace(",", "."))
    output_path.write_text(report, encoding="utf-8")
    return output_path
