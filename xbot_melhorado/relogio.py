"""
relogio.py — Relógio único do XBot.

Todo código que decide algo pelo tempo (limite de visitante, bloqueio de login,
retenção de tentativas) chama relogio.agora(). Assim os testes controlam o tempo
sem dormir de verdade e sem mexer no time.time() global (que o Flask também usa
para assinar os cookies de sessão).
"""

import time


def agora() -> float:
    """Segundos desde a época Unix (UTC)."""
    return time.time()
