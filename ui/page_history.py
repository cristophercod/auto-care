"""
ui/page_history.py
------------------
Tela HISTÓRICO: todas as manutenções realizadas, com filtros por veículo, tipo de serviço,
período e busca por texto. Somente consulta (para editar, use a tela Manutenções).
"""
import gradio as gr

from core.formatters import date_br, money
from core.formatters import km as fmt_km
from core.validators import ValidationError, parse_date
from services import maintenances as svc
from services import vehicles as vehicles_svc
from ui import components as ui
from ui.helpers import ALL_TYPES, ALL_VEHICLES, vehicle_dropdown_update
from ui.page import Page

HEADERS = ["Data", "Veículo", "Serviço", "Descrição", "Quilometragem", "Valor", "Oficina"]


def _type_choices():
    return [ALL_TYPES] + svc.recorded_service_types()


def _apply(vehicle_id, service_type, date_from, date_to, search):
    """Aplica os filtros e devolve (aviso, resumo, tabela)."""
    try:
        start = parse_date(date_from, "De", required=False)
        end = parse_date(date_to, "Até", required=False)
        if start and end and start > end:
            raise ValidationError("A data «De» é depois da data «Até». Troque uma pela outra.")
    except ValidationError as err:
        return (ui.banner("error", "Confira o período informado", err.messages), gr.update(), gr.update())

    items = svc.list_maintenances(
        vehicle_id=vehicle_id if vehicle_id not in (None, ALL_VEHICLES) else None,
        service_type=None if service_type in (None, ALL_TYPES) else service_type,
        date_from=start, date_to=end, search=search)
    rows = [[date_br(m["service_date"]), m["vehicle_label"], m["service_type"], m["description"],
             fmt_km(m["km"]), money(m["cost"]), m["workshop"] or "—"] for m in items]
    total = sum(m["cost"] for m in items)

    if rows:
        summary = ('<div class="summary-bar">'
                   f'<span><strong>{ui.plural(len(rows), "serviço", "serviços")}</strong> encontrados</span>'
                   f'<span>Total: <strong>{ui.esc(money(total))}</strong></span></div>')
    else:
        has_any = bool(svc.list_maintenances())
        summary = ui.empty_state(
            "📋", "Nenhum serviço encontrado" if has_any else "Ainda não há manutenções",
            "Tente remover algum filtro." if has_any else "Registre o primeiro serviço na tela «Manutenções».")
    return "", summary, {"headers": HEADERS, "data": rows}


def build() -> Page:
    with gr.Column(visible=False, elem_classes="page") as container:
        gr.HTML(ui.page_header("📋", "Histórico", "Consulte tudo o que já foi feito nos seus veículos."))
        feedback = gr.HTML("")
        with gr.Column(elem_classes="card"):
            gr.HTML(ui.section_title("Filtros", "A lista se atualiza ao escolher veículo ou serviço."))
            with gr.Row():
                vehicle = gr.Dropdown(label="Veículo", choices=[("Todos os veículos", ALL_VEHICLES)]
                                      + vehicles_svc.vehicle_choices(), value=ALL_VEHICLES)
                service_type = gr.Dropdown(label="Tipo de serviço", choices=_type_choices(), value=ALL_TYPES)
            with gr.Row():
                date_from = gr.Textbox(label="De (opcional)", placeholder="dd/mm/aaaa", max_lines=1,
                                       info="Data inicial do período.")
                date_to = gr.Textbox(label="Até (opcional)", placeholder="dd/mm/aaaa", max_lines=1,
                                     info="Data final do período.")
            search = gr.Textbox(label="Buscar", placeholder="Digite parte da descrição ou da oficina", max_lines=1)
            with gr.Row(elem_classes="button-row"):
                btn_apply = gr.Button("🔍 Aplicar filtros", variant="primary")
                btn_clear = gr.Button("Limpar filtros", variant="secondary")
        with gr.Column(elem_classes="card"):
            summary = gr.HTML("")
            table = gr.Dataframe(value={"headers": HEADERS, "data": []}, interactive=False, wrap=True,
                                 elem_classes="data-table", label="Histórico de manutenções")

    filters = [vehicle, service_type, date_from, date_to, search]
    outputs = [feedback, summary, table]

    def on_clear():
        return (ALL_VEHICLES, ALL_TYPES, "", "", "", *_apply(ALL_VEHICLES, ALL_TYPES, "", "", ""))

    btn_apply.click(_apply, filters, outputs)
    vehicle.change(_apply, filters, outputs)
    service_type.change(_apply, filters, outputs)
    date_from.submit(_apply, filters, outputs)
    date_to.submit(_apply, filters, outputs)
    search.submit(_apply, filters, outputs)
    btn_clear.click(on_clear, None, [*filters, *outputs])

    def refresh(current_vehicle, current_type, start, end, text):
        """Ao entrar na tela: recarrega as opções dos filtros e aplica os filtros atuais."""
        types = _type_choices()
        type_update = gr.update(choices=types, value=current_type if current_type in types else ALL_TYPES)
        selected_type = current_type if current_type in types else ALL_TYPES
        vehicle_update = vehicle_dropdown_update(current_vehicle, with_all=True)
        return (vehicle_update, type_update, *_apply(vehicle_update["value"], selected_type, start, end, text))

    return Page(container, refresh, filters, [vehicle, service_type, *outputs])
