"""CSRF (token + origem), CORS restrito às origens configuradas e cabeçalhos de segurança."""

import re
import unittest

from . import RAIZ
from .base import SENHA_BOA, XBotTestCase

CHAVE_PRODUCAO = "f3a9c1d27b8e4a06915d3c7e2b4f8a1d6e0c9b5a7d2f4e8c1a3b6d9e0f2a4c71"

# (método, URL, corpo) — tudo que altera estado ou age em nome do usuário
ROTAS_PROTEGIDAS = [
    ("post", "/responder", {"mensagem": "oi", "nome_usuario": "Ana"}),
    ("post", "/login", {"email": "x@example.com", "senha": "qualquer-coisa-1"}),
    ("post", "/registrar", {"nome": "Teste", "email": "t@example.com", "senha": SENHA_BOA}),
    ("post", "/logout", None),
    ("post", "/quiz/arquitetura", {"nome_usuario": "Ana"}),
    ("post", "/raciocinio_debug", {"mensagem": "cpu"}),
    ("delete", "/limpar_historico/Ana", None),
]


class CsrfTest(XBotTestCase):
    def chamar(self, c, metodo, url, corpo, token, headers=None):
        if metodo == "post":
            return c.post(url, corpo, token=token, headers=headers) if corpo is not None \
                else c.post(url, token=token, headers=headers)
        return c.delete(url, token=token, headers=headers)

    def test_sem_token_toda_rota_que_altera_estado_e_recusada(self):
        for metodo, url, corpo in ROTAS_PROTEGIDAS:
            with self.subTest(rota=f"{metodo.upper()} {url}"):
                c = self.cliente()
                c.sessao()                                     # tem sessão (e cookie), mas não manda o token
                r = self.chamar(c, metodo, url, corpo, token=None)
                self.assertJsonErro(r, 403, "csrf")

    def test_token_errado_ou_vazio_e_recusado(self):
        for token in ("errado", "x" * 43, " ", "tókén"):
            with self.subTest(token=token):
                c = self.cliente()
                c.sessao()
                r = c.post("/responder", {"mensagem": "oi"}, token=token)
                self.assertJsonErro(r, 403, "csrf")

    def test_sem_nenhuma_sessao_previa_tambem_e_recusado(self):
        """Um POST "frio" (sem cookie, sem token) não passa — nem para /login nem para /registrar."""
        for _metodo, url, corpo in ROTAS_PROTEGIDAS[:4]:
            with self.subTest(url=url):
                r = self.cliente().http.post(url, json=corpo or {})
                self.assertJsonErro(r, 403, "csrf")

    def test_token_correto_passa(self):
        for metodo, url, corpo in ROTAS_PROTEGIDAS:
            with self.subTest(rota=f"{metodo.upper()} {url}"):
                c = self.cliente()
                c.sessao()
                r = self.chamar(c, metodo, url, corpo, token=True)
                self.assertNotEqual(r.get_json().get("codigo"), "csrf", r.get_data(as_text=True))

    def test_rotas_de_leitura_nao_exigem_token(self):
        c = self.cliente()
        for url in ("/", "/sessao", "/status", "/conhecimento", "/exercicio/python_basico"):
            with self.subTest(url=url):
                self.assertEqual(c.http.get(url).status_code, 200)

    def test_token_de_um_navegador_nao_vale_no_outro(self):
        a, b = self.cliente(), self.cliente(ip="192.0.2.20")
        a.sessao()
        b.sessao()
        self.assertNotEqual(a.token, b.token)
        self.assertJsonErro(a.post("/responder", {"mensagem": "oi"}, token=b.token), 403, "csrf")

    def test_token_e_trocado_no_cadastro_no_login_e_no_logout(self):
        c = self.cliente()
        t0 = c.sessao()["csrf_token"]
        c.registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        t1 = c.token
        self.assertNotEqual(t0, t1)
        self.assertJsonErro(c.post("/responder", {"mensagem": "oi"}, token=t0), 403, "csrf")   # o antigo morreu
        c.logout()
        t2 = c.token
        self.assertNotEqual(t1, t2)
        self.assertJsonErro(c.post("/responder", {"mensagem": "oi"}, token=t1), 403, "csrf")
        c.login("maria@example.com")
        t3 = c.token
        self.assertNotEqual(t2, t3)
        self.assertEqual(c.post("/responder", {"mensagem": "oi"}).status_code, 200)

    def test_login_que_falha_nao_troca_a_sessao(self):
        c = self.cliente()
        t0 = c.sessao()["csrf_token"]
        c.login("ninguem@example.com", "senha-qualquer-1")
        self.assertEqual(c.sessao()["csrf_token"], t0)

    def test_mensagem_de_erro_nao_vaza_detalhes(self):
        r = self.cliente().http.post("/responder", json={"mensagem": "oi"})
        corpo = r.get_json()
        self.assertEqual(set(corpo), {"erro", "codigo"})
        self.assertIn("Recarregue a página", corpo["erro"])

    def test_token_tem_entropia_suficiente(self):
        tokens = {self.cliente().sessao()["csrf_token"] for _ in range(20)}
        self.assertEqual(len(tokens), 20)
        self.assertTrue(all(len(t) >= 40 for t in tokens))


