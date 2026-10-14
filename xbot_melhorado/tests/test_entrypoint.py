"""Ponto de entrada único: `python app.py` e `python app_improved.py` sobem o MESMO app, compatível com o frontend."""

import ast
import json
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

import app as xbot_app

from . import PASTA_TEMP, RAIZ
from .base import XBotTestCase

CHAVE = "f3a9c1d27b8e4a06915d3c7e2b4f8a1d6e0c9b5a7d2f4e8c1a3b6d9e0f2a4c71"

# Rotas que existiam no app.py e/ou no antigo app_improved.py + as que a interface chama
ROTAS_ESPERADAS = {
    "/", "/responder", "/quiz/<categoria>", "/exercicio/<categoria>", "/historico/<nome_usuario>",
    "/limpar_historico/<nome_usuario>", "/status", "/conhecimento", "/estatisticas", "/raciocinio_debug",
    "/db_status", "/registrar", "/login", "/logout", "/sessao",
}


def porta_livre() -> int:
    with socket.socket() as soquete:
        soquete.bind(("127.0.0.1", 0))
        return soquete.getsockname()[1]


def ambiente_neutro(**extra) -> dict:
    """Ambiente do subprocesso: nada do seu ambiente/.env interfere (variáveis explícitas vencem o .env)."""
    base = {chave: valor for chave, valor in os.environ.items() if not chave.startswith("XBOT_")}
    base.update({
        "XBOT_ENV": "production", "XBOT_SECRET_KEY": CHAVE, "XBOT_HOST": "127.0.0.1", "XBOT_DEBUG": "0",
        "XBOT_ALLOWED_ORIGINS": "", "XBOT_COOKIE_SAMESITE": "Lax", "XBOT_COOKIE_SECURE": "auto",
        "XBOT_TRUSTED_PROXIES": "0", "XBOT_DIAGNOSTICS": "0",
        "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1",
    })
    base.update({chave: str(valor) for chave, valor in extra.items()})
    return base


class Servidor:
    """Roda `python <script>` do jeito que a pessoa faria e espera o servidor responder."""

    def __init__(self, script: str, **ambiente):
        self.tmp = tempfile.mkdtemp(dir=PASTA_TEMP)
        self.porta = porta_livre()
        self.banco = os.path.join(self.tmp, "srv.db")
        self.ambiente = ambiente_neutro(XBOT_PORT=self.porta, XBOT_DB_PATH=self.banco, **ambiente)
        self.script = script
        self.saida = ""
        self.proc = None

    def __enter__(self):
        opcoes = {"start_new_session": True} if os.name != "nt" else {}
        self.proc = subprocess.Popen(
            [sys.executable, self.script], cwd=RAIZ, env=self.ambiente,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", **opcoes,
        )
        limite = time.time() + 40
        while time.time() < limite:
            if self.proc.poll() is not None:
                self.parar()
                raise AssertionError(f"o servidor terminou sozinho (código {self.proc.returncode}):\n{self.saida}")
            try:
                with urllib.request.urlopen(self.url("/sessao"), timeout=2):
                    return self
            except (urllib.error.URLError, ConnectionError, socket.timeout):
                time.sleep(0.2)
        self.parar()
        raise AssertionError(f"o servidor não respondeu em 40 s:\n{self.saida}")

    def __exit__(self, *_):
        self.parar()

    def url(self, caminho: str) -> str:
        return f"http://127.0.0.1:{self.porta}{caminho}"

    def parar(self):
        if self.proc is None:
            return
        if self.proc.poll() is None:
            try:
                if os.name == "nt":
                    self.proc.terminate()
                else:
                    os.killpg(self.proc.pid, signal.SIGTERM)       # recarregador: pai e filho
            except (ProcessLookupError, PermissionError):
                pass
        try:
            self.saida, _ = self.proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.saida, _ = self.proc.communicate()

    def requisitar(self, caminho, metodo="GET", corpo=None):
        dados = None if corpo is None else json.dumps(corpo).encode("utf-8")
        pedido = urllib.request.Request(self.url(caminho), data=dados, method=metodo,
                                        headers={"Content-Type": "application/json"} if dados else {})
        try:
            with urllib.request.urlopen(pedido, timeout=10) as resposta:
                return resposta.status, dict(resposta.headers), resposta.read().decode("utf-8")
        except urllib.error.HTTPError as erro:
            return erro.code, dict(erro.headers), erro.read().decode("utf-8")


