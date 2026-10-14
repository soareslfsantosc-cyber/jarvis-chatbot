"""
config.py — Configuração do XBot lida do ambiente (variáveis XBOT_*).

Princípios
----------
* Seguro por padrão: sem XBOT_ENV o modo é PRODUÇÃO (sem debug, sem chave padrão,
  servidor só em 127.0.0.1).
* Nenhum segredo no código: a chave de sessão vem de XBOT_SECRET_KEY.
* Erro de configuração falha ALTO e CEDO, com mensagem que diz o que fazer.
* Variáveis de ambiente reais têm prioridade sobre o arquivo .env (opcional,
  ao lado do app.py; nunca vai para o Git nem para o zip).

Variáveis (todas opcionais, exceto XBOT_SECRET_KEY em produção)
---------------------------------------------------------------
XBOT_ENV                      production (padrão) | development | testing
XBOT_SECRET_KEY               chave para assinar sessões (>= 32 caracteres em produção)
XBOT_HOST / XBOT_PORT         127.0.0.1 / 5000
XBOT_DEBUG                    só em development (padrão: ligado em development)
XBOT_DB_PATH                  caminho do SQLite (padrão: xbot.db na raiz do projeto)
XBOT_ALLOWED_ORIGINS          origens CORS permitidas, separadas por vírgula (padrão: nenhuma)
XBOT_COOKIE_SAMESITE          Lax (padrão) | Strict | None
XBOT_COOKIE_SECURE            auto (padrão: Secure quando a requisição é HTTPS) | 1 | 0
XBOT_TRUSTED_PROXIES          quantos proxies reversos confiáveis (padrão 0)
XBOT_GUEST_SECONDS            tempo do visitante (padrão 600 = 10 minutos)
XBOT_GUEST_COOLDOWN_SECONDS   por quanto tempo o teste esgotado continua esgotado (padrão 86400)
XBOT_GUEST_MAX_SESSIONS       janelas de teste por IP+navegador dentro do cooldown (padrão 1)
XBOT_LOGIN_MAX_FAILURES_EMAIL falhas de login por e-mail na janela (padrão 5)
XBOT_LOGIN_MAX_FAILURES_IP    falhas de login por IP na janela (padrão 20)
XBOT_LOGIN_WINDOW_SECONDS     janela das falhas de login (padrão 900 = 15 minutos)
XBOT_REGISTER_MAX_PER_HOUR    cadastros por IP por hora (padrão 10)
XBOT_DIAGNOSTICS              /db_status, /estatisticas e /raciocinio_debug abertos
                              (padrão: só em development; senão exigem login)
XBOT_MAX_BODY_BYTES           tamanho máximo do corpo das requisições (padrão 16384)
"""

from __future__ import annotations

import ipaddress
import os
import re
import secrets
from dataclasses import dataclass, field
from typing import Mapping, Optional, Tuple

RAIZ_PROJETO = os.path.dirname(os.path.abspath(__file__))
DOTENV_PADRAO = os.path.join(RAIZ_PROJETO, ".env")
BANCO_PADRAO = os.path.join(RAIZ_PROJETO, "xbot.db")

AMBIENTES = ("production", "development", "testing")
_ALIAS_AMBIENTE = {
    "prod": "production", "producao": "production", "produção": "production",
    "dev": "development", "desenvolvimento": "development",
    "test": "testing", "teste": "testing",
}

_VERDADEIROS = {"1", "true", "yes", "sim", "on", "s", "y"}
_FALSOS = {"0", "false", "no", "nao", "não", "off", "n"}

# Trechos que denunciam uma chave de exemplo copiada de tutorial/README.
_CHAVES_FRACAS = (
    "trocar", "troque", "changeme", "change-me", "change_me", "dev-secret",
    "sua-chave", "sua_chave", "your-secret", "your_secret", "secret-key",
    "exemplo", "example", "placeholder", "senha", "password",
)

COMANDO_GERAR_CHAVE = 'python -c "import secrets; print(secrets.token_hex(32))"'

