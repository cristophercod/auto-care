"""
ui/page_schedules.py
--------------------
Tela PRÓXIMAS REVISÕES: o usuário cadastra o serviço e a data e/ou quilometragem prevista.
O sistema compara com hoje e com a km atual do veículo e mostra: Atrasada, Próxima ou No prazo.

O sistema NÃO sugere intervalos de manutenção: quem informa a data/km é o usuário.
A "margem de aviso" (dias/km) só define a partir de quando uma revisão aparece como "Próxima".
"""
import gradio as gr

from core.formatters import date_br
from core.formatters import km as fmt_km
from core.validators import ValidationError
from services import maintenances as maint_svc
from services import schedules as svc
from services import vehicles as vehicles_svc
from ui import components as ui
from ui.helpers import vehicle_dropdown_update
from ui.page import Page

HEADERS = ["Nº", "Situação", "Veículo", "Serviço", "Data prevista", "Km prevista", "Detalhe", "Observação"]
NEW_HINT = "Informe o serviço e a data e/ou a quilometragem em que ele deve ser feito."
EDIT_HINT = "Altere o que precisar e clique em «Salvar alterações». Para desistir, clique em «Cancelar»."


def _table(show_done: bool = False):
    items = svc.list_schedules(include_done=bool(show_done))
    rows = [[str(s["id"]), f'{s["status_icon"]} {s["status_label"]}', s["vehicle_label"], s["service_type"],
             date_br(s["due_date"]), fmt_km(s["due_km"]), s["reason"], s["notes"] or "—"] for s in items]
    if rows:
        text = ui.caption(f"{ui.plural(len(rows), 'revisão', 'revisões')}, das mais urgentes para as menos urgentes. "
                          "Clique em uma linha para editar, concluir ou excluir.")
    else:
        text = ui.empty_state("📅", "Nenhuma revisão planejada",
                              "Preencha o formulário acima para planejar a próxima troca de óleo, revisão ou outro serviço.")
    return {"headers": HEADERS, "data": rows}, text


def _vehicle_info(vehicle_id) -> str:
    vehicle = vehicles_svc.get_vehicle(vehicle_id)
    if vehicle is None:
        return ui.hint("Escolha o veículo para ver a quilometragem atual dele.")
    return ui.hint(f"Quilometragem atual deste veículo: {fmt_km(vehicle['current_km'])}")


def _form(s=None):
    """Valores de todos os componentes do formulário (vazio ou preenchido para edição)."""
    if s is None:
        return (None, None, None, "", "", "", _vehicle_info(None), ui.form_title("Nova revisão", NEW_HINT),
                gr.update(value="💾 Salvar revisão"), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False))
    done = bool(s["done"])
    return (s["id"], s["vehicle_id"], s["service_type"], date_br(s["due_date"]) if s["due_date"] else "",
            "" if s["due_km"] is None else str(s["due_km"]), s["notes"] or "", _vehicle_info(s["vehicle_id"]),
            ui.form_title(f"Editando revisão Nº {s['id']}", EDIT_HINT, editing=True),
            gr.update(value="💾 Salvar alterações"),
            gr.update(visible=not done),      # botão "Marcar como concluída"
            gr.update(visible=done),          # botão "Reabrir"
            gr.update(visible=True),          # botão "Excluir"
            gr.update(visible=False))         # caixa de confirmação


