"""
ui/page_help.py
---------------
Tela AJUDA (Heurística 10): como usar o sistema, o significado dos indicadores e dos status.
É só conteúdo de texto, não acessa o banco.
"""
import gradio as gr

from ui import components as ui
from ui.page import Page

START = """
1. **Cadastre seu veículo** na tela **Veículos**: marca, modelo, ano, placa e quilometragem atual.
2. **Registre as manutenções que já fez** na tela **Manutenções** (troca de óleo, pneus, freios etc.).
3. **Planeje as próximas revisões** na tela **Próximas revisões**, informando a data e/ou a quilometragem.
4. **Acompanhe tudo no Dashboard**: ele mostra o que está atrasado ou chegando.
5. Consulte o **Histórico** para rever serviços e a tela **Gastos** para saber quanto foi gasto.
"""

INDICATORS = """
- **Veículos cadastrados:** quantos carros você tem no sistema.
- **Manutenções realizadas:** quantos serviços você já registrou.
- **Total gasto:** soma dos valores de todas as manutenções registradas.
- **Atenção:** quantas revisões estão atrasadas ou próximas de vencer. Fica vermelho se houver atrasadas,
  amarelo se houver só próximas e verde quando está tudo em dia.
"""

STATUS = """
- 🔴 **Atrasada:** a data prevista já passou **ou** a quilometragem atual do veículo já chegou na quilometragem prevista.
- 🟡 **Próxima:** está dentro da margem de aviso. Por padrão, 30 dias ou 1.000 km (você pode mudar em
  *Próximas revisões → Margem de aviso*).
- 🟢 **No prazo:** ainda há tempo.
- ✅ **Concluída:** você marcou a revisão como feita.

Se a revisão tem **data e quilometragem**, vale a situação mais grave das duas.
O AutoTrack **não inventa intervalos de manutenção**: use as datas e quilometragens do manual do seu veículo
ou da recomendação da sua oficina.
"""

TIPS = """
- **Placa:** use o modelo antigo (ABC-1234) ou Mercosul (ABC1D23). Hífen e letras minúsculas são aceitos.
- **Datas:** sempre no formato dia/mês/ano, por exemplo 15/03/2026.
- **Quilometragem:** apenas números inteiros, sem ponto nem vírgula (ex.: 45000).
- **Valor gasto:** pode ter centavos (ex.: 350,50). Digite 0 se o serviço foi gratuito.
- **Editar ou excluir:** clique em uma linha da tabela. Os dados vão para o formulário.
- **Quilometragem do veículo:** quando você registra um serviço com km maior que a atual, o AutoTrack atualiza o veículo.
"""

FAQ = """
**Errei um cadastro. Como corrijo?** Clique na linha na tabela, altere o formulário e use «Salvar alterações».

**Posso desfazer uma exclusão?** Não. Por isso o sistema pede confirmação e explica o que será apagado.

**O que acontece se eu excluir um veículo?** As manutenções e revisões planejadas dele também são apagadas.

**Marquei uma revisão como concluída sem querer.** Ative «Mostrar também as concluídas», clique na linha e use «Reabrir».

**Meus dados ficam salvos?** Sim. Tudo é guardado no arquivo `data/autotrack.db`, no seu computador.
"""


def build() -> Page:
    with gr.Column(visible=False, elem_classes="page") as container:
        gr.HTML(ui.page_header("❓", "Ajuda", "Aprenda a usar o AutoTrack em poucos minutos."))
        with gr.Column(elem_classes="card"):
            with gr.Accordion("🚀 Primeiros passos", open=True):
                gr.Markdown(START)
            with gr.Accordion("📊 O que significam os números do Dashboard", open=False):
                gr.Markdown(INDICATORS)
            with gr.Accordion("🚦 O que significam os status das revisões", open=False):
                gr.Markdown(STATUS)
            with gr.Accordion("✍️ Dicas de preenchimento", open=False):
                gr.Markdown(TIPS)
            with gr.Accordion("💬 Perguntas frequentes", open=False):
                gr.Markdown(FAQ)
    return Page(container)