def rodar_ate_o_fim(script: str, **ambiente):
    return subprocess.run([sys.executable, script], cwd=RAIZ, env=ambiente_neutro(**ambiente),
                          capture_output=True, text=True, encoding="utf-8", timeout=60)


class RotasETest(XBotTestCase):
    def test_o_app_unico_tem_todas_as_rotas_do_app_e_do_app_improved(self):
        regras = {regra.rule for regra in self.app.url_map.iter_rules()}
        self.assertTrue(ROTAS_ESPERADAS <= regras, ROTAS_ESPERADAS - regras)

    def test_todo_endpoint_chamado_pelo_frontend_existe(self):
        with open(os.path.join(RAIZ, "static", "script.js"), encoding="utf-8") as arquivo:
            js = arquivo.read()
        endpoints = re.findall(r"_ENDPOINT:\s*'(/[a-z_]*)'", js)
        self.assertGreaterEqual(len(endpoints), 6)
        regras = {regra.rule for regra in self.app.url_map.iter_rules()}
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                self.assertIn(endpoint, regras)
        for obrigatorio in ("/sessao", "/login", "/registrar", "/logout", "/responder"):
            self.assertIn(obrigatorio, endpoints)

    def test_frontend_envia_o_token_csrf(self):
        with open(os.path.join(RAIZ, "static", "script.js"), encoding="utf-8") as arquivo:
            js = arquivo.read()
        self.assertIn("X-CSRF-Token", js)
        # nenhum fetch "solto": POST/DELETE passam todos pela camada Http.requisitar
        posts = re.findall(r"fetch\([^)]*\{[^}]*method:\s*'(?:POST|DELETE|PUT)'", js, re.S)
        self.assertEqual(len(re.findall(r"method\s*=\s*'POST'", js)), 1)       # só o padrão de Http.requisitar
        self.assertEqual(posts, [])

    def test_flask_debug_do_ambiente_nao_liga_o_debug(self):
        """Quem tinha FLASK_DEBUG=1 exportado (o README antigo mandava) não ganha debug por tabela."""
        from unittest import mock

        with mock.patch.dict(os.environ, {"FLASK_DEBUG": "1"}):
            self.assertFalse(xbot_app.create_app(self.cfg).debug)
            self.assertFalse(self.cfg.debug)

    def test_template_usa_senha_de_10_caracteres_como_o_servidor(self):
        with open(os.path.join(RAIZ, "templates", "index.html"), encoding="utf-8") as arquivo:
            html = arquivo.read()
        self.assertIn('minlength="10"', html)
        self.assertNotIn('minlength="6"', html)

    def test_pagina_inicial_e_arquivos_estaticos(self):
        c = self.cliente()
        r = c.http.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("/static/script.js", r.get_data(as_text=True))
        for arquivo in ("script.js", "style.css"):
            with c.http.get(f"/static/{arquivo}") as estatico:        # fecha o arquivo aberto pelo send_file
                self.assertEqual(estatico.status_code, 200, arquivo)


class ShimAppImprovedTest(unittest.TestCase):
    def test_app_improved_so_delega(self):
        import app_improved

        self.assertIs(app_improved.create_app, xbot_app.create_app)
        self.assertIs(app_improved.main, xbot_app.main)
        self.assertIs(app_improved.XBotIA, xbot_app.XBotIA)
        with open(os.path.join(RAIZ, "app_improved.py"), encoding="utf-8") as arquivo:
            fonte = arquivo.read()
        self.assertNotRegex(fonte, r"\bFlask\(")                 # não define um segundo app
        self.assertNotRegex(fonte, r"\.run\(")
        self.assertNotIn("@app.route", fonte)

    def test_atributo_app_e_criado_sob_demanda(self):
        import app_improved

        sentinela = object()
        from unittest import mock

        anterior = xbot_app._app_padrao
        xbot_app._app_padrao = None
        try:
            with mock.patch.object(xbot_app, "create_app", return_value=sentinela) as fabrica:
                self.assertIs(app_improved.app, sentinela)
                self.assertIs(xbot_app.app, sentinela)               # o mesmo objeto, criado uma vez
                fabrica.assert_called_once()
        finally:
            xbot_app._app_padrao = anterior

    def test_atributo_inexistente_continua_dando_erro(self):
        import app_improved

        with self.assertRaises(AttributeError):
            app_improved.nao_existe
        with self.assertRaises(AttributeError):
            xbot_app.nao_existe


