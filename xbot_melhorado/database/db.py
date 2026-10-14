"""
database/db.py
XBot v0.3.0 Beta — Camada de Banco de Dados SQLite
XByte Games Studios

Responsabilidades deste módulo:
  - Criar o arquivo xbot.db se não existir
  - Criar as tabelas necessárias se não existirem
  - Fornecer conexões seguras (com context manager)
  - Fechar corretamente as conexões

Uso básico:
    from database.db import get_connection, init_db

    # Inicializar na startup do Flask:
    init_db()

    # Fazer uma consulta:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM knowledge")
        resultados = cursor.fetchall()
"""

import re
import sqlite3
import unicodedata
import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Caminho do banco de dados.
# Fica na raiz do projeto (junto com app.py), não dentro de database/.
# os.path.dirname(__file__)  →  .../xbot_melhorado/database
# ..  →  .../xbot_melhorado
DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DB_DIR, "xbot.db")   # caminho PADRÃO (mantido por compatibilidade)

# Caminho efetivamente usado pelo processo. Ordem de prioridade:
#   1) configurar_caminho(...)  — chamado pelo app com XBOT_DB_PATH já validado
#   2) variável de ambiente XBOT_DB_PATH (scripts avulsos: seed.py, refine.py...)
#   3) DB_PATH (xbot.db na raiz do projeto)
# É resolvido a CADA conexão: os testes apontam para um banco temporário e nunca
# encostam no xbot.db real.
_caminho_ativo = None


def configurar_caminho(caminho=None):
    """Define o banco usado por este processo. None volta ao comportamento padrão."""
    global _caminho_ativo
    _caminho_ativo = os.path.abspath(caminho) if caminho else None


def caminho_banco() -> str:
    return _caminho_ativo or os.environ.get("XBOT_DB_PATH") or DB_PATH


# ---------------------------------------------------------------------------
# Conexão
# ---------------------------------------------------------------------------

@contextmanager
def get_connection():
    """
    Context manager que abre uma conexão com xbot.db,
    confirma as alterações no sucesso e fecha sempre ao final.

    Uso:
        with get_connection() as conn:
            conn.execute("INSERT INTO knowledge ...")
        # conn já está fechado aqui
    """
    conn = None
    try:
        # timeout=10: com o servidor em várias threads, espera um escritor terminar
        # em vez de falhar na hora com "database is locked".
        conn = sqlite3.connect(caminho_banco(), timeout=10)

        # Retornar linhas como objetos acessíveis por nome de coluna
        # Ex: row["titulo"] em vez de row[1]
        conn.row_factory = sqlite3.Row

        # Ativar chaves estrangeiras (boa prática desde já)
        conn.execute("PRAGMA foreign_keys = ON")

        yield conn
        conn.commit()

    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"[XBot DB] Erro SQLite: {e}")
        raise

    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Criação das tabelas
# ---------------------------------------------------------------------------

def _criar_tabela_knowledge(cursor):
    """
    Cria a tabela 'knowledge' se ela ainda não existir.

    Campos:
      id           — chave primária auto-incrementada
      titulo       — título do tópico (ex: "Transistor")
      categoria    — categoria do conhecimento (ex: "hardware", "software")
      palavras_chave — string com palavras separadas por vírgula para busca
      conteudo     — texto explicativo (resposta do XBot)
      fonte        — origem da informação (ex: "knowledge_base.py", "manual")
      criado_em    — data/hora de criação do registro (ISO 8601)
    """
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo        TEXT    NOT NULL,
            categoria     TEXT    NOT NULL DEFAULT 'geral',
            palavras_chave TEXT   NOT NULL DEFAULT '',
            conteudo      TEXT    NOT NULL,
            fonte         TEXT    NOT NULL DEFAULT 'manual',
            criado_em     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    logger.info("[XBot DB] Tabela 'knowledge' verificada/criada com sucesso.")


# ---------------------------------------------------------------------------
# Inicialização principal
# ---------------------------------------------------------------------------

def init_db():
    """
    Ponto de entrada: inicializa o banco de dados.

    O que faz:
      1. Cria xbot.db em DB_PATH se não existir (o sqlite3 faz isso automaticamente)
      2. Cria todas as tabelas necessárias se não existirem
      3. Loga o resultado

    Deve ser chamado UMA vez na startup do Flask, antes de qualquer rota.
    """
    logger.info(f"[XBot DB] Inicializando banco em: {caminho_banco()}")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            _criar_tabela_knowledge(cursor)

        logger.info("[XBot DB] Banco de dados inicializado com sucesso.")

    except Exception as e:
        logger.error(f"[XBot DB] Falha na inicialização do banco: {e}")
        # Re-lança para que o Flask saiba que algo deu errado na startup
        raise