class OrigemTest(XBotTestCase):
    """Cabeçalho Origin/Referer: além do token, a requisição tem de vir do próprio site."""

    def post_com(self, headers, token=True):
        c = self.cliente()
        c.sessao()
        return c.post("/responder", {"mensagem": "oi"}, token=token, headers=headers)

    def test_mesma_origem_passa(self):
        self.assertEqual(self.post_com({"Origin": "http://localhost"}).status_code, 200)
        self.assertEqual(self.post_com({"Referer": "http://localhost/pagina?x=1"}).status_code, 200)

    def test_sem_origin_nem_referer_decide_o_token(self):
        """curl, scripts, apps: não mandam Origin — vale o token."""
        self.assertEqual(self.post_com({}).status_code, 200)

    def test_origem_de_outro_site_e_recusada_mesmo_com_token_valido(self):
        for origem in ("https://evil.example", "http://localhost.evil.example", "http://localhost:5000",
                       "https://localhost", "null", "http://127.0.0.1", "HTTP://LOCALHOST.EVIL.COM"):
            with self.subTest(origin=origem):
                self.assertJsonErro(self.post_com({"Origin": origem}), 403, "origem_invalida")

    def test_referer_de_outro_site_ou_malformado_e_recusado(self):
        for referer in ("https://evil.example/pagina", "isto nao e uma url", "//evil.example/x", "javascript:alert(1)"):
            with self.subTest(referer=referer):
                self.assertJsonErro(self.post_com({"Referer": referer}), 403, "origem_invalida")

    def test_origin_vale_mais_que_referer(self):
        r = self.post_com({"Origin": "https://evil.example", "Referer": "http://localhost/"})
        self.assertJsonErro(r, 403, "origem_invalida")

    def test_origem_certa_com_token_errado_continua_recusada(self):
        self.assertJsonErro(self.post_com({"Origin": "http://localhost"}, token="errado"), 403, "csrf")

    def test_login_e_cadastro_tambem_conferem_a_origem(self):
        c = self.cliente()
        c.sessao()
        r = c.post("/login", {"email": "a@example.com", "senha": "x"}, headers={"Origin": "https://evil.example"})
        self.assertJsonErro(r, 403, "origem_invalida")
        r = c.post("/registrar", {"nome": "A B", "email": "a@example.com", "senha": SENHA_BOA},
                   headers={"Origin": "https://evil.example"})
        self.assertJsonErro(r, 403, "origem_invalida")
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM users")[0][0], 0)


