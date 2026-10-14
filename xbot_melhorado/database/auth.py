"""
database/auth.py
XBot v0.3.0 Beta — Camada de Autenticação (revisão de segurança)

Responsabilidades:
  - Criar as tabelas de autenticação/limites se não existirem
    (users, visitantes, auth_tentativas) — sempre de forma ADITIVA
  - Cadastrar usuários com política de senha forte (hash via werkzeug.security)
  - Verificar login com bloqueio de tentativas repetidas, sem revelar se o
    e-mail existe (mesma mensagem e tempo de resposta parecido)
  - Buscar usuário por id

Compatibilidade com dados existentes
------------------------------------
A tabela `users` e os hashes já gravados NÃO mudam. A política de senha vale só
para NOVOS cadastros: quem já tem conta (mesmo com senha curta) continua entrando
com a senha que tem. check_password_hash entende os hashes antigos.

Sem ORM — SQL direto, mesma filosofia de database/db.py.
Sem dependências novas — werkzeug já é requirement do projeto.
"""

from __future__ import annotations

import logging
import math
import re
import secrets
import sqlite3
import unicodedata
from typing import Optional

from werkzeug.security import check_password_hash, generate_password_hash

import relogio
from database import throttle, visitantes
from database.db import get_connection

logger = logging.getLogger(__name__)

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SENHA_MIN = 10
SENHA_MAX = 128
NOME_MAX = 80
EMAIL_MAX = 254
SENHA_LOGIN_MAX = 256          # login aceita um pouco mais (contas antigas), mas nunca ilimitado


# ---------------------------------------------------------------------------
# Criação das tabelas
# ---------------------------------------------------------------------------

def init_auth_db():
    """
    Cria o que falta: 'users' (como sempre) e as tabelas de limite de uso.
    Idempotente e aditivo — não altera nem apaga nada que já exista.
    """
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                nome        TEXT    NOT NULL,
                email       TEXT    NOT NULL UNIQUE,
                senha_hash  TEXT    NOT NULL,
                criado_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
        """)
        throttle.criar_tabelas(conn)      # auth_tentativas (anti força-bruta)
        visitantes.criar_tabelas(conn)    # visitantes (limite de 10 min no servidor)
    logger.info("[Auth] Tabelas 'users', 'visitantes' e 'auth_tentativas' verificadas/criadas.")


# ---------------------------------------------------------------------------
# Política de senha (só para cadastro)
# ---------------------------------------------------------------------------

def _normalizar(texto: str) -> str:
    """minúsculas e sem acentos: 'SÃO Paulo' → 'sao paulo'."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return sem_acento.lower()


# Senhas muito comuns (PT/EN) já normalizadas. Cobre também variações óbvias:
# sufixo/prefixo numérico ("senha2026"), troca por números ("p4ssw0rd").
_SENHAS_COMUNS = frozenset("""
    123456 1234567 12345678 123456789 1234567890 12345 123123 123123123 111111 000000
    654321 112233 121212 123321 1q2w3e 1q2w3e4r 1q2w3e4r5t q1w2e3r4 senha senhasenha
    minhasenha meusenha mudar trocar mudar123 trocar123 password passw0rd pass1234 passwd
    qwerty qwertyuiop qwertyui asdfgh asdfghjkl zxcvbnm abc123 abcd1234 abcdef abcdefg
    abcdefgh iloveyou teamo tequiero letmein welcome admin administrador root toor master
    dragon monkey football futebol brasil brasileiro flamengo corinthians palmeiras
    saopaulo vasco gremio internacional cruzeiro santos botafogo amor meuamor princesa
    gatinho gatinha linda lindo deus jesus jesuscristo deusefiel casa familia felicidade
    teste testando usuario login entrar computador internet chatbot xbot xbotxbot xbyte
    xbytegames games jogos gamer minecraft freefire fortnite roblox naruto sasuke pokemon
    google facebook whatsapp instagram iphone samsung nintendo playstation xbox
""".split())

