"""
ui/page_maintenances.py
-----------------------
Tela MANUTENÇÕES: registrar serviços já realizados, consultar, editar e excluir.

Facilidades (Heurística 7): ao escolher o veículo, a quilometragem atual dele já é
sugerida no campo de km e a data de hoje já vem preenchida.
"""
import gradio as gr

from core.formatters import date_br, money
from core.formatters import km as fmt_km
from core.validators import ValidationError
from services import maintenances as svc
from services import vehicles as vehicles_svc
from ui import components as ui
from ui.helpers import today_br, vehicle_dropdown_update
from ui.page import Page

HEADERS = ["Nº", "Data", "Veículo", "Serviço", "Descrição", "Quilometragem", "Valor", "Oficina"]
NEW_HINT = "Preencha os dados do serviço e clique em «Salvar manutenção»."
EDIT_HINT = "Altere o que precisar e clique em «Salvar alterações». Para desistir, clique em «Cancelar»."


def _table(search: str = ""):
    items = svc.list_maintenances(search=search)
    rows = [[str(m["id"]), date_br(m["service_date"]), m["vehicle_label"], m["service_type"], m["description"],
             fmt_km(m["km"]), money(m["cost"]), m["workshop"] or "—"] for m in items]
    if rows:
        text = ui.caption(f"{ui.plural(len(rows), 'manutenção registrada', 'manutenções registradas')}. "
                          "Clique em uma linha para editar ou excluir.")
    elif (search or "").strip():
        text = ui.caption(f"Nenhum registro encontrado para «{search.strip()}».")
    else:
        text = ui.empty_state("🔧", "Nenhuma manutenção registrada",
                              "Escolha um veículo no formulário acima e registre o primeiro serviço.")
    return {"headers": HEADERS, "data": rows}, text


def _vehicle_info(vehicle_id) -> str:
    vehicle = vehicles_svc.get_vehicle(vehicle_id)
    if vehicle is None:
        return ui.hint("Escolha o veículo para ver a quilometragem atual dele.")
    return ui.hint(f"Quilometragem atual deste veículo: {fmt_km(vehicle['current_km'])}")


def _form(m=None):
    """Valores de todos os componentes do formulário (vazio ou preenchido para edição)."""
    if m is None:
        return (None, None, None, "", today_br(), "", "", "",
                _vehicle_info(None), ui.form_title("Nova manutenção", NEW_HINT),
                gr.update(value="💾 Salvar manutenção"), gr.update(visible=False), gr.update(visible=False))
    return (m["id"], m["vehicle_id"], m["service_type"], m["description"], date_br(m["service_date"]), str(m["km"]),
            f'{m["cost"]:.2f}'.replace(".", ","), m["workshop"] or "", _vehicle_info(m["vehicle_id"]),
            ui.form_title(f"Editando manutenção Nº {m['id']}", EDIT_HINT, editing=True),
            gr.update(value="💾 Salvar alterações"), gr.update(visible=True), gr.update(visible=False))


