"""
app_improved.py — mantido só por compatibilidade.

Este arquivo era uma SEGUNDA versão do servidor (sem login, sem /sessao, sem /registrar), e a
interface atual chama justamente essas rotas. Desde a revisão de segurança existe UM só
aplicativo, o app.py, que inclui tudo o que vivia aqui (quiz, exercícios, estatísticas).

Quem ainda executa `python app_improved.py` (como o README antigo mandava) continua funcionando:
este arquivo apenas delega para o app.py, com a mesma configuração (XBOT_* / .env).
"""

from app import XBotIA, create_app, main  # noqa: F401  (reexporta a API pública)


def __getattr__(nome):
    """`from app_improved import app` / `gunicorn app_improved:app` continuam valendo."""
    if nome == "app":
        import app as modulo_app
        return modulo_app.app            # criado sob demanda (veja __getattr__ em app.py)
    raise AttributeError(f"module {__name__!r} has no attribute {nome!r}")


if __name__ == "__main__":
    raise SystemExit(main())
