"""
database/visitantes.py
XBot v0.3.0 Beta — Limite de uso do visitante, validado no SERVIDOR

Problema que isto resolve
-------------------------
Antes, o relógio de 10 minutos do visitante vivia dentro do cookie de sessão
("guest_iniciado_em"). Apagar o cookie (ou abrir uma janela anônima) zerava o
relógio. Agora o início do teste fica no banco, preso a uma "impressão" do
visitante — um HMAC de IP + User-Agent — e o cookie só carrega um identificador
aleatório sem poder nenhum.

Regra (a de sempre: 10 minutos, configurável por XBOT_GUEST_SECONDS)
---------------------------------------------------------------------
* O relógio começa na primeira consulta (como antes: ao abrir a página).
* Visitante com cookie conhecido  → continua o relógio dele.
* Cookie novo/apagado, mesma impressão → HERDA o início mais antigo daquela
  impressão: apagar cookies não devolve tempo.
* O esgotamento vale por `cooldown` (24 h por padrão); depois disso a impressão
  ganha um novo teste.
* `max_sessoes` (padrão 1) é quantas janelas de teste independentes uma mesma
  impressão pode abrir dentro do cooldown (aumente para demonstrações em sala
  de aula, onde vários alunos compartilham o mesmo IP e navegador).

Limites conhecidos (documentados no README): quem troca de IP *ou* de navegador
(User-Agent) ganha um novo teste — apagar cookies, não; quem divide IP+navegador com
outros divide o relógio.

Tabela `visitantes` — só guarda HMACs e timestamps; nada pessoal.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass

from database.db import get_connection

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


def id_valido(valor) -> bool:
    return isinstance(valor, str) and bool(_ID_RE.match(valor))


def novo_id() -> str:
    return secrets.token_urlsafe(24)


@dataclass(frozen=True)
class StatusVisitante:
    visitor_id: str       # identificador a gravar no cookie de sessão
    iniciado_em: float    # início (epoch) do relógio que vale para este visitante
    restante: int         # segundos restantes (>= 0)
    bloqueado: bool


def criar_tabelas(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS visitantes (
            visitor_id    TEXT PRIMARY KEY,
            impressao     TEXT NOT NULL,
            iniciado_em   REAL NOT NULL,
            ultimo_acesso REAL NOT NULL
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_visitantes_impressao ON visitantes (impressao, iniciado_em)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_visitantes_iniciado ON visitantes (iniciado_em)"
    )


def consultar(visitor_id, impressao: str, *, agora: float, limite: int,
              cooldown: int, max_sessoes: int) -> StatusVisitante:
    """
    Devolve (e, se preciso, cria) o estado do relógio do visitante.
    Executa numa transação BEGIN IMMEDIATE: duas requisições simultâneas não
    conseguem abrir duas janelas para a mesma impressão.
    """
    if not id_valido(visitor_id):
        visitor_id = None

    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        # identidades cujo cooldown já passou deixam de existir (novo teste liberado)
        conn.execute("DELETE FROM visitantes WHERE iniciado_em <= ?", (agora - cooldown,))

        iniciado_em = None
        if visitor_id:
            linha = conn.execute(
                "SELECT impressao, iniciado_em FROM visitantes WHERE visitor_id = ?", (visitor_id,)
            ).fetchone()
            if linha:
                iniciado_em = linha["iniciado_em"]
                if linha["impressao"] != impressao:
                    # o visitante mudou de rede: a impressão acompanha, para que limpar
                    # o cookie na rede nova também herde o relógio
                    conn.execute(
                        "UPDATE visitantes SET impressao = ?, ultimo_acesso = ? WHERE visitor_id = ?",
                        (impressao, agora, visitor_id),
                    )

        if iniciado_em is None:
            existentes = conn.execute(
                "SELECT iniciado_em FROM visitantes WHERE impressao = ? ORDER BY iniciado_em ASC",
                (impressao,),
            ).fetchall()
            visitor_id = visitor_id or novo_id()
            if len(existentes) >= max_sessoes:
                # sem vaga para uma janela nova: herda o relógio mais antigo (não grava nada,
                # então requisições sem cookie não inflam a tabela)
                iniciado_em = existentes[0]["iniciado_em"]
            else:
                conn.execute(
                    "INSERT INTO visitantes (visitor_id, impressao, iniciado_em, ultimo_acesso) "
                    "VALUES (?, ?, ?, ?)",
                    (visitor_id, impressao, agora, agora),
                )
                iniciado_em = agora

    decorrido = max(0.0, agora - iniciado_em)          # relógio andando para trás não dá bônus
    restante = max(0, int(limite - decorrido))
    return StatusVisitante(visitor_id, iniciado_em, restante, restante <= 0)
