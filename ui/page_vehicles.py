"""
ui/page_vehicles.py
-------------------
Tela VEÍCULOS: cadastrar, consultar, editar e excluir (com confirmação).

Fluxo de uso:
  - Formulário vazio  = modo "Novo veículo".
  - Clicar numa linha da tabela = carrega o veículo no formulário (modo "Editando").
  - Botão Cancelar sempre volta ao estado inicial sem salvar nada.
  - Excluir pede confirmação e avisa o que será apagado junto.

Comunicação: botão (Gradio) -> função Python daqui -> services/vehicles.py -> SQLite.
"""
import gradio as gr

from core.formatters import km as fmt_km
from core.formatters import plate_display, vehicle_label
from core.validators import ValidationError
from services import vehicles as svc
from ui import components as ui
from ui.page import Page

HEADERS = ["Nº", "Marca", "Modelo", "Ano", "Placa", "Quilometragem", "Combustível"]
NEW_HINT = "Preencha os dados e clique em «Salvar veículo»."
EDIT_HINT = "Altere o que precisar e clique em «Salvar alterações». Para desistir, clique em «Cancelar»."


def _table(search: str = ""):
    """Devolve (tabela, legenda) com os veículos que combinam com a busca."""
    vehicles = svc.list_vehicles(search)
    rows = [[str(v["id"]), v["brand"], v["model"], str(v["year"]), plate_display(v["plate"]),
             fmt_km(v["current_km"]), v["fuel"] or "—"] for v in vehicles]
    if rows:
        text = ui.caption(f"{ui.plural(len(rows), 'veículo', 'veículos')}. Clique em uma linha para editar.")
    elif (search or "").strip():
        text = ui.caption(f"Nenhum veículo encontrado para «{search.strip()}». Tente marca, modelo ou placa.")
    else:
        text = ui.empty_state("🚗", "Nenhum veículo cadastrado ainda",
                              "Preencha o formulário acima para cadastrar o seu primeiro carro.")
    return {"headers": HEADERS, "data": rows}, text


def _form(v=None):
    """
    Valores de TODOS os componentes do formulário, na ordem de `form_outputs`.
    v=None -> formulário vazio (novo).  v=dict -> formulário preenchido (edição).
    """
    if v is None:
        return (None, "", "", "", "", "", "Não informado",
                ui.form_title("Novo veículo", NEW_HINT),
                gr.update(value="💾 Salvar veículo"), gr.update(visible=False), gr.update(visible=False))
    label = vehicle_label(v["brand"], v["model"], v["plate"])
    return (v["id"], v["brand"], v["model"], str(v["year"]), plate_display(v["plate"]), str(v["current_km"]),
            v["fuel"] or "Não informado",
            ui.form_title(f"Editando: {label}", EDIT_HINT, editing=True),
            gr.update(value="💾 Salvar alterações"), gr.update(visible=True), gr.update(visible=False))


