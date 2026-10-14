"""
database/reasoning.py
XBot v0.3.0 Beta — Camada de Raciocínio Cognitivo Heurístico
XByte Games Studios

Implementa raciocínio heurístico sobre a base SQLite existente.
Trabalha POR CIMA de db.py sem substituir nenhuma função existente.

ARQUITETURA:
  mensagem → preprocessamento → 20 parâmetros → score ponderado → ranking
           → correlação entre candidatos → contexto da sessão
           → construção da resposta → sugestões de próximos tópicos

Os 20 parâmetros são independentes, transparentes e mensuráveis.
Cada um contribui com um peso para o score final de cada candidato.
O resultado explica POR QUE aquele conhecimento foi selecionado.
"""

import re
import logging
import unicodedata
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter

logger = logging.getLogger(__name__)

# Importações do db.py existente (somente o que já existe — sem modificá-lo)
import sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from database.db import get_connection, _sem_acento, _STOPWORDS_PT

# Stopwords adicionais para linguagem casual brasileira (específicas do reasoning)
_SW_EXTRAS = {
    'pra', 'pro', 'pras', 'pros', 'mim', 'sim', 'nem', 'num',
    'ja', 'la', 'ca', 'ai', 'bem', 'sei', 'foi', 'ser', 'ter',
    'dar', 'ver', 'ler', 'eles', 'elas', 'nos', 'vos',
    'esses', 'essas', 'estes', 'estas', 'aqueles', 'aquelas',
    'tanto', 'tudo', 'nada', 'algo', 'fala', 'explica', 'conte',
    'diga', 'voce', 'ola', 'hey', 'bom', 'boa', 'quero', 'gostaria',
    'preciso', 'pode', 'poderia', 'seria', 'tenho', 'tem', 'vai',
    'vou', 'faz', 'faco', 'quer', 'diz', 'ele', 'ela', 'dele', 'nela',
    'meu', 'minha', 'seu', 'sua', 'esse', 'essa', 'este', 'esta',
    'por', 'com', 'sem', 'ate', 'apos', 'antes', 'depois', 'quando',
    'onde', 'porque', 'pois', 'mas', 'entao', 'assim', 'ainda',
}
_SW_TOTAL = _STOPWORDS_PT | _SW_EXTRAS


# ============================================================================
# OS 20 PARÂMETROS DE RACIOCÍNIO
# ============================================================================

