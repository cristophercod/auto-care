"""
ui/page.py
----------
Pequena estrutura que cada tela devolve para o app.py:
  container -> o bloco visual da tela (aparece/some ao navegar)
  refresh   -> função que recarrega os dados da tela quando o usuário entra nela
  inputs / outputs -> componentes usados por essa função
"""
from typing import Callable, NamedTuple, Optional


class Page(NamedTuple):
    container: object
    refresh: Optional[Callable] = None
    inputs: Optional[list] = None
    outputs: Optional[list] = None
