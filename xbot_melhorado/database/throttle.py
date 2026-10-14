"""
database/throttle.py
XBot v0.3.0 Beta — Proteção contra tentativas repetidas (login e cadastro)

Guarda no SQLite (tabela auth_tentativas) UMA linha por tentativa, para o limite
sobreviver a reinício do servidor e valer entre processos.

Privacidade: a "chave" de cada tentativa é um HMAC (com a chave secreta do app) do
e-mail ou do IP — nunca o e-mail/IP em texto.

Janela deslizante: bloqueia quando há N ou mais falhas dentro dos últimos
`janela` segundos; libera assim que a falha mais antiga que ainda conta expira.
Tentativas feitas DURANTE o bloqueio não são gravadas, então o bloqueio não se
prolonga sozinho.
"""

from __future__ import annotations

import hashlib
import hmac
import math
from typing import Sequence, Tuple

from database.db import get_connection

LOGIN = "login"
REGISTRO = "registro"

_RETENCAO_SEGUNDOS = 24 * 3600   # tentativas mais velhas que isso são apagadas


def chave_hmac(segredo: str, tipo: str, valor: str) -> str:
    """Identificador estável e não reversível de um e-mail/IP/navegador."""
    mensagem = f"{tipo}\0{valor}".encode("utf-8")
    return hmac.new(segredo.encode("utf-8"), mensagem, hashlib.sha256).hexdigest()[:40]


def criar_tabelas(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS auth_tentativas (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            acao    TEXT    NOT NULL,
            chave   TEXT    NOT NULL,
            quando  REAL    NOT NULL,
            sucesso INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_auth_tentativas ON auth_tentativas (acao, chave, quando)"
    )


def segundos_de_bloqueio(acao: str,
                         regras: Sequence[Tuple[str, int]],
                         *, agora: float, janela: int,
                         apenas_falhas: bool = True) -> int:
    """
    `regras` = [(chave, limite), ...]. Devolve 0 se está livre; senão, quantos
    segundos faltam para a regra mais restritiva liberar (sempre >= 1).
    """
    espera = 0
    with get_connection() as conn:
        for chave, limite in regras:
            if limite <= 0:
                continue
            sql = "SELECT quando FROM auth_tentativas WHERE acao = ? AND chave = ? AND quando > ?"
            if apenas_falhas:
                sql += " AND sucesso = 0"
            sql += " ORDER BY quando ASC"
            instantes = [linha["quando"] for linha in conn.execute(sql, (acao, chave, agora - janela))]
            if len(instantes) >= limite:
                # a falha de índice (n - limite) é a que, ao expirar, deixa a contagem em limite-1
                libera_em = instantes[len(instantes) - limite] + janela
                espera = max(espera, math.ceil(libera_em - agora))
    return max(espera, 1) if espera > 0 else 0


def registrar_tentativa(acao: str, chaves: Sequence[str], *, agora: float, sucesso: bool) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM auth_tentativas WHERE quando <= ?", (agora - _RETENCAO_SEGUNDOS,))
        conn.executemany(
            "INSERT INTO auth_tentativas (acao, chave, quando, sucesso) VALUES (?, ?, ?, ?)",
            [(acao, chave, agora, 1 if sucesso else 0) for chave in chaves],
        )


def limpar_falhas(acao: str, chave: str) -> None:
    """Apaga as falhas de uma chave (usado após um login bem-sucedido daquele e-mail)."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM auth_tentativas WHERE acao = ? AND chave = ? AND sucesso = 0",
            (acao, chave),
        )