# ---------------------------------------------------------------------------
# Funções auxiliares de consulta (usadas por outros módulos futuramente)
# ---------------------------------------------------------------------------

def buscar_por_palavras_chave(termos: list) -> list:
    """
    Busca registros na tabela knowledge cujas palavras_chave
    contenham TODOS os termos fornecidos (busca AND simples).

    Parâmetros:
      termos — lista de strings, ex: ['transistor', 'segunda geração']

    Retorna:
      lista de sqlite3.Row (acessíveis por nome de coluna)
      ou lista vazia se não encontrar nada.

    Exemplo:
      resultados = buscar_por_palavras_chave(['cpu', 'processador'])
    """
    if not termos:
        return []

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Constrói condições dinâmicas: palavras_chave LIKE '%termo%'
            condicoes = " AND ".join(
                ["palavras_chave LIKE ?"] * len(termos)
            )
            valores = [f"%{t}%" for t in termos]

            cursor.execute(
                f"SELECT * FROM knowledge WHERE {condicoes} ORDER BY id",
                valores
            )
            return cursor.fetchall()

    except sqlite3.Error as e:
        logger.error(f"[XBot DB] Erro em buscar_por_palavras_chave: {e}")
        return []


def buscar_por_categoria(categoria: str) -> list:
    """
    Retorna todos os registros de uma categoria específica.

    Exemplo:
      registros = buscar_por_categoria('hardware')
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM knowledge WHERE categoria = ? ORDER BY titulo",
                (categoria,)
            )
            return cursor.fetchall()

    except sqlite3.Error as e:
        logger.error(f"[XBot DB] Erro em buscar_por_categoria: {e}")
        return []


def inserir_conhecimento(titulo: str,
                         categoria: str,
                         palavras_chave: str,
                         conteudo: str,
                         fonte: str = "manual") -> int | None:
    """
    Insere um novo registro na tabela knowledge.

    Retorna o id do registro inserido, ou None em caso de erro.

    Exemplo:
      novo_id = inserir_conhecimento(
          titulo="Transistor",
          categoria="hardware",
          palavras_chave="transistor,segunda geração,válvula",
          conteudo="O transistor substituiu as válvulas na segunda geração...",
          fonte="knowledge_base.py"
      )
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO knowledge (titulo, categoria, palavras_chave, conteudo, fonte)
                VALUES (?, ?, ?, ?, ?)
                """,
                (titulo, categoria, palavras_chave, conteudo, fonte)
            )
            return cursor.lastrowid

    except sqlite3.Error as e:
        logger.error(f"[XBot DB] Erro em inserir_conhecimento: {e}")
        return None


def contar_registros() -> int:
    """
    Retorna o número total de registros na tabela knowledge.
    Útil para checar se o banco tem dados.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM knowledge")
            resultado = cursor.fetchone()
            return resultado["total"] if resultado else 0

    except sqlite3.Error as e:
        logger.error(f"[XBot DB] Erro em contar_registros: {e}")
        return 0


def contar_conhecimento() -> int:
    """
    Como contar_registros(), mas ESTRITA: erro de banco propaga em vez de virar 0.
    Quem decide "o banco está vazio, posso semear" não pode confundir banco ilegível com banco vazio.
    """
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]


def fazer_backup(rotulo: str = "backup") -> str:
    """
    Copia o banco em uso para <banco>.<rotulo>-AAAAMMDD-HHMMSS.bak (API de backup do SQLite:
    copia consistente mesmo com o banco aberto). Retorna o caminho do arquivo criado.
    """
    import time

    origem = caminho_banco()
    destino = f"{origem}.{rotulo}-{time.strftime('%Y%m%d-%H%M%S')}.bak"
    if os.path.exists(destino):
        raise FileExistsError(destino)
    fonte = sqlite3.connect(origem, timeout=10)
    copia = sqlite3.connect(destino)
    try:
        fonte.backup(copia)
    finally:
        copia.close()
        fonte.close()
    return destino


