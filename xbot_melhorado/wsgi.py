"""
wsgi.py — entrada para servidores de produção (o servidor embutido do Flask é só para desenvolvimento).

    # Windows / Linux / macOS (pip install waitress) — um processo, várias threads
    waitress-serve --listen=127.0.0.1:8000 wsgi:app

    # Linux / macOS (pip install gunicorn); --preload faz o seed inicial rodar uma vez só
    gunicorn --preload -w 1 --threads 4 -b 127.0.0.1:8000 wsgi:app

Use UM processo (várias threads, como acima): os históricos de conversa e o andamento dos
quizzes ficam na memória do processo, e vários processos não os compartilham. O limite de tempo
do visitante, as contas e as tentativas de login ficam no SQLite e valem para qualquer
quantidade de processos.

Requer XBOT_SECRET_KEY no ambiente (ou no arquivo .env). Sem ela o servidor NÃO sobe e a
mensagem de erro explica como gerar uma. Coloque um proxy HTTPS na frente (nginx, Caddy...) e
informe XBOT_TRUSTED_PROXIES=1 para o servidor enxergar o IP real do visitante.
"""

import logging

from app import create_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = create_app()