class OrigemConfiguradaTest(XBotTestCase):
    env_extra = {"XBOT_ALLOWED_ORIGINS": "https://app.example.com,http://localhost:5173"}

    def post_com(self, origem, token=True):
        c = self.cliente()
        c.sessao()
        return c.post("/responder", {"mensagem": "oi"}, token=token, headers={"Origin": origem})

    def test_origem_configurada_passa_com_token(self):
        self.assertEqual(self.post_com("https://app.example.com").status_code, 200)
        self.assertEqual(self.post_com("http://localhost:5173").status_code, 200)

    def test_origem_configurada_sem_token_continua_recusada(self):
        self.assertJsonErro(self.post_com("https://app.example.com", token=None), 403, "csrf")

    def test_outras_origens_continuam_recusadas(self):
        for origem in ("https://evil.example", "http://app.example.com", "https://app.example.com.evil.com",
                       "https://sub.app.example.com", "null"):
            with self.subTest(origin=origem):
                self.assertJsonErro(self.post_com(origem), 403, "origem_invalida")


class CorsSemOrigensTest(XBotTestCase):
    """Padrão: nenhuma origem externa. Antes era CORS(app) = qualquer site lendo a API com cookies."""

    def test_nenhum_cabecalho_cors_para_origem_externa(self):
        c = self.cliente()
        for url in ("/sessao", "/status", "/conhecimento"):
            with self.subTest(url=url):
                r = c.http.get(url, headers={"Origin": "https://evil.example"})
                self.assertNotIn("Access-Control-Allow-Origin", r.headers)
                self.assertNotIn("Access-Control-Allow-Credentials", r.headers)

    def test_preflight_de_origem_externa_nao_e_autorizado(self):
        r = self.cliente().http.options("/responder", headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-csrf-token",
        })
        self.assertNotIn("Access-Control-Allow-Origin", r.headers)
        self.assertNotIn("Access-Control-Allow-Headers", r.headers)

    def test_nunca_asterisco(self):
        r = self.cliente().http.get("/sessao", headers={"Origin": "https://evil.example"})
        self.assertNotEqual(r.headers.get("Access-Control-Allow-Origin"), "*")


