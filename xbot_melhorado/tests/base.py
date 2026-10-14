"""Infraestrutura comum dos testes: banco temporário, relógio simulado e cliente HTTP com cookies/CSRF."""

import os
import shutil
import tempfile
import unittest
from unittest import mock

import relogio
from config import Config
from database import db as banco

from . import PASTA_TEMP

import app as xbot_app

SENHA_BOA = "Tr0ca-Esta_Frase!42"
CHAVE_TESTE = "chave-de-teste-" + "x" * 30
_SEM = object()

_MODELO = None


def config_de_teste(db_path: str, **extra) -> Config:
    """Config de ambiente 'testing' lida de um dicionário (nunca de os.environ nem do .env)."""
    env = {"XBOT_ENV": "testing", "XBOT_SECRET_KEY": CHAVE_TESTE, "XBOT_DB_PATH": db_path}
    env.update({chave: str(valor) for chave, valor in extra.items()})
    return Config.from_env(env, dotenv_path=None)


def banco_modelo() -> str:
    """Banco já semeado — criado UMA vez por execução; cada teste recebe uma cópia."""
    global _MODELO
    if _MODELO is None:
        from database.bootstrap import inicializar_banco

        caminho = os.path.join(PASTA_TEMP, "modelo.db")
        anterior = banco._caminho_ativo          # quem chamou pode já ter configurado outro banco
        banco.configurar_caminho(caminho)
        try:
            inicializar_banco()
        finally:
            banco.configurar_caminho(anterior)
        _MODELO = caminho
    return _MODELO


class RelogioFalso:
    def __init__(self, inicio: float = 1_800_000_000.0):
        self.t = inicio

    def agora(self) -> float:
        return self.t

    def avancar(self, segundos: float) -> None:
        self.t += segundos


class Cliente:
    """Um navegador de mentira: cookies próprios, IP e User-Agent configuráveis, token CSRF automático."""

    def __init__(self, app, ip: str = "198.51.100.7", ua: str = "Mozilla/5.0 (TesteXBot)"):
        self.app = app
        self.http = app.test_client()
        self.http.environ_base["REMOTE_ADDR"] = ip
        self.http.environ_base["HTTP_USER_AGENT"] = ua
        self.token = None

    # -- requisições -------------------------------------------------------------------
    def _guardar_token(self, resposta):
        corpo = resposta.get_json(silent=True)
        if isinstance(corpo, dict) and isinstance(corpo.get("csrf_token"), str):
            self.token = corpo["csrf_token"]
        return resposta

    def _cabecalhos(self, token, extra):
        cabecalhos = dict(extra or {})
        if token is True:
            if self.token is None:
                self.sessao()
            token = self.token
        if token:
            cabecalhos["X-CSRF-Token"] = token
        return cabecalhos

    def get(self, url, **kw):
        return self._guardar_token(self.http.get(url, **kw))

    def post(self, url, json=_SEM, *, token=True, headers=None, **kw):
        cabecalhos = self._cabecalhos(token, headers)
        if json is not _SEM:
            kw["json"] = json
        return self._guardar_token(self.http.post(url, headers=cabecalhos, **kw))

    def delete(self, url, *, token=True, headers=None, **kw):
        return self._guardar_token(self.http.delete(url, headers=self._cabecalhos(token, headers), **kw))

    # -- atalhos -------------------------------------------------------------------------
    def sessao(self) -> dict:
        return self.get("/sessao").get_json()

    def registrar(self, nome="Teste Silva", email="teste@example.com", senha=SENHA_BOA):
        return self.post("/registrar", {"nome": nome, "email": email, "senha": senha})

    def login(self, email, senha=SENHA_BOA):
        return self.post("/login", {"email": email, "senha": senha})

    def logout(self):
        return self.post("/logout")

    def responder(self, mensagem, nome="Ana"):
        return self.post("/responder", {"mensagem": mensagem, "nome_usuario": nome})


class XBotTestCase(unittest.TestCase):
    """Cada teste: banco próprio (cópia do modelo), relógio simulado e um app novo."""

    env_extra: dict = {}

    def setUp(self):
        self.tmp = tempfile.mkdtemp(dir=PASTA_TEMP)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db_path = os.path.join(self.tmp, "t.db")
        shutil.copyfile(banco_modelo(), self.db_path)

        self.relogio = RelogioFalso()
        patcher = mock.patch.object(relogio, "agora", self.relogio.agora)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.cfg = config_de_teste(self.db_path, **self.env_extra)
        self.app = xbot_app.create_app(self.cfg)
        self.addCleanup(banco.configurar_caminho, None)

    # -- utilitários ---------------------------------------------------------------------
    def cliente(self, **kw) -> Cliente:
        return Cliente(self.app, **kw)

    def consulta(self, sql: str, params=()):
        """Leitura direta no banco temporário do teste."""
        with banco.get_connection() as conn:
            return [tuple(linha) for linha in conn.execute(sql, params).fetchall()]

    def assertJsonErro(self, resposta, status, codigo=None):
        self.assertEqual(resposta.status_code, status, resposta.get_data(as_text=True)[:300])
        corpo = resposta.get_json(silent=True)
        self.assertIsInstance(corpo, dict, "o erro deve vir em JSON")
        self.assertTrue(corpo.get("erro") or corpo.get("resposta"), corpo)
        if codigo is not None:
            self.assertEqual(corpo.get("codigo"), codigo)
        return corpo
