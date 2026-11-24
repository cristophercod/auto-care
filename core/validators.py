"""
core/validators.py
------------------
Regras de validação dos formulários (Heurísticas 5 e 9 de Nielsen).

Cada função recebe o valor digitado e devolve o valor já limpo,
ou lança ValidationError com uma mensagem que explica O QUE está errado
e COMO corrigir.
"""
import re
from datetime import date, datetime

PLATE_PATTERN = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")  # ABC1234 ou ABC1D23
MAX_KM = 3_000_000
MAX_MONEY = 10_000_000
MIN_YEAR = 1900


class ValidationError(Exception):
    """Erro de validação com uma ou mais mensagens para mostrar ao usuário."""

    def __init__(self, messages):
        if isinstance(messages, str):
            messages = [messages]
        self.messages = list(messages)
        super().__init__("; ".join(self.messages))


def run_checks(checks: dict) -> dict:
    """
    Executa várias validações de uma vez e junta TODOS os erros.
    Assim o usuário corrige tudo em uma só tentativa, em vez de descobrir um erro por vez.

    checks = {"campo": lambda: validar(...), ...}
    """
    cleaned, errors = {}, []
    for name, check in checks.items():
        try:
            cleaned[name] = check()
        except ValidationError as err:
            errors.extend(err.messages)
    if errors:
        raise ValidationError(errors)
    return cleaned


def validate_text(value, label, required=True, max_len=60, min_len=1):
    text = (value or "").strip()
    if not text:
        if required:
            raise ValidationError(f"Preencha o campo «{label}».")
        return None
    if len(text) < min_len:
        raise ValidationError(f"«{label}» está muito curto. Escreva pelo menos {min_len} caracteres.")
    if len(text) > max_len:
        raise ValidationError(f"«{label}» passou de {max_len} caracteres. Escreva uma versão mais curta.")
    return text


def validate_plate(value) -> str:
    plate = re.sub(r"[\s\-]", "", (value or "")).upper()
    if not plate:
        raise ValidationError("Preencha o campo «Placa».")
    if not PLATE_PATTERN.match(plate):
        raise ValidationError(
            f"A placa «{value.strip()}» não parece válida. "
            "Use o formato antigo (ABC-1234) ou Mercosul (ABC1D23)."
        )
    return plate


def _is_empty(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _to_number(value, label, decimal=False) -> float:
    """
    Converte o que o usuário digitou em número. Aceita o padrão brasileiro:
    '45000', '45.000' (milhar), '350,50' e '1.250,50' (só quando decimal=True).
    Qualquer outra coisa gera uma mensagem explicando como digitar.
    """
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower().replace("r$", "").replace("km", "").replace(" ", "")
    negative = text.startswith("-")
    text = text.lstrip("-")
    if re.fullmatch(r"\d+", text):
        normalized = text
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", text):                      # 45.000
        normalized = text.replace(".", "")
    elif decimal and re.fullmatch(r"\d{1,3}(\.\d{3})*,\d{1,2}", text):  # 1.250,50
        normalized = text.replace(".", "").replace(",", ".")
    elif decimal and re.fullmatch(r"\d+,\d{1,2}", text):                  # 350,50
        normalized = text.replace(",", ".")
    elif decimal and re.fullmatch(r"\d+\.\d{1,2}", text):                # 350.50
        normalized = text
    else:
        if decimal:
            raise ValidationError(f"«{label}» deve conter apenas números, como 350 ou 350,50.")
        raise ValidationError(f"«{label}» deve ser um número inteiro, sem vírgula (ex.: 45000).")
    number = float(normalized)
    return -number if negative else number


def validate_year(value) -> int:
    if _is_empty(value):
        raise ValidationError("Preencha o campo «Ano».")
    number = _to_number(value, "Ano")
    if number != int(number):
        raise ValidationError("O ano deve ser um número inteiro, como 2018.")
    year = int(number)
    limit = date.today().year + 1
    if year < MIN_YEAR or year > limit:
        raise ValidationError(f"O ano deve estar entre {MIN_YEAR} e {limit}. Confira o documento do veículo.")
    return year


def validate_km(value, label="Quilometragem", required=True):
    if _is_empty(value):
        if required:
            raise ValidationError(f"Preencha o campo «{label}».")
        return None
    number = _to_number(value, label)
    if number < 0:
        raise ValidationError(f"«{label}» não pode ser negativa. Digite 0 ou um valor maior.")
    if number != int(number):
        raise ValidationError(f"«{label}» deve ser um número inteiro, sem vírgula (ex.: 45000).")
    if number > MAX_KM:
        raise ValidationError(f"«{label}» parece alta demais. Confira se digitou zeros a mais.")
    return int(number)


def validate_money(value, label="Valor gasto") -> float:
    if _is_empty(value):
        raise ValidationError(f"Preencha o campo «{label}». Se o serviço foi gratuito, digite 0.")
    number = _to_number(value, label, decimal=True)
    if number < 0:
        raise ValidationError(f"«{label}» não pode ser negativo. Digite 0 ou um valor maior.")
    if number > MAX_MONEY:
        raise ValidationError(f"«{label}» parece alto demais. Confira se digitou zeros a mais.")
    return round(number, 2)


def validate_days(value, label="Dias de antecedência") -> int:
    if _is_empty(value):
        raise ValidationError(f"Preencha «{label}». Use 0 para não avisar por data.")
    number = _to_number(value, label)
    if number < 0 or number != int(number) or number > 365:
        raise ValidationError(f"«{label}» deve ser um número inteiro de 0 a 365.")
    return int(number)


def parse_date(text, label, required=True):
    """Aceita dd/mm/aaaa (padrão brasileiro) ou aaaa-mm-dd. Devolve um objeto date."""
    text = (text or "").strip()
    if not text:
        if required:
            raise ValidationError(f"Preencha o campo «{label}» no formato dd/mm/aaaa (ex.: 15/03/2026).")
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text, fmt).date()
            break
        except ValueError:
            continue
    else:
        raise ValidationError(f"«{label}» não é uma data válida. Use dd/mm/aaaa, por exemplo 15/03/2026.")
    if parsed.year < 1950 or parsed.year > date.today().year + 30:
        raise ValidationError(f"«{label}» está fora do esperado ({text}). Confira o ano digitado.")
    return parsed