def listar_tabelas() -> list:
    """
    Retorna os nomes de todas as tabelas existentes no banco.
    Usado no teste de inicialização.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            return [row["name"] for row in cursor.fetchall()]

    except sqlite3.Error as e:
        logger.error(f"[XBot DB] Erro em listar_tabelas: {e}")
        return []



# ---------------------------------------------------------------------------
# Stopwords em português — palavras comuns que não identificam um tópico.
# Usadas na Estratégia 2 para evitar falsos positivos (ex: "como" em
# "software como servico", "sobre" em "leis sobre software").
# ---------------------------------------------------------------------------
_STOPWORDS_PT = {
    # Artigos e pronomes
    "este", "esta", "esse", "essa", "isso", "aqui", "qual", "quais",
    # Preposições
    "como", "para", "sobre", "entre", "após", "antes", "além",
    "desde", "durante", "através",
    # Conjunções
    "pois", "mais", "também", "ainda", "quando", "onde", "porque",
    # Verbos auxiliares / de pedido comuns
    "fale", "diga", "falar", "contar", "saber", "quero", "posso",
    "pode", "poderia", "seria", "tenho", "fazer", "usar", "usar",
    "gostaria", "queria", "preciso", "quais",
    # Advérbios e outros
    "muito", "mais", "bem", "aqui", "então", "agora",
    # Palavras de domínio genéricas — aparecem em tantos tópicos que
    # não identificam nada. Termos específicos da mesma pergunta
    # (válvula, herança, ddr5...) devem guiar a busca.
    "computadores", "computador", "computacao", "computação",
    "programação", "tecnologia", "sistema", "digital", "informação", "dados",
}

def _score_registro(registro, mensagem_lower: str, palavras_msg: set) -> int:
    """
    Calcula a relevância de um registro para a mensagem dada.

    Pontuação:
      Parte 1 — Keywords: para cada keyword do registro que aparece na mensagem,
                soma o comprimento do keyword como pontos.
                Keywords curtos (< 5 chars): exige palavra exata (word boundary).
                Keywords longos (>= 5 chars): aceita substring (cobre plurais).
      Parte 2 — Título: para cada palavra do título (>= 3 chars, não stopword)
                que aparece na mensagem, soma 2x o comprimento como bônus.
                Isso faz registros específicos ("javascript basico") vencerem
                sobre genéricos ("desenvolvimento web") quando o título bate.

    Retorna 0 se nenhum keyword ou título bater.
    """
    score = 0

    # Parte 1: keywords
    kws = [k.strip().lower() for k in registro["palavras_chave"].split(",") if k.strip()]
    for kw in kws:
        if not kw or kw in _STOPWORDS_PT:
            continue
        if len(kw) < 5:
            if kw in palavras_msg:          # word boundary para keywords curtos
                score += len(kw)
        else:
            if kw in mensagem_lower:        # substring para keywords longos (plurais, etc.)
                score += len(kw)

    # Parte 2: bônus por palavras do título na mensagem
    titulo_palavras = {
        w for w in re.findall(r"\w+", registro["titulo"].lower())
        if len(w) >= 3 and w not in _STOPWORDS_PT
    }
    for w in titulo_palavras:
        if w in palavras_msg:
            score += len(w) * 2            # bônus 2x por palavra do título

    return score


def _sem_acento(texto: str) -> str:
    """Remove acentos para comparação: 'animação' → 'animacao'"""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def _score_registro(registro, mensagem_lower: str, palavras_msg: set) -> int:
    # Versão normalizada (sem acentos) da mensagem e palavras
    mensagem_norm  = _sem_acento(mensagem_lower)
    palavras_norm  = {_sem_acento(p) for p in palavras_msg}

    score = 0
    kws = [k.strip().lower() for k in registro["palavras_chave"].split(",") if k.strip()]
    for kw in kws:
        kw_norm = _sem_acento(kw)
        if not kw_norm or kw_norm in _STOPWORDS_PT:
            continue
        if len(kw_norm) < 5:
            if kw_norm in palavras_norm:        # word boundary, sem acento
                score += len(kw_norm)
        else:
            if kw_norm in mensagem_norm:         # substring, sem acento
                score += len(kw_norm)
    titulo_palavras = {
        _sem_acento(w) for w in re.findall(r"\w+", registro["titulo"].lower())
        if len(w) >= 3 and w not in _STOPWORDS_PT
    }
    for w in titulo_palavras:
        if w in palavras_norm:
            score += len(w) * 2
    return score


def buscar_conhecimento(mensagem: str) -> "sqlite3.Row | None":
    """
    Busca por relevância: cada registro recebe score por keywords e palavras do
    título que aparecem na mensagem. Retorna o de maior score (0 = sem resultado).
    """
    mensagem_lower = mensagem.lower().strip()
    if len(mensagem_lower) < 3:
        return None

    palavras_msg = set(re.findall(r"\w+", mensagem_lower))

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge ORDER BY id")
            todos = cursor.fetchall()

        melhor       = None
        melhor_score = 0

        for registro in todos:
            score = _score_registro(registro, mensagem_lower, palavras_msg)
            if score > melhor_score:
                melhor_score = score
                melhor       = registro

        if melhor:
            logger.info(
                f"[XBot DB] score={melhor_score} titulo='{melhor['titulo']}'"
            )
        else:
            logger.debug(f"[XBot DB] sem resultado: '{mensagem_lower[:40]}'")

        return melhor

    except sqlite3.Error as e:
        logger.error(f"[XBot DB] Erro em buscar_conhecimento: {e}")
        return None
