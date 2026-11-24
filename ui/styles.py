"""
ui/styles.py
------------
Tema do Gradio + CSS personalizado. Identidade visual: azul-escuro, branco e cinzas,
com cores de destaque só para alertas (vermelho = atrasada, amarelo = próxima, verde = ok).
Todas as telas usam as mesmas classes, então ficam consistentes (Heurística 4).
"""
import gradio as gr

# Força o modo claro para o visual não mudar conforme o tema do sistema.
FORCE_LIGHT_JS = """
() => {
  const url = new URL(window.location);
  if (url.searchParams.get('__theme') !== 'light') {
    url.searchParams.set('__theme', 'light');
    window.location.replace(url);
  }
}
"""

THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.slate,
    radius_size=gr.themes.sizes.radius_md,
    font=[gr.themes.GoogleFont("Manrope"), "ui-sans-serif", "system-ui", "Segoe UI", "sans-serif"],
).set(
    body_background_fill="#F2F5F9",
    body_background_fill_dark="#F2F5F9",
    button_primary_background_fill="#12315A",
    button_primary_background_fill_hover="#1B4377",
    button_primary_background_fill_dark="#12315A",
    button_primary_background_fill_hover_dark="#1B4377",
    button_primary_text_color="#FFFFFF",
    button_primary_text_color_dark="#FFFFFF",
)

