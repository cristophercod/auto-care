# 🚘 AutoTrack — Controle de Manutenção Veicular

Sistema web para proprietários de veículos organizarem manutenções, próximas revisões e gastos.
Feito com **Python + Gradio + SQLite + datetime**, seguindo as **10 heurísticas de Nielsen**.

---

## 1. Como executar no Windows (VS Code + PowerShell)

1. **Instale o Python 3.10 ou superior** em python.org. Na instalação, marque **"Add python.exe to PATH"**.
2. No VS Code: **Arquivo → Abrir Pasta** e escolha a pasta `autotrack`.
3. Abra o terminal: **Terminal → Novo Terminal** (confira que é PowerShell).
4. Crie o ambiente virtual (uma "caixa" só para as bibliotecas do projeto):
   ```powershell
   python -m venv .venv
   ```
5. Ative-o:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   > Se aparecer erro de "execução de scripts desabilitada", rode antes:
   > `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` e repita o passo 5.
6. Instale as bibliotecas:
   ```powershell
   pip install -r requirements.txt
   ```
7. Execute:
   ```powershell
   python app.py
   ```
   O navegador abre sozinho em `http://127.0.0.1:7860`. Para encerrar, volte ao terminal e use `Ctrl + C`.

O banco `data/autotrack.db` é **criado automaticamente** na primeira execução e os dados continuam salvos ao fechar e abrir de novo.

**Bibliotecas:** apenas `gradio` (o `pandas`, usado no gráfico de gastos, vem junto com ele). `sqlite3`, `datetime`, `re` e `html` já fazem parte do Python.

**Rodar os testes automáticos da lógica:** `python -m unittest discover -s tests -v`

---

## 2. Estrutura de pastas e responsabilidade de cada arquivo

```
autotrack/
├── app.py                  ← PONTO DE ENTRADA. Monta o menu lateral, liga as telas e abre o sistema.
├── requirements.txt        ← bibliotecas a instalar
├── README.md               ← este arquivo
├── data/
│   └── autotrack.db        ← banco SQLite (criado sozinho)
├── core/                   ← peças básicas, sem tela
│   ├── database.py         ← conexão com SQLite + criação das 4 tabelas
│   ├── validators.py       ← regras de validação (placa, ano, km, valor, datas) e mensagens de erro
│   └── formatters.py       ← transforma dados em texto: R$ 1.234,50 · 45.000 km · 15/03/2026
├── services/               ← regras de negócio e SQL (a tela nunca escreve SQL)
│   ├── vehicles.py         ← cadastrar/listar/editar/excluir veículos
│   ├── maintenances.py     ← manutenções realizadas + filtros do histórico
│   ├── schedules.py        ← próximas revisões + cálculo de Atrasada/Próxima/No prazo
│   └── reports.py          ← totais do Dashboard e da tela de Gastos
├── ui/                     ← tudo que o usuário vê
│   ├── styles.py           ← tema e CSS (azul-escuro, branco, cinzas)
│   ├── components.py       ← cartões, avisos, etiquetas (HTML reutilizável)
│   ├── helpers.py, page.py ← funções auxiliares das telas
│   ├── page_dashboard.py   ← tela inicial
│   ├── page_vehicles.py    ← Veículos
│   ├── page_maintenances.py← Manutenções
│   ├── page_schedules.py   ← Próximas revisões
│   ├── page_history.py     ← Histórico (filtros)
│   ├── page_expenses.py    ← Gastos
│   └── page_help.py        ← Ajuda
└── tests/
    └── test_services.py    ← 17 testes automáticos da lógica
```

### Banco de dados (relacionamentos)

```
vehicles (1) ───< maintenances              (manutenções realizadas)
vehicles (1) ───< scheduled_maintenances    (próximas revisões)
settings                                     (margem de aviso escolhida pelo usuário)
```
`maintenances.vehicle_id` e `scheduled_maintenances.vehicle_id` são **chaves estrangeiras** com `ON DELETE CASCADE`:
ao excluir um veículo, o SQLite apaga também os registros ligados a ele. A placa é `UNIQUE` (não repete) e há `CHECK` impedindo km e valor negativos **no próprio banco** (segunda barreira, além da validação da tela).

