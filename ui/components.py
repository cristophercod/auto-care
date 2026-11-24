"""
ui/components.py
----------------
Funções que geram pedaços de HTML reutilizados em todas as telas.
Assim os cartões, avisos e etiquetas têm SEMPRE o mesmo visual (Heurística 4: consistência).

Todo texto vindo do usuário passa por esc() para não quebrar a página nem injetar HTML.
"""
import html

from core.formatters import date_br, km as fmt_km


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def plural(n: int, singular: str, plural_: str) -> str:
    return f"{n} {singular if n == 1 else plural_}"


# ---------- Avisos de status (Heurísticas 1 e 9) ----------
_ALERT_ICONS = {"success": "✅", "error": "⛔", "warning": "⚠️", "info": "ℹ️"}


def banner(kind: str, title: str, items=None) -> str:
    """Caixa colorida de feedback. kind: success | error | warning | info."""
    details = ""
    if items:
        if isinstance(items, str):
            items = [items]
        details = "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"
    return (f'<div class="alert alert-{kind}" role="alert">'
            f'<span class="alert-icon">{_ALERT_ICONS[kind]}</span>'
            f'<div class="alert-body"><strong>{esc(title)}</strong>{details}</div></div>')


# ---------- Estrutura das telas ----------
def page_header(icon: str, title: str, subtitle: str) -> str:
    return (f'<div class="page-header"><span class="page-icon">{icon}</span>'
            f'<div><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div></div>')


def form_title(title: str, hint: str = "", editing: bool = False) -> str:
    css = "form-title editing" if editing else "form-title"
    hint_html = f"<p>{esc(hint)}</p>" if hint else ""
    return f'<div class="{css}"><h2>{esc(title)}</h2>{hint_html}</div>'


def section_title(title: str, hint: str = "") -> str:
    hint_html = f"<p>{esc(hint)}</p>" if hint else ""
    return f'<div class="form-title"><h2>{esc(title)}</h2>{hint_html}</div>'


def hint(text: str) -> str:
    return f'<div class="hint">{esc(text)}</div>' if text else ""


def caption(text: str) -> str:
    return f'<div class="table-caption">{esc(text)}</div>'


def empty_state(icon: str, title: str, text: str) -> str:
    return (f'<div class="empty-state"><div class="empty-icon">{icon}</div>'
            f'<strong>{esc(title)}</strong><p>{esc(text)}</p></div>')


# ---------- Cartões e etiquetas ----------
def stat_card(icon: str, label: str, value: str, hint_text: str = "", tone: str = "") -> str:
    return (f'<div class="stat-card {tone}"><div class="stat-icon">{icon}</div>'
            f'<div class="stat-value">{esc(value)}</div><div class="stat-label">{esc(label)}</div>'
            f'<div class="stat-hint">{esc(hint_text)}</div></div>')


def status_chip(status: str, icon: str, label: str) -> str:
    return f'<span class="chip chip-{status}">{icon} {esc(label)}</span>'


def schedule_list(items: list, limit: int = 8) -> str:
    """Lista de próximas manutenções para o Dashboard (mais urgentes primeiro)."""
    if not items:
        return empty_state("📅", "Nenhuma revisão planejada",
                           "Cadastre a próxima troca de óleo, revisão ou outro serviço na tela "
                           "«Próximas revisões» e o AutoTrack avisa quando estiver chegando.")
    rows = []
    for s in items[:limit]:
        expected = []
        if s["due_date"]:
            expected.append(f"Data: {date_br(s['due_date'])}")
        if s["due_km"] is not None:
            expected.append(f"Km: {fmt_km(s['due_km'])}")
        rows.append(
            f'<div class="sched-item sched-{s["status"]}">'
            f'<div class="sched-main"><div class="sched-title">{esc(s["service_type"])}</div>'
            f'<div class="sched-meta">{esc(s["vehicle_label"])} · {esc(" · ".join(expected))}</div></div>'
            f'<div class="sched-side">{status_chip(s["status"], s["status_icon"], s["status_label"])}'
            f'<div class="sched-reason">{esc(s["reason"])}</div></div></div>'
        )
    extra = len(items) - limit
    if extra > 0:
        rows.append(caption(f"+ {plural(extra, 'outra revisão', 'outras revisões')} na tela «Próximas revisões»."))
    return '<div class="sched-list">' + "".join(rows) + "</div>"