def build() -> Page:
    editing_id = gr.State(None)           # None = cadastrando; número = editando esse veículo

    with gr.Column(visible=False, elem_classes="page") as container:
        gr.HTML(ui.page_header("🚗", "Veículos", "Cadastre seus carros e mantenha a quilometragem em dia."))
        feedback = gr.HTML("")

        # ----- Formulário -----
        with gr.Column(elem_classes="card"):
            form_title = gr.HTML(ui.form_title("Novo veículo", NEW_HINT))
            with gr.Row():
                brand = gr.Textbox(label="Marca", placeholder="Ex.: Fiat", max_lines=1,
                                   info="Fabricante do carro.")
                model = gr.Textbox(label="Modelo", placeholder="Ex.: Uno Mille", max_lines=1,
                                   info="Nome do modelo, como no documento.")
            with gr.Row():
                year = gr.Textbox(label="Ano", placeholder="Ex.: 2018", max_lines=1, info="Ano do veículo, com 4 números.")
                plate = gr.Textbox(label="Placa", placeholder="ABC-1234 ou ABC1D23", max_lines=1,
                                   info="Aceita o modelo antigo e o Mercosul.")
            with gr.Row():
                km = gr.Textbox(label="Quilometragem atual (km)", placeholder="Ex.: 45000", max_lines=1,
                                info="O que o painel marca hoje. Só números.")
                fuel = gr.Dropdown(label="Combustível (opcional)", choices=svc.FUEL_OPTIONS,
                                   value="Não informado", info="Escolha na lista, se quiser informar.")
            with gr.Row(elem_classes="button-row"):
                btn_save = gr.Button("💾 Salvar veículo", variant="primary")
                btn_cancel = gr.Button("Cancelar", variant="secondary")
                btn_delete = gr.Button("🗑️ Excluir", variant="stop", visible=False)
            with gr.Column(visible=False, elem_classes="confirm-box") as confirm_box:
                confirm_text = gr.HTML("")
                with gr.Row(elem_classes="button-row"):
                    btn_yes = gr.Button("Sim, excluir", variant="stop")
                    btn_no = gr.Button("Não, manter", variant="secondary")

        # ----- Lista -----
        with gr.Column(elem_classes="card"):
            gr.HTML(ui.section_title("Veículos cadastrados"))
            search = gr.Textbox(label="Buscar", placeholder="Digite marca, modelo ou placa", max_lines=1)
            init_table, init_caption = _table()
            table = gr.Dataframe(value=init_table, interactive=False, wrap=True, elem_classes="data-table",
                                 label="Lista de veículos")
            caption = gr.HTML(init_caption)

    form_outputs = [editing_id, brand, model, year, plate, km, fuel, form_title, btn_save, btn_delete, confirm_box]
    table_outputs = [table, caption]

    # ----- Ações (cada função devolve valores na mesma ordem dos outputs) -----
    def on_save(editing, brand_, model_, year_, plate_, km_, fuel_, search_):
        try:
            if editing is None:
                svc.create_vehicle(brand_, model_, year_, plate_, km_, fuel_)
                message = ui.banner("success", "Veículo cadastrado com sucesso",
                                    f"{brand_.strip()} {model_.strip()} já está na lista. "
                                    "Agora você pode registrar manutenções para ele.")
            else:
                svc.update_vehicle(editing, brand_, model_, year_, plate_, km_, fuel_)
                message = ui.banner("success", "Alterações salvas",
                                    f"Os dados de {brand_.strip()} {model_.strip()} foram atualizados.")
        except ValidationError as err:
            # Erro: mostra o que corrigir e mantém tudo que o usuário digitou.
            skip = [gr.update()] * (len(form_outputs) + len(table_outputs))
            return (ui.banner("error", "Não foi possível salvar. Corrija os itens abaixo:", err.messages), *skip)
        return (message, *_form(None), *_table(search_))

    def on_select(evt: gr.SelectData):
        vehicle = svc.get_vehicle(int(evt.row_value[0]))
        if vehicle is None:
            return (ui.banner("warning", "Este veículo não existe mais", "Atualize a lista e tente de novo."),
                    *_form(None))
        return (ui.banner("info", "Veículo carregado para edição",
                          "Altere os campos e salve, ou clique em «Cancelar»."), *_form(vehicle))

    def on_cancel(editing):
        text = "Edição cancelada. Nenhuma alteração foi salva." if editing else "Formulário limpo."
        return (ui.banner("info", text), *_form(None))

    def on_ask_delete(editing):
        vehicle = svc.get_vehicle(editing)
        if vehicle is None:
            return gr.update(visible=False), ""
        done, planned = svc.count_related(editing)
        label = vehicle_label(vehicle["brand"], vehicle["model"], vehicle["plate"])
        extra = (f"Isso também apagará {ui.plural(done, 'manutenção registrada', 'manutenções registradas')} "
                 f"e {ui.plural(planned, 'revisão planejada', 'revisões planejadas')} deste veículo. ")
        return gr.update(visible=True), ui.banner("warning", f"Excluir {label}?",
                                                  extra + "Esta ação não pode ser desfeita.")

    def on_confirm_delete(editing, search_):
        try:
            svc.delete_vehicle(editing)
        except ValidationError as err:
            return (ui.banner("error", "Não foi possível excluir", err.messages), *_form(None), *_table(search_))
        return (ui.banner("success", "Veículo excluído", "Ele foi removido da lista."), *_form(None), *_table(search_))

    def on_cancel_delete():
        return ui.banner("info", "Exclusão cancelada", "O veículo foi mantido."), gr.update(visible=False)

    # ----- Ligação dos botões às funções -----
    btn_save.click(on_save, [editing_id, brand, model, year, plate, km, fuel, search],
                   [feedback, *form_outputs, *table_outputs])
    table.select(on_select, None, [feedback, *form_outputs])
    btn_cancel.click(on_cancel, [editing_id], [feedback, *form_outputs])
    btn_delete.click(on_ask_delete, [editing_id], [confirm_box, confirm_text])
    btn_yes.click(on_confirm_delete, [editing_id, search], [feedback, *form_outputs, *table_outputs])
    btn_no.click(on_cancel_delete, None, [feedback, confirm_box])
    search.change(_table, [search], table_outputs)

    return Page(container, _table, [search], table_outputs)