_SEQUENCIAS = (
    "01234567890", "09876543210", "abcdefghijklmnopqrstuvwxyz",
    "qwertyuiopasdfghjklzxcvbnm", "1q2w3e4r5t6y7u8i9o0p", "qazwsxedcrfvtgbyhnujmikolp",
)
_LEET = str.maketrans("013457@$", "oieastas")


def _tem_sequencia_dominante(alnum: str) -> bool:
    """
    True se um trecho em ordem de teclado/alfabeto/dígitos (1234567890, abcdefgh, qwertyuiop,
    também de trás para frente) ocupa a maior parte da senha. Um trecho curto dentro de uma
    frase longa ("...-qwerty-...") não conta.
    """
    if len(alnum) < 6:
        return False
    minimo = max(6, int(0.6 * len(alnum)))
    for tamanho in range(len(alnum), minimo - 1, -1):
        for inicio in range(len(alnum) - tamanho + 1):
            trecho = alnum[inicio:inicio + tamanho]
            if any(trecho in s or trecho[::-1] in s for s in _SEQUENCIAS):
                return True
    return False


def _e_sequencia_ou_repeticao(n: str) -> bool:
    alnum = re.sub(r"[^a-z0-9]", "", n)
    if len(set(alnum)) < 5:                              # ex.: 'aaaaaaaaaaaa', '1212121212'
        return True
    if re.fullmatch(r"(.{1,4})\1{2,}", alnum):          # ex.: 'abcabcabcabc'
        return True
    return _tem_sequencia_dominante(alnum)


def _e_senha_comum(n: str) -> bool:
    # O "núcleo" é a senha sem números/símbolos nas pontas: 'p4ssw0rd2026' → 'p4ssw0rd'.
    # A troca de números por letras (leet) vem DEPOIS de tirar as pontas, senão o '0' de '2026'
    # viraria um 'o' e esconderia a palavra comum.
    nucleo = re.sub(r"^[^a-z]+|[^a-z]+$", "", n)
    for forma in {n, n.translate(_LEET), nucleo, nucleo.translate(_LEET)}:
        compacta = re.sub(r"[^a-z0-9]", "", forma)
        so_letras = re.sub(r"[^a-z]", "", forma)
        if forma in _SENHAS_COMUNS or compacta in _SENHAS_COMUNS or so_letras in _SENHAS_COMUNS:
            return True
    return False


def validar_senha(senha, nome: str = "", email: str = "") -> Optional[str]:
    """Devolve a mensagem do primeiro problema encontrado, ou None se a senha serve."""
    if not isinstance(senha, str):
        return "Senha inválida."
    if len(senha) < SENHA_MIN:
        return f"Senha deve ter pelo menos {SENHA_MIN} caracteres."
    if len(senha) > SENHA_MAX:
        return f"Senha muito longa (máximo de {SENHA_MAX} caracteres)."
    if not any(c.isalpha() for c in senha):
        return "Senha deve conter pelo menos uma letra."
    if not any(not c.isalpha() for c in senha):
        return "Senha deve conter pelo menos um número, símbolo ou espaço."

    n = _normalizar(senha)
    if _e_sequencia_ou_repeticao(n):
        return "Senha muito simples: evite sequências (123456, abcdef) e caracteres repetidos."
    if _e_senha_comum(n):
        return "Senha muito comum. Escolha uma senha mais difícil de adivinhar."

    compacta = re.sub(r"[^a-z0-9]", "", n)
    local_email = re.sub(r"[^a-z0-9]", "", _normalizar(email.split("@")[0])) if email else ""
    partes = [p for p in re.findall(r"[a-z0-9]+", _normalizar(nome or "")) if len(p) >= 4]
    if len(local_email) >= 4:
        partes.append(local_email)
    if any(parte in compacta for parte in partes):
        return "Senha não pode conter o seu nome ou o seu e-mail."
    return None


# ---------------------------------------------------------------------------
# Validação do cadastro
# ---------------------------------------------------------------------------

def _limpar_nome(nome: str) -> str:
    """Remove caracteres de controle e espaços repetidos."""
    return " ".join("".join(c for c in nome if c.isprintable() or c.isspace()).split())


