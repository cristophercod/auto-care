"""
core/database.py
----------------
Responsável SOMENTE pela conexão com o SQLite e pela criação das tabelas.

Como funciona a comunicação com o banco:
  1. `init_db()` roda uma vez quando o programa abre e cria as tabelas
     caso elas ainda não existam (primeira execução).
  2. Cada operação usa `with connection() as conn:` -> abre o banco,
     executa os comandos SQL e salva (commit) ao final. Se der erro,
     desfaz tudo (rollback), então nunca ficam dados pela metade.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# O arquivo do banco fica na pasta "data/" do projeto.
# A variável de ambiente AUTOTRACK_DB permite trocar o caminho (usado nos testes).
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "autotrack.db"


def get_db_path() -> Path:
    return Path(os.environ.get("AUTOTRACK_DB", DEFAULT_DB_PATH))


@contextmanager
def connection():
    """Abre uma conexão, salva ao final e sempre fecha."""
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row            # permite acessar colunas pelo nome
    conn.execute("PRAGMA foreign_keys = ON")  # ativa as chaves estrangeiras no SQLite
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS vehicles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    brand       TEXT    NOT NULL,
    model       TEXT    NOT NULL,
    year        INTEGER NOT NULL,
    plate       TEXT    NOT NULL UNIQUE,
    current_km  INTEGER NOT NULL CHECK (current_km >= 0),
    fuel        TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Manutenções JÁ REALIZADAS. Se o veículo for excluído, seus registros também são.
CREATE TABLE IF NOT EXISTS maintenances (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id    INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    service_type  TEXT    NOT NULL,
    description   TEXT    NOT NULL,
    service_date  TEXT    NOT NULL,                       -- formato AAAA-MM-DD
    km            INTEGER NOT NULL CHECK (km >= 0),
    cost          REAL    NOT NULL CHECK (cost >= 0),
    workshop      TEXT
);

-- Manutenções PLANEJADAS (próximas revisões). Precisa ter data OU quilometragem.
CREATE TABLE IF NOT EXISTS scheduled_maintenances (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id    INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    service_type  TEXT    NOT NULL,
    due_date      TEXT,
    due_km        INTEGER CHECK (due_km IS NULL OR due_km >= 0),
    notes         TEXT,
    done          INTEGER NOT NULL DEFAULT 0,
    CHECK (due_date IS NOT NULL OR due_km IS NOT NULL)
);

-- Configurações simples (ex.: com quanta antecedência avisar).
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_maint_vehicle ON maintenances(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_sched_vehicle ON scheduled_maintenances(vehicle_id);
"""


def init_db() -> None:
    """Cria o banco e as tabelas na primeira execução (não apaga nada se já existir)."""
    with connection() as conn:
        conn.executescript(SCHEMA)