PARAMETROS = {

    # ── GRUPO 1: Correspondência de Keywords ────────────────────────────────
    'P01_keyword_exata': {
        'peso': 10.0, 'intervalo': '[0.0, 1.0]',
        'descricao': (
            "Proporção de keywords COMPLETAS do registro que aparecem como "
            "substring exata na mensagem normalizada. Sinal mais forte de match."
        ),
    },
    'P02_keyword_parcial': {
        'peso': 4.0, 'intervalo': '[0.0, 1.0]',
        'descricao': (
            "Proporção dos TERMOS DA QUERY que aparecem em algum keyword do "
            "registro. Mede cobertura da pergunta, não do registro."
        ),
    },
    'P03_titulo_match': {
        'peso': 5.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Proporção das palavras do TÍTULO que aparecem na mensagem.",
    },
    'P04_cobertura_termos': {
        'peso': 6.0, 'intervalo': '[0.0, 1.0]',
        'descricao': (
            "Porcentagem dos termos significativos da mensagem cobertos "
            "pelas keywords/título do registro (word-boundary, sem substring solto)."
        ),
    },
    'P05_especificidade_keyword': {
        'peso': 3.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Bônus por keywords longas (>= 10 chars) que batem — mais específicas.",
    },

    # ── GRUPO 2: Contexto da Conversa ───────────────────────────────────────
    'P06_continuidade_tematica': {
        'peso': 4.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Registro na mesma categoria da última resposta dada.",
    },
    'P07_contexto_sessao': {
        'peso': 3.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Termos das últimas mensagens cobertos por este registro.",
    },
    'P08_historico_recente': {
        'peso': 1.5, 'intervalo': '[-1.0, 1.0]',
        'descricao': "Penaliza repetição imediata; leve bônus para tópico recente não-imediato.",
    },

    # ── GRUPO 3: Qualidade da Evidência ─────────────────────────────────────
    'P09_densidade_evidencias': {
        'peso': 4.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Quantidade de keywords distintas que batem (normalizado por 5).",
    },
    'P10_multiplas_evidencias': {
        'peso': 3.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Bônus binário quando >= 3 keywords distintas batem.",
    },
    'P11_completude_conteudo': {
        'peso': 2.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Registros com conteúdo mais completo (até 600 chars) recebem leve bônus.",
    },
    'P12_especificidade_titulo': {
        'peso': 3.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Títulos com mais palavras são mais específicos.",
    },

    # ── GRUPO 4: Interpretação Semântica ────────────────────────────────────
    'P13_tipo_pergunta': {
        'peso': 3.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Alinha tipo de pergunta (definição/processo/aplicação/...) com o conteúdo.",
    },
    'P14_categoria_detectada': {
        'peso': 3.5, 'intervalo': '[0.0, 1.0]',
        'descricao': "Categoria inferida dos termos-sinal da pergunta bate com a do registro.",
    },
    'P15_proximidade_semantica': {
        'peso': 2.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Overlap de keywords com outros candidatos de alto score (cluster).",
    },

    # ── GRUPO 5: Penalizações ───────────────────────────────────────────────
    'P16_penalizacao_generica': {
        'peso': -3.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Penaliza títulos de 1 palavra quando há candidatos mais específicos.",
    },
    'P17_ambiguidade_query': {
        'peso': -2.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Penaliza perguntas com < 2 termos significativos e sem contexto.",
    },

    # ── GRUPO 6: Correlação e Confiança Final ───────────────────────────────
    'P18_correlacao_keywords': {
        'peso': 2.5, 'intervalo': '[0.0, 1.0]',
        'descricao': "Proporção dos top candidatos que compartilham keyword com este registro.",
    },
    'P19_categoria_dominante': {
        'peso': 2.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Bônus quando >= 40% dos top candidatos são da mesma categoria.",
    },
    'P20_margem_lideranca': {
        'peso': 3.0, 'intervalo': '[0.0, 1.0]',
        'descricao': "Margem normalizada do 1º para o 2º colocado após re-ranking.",
    },
}

_PESO = {k: v['peso'] for k, v in PARAMETROS.items()}

# ── Sinais de categoria na pergunta ────────────────────────────────────────
_SINAIS_CATEGORIA: Dict[str, set] = {
    'desenvolvimento_web': {
        'html', 'css', 'javascript', 'js', 'web', 'frontend', 'backend',
        'tag', 'elemento', 'estilo', 'dom', 'formulario', 'pagina',
        'site', 'navegador', 'browser', 'flexbox', 'grid', 'responsivo',
        'estilizar', 'estilizacao',
    },
    'programacao': {
        'python', 'codigo', 'funcao', 'classe', 'objeto', 'variavel',
        'flask', 'django', 'biblioteca', 'programar', 'script',
        'metodo', 'heranca', 'polimorfismo', 'typescript',
        'nodejs', 'npm', 'git', 'sql', 'banco', 'algoritmo', 'poo', 'oop',
    },
    'hardware': {
        'hardware', 'processador', 'memoria', 'placa', 'chip',
        'cpu', 'ram', 'ssd', 'hd', 'componente', 'gabinete',
        'transistor', 'transistores', 'litografia', 'barramento', 'interface',
    },
    'historia_computacao': {
        'geracao', 'historico', 'historia', 'evolucao',
        'primeira', 'segunda', 'terceira', 'quarta', 'quinta',
        'eniac', 'valvula', 'circuito', 'microprocessador',
    },
    'ia': {
        'inteligencia', 'artificial', 'machine', 'learning', 'neural',
        'llm', 'gpt', 'modelo', 'aprendizado', 'overfitting', 'dataset',
    },
    'redes': {
        'rede', 'protocolo', 'internet', 'tcp', 'ip', 'dns',
        'roteador', 'switch', 'http', 'arpanet', 'lan', 'wan',
        'wifi', 'conexao', 'servidor', 'pacote', 'banda',
    },
    'software': {
        'software', 'programa', 'licenca', 'aplicativo',
        'firmware', 'saas', 'pirataria', 'sistema', 'operacional',
        'protecao', 'proteger',
    },
    'futuro_tecnologia': {
        'quantico', 'quantum', 'nuvem', 'cloud', 'iot', 'dispositivo',
        'fotonica', 'neuromorfic', 'nanotecnologia',
    },
}