MSG_SEM_CHAVE = f"""XBOT_SECRET_KEY não está definida (modo produção).

O XBot não inicia sem uma chave secreta para assinar as sessões de login.
1) Gere uma chave aleatória:
       {COMANDO_GERAR_CHAVE}
2) Informe-a ao XBot, de uma destas formas:
       - arquivo .env (copie .env.example para .env e cole a chave lá), ou
       - PowerShell:  $env:XBOT_SECRET_KEY = "<chave gerada>"
       - Linux/macOS: export XBOT_SECRET_KEY="<chave gerada>"

Só para desenvolvimento local, rode com XBOT_ENV=development: o XBot usa uma
chave temporária (as sessões deixam de valer ao reiniciar)."""


class ConfigError(RuntimeError):
    """Configuração ausente/inválida. A mensagem é feita para ser lida por uma pessoa."""


# ---------------------------------------------------------------------------
# Leitura de valores
# ---------------------------------------------------------------------------

def carregar_dotenv(caminho: str) -> dict:
    """
    Lê um arquivo .env simples (CHAVE=valor, # comentários, aspas opcionais).
    Só aceita chaves XBOT_*. Arquivo ausente = sem valores. Sem expansão de variáveis.
    """
    valores: dict = {}
    try:
        with open(caminho, encoding="utf-8-sig") as arquivo:  # utf-8-sig tolera BOM do Bloco de Notas
            for bruta in arquivo:
                linha = bruta.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                if linha.startswith("export "):
                    linha = linha[len("export "):].lstrip()
                chave, _, valor = linha.partition("=")
                chave, valor = chave.strip(), valor.strip()
                if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
                    valor = valor[1:-1]
                elif " #" in valor:
                    valor = valor.split(" #", 1)[0].rstrip()
                if re.fullmatch(r"XBOT_[A-Z0-9_]+", chave):
                    valores[chave] = valor
    except FileNotFoundError:
        return {}
    except OSError as erro:
        raise ConfigError(f"Não foi possível ler {caminho}: {erro}") from None
    return valores


def _ler_bool(env: Mapping[str, str], nome: str, padrao: Optional[bool]) -> Optional[bool]:
    bruto = env.get(nome)
    if bruto is None or bruto.strip() == "":
        return padrao
    valor = bruto.strip().lower()
    if valor in _VERDADEIROS:
        return True
    if valor in _FALSOS:
        return False
    raise ConfigError(f"{nome}={bruto!r} é inválido. Use 1/0, true/false ou sim/não.")


def _ler_int(env: Mapping[str, str], nome: str, padrao: int, minimo: int, maximo: int) -> int:
    bruto = env.get(nome)
    if bruto is None or bruto.strip() == "":
        return padrao
    try:
        valor = int(bruto.strip())
    except ValueError:
        raise ConfigError(f"{nome}={bruto!r} não é um número inteiro.") from None
    if not minimo <= valor <= maximo:
        raise ConfigError(f"{nome}={valor} fora do intervalo permitido ({minimo} a {maximo}).")
    return valor


_ORIGEM_RE = re.compile(r"^https?://([A-Za-z0-9.\-]+|\[[0-9A-Fa-f:]+\])(:\d{1,5})?$")


def _ler_origens(env: Mapping[str, str]) -> Tuple[str, ...]:
    origens = []
    for parte in (env.get("XBOT_ALLOWED_ORIGINS") or "").split(","):
        origem = parte.strip().rstrip("/")
        if not origem:
            continue
        if origem == "*":
            raise ConfigError(
                "XBOT_ALLOWED_ORIGINS não aceita '*': o XBot usa cookies de sessão e "
                "'*' com credenciais é inseguro. Liste as origens exatas, por exemplo:\n"
                "    XBOT_ALLOWED_ORIGINS=https://meusite.com,http://localhost:5173"
            )
        if not _ORIGEM_RE.match(origem):
            raise ConfigError(
                f"Origem inválida em XBOT_ALLOWED_ORIGINS: {parte.strip()!r}. "
                "Formato: esquema://host[:porta], sem caminho e sem barra final."
            )
        origem = origem.lower()
        if origem not in origens:
            origens.append(origem)
    return tuple(origens)


def _e_loopback(host: str) -> bool:
    candidato = host.strip().lower()
    if candidato == "localhost":
        return True
    try:
        return ipaddress.ip_address(candidato.strip("[]")).is_loopback
    except ValueError:
        return False