def validar_cadastro(nome, email, senha) -> Optional[str]:
    """Retorna mensagem de erro (string) se inválido, ou None se ok."""
    if not all(isinstance(valor, str) for valor in (nome, email, senha)):
        return "Dados de cadastro inválidos."
    nome_limpo = _limpar_nome(nome)
    if len(nome_limpo) < 2:
        return "Nome deve ter pelo menos 2 caracteres."
    if len(nome_limpo) > NOME_MAX:
        return f"Nome muito longo (máximo de {NOME_MAX} caracteres)."
    email_norm = email.strip().lower()
    if (not email_norm or len(email_norm) > EMAIL_MAX or not _EMAIL_REGEX.match(email_norm)
            or any(ord(c) < 32 for c in email_norm)):
        return "E-mail inválido."
    return validar_senha(senha, nome_limpo, email_norm)


# ---------------------------------------------------------------------------
# Operações
# ---------------------------------------------------------------------------

def criar_usuario(nome, email, senha) -> dict:
    """
    Cria um novo usuário (sem limite de tentativas — o limite fica em cadastrar()).
    Retorna {'sucesso': bool, 'usuario': {...} | None, 'erro': str | None}.
    """
    erro = validar_cadastro(nome, email, senha)
    if erro:
        return {"sucesso": False, "usuario": None, "erro": erro, "codigo": "dados_invalidos"}

    nome_limpo = _limpar_nome(nome)
    email_norm = email.strip().lower()
    senha_hash = generate_password_hash(senha)

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (nome, email, senha_hash) VALUES (?, ?, ?)",
                (nome_limpo, email_norm, senha_hash)
            )
            user_id = cursor.lastrowid
        logger.info(f"[Auth] Novo usuário criado: id={user_id}")
        return {
            "sucesso": True,
            "usuario": {"id": user_id, "nome": nome_limpo, "email": email_norm},
            "erro": None,
        }
    except sqlite3.IntegrityError:
        return {"sucesso": False, "usuario": None, "erro": "Este e-mail já está cadastrado.",
                "codigo": "email_em_uso"}
    except sqlite3.Error as e:
        logger.error(f"[Auth] Erro ao criar usuário: {e}")
        return {"sucesso": False, "usuario": None, "erro": "Erro interno ao cadastrar.",
                "codigo": "erro_interno"}


_hash_falso_cache: Optional[str] = None


def _hash_falso() -> str:
    """
    Hash descartável: quando o e-mail não existe, conferimos a senha contra ele para
    que "e-mail inexistente" e "senha errada" gastem o mesmo tempo (sem enumeração).
    """
    global _hash_falso_cache
    if _hash_falso_cache is None:
        _hash_falso_cache = generate_password_hash(secrets.token_urlsafe(16))
    return _hash_falso_cache


_ERRO_CREDENCIAIS = {"sucesso": False, "usuario": None, "erro": "E-mail ou senha incorretos."}


def verificar_login(email, senha) -> dict:
    """
    Confere e-mail + senha (SEM limite de tentativas — o limite fica em autenticar()).
    Retorna {'sucesso': bool, 'usuario': {...} | None, 'erro': str | None}.
    """
    if not isinstance(email, str) or not isinstance(senha, str) or not email or not senha:
        return {"sucesso": False, "usuario": None, "erro": "E-mail e senha obrigatórios."}

    email_norm = email.strip().lower()
    if len(email_norm) > EMAIL_MAX or len(senha) > SENHA_LOGIN_MAX:
        return dict(_ERRO_CREDENCIAIS)          # nem tenta calcular hash de entrada absurda

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome, email, senha_hash FROM users WHERE email = ?",
                (email_norm,)
            )
            row = cursor.fetchone()
    except sqlite3.Error as e:
        logger.error(f"[Auth] Erro ao verificar login: {e}")
        return {"sucesso": False, "usuario": None, "erro": "Erro interno ao entrar."}

    try:
        senha_confere = check_password_hash(row["senha_hash"] if row else _hash_falso(), senha)
    except ValueError:                          # hash gravado num formato desconhecido
        logger.error("[Auth] Hash em formato não reconhecido (usuário id=%s).", row["id"] if row else "?")
        senha_confere = False

    if not row or not senha_confere:
        return dict(_ERRO_CREDENCIAIS)

    logger.info(f"[Auth] Login bem-sucedido: id={row['id']}")
    return {
        "sucesso": True,
        "usuario": {"id": row["id"], "nome": row["nome"], "email": row["email"]},
        "erro": None,
    }


