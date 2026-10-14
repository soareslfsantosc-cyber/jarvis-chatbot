"""
historico.py — Histórico de conversas em memória, isolado por DONO da sessão.

Antes: um dict global indexado pelo nome que o PRÓPRIO CLIENTE enviava — qualquer
pessoa lia ou apagava o histórico de qualquer nome (/historico/<nome>).

Agora a chave é (dono, nome de exibição), e o `dono` vem da sessão validada no
servidor: "u:<id>" para usuário logado, "g:<visitante>" para visitante. O nome na
URL só escolhe QUAL conversa do próprio dono — nunca de quem.

Continua em memória (como antes): reiniciar o servidor limpa as conversas. Há tetos
para um cliente mal-intencionado não esgotar a memória.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Dict, List


class HistoricoConversas:
    def __init__(self, max_mensagens: int = 100, max_nomes_por_dono: int = 5,
                 max_conversas: int = 2000):
        self._max_mensagens = max_mensagens
        self._max_nomes = max_nomes_por_dono
        self._max_conversas = max_conversas
        self._dados: "OrderedDict[tuple, List[Dict]]" = OrderedDict()
        self._trava = threading.RLock()

    def obter(self, dono: str, nome: str) -> List[Dict]:
        """Cópia da lista (o chamador pode ler à vontade, sem competir com novas mensagens)."""
        with self._trava:
            return list(self._dados.get((dono, nome), []))

    def adicionar(self, dono: str, nome: str, entrada: Dict) -> None:
        chave = (dono, nome)
        with self._trava:
            if chave not in self._dados:
                self._abrir_vaga(dono)
                self._dados[chave] = []
            self._dados.move_to_end(chave)
            conversa = self._dados[chave]
            conversa.append(entrada)
            if len(conversa) > self._max_mensagens:
                del conversa[:-self._max_mensagens]

    def limpar(self, dono: str, nome: str) -> bool:
        with self._trava:
            return self._dados.pop((dono, nome), None) is not None

    def total_conversas(self) -> int:
        with self._trava:
            return len(self._dados)

    def todas_as_entradas(self) -> List[Dict]:
        with self._trava:
            return [entrada for conversa in self._dados.values() for entrada in conversa]

    def _abrir_vaga(self, dono: str) -> None:
        """Chamado dentro da trava, antes de criar uma conversa nova."""
        do_dono = [chave for chave in self._dados if chave[0] == dono]
        if len(do_dono) >= self._max_nomes:
            self._dados.pop(do_dono[0], None)            # a menos recente deste dono
        while len(self._dados) >= self._max_conversas:
            self._dados.popitem(last=False)              # a menos recente de todas