def build() -> Page:
    editing_id = gr.State(None)

    with gr.Column(visible=False, elem_classes="page") as container:
        gr.HTML(ui.page_header("🔧", "Manutenções", "Registre os serviços que você já fez nos seus veículos."))
        feedback = gr.HTML("")

        with gr.Column(elem_classes="card"):
            form_title = gr.HTML(ui.form_title("Nova manutenção", NEW_HINT))
            vehicle = gr.Dropdown(label="Veículo", choices=vehicles_svc.vehicle_choices(), value=None,
                                  info="Escolha o carro que recebeu o serviço. Cadastre veículos na tela «Veículos».")
            vehicle_info = gr.HTML(_vehicle_info(None))
            with gr.Row():
                service_type = gr.Dropdown(label="Tipo de manutenção", choices=svc.service_type_choices(),
                                           value=None, allow_custom_value=True,
                                           info="Escolha na lista ou digite outro tipo.")
                date = gr.Textbox(label="Data da manutenção", value=today_br(), max_lines=1,
                                  info="Formato dia/mês/ano. Ex.: 15/03/2026")
            description = gr.Textbox(label="Descrição do serviço", lines=2, max_lines=3,
                                     placeholder="Ex.: Óleo 5W30 sintético e filtro de óleo",
                                     info="Conte em poucas palavras o que foi feito.")
            with gr.Row():
                km = gr.Textbox(label="Quilometragem no serviço (km)", placeholder="Ex.: 45000", max_lines=1,
                                info="O que o painel marcava no dia. Só números.")
                cost = gr.Textbox(label="Valor gasto (R$)", placeholder="Ex.: 350,50", max_lines=1,
                                  info="Some peças e mão de obra. Digite 0 se foi gratuito.")
            workshop = gr.Textbox(label="Oficina (opcional)", placeholder="Ex.: Auto Center Silva", max_lines=1)
            with gr.Row(elem_classes="button-row"):
                btn_save = gr.Button("💾 Salvar manutenção", variant="primary")
                btn_cancel = gr.Button("Cancelar", variant="secondary")
                btn_delete = gr.Button("🗑️ Excluir", variant="stop", visible=False)
            with gr.Column(visible=False, elem_classes="confirm-box") as confirm_box:
                confirm_text = gr.HTML("")
                with gr.Row(elem_classes="button-row"):
                    btn_yes = gr.Button("Sim, excluir", variant="stop")
                    btn_no = gr.Button("Não, manter", variant="secondary")

        with gr.Column(elem_classes="card"):
            gr.HTML(ui.section_title("Manutenções registradas"))
            search = gr.Textbox(label="Buscar", placeholder="Digite o serviço, a descrição ou a oficina",
                                max_lines=1)
            init_table, init_caption = _table()
            table = gr.Dataframe(value=init_table, interactive=False, wrap=True, elem_classes="data-table",
                                 label="Lista de manutenções")
            caption = gr.HTML(init_caption)

    form_outputs = [editing_id, vehicle, service_type, description, date, km, cost, workshop, vehicle_info,
                    form_title, btn_save, btn_delete, confirm_box]
    table_outputs = [table, caption]

    def on_save(editing, vehicle_, type_, description_, date_, km_, cost_, workshop_, search_):
        try:
            if editing is None:
                result = svc.create_maintenance(vehicle_, type_, description_, date_, km_, cost_, workshop_)
                title = "Manutenção registrada com sucesso"
            else:
                result = svc.update_maintenance(editing, vehicle_, type_, description_, date_, km_, cost_,
                                                workshop_)
                title = "Alterações salvas"
        except ValidationError as err:
            skip = [gr.update()] * (len(form_outputs) + len(table_outputs))
            return (ui.banner("error", "Não foi possível salvar. Corrija os itens abaixo:", err.messages), *skip)
        details = ["Ela já aparece no Histórico e entra no total de Gastos."]
        if result["km_updated"]:
            details.append(f"A quilometragem atual do veículo foi atualizada para {fmt_km(result['km'])}.")
        return (ui.banner("success", title, details), *_form(None), *_table(search_))

    def on_select(evt: gr.SelectData):
        item = svc.get_maintenance(int(evt.row_value[0]))
        if item is None:
            return (ui.banner("warning", "Este registro não existe mais", "Atualize a lista e tente de novo."),
                    *_form(None))
        return (ui.banner("info", "Registro carregado para edição",
                          "Altere os campos e salve, ou clique em «Cancelar»."), *_form(item))

    def on_cancel(editing):
        text = "Edição cancelada. Nenhuma alteração foi salva." if editing else "Formulário limpo."
        return (ui.banner("info", text), *_form(None))

    def on_vehicle_change(vehicle_, editing, km_):
        """Mostra a km atual do veículo e, se o campo km estiver vazio, já sugere esse valor."""
        info = _vehicle_info(vehicle_)
        current = vehicles_svc.get_vehicle(vehicle_)
        if current and editing is None and not (km_ or "").strip():
            return info, gr.update(value=str(current["current_km"]))
        return info, gr.update()

    def on_ask_delete(editing):
        item = svc.get_maintenance(editing)
        if item is None:
            return gr.update(visible=False), ""
        text = (f"{item['service_type']} de {date_br(item['service_date'])} "
                f"({money(item['cost'])}) será removida do histórico e dos gastos. Esta ação não pode ser desfeita.")
        return gr.update(visible=True), ui.banner("warning", "Excluir este registro?", text)

    def on_confirm_delete(editing, search_):
        try:
            svc.delete_maintenance(editing)
        except ValidationError as err:
            return (ui.banner("error", "Não foi possível excluir", err.messages), *_form(None), *_table(search_))
        return (ui.banner("success", "Registro excluído", "Ele saiu do histórico e do total de gastos."),
                *_form(None), *_table(search_))

    def on_cancel_delete():
        return ui.banner("info", "Exclusão cancelada", "O registro foi mantido."), gr.update(visible=False)

    btn_save.click(on_save, [editing_id, vehicle, service_type, description, date, km, cost, workshop, search],
                   [feedback, *form_outputs, *table_outputs])
    table.select(on_select, None, [feedback, *form_outputs])
    btn_cancel.click(on_cancel, [editing_id], [feedback, *form_outputs])
    vehicle.change(on_vehicle_change, [vehicle, editing_id, km], [vehicle_info, km])
    btn_delete.click(on_ask_delete, [editing_id], [confirm_box, confirm_text])
    btn_yes.click(on_confirm_delete, [editing_id, search], [feedback, *form_outputs, *table_outputs])
    btn_no.click(on_cancel_delete, None, [feedback, confirm_box])
    search.change(_table, [search], table_outputs)

    def refresh(current_vehicle, search_):
        """Ao entrar na tela: atualiza a lista de veículos, os tipos de serviço e a tabela."""
        return (vehicle_dropdown_update(current_vehicle), gr.update(choices=svc.service_type_choices()),
                *_table(search_))

    return Page(container, refresh, [vehicle, search], [vehicle, service_type, *table_outputs])