---

## 3. Como Python, Gradio e SQLite conversam

Exemplo: o usuário clica em **"Salvar veículo"**.

```
[Navegador]  clique no botão
     │   (Gradio envia os valores dos campos)
     ▼
ui/page_vehicles.py  → on_save(...)            ← função Python ligada ao botão (btn_save.click)
     ▼
services/vehicles.py → create_vehicle(...)     ← valida (core/validators.py) e monta o SQL
     ▼
core/database.py     → connection()            ← abre o SQLite, executa INSERT, faz commit
     ▼
[arquivo data/autotrack.db]
     ▲
     │  volta o resultado (ou ValidationError com as mensagens)
ui/page_vehicles.py  → devolve: aviso verde/vermelho + formulário limpo + tabela atualizada
     ▼
[Navegador]  Gradio atualiza só os componentes listados em `outputs`
```

Três ideias para explicar ao professor:
1. **`botão.click(função, entradas, saídas)`** é a base do Gradio: *entradas* são os campos lidos, *saídas* são os componentes atualizados com o `return` da função.
2. **Camadas:** `ui/` (aparência) → `services/` (regras + SQL) → `core/` (banco e validação). Cada uma só conversa com a de baixo.
3. **`ValidationError`:** quando algo está errado, a camada de serviço "lança" o erro com uma lista de mensagens; a tela captura (`try/except`) e mostra o aviso vermelho. Nada é salvo.

**Navegação:** cada tela é um bloco (`gr.Column`) e o menu só alterna `visible=True/False`. Ao entrar numa tela, o app recarrega os dados dela do banco (listas de veículos, tabelas, totais), por isso o Dashboard sempre reflete o que está salvo.

**datetime:** `services/schedules.py → compute_status` compara `date.today()` com a data prevista e a km atual do veículo com a km prevista. As datas são guardadas no banco como `AAAA-MM-DD` e exibidas como `dd/mm/aaaa`.

---

## 4. As 10 heurísticas de Nielsen — onde ver cada uma no sistema

| # | Heurística | Como foi aplicada (e onde ver) |
|---|---|---|
| 1 | **Visibilidade do status** | Todo salvar/editar/excluir mostra um aviso colorido (verde = sucesso, vermelho = erro, amarelo = atenção, azul = informação). O Gradio exibe o indicador de carregamento nos componentes durante o processamento. Revisões mostram etiquetas 🔴 Atrasada / 🟡 Próxima / 🟢 No prazo com o motivo ("Venceu há 3 dias", "Faltam 500 km"). O formulário muda de título para **"Editando: …"** quando você seleciona um registro. |
| 2 | **Correspondência com o mundo real** | Linguagem do dia a dia ("Troca de óleo", "Oficina", "Quilometragem"), valores em **R$ 1.250,50**, datas **dd/mm/aaaa**, km com ponto de milhar, placa no formato real (ABC-1234 / Mercosul). Telas organizadas na ordem natural: veículo → manutenção → revisão → histórico → gastos. |
| 3 | **Controle e liberdade** | Botão **Cancelar** em todo formulário; editar e excluir qualquer registro; **excluir pede confirmação** com "Não, manter"; revisão concluída por engano pode ser **reaberta**. |
| 4 | **Consistência** | Mesmo menu em todas as telas, mesmos botões (azul-escuro = ação principal, cinza = secundária, vermelho = excluir), mesmos cartões, avisos e etiquetas (todos gerados por `ui/components.py` e `ui/styles.py`). Emojis fixos por função (🚗 🔧 📅 📋 💰 ❓). |
| 5 | **Prevenção de erros** | Campos obrigatórios; placa validada (e sem duplicar); km e valores **não aceitam negativos**; data da manutenção **não pode ser futura**; revisão exige data **ou** km; menus de seleção no lugar de digitação (veículo, tipo, combustível); campo vazio nunca vira 0; confirmação antes de excluir; o banco ainda tem `CHECK`, `UNIQUE` e chaves estrangeiras. |
| 6 | **Reconhecimento em vez de memorização** | Veículos e tipos de serviço em menus; ao escolher o veículo aparece **"Quilometragem atual: 50.000 km"**; filtros visíveis no Histórico; textos de exemplo nos campos; a legenda dos status aparece junto da lista. |
| 7 | **Flexibilidade e eficiência** | Atalhos no Dashboard (➕ Novo veículo / Registrar manutenção / Planejar revisão); **clicar na linha** da tabela para editar; busca por texto; filtros por veículo, tipo e período; atalhos de período em Gastos (Este mês, Últimos 30 dias, Este ano, Tudo); data de hoje e km do veículo já preenchidas; Enter aplica filtros. |
| 8 | **Estética e minimalismo** | Layout limpo, campos sem caixas extras, cartões brancos sobre fundo cinza, cor forte **só** para alertas. Cada tela mostra apenas o necessário; a margem de aviso fica dentro de um acordeão fechado. |
| 9 | **Reconhecer, diagnosticar e recuperar erros** | Mensagens explicam **o que** está errado e **como corrigir**, todas de uma vez: *"A placa «12-XYZ» não parece válida. Use o formato antigo (ABC-1234) ou Mercosul (ABC1D23)."* O que foi digitado **não é apagado** quando há erro. Nunca aparece só "Erro". |
| 10 | **Ajuda e documentação** | Tela **❓ Ajuda** (primeiros passos, significado dos números do Dashboard e dos status, dicas de preenchimento, perguntas frequentes); texto de orientação (`info`) embaixo de cada campo; legenda dos status; mensagens vazias que dizem o próximo passo ("Cadastre seu primeiro veículo…"). |