class ServidorRealTest(unittest.TestCase):
    """Sobe o servidor de verdade (processo separado, banco temporário) e fala com ele por HTTP."""

    def conferir_app_compativel(self, servidor):
        status, cabecalhos, corpo = servidor.requisitar("/sessao")
        self.assertEqual(status, 200)
        sessao = json.loads(corpo)
        self.assertIn(sessao["tempo_restante"], (599, 600))       # relógio real: int(600 - alguns milissegundos)
        self.assertFalse(sessao["autenticado"])
        self.assertTrue(sessao["csrf_token"])
        self.assertIn("default-src 'self'", cabecalhos.get("Content-Security-Policy", ""))

        status, _, corpo = servidor.requisitar("/")
        self.assertEqual(status, 200)
        self.assertIn("/static/script.js", corpo)

        # as rotas que a interface chama existem e o CSRF está ligado
        for rota in ("/login", "/registrar", "/responder", "/logout"):
            status, _, corpo = servidor.requisitar(rota, "POST", {})
            self.assertEqual(status, 403, f"{rota}: {corpo}")
            self.assertEqual(json.loads(corpo)["codigo"], "csrf")
        self.assertEqual(servidor.requisitar("/nao-existe")[0], 404)

    def test_python_app_py_em_producao(self):
        with Servidor("app.py") as servidor:
            self.conferir_app_compativel(servidor)
        saida = servidor.saida
        self.assertIn(f"Running on http://127.0.0.1:{servidor.porta}", saida)
        self.assertNotIn("Debugger is active", saida)
        self.assertNotIn("Debug mode: on", saida)
        self.assertNotIn("0.0.0.0", saida.replace("0.0.0.0/0", ""))             # não escuta na rede
        self.assertEqual(saida.count("executando seed inicial"), 1)
        self.assertEqual(saida.count("Iniciando XBot v0.3.0 Beta"), 1)

    def test_python_app_improved_py_sobe_o_mesmo_app(self):
        with Servidor("app_improved.py") as servidor:
            self.conferir_app_compativel(servidor)
        self.assertNotIn("Debugger is active", servidor.saida)
        self.assertEqual(servidor.saida.count("Iniciando XBot v0.3.0 Beta"), 1)

    def test_segundo_inicio_nao_semeia_de_novo(self):
        with Servidor("app.py") as primeiro:
            self.assertEqual(primeiro.requisitar("/sessao")[0], 200)
        self.assertEqual(primeiro.saida.count("executando seed inicial"), 1)
        # mesmo banco, novo processo (reinício do servidor)
        segundo = Servidor("app.py")
        segundo.banco = primeiro.banco
        segundo.ambiente["XBOT_DB_PATH"] = primeiro.banco
        with segundo:
            self.assertEqual(segundo.requisitar("/sessao")[0], 200)
        self.assertEqual(segundo.saida.count("executando seed inicial"), 0)
        self.assertIn("SQLite pronto", segundo.saida)

    @unittest.skipIf(os.name == "nt", "o teste do recarregador usa grupo de processos POSIX")
    def test_modo_desenvolvimento_com_recarregador_inicializa_uma_vez_so(self):
        # XBOT_DIAGNOSTICS vazio = "usa o padrão do ambiente" (em development, aberto)
        with Servidor("app.py", XBOT_ENV="development", XBOT_DEBUG="1", XBOT_DIAGNOSTICS="") as servidor:
            self.assertEqual(servidor.requisitar("/sessao")[0], 200)
            self.assertEqual(servidor.requisitar("/db_status")[0], 200)
        saida = servidor.saida
        self.assertIn("Debugger is active", saida)                              # recarregador/debug ligados
        self.assertEqual(saida.count("executando seed inicial"), 1, saida)      # antes: 2 (pai e filho)
        self.assertEqual(saida.count("Iniciando XBot v0.3.0 Beta"), 1, saida)
        self.assertEqual(saida.count("SQLite pronto"), 1, saida)

    def test_producao_sem_chave_nao_inicia(self):
        for script in ("app.py", "app_improved.py"):
            with self.subTest(script=script):
                banco = os.path.join(tempfile.mkdtemp(dir=PASTA_TEMP), "nao_deve_existir.db")
                resultado = rodar_ate_o_fim(script, XBOT_SECRET_KEY="", XBOT_DB_PATH=banco, XBOT_PORT=porta_livre())
                self.assertEqual(resultado.returncode, 2, resultado.stdout)
                self.assertIn("XBOT_SECRET_KEY", resultado.stderr)
                self.assertIn("secrets.token_hex(32)", resultado.stderr)
                self.assertFalse(os.path.exists(banco))

    def test_producao_com_host_de_rede_nao_inicia_o_servidor_de_desenvolvimento(self):
        banco = os.path.join(tempfile.mkdtemp(dir=PASTA_TEMP), "nao_deve_existir.db")
        resultado = rodar_ate_o_fim("app.py", XBOT_HOST="0.0.0.0", XBOT_DB_PATH=banco, XBOT_PORT=porta_livre())
        self.assertEqual(resultado.returncode, 2)
        self.assertIn("waitress", resultado.stderr)
        self.assertFalse(os.path.exists(banco))

    def test_wsgi_exige_a_chave_e_entrega_o_app(self):
        banco = os.path.join(tempfile.mkdtemp(dir=PASTA_TEMP), "wsgi.db")
        sem_chave = subprocess.run(
            [sys.executable, "-c", "import wsgi"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
            env=ambiente_neutro(XBOT_SECRET_KEY="", XBOT_DB_PATH=banco), timeout=60)
        self.assertNotEqual(sem_chave.returncode, 0)
        self.assertIn("XBOT_SECRET_KEY", sem_chave.stderr)
        self.assertFalse(os.path.exists(banco))

        com_chave = subprocess.run(
            [sys.executable, "-c", "import wsgi; print(type(wsgi.app).__name__, wsgi.app.debug)"],
            cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
            env=ambiente_neutro(XBOT_DB_PATH=banco, FLASK_DEBUG="1"), timeout=60)
        self.assertEqual(com_chave.returncode, 0, com_chave.stderr)
        self.assertEqual(com_chave.stdout.strip(), "Flask False")          # mesmo com FLASK_DEBUG=1 no ambiente


class ArquivosDoProjetoTest(unittest.TestCase):
    """Verificações de código-fonte que protegem os requisitos de segurança contra regressões."""

    def codigo(self):
        for pasta, _dirs, arquivos in os.walk(RAIZ):
            if any(parte in pasta for parte in ("__pycache__", f"{os.sep}tests", ".git", "venv")):
                continue
            for nome in arquivos:
                if nome.endswith(".py"):
                    caminho = os.path.join(pasta, nome)
                    with open(caminho, encoding="utf-8") as arquivo:
                        yield os.path.relpath(caminho, RAIZ), arquivo.read()

    @staticmethod
    def _nome(alvo):
        if isinstance(alvo, ast.Name):
            return alvo.id
        if isinstance(alvo, ast.Attribute):
            return alvo.attr
        if isinstance(alvo, ast.Subscript) and isinstance(alvo.slice, ast.Constant):
            return str(alvo.slice.value)
        return ""

    def chaves_literais(self, fonte):
        """Atribuições/argumentos/consultas ao ambiente em que uma chave secreta recebe um texto fixo."""
        achados = []
        for no in ast.walk(ast.parse(fonte)):
            pares = []                                              # (nome, nó do valor)
            if isinstance(no, ast.Assign):
                pares = [(self._nome(alvo), no.value) for alvo in no.targets]
            elif isinstance(no, ast.AnnAssign) and no.value is not None:
                pares = [(self._nome(no.target), no.value)]
            elif isinstance(no, ast.keyword) and no.arg:
                pares = [(no.arg, no.value)]
            elif isinstance(no, ast.Dict):
                pares = [(str(k.value), v) for k, v in zip(no.keys, no.values) if isinstance(k, ast.Constant)]
            elif (isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)
                  and no.func.attr in ("get", "getenv", "setdefault") and len(no.args) >= 2
                  and isinstance(no.args[0], ast.Constant)):
                pares = [(str(no.args[0].value), no.args[1])]       # os.environ.get("..._KEY", "padrão")
            for nome, valor in pares:
                if ("secret_key" in nome.lower() and isinstance(valor, ast.Constant)
                        and isinstance(valor.value, str) and len(valor.value) >= 4):
                    achados.append((no.lineno, nome))
        return achados

    def test_nenhuma_chave_secreta_padrao_no_codigo(self):
        antiga = "dev-secret-key" + "-trocar-em-producao"            # o valor que existia no app.py original
        for caminho, fonte in self.codigo():
            with self.subTest(arquivo=caminho):
                self.assertNotIn(antiga, fonte)
                self.assertEqual(self.chaves_literais(fonte), [])

    def test_o_detector_de_chave_fixa_funciona(self):
        """Garante que o teste acima não é cego: ele pega os jeitos clássicos de embutir uma chave."""
        ruins = [
            "app.secret_key = 'abcd1234'",
            "SECRET_KEY = 'abcd1234'",
            "app.config['SECRET_KEY'] = 'abcd1234'",
            "x = os.environ.get('XBOT_SECRET_KEY', 'abcd1234')",
            "os.getenv('SECRET_KEY', 'abcd1234')",
            "Config(secret_key='abcd1234')",
            "cfg = {'SECRET_KEY': 'abcd1234'}",
        ]
        for trecho in ruins:
            with self.subTest(trecho=trecho):
                self.assertTrue(self.chaves_literais(trecho), trecho)
        bons = [
            "app.secret_key = cfg.secret_key",
            "chave = env.get('XBOT_SECRET_KEY')",
            "SECRET_KEY = os.environ['XBOT_SECRET_KEY']",
            "MSG = 'use XBOT_SECRET_KEY = \"<chave gerada>\"'",
        ]
        for trecho in bons:
            with self.subTest(trecho=trecho):
                self.assertEqual(self.chaves_literais(trecho), [], trecho)

    def test_chave_so_vem_do_ambiente(self):
        with open(os.path.join(RAIZ, "app.py"), encoding="utf-8") as arquivo:
            fonte = arquivo.read()
        self.assertIn("cfg.secret_key", fonte)
        self.assertNotIn("os.environ.get('XBOT_SECRET_KEY'", fonte)
        with open(os.path.join(RAIZ, "config.py"), encoding="utf-8") as arquivo:
            self.assertIn('env.get("XBOT_SECRET_KEY")', arquivo.read())

    def test_servidor_nao_e_ligado_com_debug_nem_na_rede_por_codigo(self):
        for nome in ("app.py", "app_improved.py", "wsgi.py"):
            with open(os.path.join(RAIZ, nome), encoding="utf-8") as arquivo:
                fonte = arquivo.read()
            with self.subTest(arquivo=nome):
                self.assertNotRegex(fonte, r"debug\s*=\s*True")
                self.assertNotRegex(fonte, r"host\s*=\s*['\"]0\.0\.0\.0['\"]")
                self.assertNotRegex(fonte, r"use_reloader\s*=\s*True")
        with open(os.path.join(RAIZ, "app.py"), encoding="utf-8") as arquivo:
            fonte = arquivo.read()
        self.assertIn("debug=cfg.debug", fonte)
        self.assertIn("host=cfg.host", fonte)

    def test_cors_nunca_aberto_para_todos(self):
        for caminho, fonte in self.codigo():
            with self.subTest(arquivo=caminho):
                self.assertNotRegex(fonte, r"CORS\(\s*app\s*\)")
                self.assertNotRegex(fonte, r"origins\s*=\s*['\"]\*['\"]")
                self.assertNotRegex(fonte, r"supports_credentials\s*=\s*True[^)]*origins\s*=\s*['\"]\*")

    def test_gitignore_protege_segredos_e_banco(self):
        with open(os.path.join(RAIZ, ".gitignore"), encoding="utf-8") as arquivo:
            linhas = {linha.strip() for linha in arquivo}
        for esperado in (".env", "xbot.db", "__pycache__/"):
            self.assertIn(esperado, linhas)

    def test_env_example_nao_traz_chave_pronta(self):
        with open(os.path.join(RAIZ, ".env.example"), encoding="utf-8") as arquivo:
            linhas = [l.strip() for l in arquivo if l.strip() and not l.startswith("#")]
        chave = next(l for l in linhas if l.startswith("XBOT_SECRET_KEY="))
        self.assertEqual(chave, "XBOT_SECRET_KEY=")


if __name__ == "__main__":
    unittest.main()