CSS = """
:root {
  --navy: #12315A;  --navy-2: #1B4377;  --navy-3: #0D2444;
  --bg: #F2F5F9;    --card: #FFFFFF;    --line: #E1E7F0;
  --text: #1A2638;  --muted: #5E6E86;
  --blue: #2F6FDE;  --blue-bg: #E8F0FD;
  --red: #C23B3B;   --red-bg: #FCECEC;
  --amber: #A66A00; --amber-bg: #FFF3D6;
  --green: #1B7F55; --green-bg: #E4F5EC;
}

footer, .show-api, .built-with { display: none !important; }
.gradio-container { max-width: 100% !important; padding: 0 !important; background: var(--bg); }
.gradio-container .main, .gradio-container .wrap, .gradio-container .contain {
  padding: 0 !important; max-width: 100% !important; width: 100% !important; margin: 0 !important; }
.page .html-container, #sidebar .html-container { padding: 0 !important; }

/* ---------- Estrutura: menu lateral + conteúdo ---------- */
#layout { gap: 0 !important; flex-wrap: nowrap !important; align-items: stretch !important; }
#sidebar {
  background: linear-gradient(180deg, var(--navy) 0%, var(--navy-3) 100%);
  flex: 0 0 260px !important; min-width: 260px !important; max-width: 260px;
  padding: 22px 14px !important; gap: 4px !important; border-radius: 0 !important;
  min-height: 100vh; position: sticky; top: 0; align-self: flex-start; height: 100vh; overflow-y: auto;
}
#main { padding: 28px 36px 48px !important; min-width: 0 !important; max-width: 1180px; }

.brand { display: flex; align-items: center; gap: 12px; padding: 4px 10px 22px; color: #fff; }
.brand-logo { width: 42px; height: 42px; border-radius: 12px; background: #fff; display: grid; place-items: center; font-size: 22px; }
.brand .brand-name { color: #fff !important; font-weight: 800; font-size: 20px; letter-spacing: -0.01em; line-height: 1.1; }
.brand .brand-sub { font-size: 12px; color: #A9BEDD !important; margin-top: 2px; }
.sidebar-tip { color: #A9BEDD !important; font-size: 12px; line-height: 1.5; padding: 18px 10px 0; border-top: 1px solid rgba(255,255,255,.12); margin-top: 18px; }

#sidebar button.nav-btn {
  width: 100%; justify-content: flex-start !important; text-align: left; background: transparent !important;
  color: #D5E2F5 !important; border: none !important; box-shadow: none !important; font-weight: 600; font-size: 15px;
  padding: 12px 14px !important; border-radius: 10px !important; min-height: 46px;
}
#sidebar button.nav-btn:hover { background: rgba(255,255,255,.09) !important; color: #fff !important; }
#sidebar button.nav-btn.nav-active { background: #fff !important; color: var(--navy) !important; }
#sidebar button.nav-btn:focus-visible { outline: 3px solid #8DB5F5; outline-offset: 2px; }

/* ---------- Conteúdo das telas ---------- */
.page { gap: 18px !important; background: transparent !important; border: none !important; }
.page-header { display: flex; gap: 14px; align-items: center; margin-bottom: 4px; }
.page-icon { width: 48px; height: 48px; border-radius: 14px; background: var(--navy); display: grid; place-items: center; font-size: 24px; flex: none; }
.page-header h1 { margin: 0; font-size: 26px; font-weight: 800; color: var(--text); letter-spacing: -0.02em; }
.page-header p { margin: 2px 0 0; color: var(--muted); font-size: 14px; }

.card { background: var(--card) !important; border: 1px solid var(--line) !important; border-radius: 16px !important;
        padding: 22px !important; gap: 14px !important; box-shadow: 0 1px 2px rgba(18,49,90,.04); }
.form-title h2 { margin: 0; font-size: 18px; font-weight: 700; color: var(--text); }
.form-title p { margin: 4px 0 0; color: var(--muted); font-size: 13px; }
.form-title.editing h2 { color: var(--navy); }
.form-title.editing { border-left: 4px solid var(--blue); padding-left: 12px; }
.hint { color: var(--muted); font-size: 13px; line-height: 1.5; padding: 2px 0; }
.table-caption { color: var(--muted); font-size: 13px; padding-top: 4px; }

.button-row { gap: 10px !important; flex-wrap: wrap !important; }
.button-row button { flex: 0 0 auto !important; min-width: 0 !important; }
.quick-actions button { font-weight: 700; }

/* ---------- Avisos (feedback) ---------- */
.alert { display: flex; gap: 12px; align-items: flex-start; padding: 14px 16px; border-radius: 12px; border: 1px solid; font-size: 14px; line-height: 1.45; }
.alert strong { display: block; font-weight: 700; }
.alert ul { margin: 6px 0 0; padding-left: 18px; }
.alert-icon { font-size: 18px; line-height: 1.3; }
.alert-success { background: var(--green-bg); border-color: #BFE5D1; color: #14573B; }
.alert-error   { background: var(--red-bg);   border-color: #F2C4C4; color: #8C2525; }
.alert-warning { background: var(--amber-bg); border-color: #F1DBA0; color: #7A4F00; }
.alert-info    { background: var(--blue-bg);  border-color: #C5D8F7; color: #1E4C9A; }
.confirm-box { background: var(--amber-bg) !important; border: 1px solid #F1DBA0 !important; border-radius: 12px !important; padding: 14px !important; }
.confirm-box .alert { background: transparent; border: none; padding: 0 0 6px; }

/* ---------- Cartões de indicadores ---------- */
.stat-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.stat-grid-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.stat-card { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 18px 20px; border-top: 4px solid var(--navy); box-shadow: 0 1px 2px rgba(18,49,90,.04); }
.stat-icon { font-size: 22px; }
.stat-value { font-size: 30px; font-weight: 800; color: var(--text); letter-spacing: -0.02em; margin-top: 6px; overflow-wrap: anywhere; }
.stat-label { font-weight: 700; font-size: 14px; color: var(--text); margin-top: 2px; }
.stat-hint { font-size: 12px; color: var(--muted); margin-top: 4px; }
.stat-card.tone-danger  { border-top-color: var(--red);   background: var(--red-bg); }
.stat-card.tone-danger .stat-value { color: var(--red); }
.stat-card.tone-warning { border-top-color: #E0A100; background: var(--amber-bg); }
.stat-card.tone-warning .stat-value { color: var(--amber); }
.stat-card.tone-ok      { border-top-color: var(--green); }
.stat-card.tone-ok .stat-value { color: var(--green); }

/* ---------- Lista de próximas manutenções ---------- */
.sched-list { display: flex; flex-direction: column; gap: 10px; }
.sched-item { display: flex; justify-content: space-between; gap: 16px; align-items: center; padding: 14px 16px; border-radius: 12px; border: 1px solid var(--line); border-left: 6px solid var(--green); background: #fff; }
.sched-atrasada { border-left-color: var(--red); background: var(--red-bg); border-color: #F2C4C4; }
.sched-proxima  { border-left-color: #E0A100; background: var(--amber-bg); border-color: #F1DBA0; }
.sched-title { font-weight: 700; font-size: 15px; color: var(--text); }
.sched-meta { font-size: 13px; color: var(--muted); margin-top: 2px; }
.sched-side { text-align: right; flex: none; }
.sched-reason { font-size: 12px; color: var(--muted); margin-top: 4px; }
.chip { display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; white-space: nowrap; }
.chip-atrasada { background: var(--red); color: #fff; }
.chip-proxima { background: #E0A100; color: #2B1D00; }
.chip-no_prazo { background: var(--green-bg); color: var(--green); }
.chip-concluida { background: #E8ECF3; color: var(--muted); }

.empty-state { text-align: center; padding: 28px 16px; color: var(--muted); }
.empty-icon { font-size: 34px; }
.empty-state strong { display: block; color: var(--text); font-size: 16px; margin-top: 6px; }
.empty-state p { margin: 6px auto 0; max-width: 480px; font-size: 14px; line-height: 1.5; }
.summary-bar { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; background: var(--blue-bg); color: #1E4C9A; border-radius: 10px; padding: 10px 14px; font-size: 14px; }

/* ---------- Tabelas e campos ---------- */
/* Campos sem caixa extra ao redor: só o próprio campo tem borda (visual mais limpo). */
.card .block:not(.data-table) { border: none !important; box-shadow: none !important; background: transparent !important; padding: 0 !important; }
.card label, .card label > span, .card [data-testid="block-info"], .card .block-title, .card .block-info {
  background: transparent !important; box-shadow: none !important; }
.card .form { background: transparent !important; border: none !important; box-shadow: none !important; gap: 14px !important; }
.card .hint, .card .empty-state { background: transparent; }
.sched-list + .hint, .page .hint { margin-top: 6px; }
.data-table { border-radius: 12px !important; }
.data-table table, .data-table td, .data-table th, .data-table .cell-wrap, .data-table span {
  font-family: "Manrope", ui-sans-serif, system-ui, "Segoe UI", sans-serif !important; font-size: 14px; }
.data-table th { font-weight: 700; color: var(--navy); }
.data-table tbody tr { cursor: pointer; }
.card label span, .card .block-title { font-weight: 600; }
.card input:focus-visible, .card textarea:focus-visible, button:focus-visible { outline: 3px solid #8DB5F5; outline-offset: 1px; }

/* ---------- Responsivo (celular e tablet) ---------- */
@media (max-width: 960px) {
  #layout { flex-wrap: wrap !important; }
  #sidebar { flex: 1 1 100% !important; max-width: 100%; min-width: 0 !important; height: auto; min-height: 0; position: static; padding: 12px !important; flex-direction: row !important; flex-wrap: wrap; align-items: center; }
  .brand { padding: 0 8px 0 4px; }
  .sidebar-tip { display: none; }
  #sidebar button.nav-btn { width: auto; flex: 0 0 auto; min-height: 40px; padding: 8px 12px !important; font-size: 14px; }
  #main { padding: 18px 14px 40px !important; flex: 1 1 100% !important; max-width: 100%; }
  .stat-grid, .stat-grid-3 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .sched-item { flex-direction: column; align-items: flex-start; }
  .sched-side { text-align: left; }
}
@media (max-width: 520px) {
  .stat-grid, .stat-grid-3 { grid-template-columns: 1fr; }
  .page-header h1 { font-size: 22px; }
  .card { padding: 16px !important; }
}
"""