_TIPOS_PERGUNTA = {
    'definicao':  r'o que (e|eh|é|sao|são)|o que significa|defin[ia]|conceito|significado|explica[r]?',
    'processo':   r'como (funciona|usar|fazer|criar|implementar|trabalha|e feito)|de que (forma|maneira)',
    'aplicacao':  r'para que (serve|e usado|é usado)|onde (usar|aplicar)|beneficio|vantagem|uso de',
    'comparacao': r'diferen[cç]a entre|qual (a|e|é) (melhor|diferenca)|vs\.?|versus|comparar|comparacao',
    'exemplo':    r'exemplo de|como (é|e|seria) um exemplo|mostra[r]?|ilustra[r]?',
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AnaliseQuery:
    mensagem_original: str
    mensagem_norm:     str
    termos:            List[str]
    palavras_msg:      set
    tipo_pergunta:     str
    categoria_detectada: Optional[str]
    termos_contexto:   List[str]
    ultima_categoria:  Optional[str]
    ultimos_titulos:   List[str]
    e_continuacao:     bool
    e_pergunta_curta:  bool


@dataclass
class CandidatoRaciocinio:
    registro:           Any
    valores_param:      Dict[str, float] = field(default_factory=dict)
    score_final:        float = 0.0
    keywords_que_batem: List[str] = field(default_factory=list)

    @property
    def titulo(self) -> str:     return self.registro['titulo']
    @property
    def conteudo(self) -> str:   return self.registro['conteudo']
    @property
    def categoria(self) -> str:  return self.registro['categoria']
    @property
    def fonte(self) -> str:      return self.registro['fonte']


@dataclass
class ResultadoRaciocinio:
    vencedor:            Optional[CandidatoRaciocinio]
    todos_candidatos:    List[CandidatoRaciocinio]
    nivel_confianca:     str
    topicos_relacionados: List[str]
    sugestoes_proximas:  List[str]
    resposta_construida: str
    analise:             AnaliseQuery
    contexto_utilizado:  bool
    margem_lideranca:    float
    explicacao_debug:    str


# ============================================================================
# MOTOR DE RACIOCÍNIO PRINCIPAL
# ============================================================================

class RaciocinioCognitivo:
    """
    Motor de raciocínio heurístico do XBot. Avalia cada registro do SQLite
    com 20 parâmetros, aplica correlação entre candidatos, usa contexto de
    sessão e retorna o resultado mais relevante com nível de confiança,
    tópicos correlacionados e sugestões de próximas perguntas.

    Não usa LLMs, embeddings nem qualquer API externa — tudo local,
    determinístico e explicável.
    """

    def __init__(self):
        self._registros: Optional[list] = None

    def analisar(self, mensagem: str, historico_sessao: list = None) -> ResultadoRaciocinio:
        if historico_sessao is None:
            historico_sessao = []

        analise = self._preprocessar(mensagem, historico_sessao)
        registros = self._carregar_registros()

        candidatos: List[CandidatoRaciocinio] = []
        for reg in registros:
            c = CandidatoRaciocinio(registro=reg)
            c.valores_param      = self._calcular_params_individuais(reg, analise)
            c.keywords_que_batem = self._kws_que_batem(reg, analise)
            c.score_final = self._score_soma(
                c.valores_param,
                excluir=['P15_proximidade_semantica', 'P18_correlacao_keywords',
                         'P19_categoria_dominante', 'P20_margem_lideranca'],
            )
            candidatos.append(c)

        validos = sorted(
            [c for c in candidatos if c.score_final > 0],
            key=lambda c: c.score_final, reverse=True,
        )
        top10 = validos[:10]

        if not top10:
            return self._sem_resultado(analise)

        cat_dominante = self._detectar_categoria_dominante(top10)
        for c in top10:
            extras = self._calcular_params_cross(c, top10, cat_dominante)
            c.valores_param.update(extras)
            c.score_final += self._score_soma(extras)

        top10.sort(key=lambda c: c.score_final, reverse=True)
        vencedor = top10[0]
        segundo  = top10[1] if len(top10) > 1 else None

        margem = (vencedor.score_final - segundo.score_final) if segundo else vencedor.score_final
        p20 = min(margem / 25.0, 1.0)
        vencedor.valores_param['P20_margem_lideranca'] = p20
        vencedor.score_final += p20 * _PESO['P20_margem_lideranca']

        nivel_conf = self._calcular_confianca(vencedor, segundo, analise)
        relacionados = self._encontrar_relacionados(vencedor, top10, registros)
        sugestoes = self._prever_proximas(vencedor, analise)
        resposta = self._construir_resposta(vencedor, nivel_conf, relacionados, sugestoes, analise)
        explicacao = self._gerar_explicacao(vencedor, analise, nivel_conf, margem)

        logger.info(
            f"[Reasoning] '{vencedor.titulo}' | confiança={nivel_conf} | "
            f"score={vencedor.score_final:.1f} | margem={margem:.1f} | "
            f"evidências={len(vencedor.keywords_que_batem)}"
        )

        return ResultadoRaciocinio(
            vencedor=vencedor, todos_candidatos=top10, nivel_confianca=nivel_conf,
            topicos_relacionados=relacionados, sugestoes_proximas=sugestoes,
            resposta_construida=resposta, analise=analise,
            contexto_utilizado=(analise.e_continuacao and bool(analise.termos_contexto)),
            margem_lideranca=margem, explicacao_debug=explicacao,
        )

    # ── Preprocessamento ────────────────────────────────────────────────────

    def _preprocessar(self, mensagem: str, historico: list) -> AnaliseQuery:
        msg_norm  = _sem_acento(mensagem.lower().strip())
        palavras  = set(re.findall(r'\w+', msg_norm))

        termos = [p for p in palavras if len(p) >= 3 and p not in _SW_TOTAL]

        tipo = 'geral'
        for nome, padrao in _TIPOS_PERGUNTA.items():
            if re.search(padrao, msg_norm):
                tipo = nome
                break

        categoria_detectada = None
        melhor_overlap = 0
        for cat, sinais in _SINAIS_CATEGORIA.items():
            sinais_norm = {_sem_acento(s) for s in sinais}
            overlap = len(palavras & sinais_norm)
            if overlap > melhor_overlap or (
                overlap == melhor_overlap and overlap > 0 and
                cat in ('redes', 'ia', 'futuro_tecnologia')
            ):
                melhor_overlap = overlap
                categoria_detectada = cat
        if melhor_overlap == 0:
            categoria_detectada = None

        msgs_usuario = []
        for h in historico[-6:]:
            texto = h.get('usuario', h.get('mensagem', h.get('content', '')))
            if texto and texto.strip():
                msgs_usuario.append(texto)

        termos_contexto: List[str] = []
        for m in msgs_usuario[-3:]:
            termos_m = [
                p for p in re.findall(r'\w+', _sem_acento(m.lower()))
                if len(p) >= 4 and p not in _SW_TOTAL
            ]
            termos_contexto.extend(termos_m)
        vistos: set = set()
        termos_contexto_unicos: List[str] = []
        for t in termos_contexto:
            if t not in vistos:
                vistos.add(t)
                termos_contexto_unicos.append(t)

        ultima_categoria: Optional[str] = None
        ultimos_titulos:  List[str]     = []
        for h in reversed(historico[-6:]):
            cat_h = h.get('categoria_respondida', None)
            tit_h = h.get('titulo_conhecimento', None)
            if cat_h and not ultima_categoria:
                ultima_categoria = cat_h
            if tit_h and tit_h not in ultimos_titulos:
                ultimos_titulos.append(tit_h)
            if len(ultimos_titulos) >= 3:
                break

        sinais_continuacao = {
            'e', 'isso', 'ele', 'ela', 'aquilo', 'nele', 'nela',
            'disso', 'dele', 'dela', 'tambem', 'outro', 'outra',
            'mais', 'agora', 'entao', 'ai',
        }
        e_continuacao = (
            len(termos) <= 2 and bool(historico) and bool(palavras & sinais_continuacao)
        )

        return AnaliseQuery(
            mensagem_original=mensagem, mensagem_norm=msg_norm, termos=termos,
            palavras_msg=palavras, tipo_pergunta=tipo,
            categoria_detectada=categoria_detectada,
            termos_contexto=termos_contexto_unicos, ultima_categoria=ultima_categoria,
            ultimos_titulos=ultimos_titulos, e_continuacao=e_continuacao,
            e_pergunta_curta=(len(termos) < 2 and not termos_contexto_unicos),
        )

    # ── Cálculo dos parâmetros individuais ──────────────────────────────────

    def _calcular_params_individuais(self, reg, analise: AnaliseQuery) -> Dict[str, float]:
        params: Dict[str, float] = {}
        msg_norm = analise.mensagem_norm
        termos   = analise.termos

        ctx = ' '.join(analise.termos_contexto)
        msg_exp = (msg_norm + ' ' + ctx).strip()
        palavras_exp = set(re.findall(r'\w+', msg_exp))

        kws_norm = [
            _sem_acento(k.strip().lower())
            for k in reg['palavras_chave'].split(',') if k.strip()
        ]
        titulo_norm  = _sem_acento(reg['titulo'].lower())
        titulo_words = {
            _sem_acento(w) for w in re.findall(r'\w+', reg['titulo'].lower())
            if len(w) >= 3 and w not in _SW_TOTAL
        }

        # P01: Keywords exatas
        kws_exatas = [kw for kw in kws_norm if len(kw) >= 5 and kw in msg_exp]
        params['P01_keyword_exata'] = (
            len(kws_exatas) / max(len(kws_norm), 1) if kws_exatas else 0.0
        )

        # P02: Termos da query cobertos por palavras nos keywords
        kw_palavras_set = set()
        for kw in kws_norm:
            kw_palavras_set.update(re.findall(r'\w+', kw))
        termos_cobertos_p02 = sum(
            1 for t in (termos + analise.termos_contexto) if t in kw_palavras_set
        )
        params['P02_keyword_parcial'] = min(
            termos_cobertos_p02 / max(len(termos) + len(analise.termos_contexto), 1), 1.0
        )

        # P03: Título match
        titulo_hits = titulo_words & palavras_exp
        params['P03_titulo_match'] = (
            len(titulo_hits) / max(len(titulo_words), 1) if titulo_words else 0.0
        )

        # P04: Cobertura dos termos (word-boundary)
        titulo_word_set = set(re.findall(r'\w+', titulo_norm))
        if termos:
            cobertos = sum(1 for t in termos if t in kw_palavras_set or t in titulo_word_set)
            cobertos_ctx = sum(1 for t in analise.termos_contexto if t in kw_palavras_set)
            params['P04_cobertura_termos'] = min((cobertos + cobertos_ctx * 0.4) / len(termos), 1.0)
        else:
            params['P04_cobertura_termos'] = 0.0

        # P05: Especificidade das keywords
        kws_longas = [kw for kw in kws_exatas if len(kw) >= 10]
        params['P05_especificidade_keyword'] = min(len(kws_longas) * 0.4, 1.0)

        # P06: Continuidade temática
        params['P06_continuidade_tematica'] = (
            1.0 if analise.ultima_categoria and reg['categoria'] == analise.ultima_categoria else 0.0
        )

        # P07: Contexto de sessão
        if analise.termos_contexto:
            ctx_cobertos = sum(
                1 for t in analise.termos_contexto
                if t in kw_palavras_set or t in titulo_norm
            )
            params['P07_contexto_sessao'] = min(ctx_cobertos / len(analise.termos_contexto), 1.0)
        else:
            params['P07_contexto_sessao'] = 0.0

        # P08: Histórico recente
        titulo_lower = reg['titulo'].lower()
        ultimos_lower = [t.lower() for t in analise.ultimos_titulos]
        if ultimos_lower and titulo_lower == ultimos_lower[0]:
            params['P08_historico_recente'] = -0.5
        elif titulo_lower in ultimos_lower[1:]:
            params['P08_historico_recente'] = 0.3
        else:
            params['P08_historico_recente'] = 0.0

        # P09/P10: Densidade e múltiplas evidências
        kws_batem = {
            kw for kw in kws_norm
            if (len(kw) < 5 and kw in palavras_exp) or (len(kw) >= 5 and kw in msg_exp)
        }
        params['P09_densidade_evidencias'] = min(len(kws_batem) / 5.0, 1.0)
        params['P10_multiplas_evidencias'] = 1.0 if len(kws_batem) >= 3 else 0.0

        # P11: Completude do conteúdo
        params['P11_completude_conteudo'] = min(len(reg['conteudo']) / 600.0, 1.0)

        # P12: Especificidade do título
        n_words_titulo = len([w for w in re.findall(r'\w+', reg['titulo']) if len(w) >= 3])
        params['P12_especificidade_titulo'] = min(n_words_titulo / 4.0, 1.0)

        # P13: Tipo de pergunta alinhado
        tipo_ok = False
        conteudo_lower = reg['conteudo'].lower()
        if analise.tipo_pergunta == 'definicao':
            tipo_ok = True
        elif analise.tipo_pergunta == 'processo':
            tipo_ok = any(w in conteudo_lower for w in ('como', 'funciona', 'processo', 'etapa', 'passo', 'usando'))
        elif analise.tipo_pergunta == 'aplicacao':
            tipo_ok = any(w in conteudo_lower for w in ('serve', 'usado', 'aplicacao', 'uso', 'utilizado', 'permite', 'vantagem'))
        elif analise.tipo_pergunta == 'comparacao':
            tipo_ok = any(w in conteudo_lower for w in ('diferenca', 'diferença', 'vs', 'versus', 'comparando', 'enquanto'))
        elif analise.tipo_pergunta == 'exemplo':
            tipo_ok = any(w in conteudo_lower for w in ('exemplo', 'ex:', 'ex.', 'ilustra', 'caso'))
        params['P13_tipo_pergunta'] = 1.0 if tipo_ok else 0.0

        # P14: Categoria detectada
        params['P14_categoria_detectada'] = (
            1.0 if analise.categoria_detectada and reg['categoria'] == analise.categoria_detectada else 0.0
        )

        # P16: Penalização por genericidade
        n_palavras_titulo = len(re.findall(r'\w+', reg['titulo']))
        params['P16_penalizacao_generica'] = 1.0 if n_palavras_titulo <= 1 else 0.0

        # P17: Ambiguidade
        params['P17_ambiguidade_query'] = 1.0 if analise.e_pergunta_curta else 0.0

        params['P15_proximidade_semantica'] = 0.0
        params['P18_correlacao_keywords']   = 0.0
        params['P19_categoria_dominante']   = 0.0
        params['P20_margem_lideranca']      = 0.0

        return params

    def _kws_que_batem(self, reg, analise: AnaliseQuery) -> List[str]:
        ctx = ' '.join(analise.termos_contexto)
        msg_ex = (analise.mensagem_norm + ' ' + ctx).strip()
        pals_ex = set(re.findall(r'\w+', msg_ex))
        kws_norm = [
            _sem_acento(k.strip().lower())
            for k in reg['palavras_chave'].split(',') if k.strip()
        ]
        return [
            kw for kw in kws_norm
            if (len(kw) < 5 and kw in pals_ex) or (len(kw) >= 5 and kw in msg_ex)
        ]

    # ── Parâmetros cross-candidate ───────────────────────────────────────────

    def _calcular_params_cross(self, candidato, top, cat_dominante):
        params: Dict[str, float] = {}
        kws_proprio = set(candidato.keywords_que_batem)

        overlaps = []
        for outro in top:
            if outro.titulo == candidato.titulo:
                continue
            kws_outro = set(outro.keywords_que_batem)
            uniao = kws_proprio | kws_outro
            if uniao:
                overlaps.append(len(kws_proprio & kws_outro) / len(uniao))
        params['P15_proximidade_semantica'] = sum(overlaps) / len(overlaps) if overlaps else 0.0

        outros = [c for c in top if c.titulo != candidato.titulo]
        if outros and kws_proprio:
            compartilham = sum(1 for c in outros if set(c.keywords_que_batem) & kws_proprio)
            params['P18_correlacao_keywords'] = compartilham / len(outros)
        else:
            params['P18_correlacao_keywords'] = 0.0

        params['P19_categoria_dominante'] = (
            1.0 if cat_dominante and candidato.categoria == cat_dominante else 0.0
        )
        return params

    def _detectar_categoria_dominante(self, candidatos):
        if not candidatos:
            return None
        cats = Counter(c.categoria for c in candidatos)
        mais_comum, contagem = cats.most_common(1)[0]
        return mais_comum if (contagem / len(candidatos)) >= 0.40 else None

    # ── Score e Confiança ────────────────────────────────────────────────────

    def _score_soma(self, params, excluir=None):
        excluir = excluir or []
        total = sum(
            v * _PESO.get(k, 0.0) for k, v in params.items()
            if k not in excluir and k in _PESO
        )
        return max(total, 0.0)

    def _calcular_confianca(self, vencedor, segundo, analise):
        score  = vencedor.score_final
        margem = (vencedor.score_final - segundo.score_final) if segundo else score
        n_ev   = len(vencedor.keywords_que_batem)

        if score >= 28 and margem >= 8 and n_ev >= 2:
            return 'alta'
        elif score >= 14 and margem >= 3:
            return 'media'
        elif score >= 5:
            return 'baixa'
        else:
            return 'nenhuma'

    # ── Correlação entre conhecimentos ───────────────────────────────────────

    def _encontrar_relacionados(self, vencedor, top, todos):
        relacionados: set = set()
        limiar = vencedor.score_final * 0.30
        for c in top[1:6]:
            if c.score_final >= limiar:
                relacionados.add(c.titulo)

        kws_v = set(
            _sem_acento(k.strip().lower())
            for k in vencedor.registro['palavras_chave'].split(',') if k.strip()
        )
        cat_v = vencedor.categoria

        for reg in todos:
            if reg['titulo'].lower() == vencedor.titulo.lower():
                continue
            kws_r = set(
                _sem_acento(k.strip().lower())
                for k in reg['palavras_chave'].split(',') if k.strip()
            )
            overlap = len(kws_v & kws_r)
            if overlap >= 2 or (reg['categoria'] == cat_v and overlap >= 1):
                relacionados.add(reg['titulo'])

        relacionados.discard(vencedor.titulo)
        top_titulos = [c.titulo for c in top[1:]]
        ordenados = (
            [t for t in top_titulos if t in relacionados] +
            [t for t in relacionados if t not in top_titulos]
        )
        return ordenados[:5]

    # ── Previsão de próximas perguntas ───────────────────────────────────────

    def _prever_proximas(self, vencedor, analise):
        todos = self._carregar_registros()
        cat = vencedor.categoria
        kws_v = set(
            _sem_acento(k.strip().lower())
            for k in vencedor.registro['palavras_chave'].split(',') if k.strip()
        )
        usados = {vencedor.titulo.lower()} | {t.lower() for t in analise.ultimos_titulos}

        candidatos_prox: List[Tuple[float, str]] = []
        for reg in todos:
            if reg['titulo'].lower() in usados:
                continue
            kws_r = set(
                _sem_acento(k.strip().lower())
                for k in reg['palavras_chave'].split(',') if k.strip()
            )
            score_prox = 0.0
            if reg['categoria'] == cat:
                score_prox += 3.0
            overlap = len(kws_v & kws_r)
            score_prox += overlap * 0.5
            if score_prox >= 2.0:
                candidatos_prox.append((score_prox, reg['titulo']))

        candidatos_prox.sort(key=lambda x: x[0], reverse=True)
        return [f'O que é {titulo}?' for _, titulo in candidatos_prox[:3]]

    # ── Construção da resposta ───────────────────────────────────────────────

    def _construir_resposta(self, vencedor, nivel_conf, relacionados, sugestoes, analise):
        resposta = vencedor.conteudo
        if relacionados:
            resposta += f"\n\n📚 Tópicos relacionados: {' • '.join(relacionados[:4])}"
        if sugestoes and nivel_conf in ('alta', 'media'):
            resposta += f"\n💡 Você pode perguntar também: {'  |  '.join(sugestoes[:2])}"
        return resposta

    def _sem_resultado(self, analise):
        return ResultadoRaciocinio(
            vencedor=None, todos_candidatos=[], nivel_confianca='nenhuma',
            topicos_relacionados=[], sugestoes_proximas=[], resposta_construida='',
            analise=analise, contexto_utilizado=False, margem_lideranca=0.0,
            explicacao_debug='Nenhum candidato com score > 0 encontrado.',
        )

    def _gerar_explicacao(self, vencedor, analise, nivel_conf, margem):
        p = vencedor.valores_param
        linhas = [
            f"Vencedor: '{vencedor.titulo}'",
            f"  Score final    : {vencedor.score_final:.1f}",
            f"  Confiança      : {nivel_conf}",
            f"  Margem 1º→2º  : {margem:.1f}",
            f"  Categoria      : {vencedor.categoria}",
            f"  Fonte          : {vencedor.fonte}",
            f"  Tipo pergunta  : {analise.tipo_pergunta}",
            f"  Cat. detectada : {analise.categoria_detectada}",
            f"  Contexto usado : {analise.e_continuacao}",
            f"  Keywords batem : {', '.join(vencedor.keywords_que_batem[:6]) or 'nenhuma'}",
            "", "Contribuição dos parâmetros (valor × peso → contribuição):",
        ]
        contribs = []
        for param, valor in p.items():
            peso = _PESO.get(param, 0.0)
            contrib = valor * peso
            if abs(contrib) > 0.01:
                contribs.append((abs(contrib), param, valor, peso, contrib))
        for _, param, valor, peso, contrib in sorted(contribs, reverse=True)[:8]:
            sinal = '+' if contrib >= 0 else ''
            linhas.append(f"  {param:<32s}: {valor:.2f} × {peso:+.1f} = {sinal}{contrib:.2f}")
        return '\n'.join(linhas)

    # ── Cache e utilitários ───────────────────────────────────────────────────

    def _carregar_registros(self) -> list:
        if self._registros is None:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM knowledge ORDER BY id")
                self._registros = cursor.fetchall()
            logger.debug(f"[Reasoning] Cache carregado: {len(self._registros)} registros")
        return self._registros

    def invalidar_cache(self):
        self._registros = None
        logger.info("[Reasoning] Cache de registros invalidado.")

    def resumo_parametros(self) -> str:
        linhas = ["=" * 60, "  OS 20 PARÂMETROS DE RACIOCÍNIO DO XBOT", "=" * 60]
        grupos = {
            'GRUPO 1 — Correspondência de Keywords': [f'P0{i}' for i in range(1, 6)],
            'GRUPO 2 — Contexto da Conversa':        ['P06', 'P07', 'P08'],
            'GRUPO 3 — Qualidade da Evidência':      ['P09', 'P10', 'P11', 'P12'],
            'GRUPO 4 — Interpretação Semântica':     ['P13', 'P14', 'P15'],
            'GRUPO 5 — Penalizações':                ['P16', 'P17'],
            'GRUPO 6 — Correlação e Confiança Final':['P18', 'P19', 'P20'],
        }
        for grupo, prefixos in grupos.items():
            linhas.append(f"\n{grupo}")
            for k, v in PARAMETROS.items():
                if any(k.startswith(p) for p in prefixos):
                    linhas.append(f"  {k:<32s} peso={v['peso']:+.1f}  [{v['intervalo']}]")
                    linhas.append(f"    {v['descricao'][:80]}")
        linhas.append("\n" + "=" * 60)
        return '\n'.join(linhas)