def build() -> Page:
    editing_id = gr.State(None)
    warn_days_now, warn_km_now = svc.get_alert_settings()

    with gr.Column(visible=False, elem_classes="page") as container:
        gr.HTML(ui.page_header("📅", "Próximas revisões",
                               "Planeje os próximos serviços e acompanhe o que está chegando ou atrasado."))
        feedback = gr.HTML("")

        with gr.Column(elem_classes="card"):
            form_title = gr.HTML(ui.form_title("Nova revisão", NEW_HINT))
            vehicle = gr.Dropdown(label="Veículo", choices=vehicles_svc.vehicle_choices(), value=None,
                                  info="Escolha o carro que vai receber o serviço.")
            vehicle_info = gr.HTML(_vehicle_info(None))
            service_type = gr.Dropdown(label="Tipo de serviço", choices=maint_svc.service_type_choices(),
                                       value=None, allow_custom_value=True,
                                       info="Escolha na lista ou digite outro tipo.")
            with gr.Row():
                due_date = gr.Textbox(label="Data prevista (opcional)", placeholder="dd/mm/aaaa", max_lines=1,
                                      info="Use a data recomendada para o seu veículo. Ex.: 15/09/2026")
                due_km = gr.Textbox(label="Quilometragem prevista (opcional)", placeholder="Ex.: 55000", max_lines=1,
                                    info="Informe a data, a quilometragem ou as duas.")
            notes = gr.Textbox(label="Observação (opcional)", placeholder="Ex.: Conforme manual do proprietário",
                               max_lines=1)
            with gr.Row(elem_classes="button-row"):
                btn_save = gr.Button("💾 Salvar revisão", variant="primary")
                btn_cancel = gr.Button("Cancelar", variant="secondary")
                btn_done = gr.Button("✅ Marcar como concluída", variant="secondary", visible=False)
                btn_reopen = gr.Button("↩️ Reabrir", variant="secondary", visible=False)
                btn_delete = gr.Button("🗑️ Excluir", variant="stop", visible=False)
            with gr.Column(visible=False, elem_classes="confirm-box") as confirm_box:
                confirm_text = gr.HTML("")
                with gr.Row(elem_classes="button-row"):
                    btn_yes = gr.Button("Sim, excluir", variant="stop")
                    btn_no = gr.Button("Não, manter", variant="secondary")

        with gr.Column(elem_classes="card"):
            gr.HTML(ui.section_title("Revisões planejadas"))
            show_done = gr.Checkbox(label="Mostrar também as concluídas", value=False)
            init_table, init_caption = _table()
            table = gr.Dataframe(value=init_table, interactive=False, wrap=True, elem_classes="data-table",
                                 label="Lista de revisões")
            caption = gr.HTML(init_caption)
            gr.HTML(ui.hint("🔴 Atrasada: a data já passou ou a quilometragem já foi atingida.  "
                            "🟡 Próxima: está dentro da margem de aviso.  🟢 No prazo: ainda há tempo."))

        with gr.Accordion("⚙️ Margem de aviso (quando uma revisão aparece como «Próxima»)", open=False):
            gr.HTML(ui.hint("É só um alerta para você. As datas e quilometragens das revisões são sempre as que você informa."))
            with gr.Row():
                warn_days = gr.Textbox(label="Avisar com quantos dias de antecedência", value=str(warn_days_now),
                                       max_lines=1, info="Padrão: 30 dias.")
                warn_km = gr.Textbox(label="Avisar com quantos km de antecedência", value=str(warn_km_now),
                                     max_lines=1, info="Padrão: 1000 km.")
            btn_save_warn = gr.Button("💾 Salvar margem de aviso", variant="primary")

    form_outputs = [editing_id, vehicle, service_type, due_date, due_km, notes, vehicle_info, form_title,
                    btn_save, btn_done, btn_reopen, btn_delete, confirm_box]
    table_outputs = [table, caption]

    def on_save(editing, vehicle_, type_, date_, km_, notes_, done_flag):
        try:
            if editing is None:
                svc.create_schedule(vehicle_, type_, date_, km_, notes_)
                title = "Revisão planejada com sucesso"
            else:
                svc.update_schedule(editing, vehicle_, type_, date_, km_, notes_)
                title = "Alterações salvas"
        except ValidationError as err:
            skip = [gr.update()] * (len(form_outputs) + len(table_outputs))
            return (ui.banner("error", "Não foi possível salvar. Corrija os itens abaixo:", err.messages), *skip)
        return (ui.banner("success", title, "Veja a situação dela na lista abaixo e no Dashboard."),
                *_form(None), *_table(done_flag))

    def on_select(evt: gr.SelectData):
        item = svc.get_schedule(int(evt.row_value[0]))
        if item is None:
            return (ui.banner("warning", "Esta revisão não existe mais", "Atualize a lista e tente de novo."),
                    *_form(None))
        return (ui.banner("info", "Revisão carregada para edição",
                          "Altere os campos e salve, ou use os botões de concluir, excluir ou cancelar."),
                *_form(item))

    def on_cancel(editing):
        text = "Edição cancelada. Nenhuma alteração foi salva." if editing else "Formulário limpo."
        return (ui.banner("info", text), *_form(None))

    def on_vehicle_change(vehicle_):
        return _vehicle_info(vehicle_)

    def change_done(editing, done_flag, new_state):
        try:
            svc.set_done(editing, new_state)
        except ValidationError as err:
            return (ui.banner("error", "Não foi possível atualizar", err.messages), *_form(None), *_table(done_flag))
        if new_state:
            banner = ui.banner("success", "Revisão marcada como concluída",
                               ["Ela saiu dos avisos do Dashboard.",
                                "Se ainda não registrou o serviço, registre na tela «Manutenções» "
                                "para ele entrar no histórico e nos gastos."])
        else:
            banner = ui.banner("success", "Revisão reaberta", "Ela voltou para a lista de pendentes.")
        return (banner, *_form(None), *_table(done_flag))

    def on_ask_delete(editing):
        item = svc.get_schedule(editing)
        if item is None:
            return gr.update(visible=False), ""
        return gr.update(visible=True), ui.banner(
            "warning", f"Excluir a revisão «{item['service_type']}»?", "Esta ação não pode ser desfeita.")

    def on_confirm_delete(editing, done_flag):
        try:
            svc.delete_schedule(editing)
        except ValidationError as err:
            return (ui.banner("error", "Não foi possível excluir", err.messages), *_form(None), *_table(done_flag))
        return (ui.banner("success", "Revisão excluída", "Ela foi removida da lista."), *_form(None), *_table(done_flag))

    def on_cancel_delete():
        return ui.banner("info", "Exclusão cancelada", "A revisão foi mantida."), gr.update(visible=False)

    def on_save_warn(days, km_margin, done_flag):
        try:
            days, km_margin = svc.save_alert_settings(days, km_margin)
        except ValidationError as err:
            return ui.banner("error", "Não foi possível salvar a margem. Corrija:", err.messages), gr.update(), gr.update()
        return (ui.banner("success", "Margem de aviso salva",
                          f"Revisões aparecem como «Próxima» com {days} dias ou {fmt_km(km_margin)} de antecedência."),
                *_table(done_flag))

    btn_save.click(on_save, [editing_id, vehicle, service_type, due_date, due_km, notes, show_done],
                   [feedback, *form_outputs, *table_outputs])
    table.select(on_select, None, [feedback, *form_outputs])
    btn_cancel.click(on_cancel, [editing_id], [feedback, *form_outputs])
    vehicle.change(on_vehicle_change, [vehicle], [vehicle_info])
    btn_done.click(lambda e, d: change_done(e, d, True), [editing_id, show_done],
                   [feedback, *form_outputs, *table_outputs])
    btn_reopen.click(lambda e, d: change_done(e, d, False), [editing_id, show_done],
                     [feedback, *form_outputs, *table_outputs])
    btn_delete.click(on_ask_delete, [editing_id], [confirm_box, confirm_text])
    btn_yes.click(on_confirm_delete, [editing_id, show_done], [feedback, *form_outputs, *table_outputs])
    btn_no.click(on_cancel_delete, None, [feedback, confirm_box])
    show_done.change(_table, [show_done], table_outputs)
    btn_save_warn.click(on_save_warn, [warn_days, warn_km, show_done], [feedback, *table_outputs])

    def refresh(current_vehicle, done_flag):
        """Ao entrar na tela: atualiza veículos, tipos, margem de aviso e a tabela (status recalculado)."""
        days, km_margin = svc.get_alert_settings()
        return (vehicle_dropdown_update(current_vehicle), gr.update(choices=maint_svc.service_type_choices()),
                str(days), str(km_margin), *_table(done_flag))

    return Page(container, refresh, [vehicle, show_done], [vehicle, service_type, warn_days, warn_km, *table_outputs])