### Requisito: "não inventar intervalos de manutenção"
O sistema **não sugere** quando trocar óleo, pneus etc. O usuário informa a data e/ou km de cada revisão. A única configuração do sistema é a **margem de aviso** (padrão 30 dias / 1.000 km), que só define a partir de quando uma revisão aparece como "Próxima" — e pode ser alterada pelo usuário.

---

## 5. Regras de status das revisões

- 🔴 **Atrasada:** a data prevista já passou **ou** a km atual do veículo ≥ km prevista.
- 🟡 **Próxima:** faltam até a margem de aviso (dias ou km). "Vence hoje" também entra aqui.
- 🟢 **No prazo:** ainda há tempo.
- ✅ **Concluída:** marcada pelo usuário; some dos avisos.
- Se há data **e** km, vale a situação mais grave das duas.

Ao registrar uma manutenção com km maior que a atual do veículo, o sistema atualiza a km do veículo automaticamente (e avisa).

---

## 6. Avaliação crítica (testes realizados)

**Como foi testado:** (a) 17 testes automáticos da lógica; (b) 39 verificações automatizadas **pela interface real** num navegador (Chromium), clicando em botões, preenchendo formulários e lendo a tela, cobrindo cadastrar/consultar/editar/excluir de veículos, manutenções e revisões, validações, filtros, gastos, Dashboard e navegação; (c) conferência de que os dados permanecem no arquivo `.db` após fechar o servidor; (d) teste de layout em tela de celular (390 px) sem rolagem lateral.

**Problema encontrado e corrigido durante os testes:** o campo numérico do Gradio envia **0** quando fica vazio, o que salvava km 0 sem o usuário perceber (e criava revisão "atrasada" sem data/km). Por isso, ano, km e valores são **caixas de texto validadas em Python**, que também aceitam o padrão brasileiro (`1.250,50`) e dão mensagens claras.

**Limitações conhecidas (honestas):**
- Foi testado com Gradio 6.31 e Chromium em Linux; não pude executar no Windows. Os comandos do passo a passo são os padrões do Python/Windows.
- A fonte Manrope vem do Google Fonts: sem internet, o sistema usa a fonte do sistema (visual quase igual).
- O indicador de carregamento é o nativo do Gradio; como o SQLite local é muito rápido, ele aparece por uma fração de segundo.
- As datas são digitadas como texto (dd/mm/aaaa), com validação, para garantir o formato brasileiro.
- É um sistema de **um usuário local** (sem login). Valores em `REAL` do SQLite; para um sistema financeiro real, o ideal seria guardar centavos como inteiros.
- Não há exportação (CSV/PDF) nem notificações por e-mail, de propósito, para manter o projeto simples de explicar.
