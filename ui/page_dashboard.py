"""
ui/page_dashboard.py
--------------------
Tela inicial: visão geral (cartões de indicadores) + próximas manutenções com destaque
para o que está atrasado ou perto de vencer. Os números vêm do banco a cada vez
que a tela é aberta.
"""
import gradio as gr

from core.formatters import date_br, money, today
from services import reports
from ui import components as ui
from ui.page import Page


def _render():
    data = reports.dashboard_summary()

    # Cartão de alertas: muda de cor conforme a gravidade (vermelho > amarelo > verde).
    if data["overdue"]:
        alert_tone, alert_value = "tone-danger", str(data["overdue"] + data["soon"])
        alert_hint = f"{ui.plural(data['overdue'], 'atrasada', 'atrasadas')}, {ui.plural(data['soon'], 'próxima', 'próximas')}"
    elif data["soon"]:
        alert_tone, alert_value = "tone-warning", str(data["soon"])
        alert_hint = f"{ui.plural(data['soon'], 'revisão próxima', 'revisões próximas')} do vencimento"
    else:
        alert_tone, alert_value = "tone-ok", "0"
        alert_hint = "Nada atrasado ou perto de vencer"

    cards = (
        '<div class="stat-grid">'
        + ui.stat_card("🚗", "Veículos cadastrados", str(data["vehicles"]), "Carros que você acompanha")
        + ui.stat_card("🔧", "Manutenções realizadas", str(data["maintenances"]), "Serviços registrados")
        + ui.stat_card("💰", "Total gasto", money(data["total_spent"]), "Soma de todos os serviços")
        + ui.stat_card("🔔", "Atenção", alert_value, alert_hint, alert_tone)
        + "</div>"
    )

    if data["vehicles"] == 0:
        schedule_html = ui.empty_state("👋", "Bem-vindo ao AutoTrack!",
                                       "Comece cadastrando seu primeiro veículo na tela «Veículos». "
                                       "Depois registre manutenções e planeje as próximas revisões.")
    else:
        schedule_html = ui.schedule_list(data["upcoming"])
    legend = ui.hint("🔴 Atrasada: a data já passou ou a quilometragem foi atingida.  "
                     "🟡 Próxima: está chegando (dentro da margem de aviso).  🟢 No prazo: ainda há tempo.")
    return cards, schedule_html + legend


def build():
    with gr.Column(visible=True, elem_classes="page") as container:
        gr.HTML(ui.page_header("🏠", "Dashboard", f"Resumo de hoje, {date_br(today())}."))
        with gr.Row(elem_classes="button-row quick-actions"):
            go_vehicle = gr.Button("➕ Novo veículo", variant="primary")
            go_maint = gr.Button("➕ Registrar manutenção", variant="secondary")
            go_sched = gr.Button("➕ Planejar revisão", variant="secondary")
        cards_html, schedule_html = _render()
        cards = gr.HTML(cards_html)
        with gr.Column(elem_classes="card"):
            gr.HTML(ui.section_title("Próximas manutenções", "As mais urgentes aparecem primeiro."))
            upcoming = gr.HTML(schedule_html)

    def refresh():
        return _render()

    page = Page(container, refresh, None, [cards, upcoming])
    return page, (go_vehicle, go_maint, go_sched)
