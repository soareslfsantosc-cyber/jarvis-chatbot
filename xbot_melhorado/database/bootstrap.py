"""
database/bootstrap.py
XBot v0.3.0 Beta — Inicialização do banco na subida do servidor

Regra de ouro: NUNCA mexer em conhecimento que já existe.

Antes, a cada start o app rodava run_apostilas_seed(), cujo modo "update" reescreve
as palavras-chave de registros já refinados (html, python basico, design digital)
e reinsere tópicos que a auditoria apagou de propósito (protocolos e topologias de
rede). Agora:

  * tabelas que faltam são criadas (aditivo);
  * os seeds só rodam quando a tabela `knowledge` está VAZIA (instalação nova);
  * um banco que já tem conhecimento não é tocado.

Para reaplicar as apostilas de propósito, use o script manual (database/apostilas_seed.py).
"""

from __future__ import annotations

import logging

from database.auth import contar_usuarios, init_auth_db
from database.db import caminho_banco, contar_conhecimento, init_db

logger = logging.getLogger(__name__)

# Contagem ESTRITA (db.contar_conhecimento): se o banco estiver inacessível, o início falha em
# vez de "achar que está vazio" e semear por cima.
_contar_conhecimento = contar_conhecimento


def inicializar_banco() -> dict:
    """
    Cria o que falta e semeia apenas um banco de conhecimento vazio.
    Retorna um resumo: {'semeado': bool, 'registros': int, 'usuarios': int, 'banco': str}.
    """
    init_db()
    init_auth_db()

    semeado = False
    if _contar_conhecimento() == 0:
        from database.apostilas_seed import run_apostilas_seed
        from database.seed import run_seed

        logger.info("Tabela knowledge vazia: executando seed inicial (uma única vez).")
        _enc, ins, dup = run_seed()
        logger.info(f"Seed base — Inseridos: {ins} | Duplicados: {dup}")
        _enc, ins, upd, _ign = run_apostilas_seed()
        logger.info(f"Apostilas — Inseridos: {ins} | Atualizados: {upd}")
        semeado = True

    resumo = {
        "semeado": semeado,
        "registros": _contar_conhecimento(),
        "usuarios": contar_usuarios(),
        "banco": caminho_banco(),
    }
    logger.info(
        f"SQLite pronto: {resumo['registros']} registros de conhecimento, "
        f"{resumo['usuarios']} usuário(s)."
    )
    return resumo
