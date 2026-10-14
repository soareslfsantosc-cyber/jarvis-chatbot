"""
seguranca.py — Proteções HTTP do XBot (camada Flask)

  * Validação de JSON: tipo errado / corpo malformado vira 400 controlado, nunca 500
  * CSRF: token por sessão no cabeçalho X-CSRF-Token + checagem de Origin/Referer
  * "Impressão" do cliente (IP + navegador) usada no limite de visitante
  * Cabeçalhos de segurança e erros sempre em JSON, sem vazar detalhes internos
"""

from __future__ import annotations

import hmac
import ipaddress
import logging
import secrets
from urllib.parse import urlsplit

from flask import current_app, jsonify, request, session
from werkzeug.exceptions import HTTPException

from database import throttle

logger = logging.getLogger(__name__)

CABECALHO_CSRF = "X-CSRF-Token"
METODOS_SEGUROS = frozenset({"GET", "HEAD", "OPTIONS"})

# A página só carrega script/estilo/imagem do próprio site (o favicon é um data: URI).
_CSP = (
    "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
    "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
)


def _cfg():
    return current_app.config["XBOT"]


# ---------------------------------------------------------------------------
# Erros "esperados" (viram resposta JSON com o status certo)
# ---------------------------------------------------------------------------

class ErroRequisicao(Exception):
    """Levante dentro de uma rota/hook: o handler devolve JSON {erro, codigo, ...} com `status`."""

    def __init__(self, mensagem: str, status: int = 400, codigo: str = "requisicao_invalida", **extra):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status
        self.codigo = codigo
        self.extra = extra

    def para_resposta(self):
        corpo = {"erro": self.mensagem, "codigo": self.codigo}
        corpo.update(self.extra)
        resposta = jsonify(corpo)
        resposta.status_code = self.status
        if "retry_after" in self.extra:
            resposta.headers["Retry-After"] = str(self.extra["retry_after"])
        return resposta


# ---------------------------------------------------------------------------
# Validação de entrada JSON
# ---------------------------------------------------------------------------

def obter_json_objeto() -> dict:
    """O corpo precisa ser JSON e ser um OBJETO ({...}). Qualquer outra coisa é 400/415."""
    if not request.is_json:
        raise ErroRequisicao("Envie o corpo como JSON (Content-Type: application/json).",
                             415, "tipo_nao_suportado")
    try:
        dados = request.get_json(silent=True)
    except RecursionError:                      # JSON absurdamente aninhado
        dados = None
    if dados is None:
        raise ErroRequisicao("JSON inválido ou vazio.", 400, "json_invalido")
    if not isinstance(dados, dict):
        raise ErroRequisicao("O corpo da requisição deve ser um objeto JSON.", 400, "json_invalido")
    return dados


def campo_texto(dados: dict, nome: str, *, obrigatorio: bool = False,
                max_len: int | None = None, padrao: str = "", strip: bool = True) -> str:
    """
    Lê um campo de texto do JSON. Ausente/null → `padrao` (ou 400 se obrigatório).
    Número, lista, objeto, booleano → 400. Caractere NUL → 400. Texto que não codifica em
    UTF-8 (surrogate solto, como "\\ud800", que o JSON permite mas não é texto válido) → 400:
    sem isso ele estouraria mais adiante (HMAC do limitador, SQLite) e viraria um 500.
    """
    valor = dados.get(nome)
    if valor is None:
        if obrigatorio:
            raise ErroRequisicao(f"O campo '{nome}' é obrigatório.", 400, "campo_obrigatorio")
        return padrao
    if not isinstance(valor, str):
        raise ErroRequisicao(f"O campo '{nome}' deve ser um texto.", 400, "tipo_invalido")
    if "\x00" in valor:
        raise ErroRequisicao(f"O campo '{nome}' contém caracteres inválidos.", 400, "caractere_invalido")
    try:
        valor.encode("utf-8")
    except UnicodeEncodeError:
        raise ErroRequisicao(f"O campo '{nome}' contém caracteres inválidos.", 400, "caractere_invalido") from None
    if strip:
        valor = valor.strip()
    if obrigatorio and not valor:
        raise ErroRequisicao(f"O campo '{nome}' é obrigatório.", 400, "campo_obrigatorio")
    if max_len is not None and len(valor) > max_len:
        raise ErroRequisicao(f"O campo '{nome}' excede {max_len} caracteres.", 400, "campo_muito_longo")
    return valor


def limpar_nome_exibicao(valor: str, padrao: str = "usuário", max_len: int = 40) -> str:
    """Nome só para exibição/saudação: sem caracteres de controle, espaços normalizados, até 40."""
    texto = "".join(c for c in valor if c.isprintable() or c.isspace())
    texto = " ".join(texto.split())
    return texto[:max_len].strip() or padrao


# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------

def token_csrf() -> str:
    """Token da sessão atual (cria se não houver). Só é entregue ao próprio navegador."""
    token = session.get("csrf")
    if not isinstance(token, str) or len(token) < 20:
        token = secrets.token_urlsafe(32)
        session["csrf"] = token
    return token