class CorsConfiguradoTest(XBotTestCase):
    env_extra = {"XBOT_ALLOWED_ORIGINS": "https://app.example.com,http://localhost:5173"}

    def test_origem_permitida_recebe_cabecalhos_com_credenciais(self):
        r = self.cliente().http.get("/sessao", headers={"Origin": "https://app.example.com"})
        self.assertEqual(r.headers["Access-Control-Allow-Origin"], "https://app.example.com")
        self.assertEqual(r.headers["Access-Control-Allow-Credentials"], "true")
        self.assertIn("Origin", r.headers.get("Vary", ""))

    def test_origem_nao_listada_nao_recebe_nada(self):
        for origem in ("https://evil.example", "https://app.example.com.evil.com", "http://app.example.com",
                       "https://APP.example.com.br", "null"):
            with self.subTest(origin=origem):
                r = self.cliente().http.get("/sessao", headers={"Origin": origem})
                self.assertNotIn("Access-Control-Allow-Origin", r.headers)

    def test_nunca_asterisco_nem_refletir_qualquer_origem(self):
        for origem in ("https://app.example.com", "https://evil.example"):
            r = self.cliente().http.get("/sessao", headers={"Origin": origem})
            self.assertNotEqual(r.headers.get("Access-Control-Allow-Origin"), "*")

    def test_preflight_da_origem_permitida(self):
        r = self.cliente().http.options("/responder", headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-csrf-token",
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Access-Control-Allow-Origin"], "https://app.example.com")
        permitidos = r.headers["Access-Control-Allow-Headers"].lower()
        self.assertIn("x-csrf-token", permitidos)
        self.assertIn("content-type", permitidos)
        metodos = r.headers["Access-Control-Allow-Methods"].upper()
        self.assertIn("POST", metodos)
        self.assertIn("DELETE", metodos)
        self.assertNotIn("PUT", metodos)
        self.assertEqual(r.headers["Access-Control-Max-Age"], "600")

    def test_preflight_de_origem_nao_listada(self):
        r = self.cliente().http.options("/responder", headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-csrf-token",
        })
        self.assertNotIn("Access-Control-Allow-Origin", r.headers)

    def test_preflight_nao_e_barrado_pelo_csrf(self):
        """OPTIONS não carrega token nem cookie: precisa passar para o navegador poder perguntar."""
        r = self.cliente().http.options("/login", headers={
            "Origin": "https://app.example.com", "Access-Control-Request-Method": "POST"})
        self.assertEqual(r.status_code, 200)

    def test_erro_403_de_csrf_tambem_leva_cors_para_o_site_conseguir_ler(self):
        r = self.cliente().http.post("/responder", json={"mensagem": "oi"},
                                     headers={"Origin": "https://app.example.com"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.headers.get("Access-Control-Allow-Origin"), "https://app.example.com")


class CabecalhosDeSegurancaTest(XBotTestCase):
    def test_pagina_e_api_levam_os_cabecalhos(self):
        c = self.cliente()
        for url in ("/", "/sessao", "/rota-que-nao-existe"):
            with self.subTest(url=url):
                r = c.http.get(url)
                self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
                self.assertEqual(r.headers["X-Frame-Options"], "DENY")
                self.assertEqual(r.headers["Referrer-Policy"], "same-origin")
                csp = r.headers["Content-Security-Policy"]
                for diretiva in ("default-src 'self'", "script-src 'self'", "style-src 'self'",
                                 "frame-ancestors 'none'", "object-src 'none'", "base-uri 'none'"):
                    self.assertIn(diretiva, csp)
                self.assertNotIn("unsafe-inline", csp)
                self.assertNotIn("unsafe-eval", csp)

    def test_json_nunca_fica_em_cache(self):
        c = self.cliente()
        for url in ("/sessao", "/status", "/rota-que-nao-existe"):
            self.assertEqual(c.http.get(url).headers["Cache-Control"], "no-store")

    def test_sem_hsts_em_http_simples(self):
        self.assertNotIn("Strict-Transport-Security", self.cliente().http.get("/sessao").headers)

    def test_servidor_nao_anuncia_versao_do_flask_em_erros(self):
        r = self.cliente().http.get("/rota-que-nao-existe")
        self.assertNotIn("Traceback", r.get_data(as_text=True))
        self.assertNotIn("werkzeug", r.get_data(as_text=True).lower())


class HstsEmProducaoTest(XBotTestCase):
    env_extra = {"XBOT_ENV": "production", "XBOT_SECRET_KEY": CHAVE_PRODUCAO}

    def test_hsts_so_com_https_em_producao(self):
        c = self.cliente()
        self.assertNotIn("Strict-Transport-Security", c.http.get("/sessao").headers)
        r = c.http.get("/sessao", base_url="https://localhost")
        self.assertIn("max-age=", r.headers["Strict-Transport-Security"])


class PaginaCompativelComCspTest(unittest.TestCase):
    """A CSP (sem 'unsafe-inline') só funciona se a página não tiver script/estilo embutido."""

    def ler(self, caminho):
        with open(f"{RAIZ}/{caminho}", encoding="utf-8") as arquivo:
            return arquivo.read()

    def test_html_sem_script_estilo_ou_manipulador_embutido(self):
        html = self.ler("templates/index.html")
        for script in re.findall(r"<script\b[^>]*>", html, re.I):
            self.assertIn("src=", script)
        self.assertNotRegex(html, r"<style\b")
        self.assertNotRegex(html, r'\sstyle\s*=')
        self.assertNotRegex(html, r'\son[a-z]+\s*=')
        self.assertNotRegex(html, r"javascript:")

    def test_js_sem_eval(self):
        js = self.ler("static/script.js")
        self.assertNotRegex(js, r"\beval\s*\(")
        self.assertNotRegex(js, r"new\s+Function\s*\(")
        self.assertNotRegex(js, r"document\.write\s*\(")

    def test_css_sem_importar_recursos_externos(self):
        css = self.ler("static/style.css")
        self.assertNotRegex(css, r"@import\s+url\(\s*['\"]?https?:")
        self.assertNotRegex(css, r"url\(\s*['\"]?https?://")


if __name__ == "__main__":
    unittest.main()
