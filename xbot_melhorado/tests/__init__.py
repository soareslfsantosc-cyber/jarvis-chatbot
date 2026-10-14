"""
Testes do XBot (unittest da biblioteca padrão — nenhuma dependência nova).

    python -m unittest discover -v        # a partir da pasta do projeto (onde fica o app.py)

Garantias de segurança desta suíte
----------------------------------
* NENHUM teste usa o seu xbot.db. Este arquivo aponta XBOT_DB_PATH para uma pasta temporária
  ANTES de qualquer importação do app, e cada teste trabalha numa cópia própria de um banco-modelo
  descartável. O último teste (test_zz_banco_real) confere que o xbot.db real não mudou.
* Nenhuma conta real é criada: os usuários dos testes vivem só nos bancos temporários.
* O tempo é simulado (relogio.agora), então "10 minutos de visitante", "15 minutos de bloqueio" e
  "24 horas de espera" são testados sem esperar de verdade.
"""

import atexit
import logging
import os
import shutil
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO_REAL = os.path.join(RAIZ, "xbot.db")


def assinatura_arquivo(caminho):
    """(tamanho, mtime em ns) — ou None se o arquivo não existe."""
    try:
        info = os.stat(caminho)
    except FileNotFoundError:
        return None
    return (info.st_size, info.st_mtime_ns)


# Foto do banco real ANTES de qualquer teste (comparada no último teste).
ASSINATURA_BANCO_REAL_INICIAL = assinatura_arquivo(BANCO_REAL)

PASTA_TEMP = tempfile.mkdtemp(prefix="xbot_testes_")
atexit.register(shutil.rmtree, PASTA_TEMP, ignore_errors=True)

# Rede de proteção: qualquer código que ainda cair no "banco padrão" cai aqui, nunca no xbot.db real.
os.environ["XBOT_DB_PATH"] = os.path.join(PASTA_TEMP, "padrao_nao_usar.db")

# Sem isto o Python imprime avisos de log (ex.: "login bloqueado") no meio da saída dos testes.
# Os testes que precisam ler logs usam assertLogs, que funciona normalmente.
logging.getLogger().addHandler(logging.NullHandler())