def _duracao(segundos: int) -> str:
    if segundos < 60:
        return f"{segundos} segundo{'s' if segundos != 1 else ''}"
    minutos = math.ceil(segundos / 60)
    return f"{minutos} minuto{'s' if minutos != 1 else ''}"


def autenticar(email, senha, *, ip: str, cfg) -> dict:
    """
    Login com proteção contra tentativas repetidas.

    Bloqueia por e-mail (força bruta contra uma conta, mesmo vinda de vários IPs) e
    por IP (um endereço testando várias contas). Durante o bloqueio a senha nem é
    conferida. Retorna o mesmo formato de verificar_login(); no bloqueio traz
    codigo='muitas_tentativas' e retry_after (segundos).
    """
    agora = relogio.agora()
    email_norm = email.strip().lower() if isinstance(email, str) else ""
    chave_email = throttle.chave_hmac(cfg.secret_key, "email", email_norm)
    chave_ip = throttle.chave_hmac(cfg.secret_key, "ip", ip)

    espera = throttle.segundos_de_bloqueio(
        throttle.LOGIN,
        [(chave_email, cfg.login_max_failures_email), (chave_ip, cfg.login_max_failures_ip)],
        agora=agora, janela=cfg.login_window_seconds,
    )
    if espera:
        logger.warning("[Auth] Login bloqueado por excesso de tentativas (espera=%ss)", espera)
        return {"sucesso": False, "usuario": None, "codigo": "muitas_tentativas",
                "retry_after": espera,
                "erro": f"Muitas tentativas de login. Tente novamente em {_duracao(espera)}."}

    resultado = verificar_login(email, senha)
    if resultado["sucesso"]:
        throttle.limpar_falhas(throttle.LOGIN, chave_email)
    else:
        throttle.registrar_tentativa(throttle.LOGIN, [chave_email, chave_ip], agora=agora, sucesso=False)
    return resultado


def cadastrar(nome, email, senha, *, ip: str, cfg) -> dict:
    """
    Cadastro com limite por IP (anti-spam). Dados inválidos são recusados ANTES de
    contar no limite (não gasta cota nem toca no banco de usuários).
    """
    erro = validar_cadastro(nome, email, senha)
    if erro:
        return {"sucesso": False, "usuario": None, "erro": erro, "codigo": "dados_invalidos"}

    agora = relogio.agora()
    chave_ip = throttle.chave_hmac(cfg.secret_key, "ip", ip)
    espera = throttle.segundos_de_bloqueio(
        throttle.REGISTRO, [(chave_ip, cfg.register_max_per_hour)],
        agora=agora, janela=3600, apenas_falhas=False,
    )
    if espera:
        return {"sucesso": False, "usuario": None, "codigo": "muitas_tentativas",
                "retry_after": espera,
                "erro": f"Muitos cadastros a partir deste endereço. Tente novamente em {_duracao(espera)}."}

    resultado = criar_usuario(nome, email, senha)
    throttle.registrar_tentativa(throttle.REGISTRO, [chave_ip], agora=agora, sucesso=resultado["sucesso"])
    return resultado


def buscar_usuario_por_id(user_id) -> Optional[dict]:
    """Retorna {'id','nome','email'} ou None se não encontrado."""
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        return None
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, email FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"[Auth] Erro ao buscar usuário por id: {e}")
        return None


def contar_usuarios() -> int:
    """Retorna o total de usuários cadastrados."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM users")
            row = cursor.fetchone()
            return row["total"] if row else 0
    except sqlite3.Error as e:
        logger.error(f"[Auth] Erro ao contar usuários: {e}")
        return 0