def _validar_chave_producao(chave: str) -> None:
    if len(chave) < 32:
        raise ConfigError(
            f"XBOT_SECRET_KEY é curta demais ({len(chave)} caracteres); use pelo menos 32.\n"
            f"Gere uma boa chave com:\n    {COMANDO_GERAR_CHAVE}"
        )
    baixa = chave.lower()
    if any(trecho in baixa for trecho in _CHAVES_FRACAS) or len(set(chave)) < 8:
        raise ConfigError(
            "XBOT_SECRET_KEY parece um valor de exemplo (ou tem pouca variedade de caracteres).\n"
            f"Gere uma chave aleatória com:\n    {COMANDO_GERAR_CHAVE}"
        )


# ---------------------------------------------------------------------------
# Objeto de configuração
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Config:
    ambiente: str
    secret_key: str = field(repr=False)
    secret_efemera: bool
    debug: bool
    host: str
    port: int
    db_path: str
    allowed_origins: Tuple[str, ...]
    cookie_samesite: str
    cookie_secure: Optional[bool]          # None = "auto": Secure quando a requisição é HTTPS
    trusted_proxies: int
    guest_seconds: int
    guest_cooldown_seconds: int
    guest_max_sessions: int
    login_max_failures_email: int
    login_max_failures_ip: int
    login_window_seconds: int
    register_max_per_hour: int
    diagnostics_open: bool
    max_body_bytes: int
    avisos: Tuple[str, ...] = ()

    @property
    def producao(self) -> bool:
        return self.ambiente == "production"

    @property
    def host_na_rede(self) -> bool:
        return not _e_loopback(self.host)

    def resumo(self) -> str:
        """Linha segura para log (nunca inclui a chave)."""
        return (
            f"ambiente={self.ambiente} debug={self.debug} host={self.host}:{self.port} "
            f"cors={'sim' if self.allowed_origins else 'não'} "
            f"visitante={self.guest_seconds}s login_max_email={self.login_max_failures_email}"
        )

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None, *,
                 dotenv_path: Optional[str] = DOTENV_PADRAO) -> "Config":
        """
        Lê e valida a configuração. Sem `env`, usa os.environ por cima do arquivo .env.
        Com `env` explícito (testes), usa SOMENTE o dicionário recebido.
        """
        if env is None:
            env = {**(carregar_dotenv(dotenv_path) if dotenv_path else {}), **os.environ}

        avisos = []

        # --- ambiente --------------------------------------------------------
        bruto_ambiente = (env.get("XBOT_ENV") or "production").strip().lower()
        ambiente = _ALIAS_AMBIENTE.get(bruto_ambiente, bruto_ambiente)
        if ambiente not in AMBIENTES:
            raise ConfigError(
                f"XBOT_ENV={bruto_ambiente!r} é inválido. Use: {', '.join(AMBIENTES)}."
            )

        # --- chave secreta ---------------------------------------------------
        chave = (env.get("XBOT_SECRET_KEY") or "").strip()
        efemera = False
        if ambiente == "production":
            if not chave:
                raise ConfigError(MSG_SEM_CHAVE)
            _validar_chave_producao(chave)
        elif not chave:
            chave = secrets.token_hex(32)
            efemera = True
            avisos.append(
                "XBOT_SECRET_KEY não definida: usando chave TEMPORÁRIA "
                "(logins e cookies deixam de valer quando o servidor reinicia)."
            )

        # --- rede e debug ----------------------------------------------------
        host = (env.get("XBOT_HOST") or "127.0.0.1").strip()
        porta = _ler_int(env, "XBOT_PORT", 5000, 1, 65535)
        debug_pedido = _ler_bool(env, "XBOT_DEBUG", None)

        if ambiente != "development":
            if debug_pedido:
                raise ConfigError(
                    "XBOT_DEBUG=1 só é permitido com XBOT_ENV=development: o modo debug "
                    "permite executar código no servidor a quem conseguir acessá-lo."
                )
            debug = False
        else:
            debug = True if debug_pedido is None else debug_pedido
            if debug and not _e_loopback(host):
                if debug_pedido:
                    raise ConfigError(
                        f"XBOT_DEBUG=1 com XBOT_HOST={host} expõe o depurador na rede. "
                        "Use XBOT_HOST=127.0.0.1 ou desligue o debug (XBOT_DEBUG=0)."
                    )
                debug = False
                avisos.append(
                    f"Debug desativado automaticamente porque XBOT_HOST={host} expõe o servidor na rede."
                )
        if not _e_loopback(host):
            avisos.append(
                f"Servidor acessível pela rede (XBOT_HOST={host}). O servidor embutido do Flask é só "
                "para testes: para uso real rode com waitress/gunicorn usando wsgi.py (veja o README)."
            )

        # --- banco -----------------------------------------------------------
        caminho_bruto = (env.get("XBOT_DB_PATH") or "").strip()
        if caminho_bruto == ":memory:":
            raise ConfigError("XBOT_DB_PATH=:memory: não é suportado (cada conexão veria um banco diferente).")
        db_path = os.path.abspath(caminho_bruto) if caminho_bruto else BANCO_PADRAO
        if os.path.isdir(db_path):
            raise ConfigError(f"XBOT_DB_PATH aponta para uma pasta, não para um arquivo: {db_path}")
        if not os.path.isdir(os.path.dirname(db_path)):
            raise ConfigError(f"A pasta do banco não existe: {os.path.dirname(db_path)}")

        # --- cookies ---------------------------------------------------------
        samesite = (env.get("XBOT_COOKIE_SAMESITE") or "Lax").strip().capitalize()
        if samesite not in ("Lax", "Strict", "None"):
            raise ConfigError(f"XBOT_COOKIE_SAMESITE={samesite!r} é inválido. Use Lax, Strict ou None.")
        seguro_bruto = (env.get("XBOT_COOKIE_SECURE") or "auto").strip().lower()
        cookie_secure = None if seguro_bruto == "auto" else _ler_bool(env, "XBOT_COOKIE_SECURE", None)
        if samesite == "None":
            if cookie_secure is False:
                raise ConfigError("XBOT_COOKIE_SAMESITE=None exige cookie Secure (HTTPS): não use XBOT_COOKIE_SECURE=0.")
            cookie_secure = True

        # --- limites ---------------------------------------------------------
        guest_seconds = _ler_int(env, "XBOT_GUEST_SECONDS", 600, 10, 86400)
        guest_cooldown = _ler_int(env, "XBOT_GUEST_COOLDOWN_SECONDS", 86400, 60, 30 * 86400)
        if guest_cooldown < guest_seconds:
            raise ConfigError("XBOT_GUEST_COOLDOWN_SECONDS não pode ser menor que XBOT_GUEST_SECONDS.")

        diagnostics = _ler_bool(env, "XBOT_DIAGNOSTICS", ambiente == "development")

        return cls(
            ambiente=ambiente,
            secret_key=chave,
            secret_efemera=efemera,
            debug=debug,
            host=host,
            port=porta,
            db_path=db_path,
            allowed_origins=_ler_origens(env),
            cookie_samesite=samesite,
            cookie_secure=cookie_secure,
            trusted_proxies=_ler_int(env, "XBOT_TRUSTED_PROXIES", 0, 0, 5),
            guest_seconds=guest_seconds,
            guest_cooldown_seconds=guest_cooldown,
            guest_max_sessions=_ler_int(env, "XBOT_GUEST_MAX_SESSIONS", 1, 1, 50),
            login_max_failures_email=_ler_int(env, "XBOT_LOGIN_MAX_FAILURES_EMAIL", 5, 1, 100),
            login_max_failures_ip=_ler_int(env, "XBOT_LOGIN_MAX_FAILURES_IP", 20, 1, 1000),
            login_window_seconds=_ler_int(env, "XBOT_LOGIN_WINDOW_SECONDS", 900, 30, 86400),
            register_max_per_hour=_ler_int(env, "XBOT_REGISTER_MAX_PER_HOUR", 10, 1, 1000),
            diagnostics_open=bool(diagnostics),
            max_body_bytes=_ler_int(env, "XBOT_MAX_BODY_BYTES", 16384, 1024, 1048576),
            avisos=tuple(avisos),
        )