def renovar_token_csrf() -> str:
    """Novo token (usado em login/logout/cadastro, quando a sessão muda de dono)."""
    session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def _origem_da_requisicao() -> str:
    return f"{request.scheme}://{request.host}".lower()


def _origem_permitida(origem: str) -> bool:
    origem = origem.strip().rstrip("/").lower()
    return origem == _origem_da_requisicao() or origem in _cfg().allowed_origins


def verificar_origem() -> None:
    """
    Origin (ou, na falta, Referer) tem de ser o próprio site ou uma origem configurada em
    XBOT_ALLOWED_ORIGINS. Sem nenhum dos dois (curl, scripts) a decisão fica com o token.
    """
    origem = request.headers.get("Origin")
    if origem is not None:
        if origem == "null" or not _origem_permitida(origem):
            raise ErroRequisicao("Origem da requisição não permitida.", 403, "origem_invalida")
        return
    referer = request.headers.get("Referer")
    if referer:
        partes = urlsplit(referer)
        if not partes.scheme or not partes.netloc or not _origem_permitida(f"{partes.scheme}://{partes.netloc}"):
            raise ErroRequisicao("Origem da requisição não permitida.", 403, "origem_invalida")


def validar_csrf() -> None:
    verificar_origem()
    esperado = session.get("csrf")
    enviado = request.headers.get(CABECALHO_CSRF, "")
    if (not isinstance(esperado, str) or not enviado
            or not hmac.compare_digest(esperado.encode("utf-8"), enviado.encode("utf-8"))):
        raise ErroRequisicao(
            "Sessão de segurança inválida ou expirada. Recarregue a página e tente novamente.",
            403, "csrf",
        )


# ---------------------------------------------------------------------------
# Identificação do cliente (para o limite de visitante e o anti força-bruta)
# ---------------------------------------------------------------------------

def ip_do_cliente() -> str:
    """
    IP visto pelo servidor. X-Forwarded-For só é considerado se XBOT_TRUSTED_PROXIES > 0
    (via ProxyFix); do contrário, quem falsifica o cabeçalho não ganha nada.
    IPv6 é reduzido ao prefixo /64 (um mesmo aparelho troca de endereço dentro dele).
    """
    bruto = request.remote_addr or "0.0.0.0"
    try:
        ip = ipaddress.ip_address(bruto)
    except ValueError:
        return bruto[:64]
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped:
            return str(ip.ipv4_mapped)
        return f"{ipaddress.ip_network(f'{ip}/64', strict=False).network_address}/64"
    return str(ip)


def impressao_do_cliente() -> str:
    """HMAC de IP + User-Agent: estável se o cookie for apagado, sem guardar o IP em claro."""
    agente = (request.headers.get("User-Agent") or "")[:200].strip().lower()
    return throttle.chave_hmac(_cfg().secret_key, "visitante", f"{ip_do_cliente()}\0{agente}")


# ---------------------------------------------------------------------------
# Hooks e handlers
# ---------------------------------------------------------------------------

def _antes_da_requisicao():
    if request.method not in METODOS_SEGUROS:
        validar_csrf()


def _depois_da_requisicao(resposta):
    cabecalhos = resposta.headers
    cabecalhos.setdefault("X-Content-Type-Options", "nosniff")
    cabecalhos.setdefault("X-Frame-Options", "DENY")
    cabecalhos.setdefault("Referrer-Policy", "same-origin")
    cabecalhos.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    cabecalhos.setdefault("Content-Security-Policy", _CSP)
    if resposta.mimetype == "application/json":
        cabecalhos["Cache-Control"] = "no-store"       # sessão, tempo restante e tokens nunca em cache
    if request.is_secure and _cfg().producao:
        cabecalhos.setdefault("Strict-Transport-Security", "max-age=31536000")
    return resposta


_MENSAGENS_HTTP = {
    400: "Requisição inválida.",
    401: "Autenticação necessária.",
    403: "Acesso negado.",
    404: "Endpoint não encontrado",
    405: "Método não permitido.",
    413: "Requisição grande demais.",
    415: "Tipo de conteúdo não suportado. Envie JSON.",
    429: "Muitas requisições. Tente novamente em instantes.",
    500: "Erro interno do servidor",
}


def _tratar_erro_http(erro: HTTPException):
    status = erro.code or 500
    resposta = jsonify({
        "erro": _MENSAGENS_HTTP.get(status, erro.name),
        "codigo": erro.name.lower().replace(" ", "_"),
    })
    resposta.status_code = status
    if status == 405 and getattr(erro, "valid_methods", None):
        resposta.headers["Allow"] = ", ".join(erro.valid_methods)
    return resposta


def registrar_seguranca(app) -> None:
    """Liga CSRF, cabeçalhos e tratadores de erro ao app."""
    app.before_request(_antes_da_requisicao)
    app.after_request(_depois_da_requisicao)
    app.register_error_handler(ErroRequisicao, lambda erro: erro.para_resposta())
    # HTTPException cobre 404/405/413/500...; um erro inesperado vira InternalServerError
    # (o Flask já registra o traceback no log) e chega aqui SEM o texto da exceção.
    app.register_error_handler(HTTPException, _tratar_erro_http)
