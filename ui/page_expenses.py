"""
ui/page_expenses.py
-------------------
Tela GASTOS: total gasto com manutenção, total por veículo e consulta por período.
Atalhos de período (Este mês, Últimos 30 dias, Este ano, Tudo) evitam digitar datas.
"""
from datetime import timedelta

import gradio as gr
import pandas as pd

from core.formatters import date_br, money, today
from core.validators import ValidationError, parse_date
from services import reports
from ui import components as ui
from ui.page import Page

HEADERS = ["Veículo", "Serviços", "Total gasto", "% do total"]
PLOT_X, PLOT_Y = "Veículo", "Total gasto (R$)"


def _apply(date_from, date_to):
    """Calcula os gastos do período e devolve (aviso, cartões, tabela, gráfico)."""
    try:
        start = parse_date(date_from, "De", required=False)
        end = parse_date(date_to, "Até", required=False)
        if start and end and start > end:
            raise ValidationError("A data «De» é depois da data «Até». Troque uma pela outra.")
    except ValidationError as err:
        return (ui.banner("error", "Confira o período informado", err.messages),
                gr.update(), gr.update(), gr.update())

    data = reports.expenses_summary(start, end)
    if start or end:
        period = f"{date_br(start) if start else 'o início'} até {date_br(end) if end else 'hoje'}"
        scope = f"Período: {period}"
    else:
        scope = "Todo o período"

    cards = ('<div class="stat-grid stat-grid-3">'
             + ui.stat_card("💰", "Total gasto", money(data["total"]), scope)
             + ui.stat_card("🔧", "Serviços realizados", str(data["services"]), "No período escolhido")
             + ui.stat_card("🧮", "Média por serviço", money(data["average"]), "Total dividido pelos serviços")
             + "</div>")
    if not data["by_vehicle"]:
        cards += ui.empty_state("🚗", "Nenhum veículo cadastrado", "Cadastre um veículo e registre manutenções para ver os gastos.")

    rows = [[v["vehicle_label"], str(v["services"]), money(v["total"]), f'{v["percent"]:.1f}%'.replace(".", ",")]
            for v in data["by_vehicle"]]
    spent = [v for v in data["by_vehicle"] if v["total"] > 0]
    frame = pd.DataFrame({PLOT_X: [v["vehicle_label"] for v in spent], PLOT_Y: [v["total"] for v in spent]})
    plot = gr.update(value=frame, visible=bool(spent))
    return "", cards, {"headers": HEADERS, "data": rows}, plot


def _shortcut(kind: str):
    """Preenche o período com um atalho e já calcula os gastos."""
    def run():
        end = today()
        if kind == "month":
            start = end.replace(day=1)
        elif kind == "30days":
            start = end - timedelta(days=30)
        elif kind == "year":
            start = end.replace(month=1, day=1)
        else:
            start, end = None, None
        start_text, end_text = (date_br(start), date_br(end)) if start else ("", "")
        return (start_text, end_text, *_apply(start_text, end_text))
    return run


def build() -> Page:
    with gr.Column(visible=False, elem_classes="page") as container:
        gr.HTML(ui.page_header("💰", "Gastos", "Veja quanto você gastou com manutenção, no total e por veículo."))
        feedback = gr.HTML("")
        with gr.Column(elem_classes="card"):
            gr.HTML(ui.section_title("Período", "Deixe em branco para ver tudo, ou use um atalho."))
            with gr.Row(elem_classes="button-row"):
                btn_month = gr.Button("Este mês", variant="secondary")
                btn_30 = gr.Button("Últimos 30 dias", variant="secondary")
                btn_year = gr.Button("Este ano", variant="secondary")
                btn_all = gr.Button("Tudo", variant="secondary")
            with gr.Row():
                date_from = gr.Textbox(label="De (opcional)", placeholder="dd/mm/aaaa", max_lines=1,
                                       info="Data inicial. Ex.: 01/01/2026")
                date_to = gr.Textbox(label="Até (opcional)", placeholder="dd/mm/aaaa", max_lines=1,
                                     info="Data final. Ex.: 31/03/2026")
            btn_apply = gr.Button("🔍 Calcular gastos", variant="primary")
        cards = gr.HTML("")
        with gr.Column(elem_classes="card"):
            gr.HTML(ui.section_title("Gastos por veículo"))
            table = gr.Dataframe(value={"headers": HEADERS, "data": []}, interactive=False, wrap=True,
                                 elem_classes="data-table", label="Total por veículo")
            plot = gr.BarPlot(value=pd.DataFrame({PLOT_X: [], PLOT_Y: []}), x=PLOT_X, y=PLOT_Y,
                              title="Total gasto por veículo (R$)", visible=False, height=300)

    outputs = [feedback, cards, table, plot]
    btn_apply.click(_apply, [date_from, date_to], outputs)
    date_from.submit(_apply, [date_from, date_to], outputs)
    date_to.submit(_apply, [date_from, date_to], outputs)
    for button, kind in ((btn_month, "month"), (btn_30, "30days"), (btn_year, "year"), (btn_all, "all")):
        button.click(_shortcut(kind), None, [date_from, date_to, *outputs])

    return Page(container, _apply, [date_from, date_to], outputs)
