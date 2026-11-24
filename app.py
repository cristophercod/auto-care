"""
app.py
------
PONTO DE ENTRADA do AutoTrack. Execute com:   python app.py

O que este arquivo faz:
  1. Cria o banco de dados na primeira execução (init_db).
  2. Monta a tela: menu lateral + uma "página" para cada funcionalidade.
  3. Liga os botões do menu para mostrar só a página escolhida.
  4. Abre o sistema no navegador.
"""
import gradio as gr

from core.database import init_db
from ui import (page_dashboard, page_expenses, page_help, page_history, page_maintenances, page_schedules,
                page_vehicles)
from ui.styles import CSS, FORCE_LIGHT_JS, THEME

# (ícone, nome no menu) na mesma ordem das páginas criadas abaixo
MENU = [("🏠", "Dashboard"), ("🚗", "Veículos"), ("🔧", "Manutenções"), ("📅", "Próximas revisões"),
        ("📋", "Histórico"), ("💰", "Gastos"), ("❓", "Ajuda")]

BRAND_HTML = """
<div class="brand">
  <div class="brand-logo">🚘</div>
  <div><div class="brand-name">AutoCare</div><div class="brand-sub">Manutenção veicular</div></div>
</div>
"""
TIP_HTML = '<div class="sidebar-tip">💡 Dica: nas tabelas, clique em uma linha para editar ou excluir.</div>'


def build_app() -> gr.Blocks:
    init_db()                                   # cria o banco e as tabelas se ainda não existirem
    with gr.Blocks(title="AutoTrack — Controle de manutenção veicular") as demo:
        with gr.Row(elem_id="layout"):
            # ----- Menu lateral (igual em todas as telas) -----
            with gr.Column(elem_id="sidebar", scale=0, min_width=260):
                gr.HTML(BRAND_HTML)
                nav_buttons = [
                    gr.Button(f"{icon}  {name}", elem_classes=["nav-btn", "nav-active"] if i == 0 else ["nav-btn"])
                    for i, (icon, name) in enumerate(MENU)
                ]
                gr.HTML(TIP_HTML)

            # ----- Área de conteúdo: uma página por funcionalidade -----
            with gr.Column(elem_id="main", scale=1):
                dashboard, quick_buttons = page_dashboard.build()
                pages = [
                    dashboard,
                    page_vehicles.build(),
                    page_maintenances.build(),
                    page_schedules.build(),
                    page_history.build(),
                    page_expenses.build(),
                    page_help.build(),
                ]

        containers = [p.container for p in pages]

        def make_navigation(index):
            """Mostra só a página `index` e destaca o botão ativo no menu."""
            def navigate():
                shown = [gr.update(visible=(i == index)) for i in range(len(pages))]
                active = [gr.update(elem_classes=["nav-btn", "nav-active"] if i == index else ["nav-btn"])
                          for i in range(len(pages))]
                return shown + active
            return navigate

        def connect(button, index):
            """Ao clicar: troca de página e depois recarrega os dados dela (veículos, tabelas, totais)."""
            event = button.click(make_navigation(index), None, containers + nav_buttons)
            page = pages[index]
            if page.refresh:
                event.then(page.refresh, page.inputs, page.outputs)

        for index, button in enumerate(nav_buttons):
            connect(button, index)

        # Atalhos do Dashboard (Heurística 7): vão direto para o formulário desejado.
        for button, index in zip(quick_buttons, (1, 2, 3)):
            connect(button, index)

        # Ao abrir o sistema, o Dashboard é atualizado com os dados do banco.
        demo.load(dashboard.refresh, None, dashboard.outputs)
    return demo


if __name__ == "__main__":
    build_app().launch(inbrowser=True, theme=THEME, css=CSS, js=FORCE_LIGHT_JS, footer_links=[])
