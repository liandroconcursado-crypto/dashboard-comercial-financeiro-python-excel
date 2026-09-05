"""Geração das imagens de portfólio em alta resolução."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from .config import PORTFOLIO_DIR, ensure_directories


NAVY = "#0B172A"
NAVY_LIGHT = "#13263E"
CYAN = "#22D3EE"
BLUE = "#38BDF8"
GREEN = "#34D399"
ORANGE = "#FB923C"
RED = "#FB7185"
WHITE = "#F8FAFC"
MUTED = "#A8B3C5"
GRID = "#334155"


def format_brl(value: float, compact: bool = False) -> str:
    """Formata valores em real sem depender da localidade do sistema."""
    if compact:
        absolute = abs(value)
        if absolute >= 1_000_000:
            return f"R$ {value / 1_000_000:.1f} mi".replace(".", ",")
        if absolute >= 1_000:
            return f"R$ {value / 1_000:.0f} mil".replace(".", ",")
    formatted = f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted


def _money_axis(value: float, _position: int) -> str:
    if abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:.1f} mi".replace(".", ",")
    return f"R$ {value / 1_000:.0f} mil".replace(".", ",")


def _style_axis(ax: plt.Axes, *, grid_axis: str = "y") -> None:
    ax.set_facecolor(NAVY_LIGHT)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.7, alpha=0.55)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.title.set_color(WHITE)
    ax.title.set_fontweight("bold")
    ax.title.set_fontsize(12)


def _save(fig: plt.Figure, path: Path) -> None:
    fig.savefig(path, dpi=220, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


def _add_card(fig: plt.Figure, rect: list[float], label: str, value: str, color: str, detail: str = "") -> None:
    ax = fig.add_axes(rect)
    ax.set_facecolor(NAVY_LIGHT)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(GRID)
        spine.set_linewidth(1.0)
    ax.text(0.06, 0.76, label.upper(), color=MUTED, fontsize=9, fontweight="bold", transform=ax.transAxes)
    ax.text(0.06, 0.38, value, color=WHITE, fontsize=18, fontweight="bold", transform=ax.transAxes)
    if detail:
        ax.text(0.06, 0.10, detail, color=color, fontsize=9, transform=ax.transAxes)
    ax.plot([0.0, 1.0], [0.98, 0.98], color=color, linewidth=3, transform=ax.transAxes, clip_on=False)


def create_dashboard_image(analysis: dict[str, Any], output_path: Path) -> None:
    monthly = analysis["mensal"]
    rankings = analysis["rankings"]
    kpis = analysis["kpis"]
    fig = plt.figure(figsize=(16, 10), facecolor=NAVY)
    fig.text(0.045, 0.965, "Dashboard comercial e financeiro", color=WHITE, fontsize=24, fontweight="bold")
    fig.text(0.045, 0.936, "Visão executiva | janeiro a dezembro de 2025 | dados fictícios", color=MUTED, fontsize=10)

    cards = [
        ("Faturamento líquido", format_brl(kpis["faturamento_liquido"], True), CYAN),
        ("Lucro bruto", format_brl(kpis["lucro_bruto"], True), GREEN),
        ("Margem bruta", f"{kpis['margem_media']:.1%}".replace(".", ","), BLUE),
        ("Despesas", format_brl(kpis["despesas_totais"], True), ORANGE),
        ("Pedidos", f"{kpis['numero_pedidos']:,}".replace(",", "."), CYAN),
        ("Ticket médio", format_brl(kpis["ticket_medio"]), GREEN),
    ]
    card_width = 0.142
    for index, (label, value, color) in enumerate(cards):
        _add_card(fig, [0.045 + index * 0.155, 0.80, card_width, 0.11], label, value, color)

    grid = fig.add_gridspec(2, 2, left=0.045, right=0.965, bottom=0.07, top=0.75, hspace=0.34, wspace=0.25)
    ax1 = fig.add_subplot(grid[0, 0])
    ax2 = fig.add_subplot(grid[0, 1])
    ax3 = fig.add_subplot(grid[1, 0])
    ax4 = fig.add_subplot(grid[1, 1])
    for ax in (ax1, ax2, ax3, ax4):
        _style_axis(ax)

    x = np.arange(len(monthly))
    ax1.plot(x, monthly["faturamento_liquido"], color=CYAN, linewidth=2.6, marker="o", markersize=4)
    ax1.fill_between(x, monthly["faturamento_liquido"], color=CYAN, alpha=0.08)
    ax1.set_title("Faturamento líquido mensal", loc="left", pad=12, color=WHITE)
    ax1.set_xticks(x, monthly["mes_label"])
    ax1.tick_params(axis="x", rotation=35)
    ax1.yaxis.set_major_formatter(FuncFormatter(_money_axis))

    ax2.plot(x, monthly["lucro_bruto"], color=GREEN, linewidth=2.4, marker="o", markersize=4, label="Lucro bruto")
    ax2.plot(x, monthly["resultado_operacional"], color=ORANGE, linewidth=2.1, marker="o", markersize=4, label="Resultado operacional")
    ax2.axhline(0, color=MUTED, linewidth=0.8)
    ax2.set_title("Lucro e resultado operacional", loc="left", pad=12, color=WHITE)
    ax2.set_xticks(x, monthly["mes_label"])
    ax2.tick_params(axis="x", rotation=35)
    ax2.yaxis.set_major_formatter(FuncFormatter(_money_axis))
    legend = ax2.legend(frameon=False, fontsize=8, loc="upper left")
    for text in legend.get_texts():
        text.set_color(MUTED)

    categories = rankings["categorias"].sort_values("faturamento_liquido")
    ax3.barh(categories["categoria"], categories["faturamento_liquido"], color=BLUE, alpha=0.9)
    ax3.set_title("Faturamento por categoria", loc="left", pad=12, color=WHITE)
    ax3.xaxis.set_major_formatter(FuncFormatter(_money_axis))
    ax3.grid(axis="x", color=GRID, linewidth=0.7, alpha=0.55)
    ax3.grid(axis="y", visible=False)

    products = rankings["produtos"].head(8).sort_values("unidades_vendidas")
    ax4.barh(products["produto"], products["unidades_vendidas"], color=ORANGE, alpha=0.9)
    ax4.set_title("Produtos com mais unidades vendidas", loc="left", pad=12, color=WHITE)
    ax4.tick_params(axis="y", labelsize=8)
    ax4.grid(axis="x", color=GRID, linewidth=0.7, alpha=0.55)
    ax4.grid(axis="y", visible=False)

    _save(fig, output_path)


def create_indicators_image(analysis: dict[str, Any], output_path: Path) -> None:
    kpis = analysis["kpis"]
    fig = plt.figure(figsize=(16, 9), facecolor=NAVY)
    fig.text(0.05, 0.93, "Indicadores gerenciais", color=WHITE, fontsize=25, fontweight="bold")
    fig.text(0.05, 0.895, "Resumo anual da operação simulada | dados fictícios", color=MUTED, fontsize=10)
    cards = [
        ("Receita bruta", format_brl(kpis["faturamento_total"], True), CYAN),
        ("Receita líquida", format_brl(kpis["faturamento_liquido"], True), BLUE),
        ("Lucro bruto", format_brl(kpis["lucro_bruto"], True), GREEN),
        ("Resultado operacional", format_brl(kpis["resultado_operacional"], True), GREEN if kpis["resultado_operacional"] >= 0 else RED),
        ("Margem bruta", f"{kpis['margem_media']:.1%}".replace(".", ","), BLUE),
        ("Despesas operacionais", format_brl(kpis["despesas_totais"], True), ORANGE),
        ("Pedidos", f"{kpis['numero_pedidos']:,}".replace(",", "."), CYAN),
        ("Ticket médio", format_brl(kpis["ticket_medio"]), GREEN),
        ("Unidades vendidas", f"{kpis['unidades_vendidas']:,}".replace(",", "."), CYAN),
        ("Produto líder", kpis["produto_mais_vendido"], ORANGE),
        ("Melhor vendedor", kpis["melhor_vendedor"], GREEN),
        ("Estado líder", kpis["estado_maior_faturamento"], BLUE),
    ]
    for index, (label, value, color) in enumerate(cards):
        row, col = divmod(index, 4)
        _add_card(fig, [0.05 + col * 0.237, 0.64 - row * 0.245, 0.215, 0.19], label, value, color)
    fig.text(0.05, 0.06, "Indicadores calculados automaticamente a partir das bases tratadas.", color=MUTED, fontsize=9)
    _save(fig, output_path)


def create_dre_image(analysis: dict[str, Any], output_path: Path) -> None:
    kpis = analysis["kpis"]
    labels = ["Receita bruta", "Descontos", "Receita líquida", "CMV", "Lucro bruto", "Despesas", "Resultado operacional"]
    values = np.array(
        [
            kpis["faturamento_total"],
            -kpis["descontos_totais"],
            kpis["faturamento_liquido"],
            -kpis["custo_total"],
            kpis["lucro_bruto"],
            -kpis["despesas_totais"],
            kpis["resultado_operacional"],
        ]
    )
    colors = [CYAN, ORANGE, BLUE, ORANGE, GREEN, ORANGE, GREEN if values[-1] >= 0 else RED]
    fig, ax = plt.subplots(figsize=(16, 9), facecolor=NAVY)
    _style_axis(ax, grid_axis="x")
    ax.barh(labels[::-1], values[::-1], color=colors[::-1], alpha=0.92)
    ax.axvline(0, color=WHITE, linewidth=0.9, alpha=0.7)
    ax.xaxis.set_major_formatter(FuncFormatter(_money_axis))
    fig.text(0.08, 0.95, "DRE gerencial simplificada", color=WHITE, fontsize=24, fontweight="bold")
    fig.text(0.08, 0.915, "Demonstração conceitual para fins de análise — não representa contabilidade fiscal oficial.", color=MUTED, fontsize=10)
    max_abs = max(abs(values))
    for idx, value in enumerate(values[::-1]):
        text_x = value + max_abs * 0.015 if value >= 0 else value * 0.95
        ax.text(text_x, idx, format_brl(value, True), color=WHITE, va="center", ha="left", fontsize=9, fontweight="bold")
    fig.subplots_adjust(left=0.19, right=0.95, bottom=0.10, top=0.86)
    _save(fig, output_path)


def create_cash_flow_image(analysis: dict[str, Any], output_path: Path) -> None:
    cash = analysis["fluxo_caixa"]
    x = np.arange(len(cash))
    fig, ax = plt.subplots(figsize=(16, 9), facecolor=NAVY)
    _style_axis(ax)
    width = 0.34
    ax.bar(x - width / 2, cash["entradas"], width=width, color=CYAN, label="Entradas")
    ax.bar(x + width / 2, cash["saidas_totais"], width=width, color=ORANGE, label="Saídas totais")
    ax.plot(x, cash["saldo_mensal"], color=GREEN, marker="o", linewidth=2.5, label="Saldo mensal")
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.set_xticks(x, cash["mes_label"])
    fig.text(0.07, 0.95, "Fluxo de caixa mensal simplificado", color=WHITE, fontsize=24, fontweight="bold")
    fig.text(0.07, 0.915, "Entradas – saídas (CMV + despesas) = saldo mensal | dados fictícios", color=MUTED, fontsize=10)
    ax.yaxis.set_major_formatter(FuncFormatter(_money_axis))
    legend = ax.legend(frameon=False, loc="upper left", ncols=3)
    for text in legend.get_texts():
        text.set_color(MUTED)
    fig.subplots_adjust(left=0.08, right=0.96, bottom=0.12, top=0.86)
    _save(fig, output_path)


def create_sales_analysis_image(analysis: dict[str, Any], output_path: Path) -> None:
    rankings = analysis["rankings"]
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), facecolor=NAVY)
    fig.suptitle("Análise de vendas", color=WHITE, fontsize=24, fontweight="bold", x=0.06, ha="left", y=0.97)
    fig.text(0.06, 0.915, "Categorias, vendedores, produtos e distribuição regional | dados fictícios", color=MUTED, fontsize=10)
    for ax in axes.flat:
        _style_axis(ax, grid_axis="x")

    categories = rankings["categorias"].sort_values("faturamento_liquido")
    axes[0, 0].barh(categories["categoria"], categories["faturamento_liquido"], color=BLUE)
    axes[0, 0].set_title("Faturamento por categoria", loc="left", color=WHITE)
    axes[0, 0].xaxis.set_major_formatter(FuncFormatter(_money_axis))

    sellers = rankings["vendedores"].sort_values("faturamento_liquido")
    axes[0, 1].barh(sellers["vendedor"], sellers["faturamento_liquido"], color=GREEN)
    axes[0, 1].set_title("Faturamento por vendedor", loc="left", color=WHITE)
    axes[0, 1].xaxis.set_major_formatter(FuncFormatter(_money_axis))

    products = rankings["produtos"].head(10).sort_values("unidades_vendidas")
    axes[1, 0].barh(products["produto"], products["unidades_vendidas"], color=ORANGE)
    axes[1, 0].set_title("Top 10 produtos por unidades", loc="left", color=WHITE)

    states = rankings["estados"].sort_values("faturamento_liquido")
    axes[1, 1].barh(states["estado"], states["faturamento_liquido"], color=CYAN)
    axes[1, 1].set_title("Distribuição regional", loc="left", color=WHITE)
    axes[1, 1].xaxis.set_major_formatter(FuncFormatter(_money_axis))

    fig.subplots_adjust(left=0.11, right=0.97, bottom=0.07, top=0.875, hspace=0.32, wspace=0.26)
    _save(fig, output_path)


def generate_portfolio_images(analysis: dict[str, Any]) -> list[Path]:
    """Gera as cinco imagens solicitadas e retorna seus caminhos."""
    ensure_directories()
    outputs = [
        PORTFOLIO_DIR / "01_dashboard.png",
        PORTFOLIO_DIR / "02_indicadores.png",
        PORTFOLIO_DIR / "03_dre.png",
        PORTFOLIO_DIR / "04_fluxo_caixa.png",
        PORTFOLIO_DIR / "05_analise_vendas.png",
    ]
    creators = [
        create_dashboard_image,
        create_indicators_image,
        create_dre_image,
        create_cash_flow_image,
        create_sales_analysis_image,
    ]
    for creator, path in zip(creators, outputs, strict=True):
        creator(analysis, path)
    return outputs
