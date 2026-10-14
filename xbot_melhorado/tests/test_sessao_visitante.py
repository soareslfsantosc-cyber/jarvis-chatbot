"""Sessão (/sessao, /logout, cookies) e limite de 10 minutos do visitante, validado no servidor."""

import re
import unittest

from .base import SENHA_BOA, XBotTestCase

PERGUNTA = "o que é a arquitetura de von neumann?"


def cookie_de_sessao(resposta) -> str | None:
    """Valor do cookie 'session' enviado nesta resposta (None se a resposta não mexeu na sessão)."""
    for linha in resposta.headers.getlist("Set-Cookie"):
        achado = re.match(r"session=([^;]*)", linha)
        if achado:
            return achado.group(1)
    return None


class SessaoTest(XBotTestCase):
    def test_visitante_novo(self):
        r = self.cliente().get("/sessao")
        self.assertEqual(r.status_code, 200)
        corpo = r.get_json()
        self.assertFalse(corpo["autenticado"])
        self.assertIsNone(corpo["usuario"])
        self.assertEqual(corpo["tempo_restante"], 600)
        self.assertFalse(corpo["bloqueado"])
        self.assertGreaterEqual(len(corpo["csrf_token"]), 30)

    def test_resposta_de_sessao_nao_fica_em_cache(self):
        r = self.cliente().get("/sessao")
        self.assertEqual(r.headers["Cache-Control"], "no-store")

    def test_usuario_logado_nao_tem_relogio(self):
        c = self.cliente()
        c.registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        corpo = c.sessao()
        self.assertTrue(corpo["autenticado"])
        self.assertEqual(corpo["usuario"], {"id": 1, "nome": "Maria Souza", "email": "maria@example.com"})
        self.assertIsNone(corpo["tempo_restante"])
        self.assertFalse(corpo["bloqueado"])

    def test_logout_volta_a_ser_visitante_e_troca_o_token(self):
        c = self.cliente()
        c.registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        token_logado = c.token
        r = c.logout()
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["sucesso"])
        self.assertNotEqual(c.token, token_logado)
        self.assertFalse(c.sessao()["autenticado"])
        # o token antigo não vale mais
        self.assertJsonErro(c.post("/logout", token=token_logado), 403, "csrf")

    def test_logout_exige_csrf(self):
        c = self.cliente()
        c.registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        self.assertJsonErro(c.post("/logout", token=None), 403, "csrf")
        self.assertTrue(c.sessao()["autenticado"])             # nada aconteceu

    def test_cookie_com_usuario_apagado_vira_visitante(self):
        """Sessão 'órfã' (conta removida): volta a ser visitante, sem erro 500."""
        c = self.cliente()
        c.registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        from database.db import get_connection

        with get_connection() as conn:
            conn.execute("DELETE FROM users")
        corpo = c.sessao()
        self.assertFalse(corpo["autenticado"])
        self.assertEqual(c.responder("oi").status_code, 200)

    def test_cookie_forjado_com_user_id_inexistente_ou_de_tipo_errado(self):
        serializador = self.app.session_interface.get_signing_serializer(self.app)
        for conteudo in ({"user_id": 999}, {"user_id": "1"}, {"user_id": [1]}, {"user_id": True},
                         {"user_id": None}, {"user_id": 1.5}):
            with self.subTest(conteudo=conteudo):
                c = self.cliente()
                r = c.http.get("/sessao", headers={"Cookie": f"session={serializador.dumps(conteudo)}"})
                self.assertEqual(r.status_code, 200)
                self.assertFalse(r.get_json()["autenticado"])

    def test_cookie_lixo_ou_assinado_com_outra_chave(self):
        from itsdangerous import URLSafeTimedSerializer

        falso = URLSafeTimedSerializer("outra-chave-qualquer", salt="cookie-session").dumps({"user_id": 1})
        for valor in ("lixo", "a.b.c", "", falso):
            with self.subTest(valor=valor[:12]):
                r = self.cliente().http.get("/sessao", headers={"Cookie": f"session={valor}"})
                self.assertEqual(r.status_code, 200)
                self.assertFalse(r.get_json()["autenticado"])

    def test_login_troca_a_sessao_inteira(self):
        """Contra fixação de sessão: o que existia na sessão anônima não sobrevive ao login."""
        self.cliente().registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        c = self.cliente(ip="192.0.2.50")
        c.sessao()
        antigo_cookie = c.http.get("/sessao").headers.get("Set-Cookie")
        r = c.login("maria@example.com")
        serializador = self.app.session_interface.get_signing_serializer(self.app)
        novo = serializador.loads(cookie_de_sessao(r))
        self.assertEqual(set(novo), {"user_id", "csrf"})        # sem visitor_id da sessão anterior
        self.assertEqual(novo["user_id"], 1)
        self.assertIsNone(antigo_cookie)                        # (a 2ª leitura não reemitiu cookie)


class CookiesTest(XBotTestCase):
    def flags(self, resposta):
        linha = next(l for l in resposta.headers.getlist("Set-Cookie") if l.startswith("session="))
        return linha.lower()

    def test_cookie_httponly_e_samesite(self):
        linha = self.flags(self.cliente().get("/sessao"))
        self.assertIn("httponly", linha)
        self.assertIn("samesite=lax", linha)
        self.assertNotIn("secure", linha)            # requisição HTTP simples: não marca Secure

    def test_cookie_secure_automatico_em_https(self):
        r = self.cliente().http.get("/sessao", base_url="https://localhost")
        self.assertIn("secure", self.flags(r))

    def test_cookie_guarda_so_identificadores_nenhum_horario(self):
        c = self.cliente()
        r = c.get("/sessao")
        serializador = self.app.session_interface.get_signing_serializer(self.app)
        conteudo = serializador.loads(cookie_de_sessao(r))
        self.assertEqual(set(conteudo), {"visitor_id", "csrf"})
        self.assertNotIn("guest_iniciado_em", conteudo)


class CookieSeguroConfiguradoTest(XBotTestCase):
    env_extra = {"XBOT_COOKIE_SECURE": 1, "XBOT_COOKIE_SAMESITE": "Strict"}

    def test_secure_sempre_e_samesite_strict(self):
        r = self.cliente().get("/sessao")
        linha = next(l for l in r.headers.getlist("Set-Cookie") if l.startswith("session=")).lower()
        self.assertIn("secure", linha)
        self.assertIn("samesite=strict", linha)


class VisitanteTest(XBotTestCase):
    """A regra de sempre — 10 minutos — agora contada e imposta pelo servidor."""

    def test_contagem_regressiva_vem_do_relogio_do_servidor(self):
        c = self.cliente()
        self.assertEqual(c.sessao()["tempo_restante"], 600)
        self.relogio.avancar(60)
        self.assertEqual(c.sessao()["tempo_restante"], 540)
        self.relogio.avancar(240)
        self.assertEqual(c.sessao()["tempo_restante"], 300)

    def test_mensagens_mostram_o_tempo_e_nao_estendem_o_relogio(self):
        c = self.cliente()
        c.sessao()
        self.relogio.avancar(100)
        corpo = c.responder("oi").get_json()
        self.assertFalse(corpo["autenticado"])
        self.assertEqual(corpo["tempo_restante"], 500)
        self.assertFalse(corpo["bloqueado"])
        self.relogio.avancar(100)
        self.assertEqual(c.responder("oi").get_json()["tempo_restante"], 400)

    def test_bloqueio_exatamente_aos_600_segundos(self):
        c = self.cliente()
        c.sessao()
        self.relogio.avancar(598)
        self.assertEqual(c.responder("oi").status_code, 200)       # 2 s sobrando
        self.relogio.avancar(2)                                     # 600 s no total
        r = c.responder("oi")
        corpo = self.assertJsonErro(r, 403)
        self.assertTrue(corpo["bloqueado"])
        self.assertFalse(corpo["autenticado"])
        self.assertEqual(corpo["tempo_restante"], 0)
        self.assertEqual(corpo["codigo"], "limite_visitante")
        self.assertIn("tempo de teste gratuito acabou", corpo["resposta"])
        estado = c.sessao()
        self.assertTrue(estado["bloqueado"])
        self.assertEqual(estado["tempo_restante"], 0)

    def test_bloqueado_nao_recebe_nenhuma_funcao_do_bot(self):
        c = self.cliente()
        c.sessao()
        self.relogio.avancar(601)
        for r in (c.responder("oi"), c.post("/quiz/arquitetura", {"nome_usuario": "Ana"}),
                  c.get("/exercicio/python_basico")):
            self.assertEqual(r.status_code, 403)
            self.assertTrue(r.get_json()["bloqueado"])

    def test_apagar_o_cookie_nao_devolve_o_tempo(self):
        c1 = self.cliente()
        c1.sessao()
        self.relogio.avancar(300)
        # "apagar cookies" = navegador novo (sem cookie) no mesmo IP + User-Agent
        c2 = self.cliente()
        self.assertEqual(c2.sessao()["tempo_restante"], 300)
        self.relogio.avancar(301)
        self.assertTrue(self.cliente().sessao()["bloqueado"])
        self.assertEqual(self.cliente().responder("oi").status_code, 403)
        # o cookie original continua bloqueado também
        self.assertEqual(c1.responder("oi").status_code, 403)

    def test_apagar_o_cookie_varias_vezes_nao_cria_tempo_nem_enche_a_tabela(self):
        for i in range(30):                                  # 30 "navegadores novos" em sequência
            # cada um herda o relógio da 1ª visita (que segue andando): 600, 590, 580...
            self.assertEqual(self.cliente().sessao()["tempo_restante"], 600 - 10 * i)
            self.relogio.avancar(10)
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM visitantes")[0][0], 1)    # tabela não cresce
        self.assertFalse(self.cliente().sessao()["bloqueado"])                          # 300 s usados de 600
        self.relogio.avancar(300)
        self.assertTrue(self.cliente().sessao()["bloqueado"])

    def test_cookie_adulterado_nao_da_bonus(self):
        c = self.cliente()
        c.sessao()
        self.relogio.avancar(400)
        serializador = self.app.session_interface.get_signing_serializer(self.app)
        # visitor_id inventado, no formato certo (assinatura válida): é tratado como visitante novo
        # da mesma impressão, que herda o relógio já em andamento.
        forjado = serializador.dumps({"visitor_id": "A" * 32, "csrf": "x" * 40})
        outro = self.cliente()
        r = outro.http.get("/sessao", headers={"Cookie": f"session={forjado}"})
        self.assertEqual(r.get_json()["tempo_restante"], 200)
        # visitor_id com formato inválido (injeção etc.): ignorado
        for valor in ("x", "../../etc/passwd" + "a" * 20, "a" * 200, 12345, ["a"], {"a": 1}):
            with self.subTest(valor=str(valor)[:20]):
                forjado = serializador.dumps({"visitor_id": valor})
                r = self.cliente().http.get("/sessao", headers={"Cookie": f"session={forjado}"})
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.get_json()["tempo_restante"], 200)

    def test_outro_navegador_ou_outro_ip_ganha_um_teste_novo(self):
        """Limite conhecido e documentado: o controle prende IP + navegador, não a pessoa."""
        self.cliente().sessao()
        self.relogio.avancar(500)
        self.assertEqual(self.cliente().sessao()["tempo_restante"], 100)
        self.assertEqual(self.cliente(ua="Outro Navegador/9.0").sessao()["tempo_restante"], 600)
        self.assertEqual(self.cliente(ip="203.0.113.77").sessao()["tempo_restante"], 600)

    def test_ipv6_do_mesmo_prefixo_conta_como_o_mesmo_aparelho(self):
        a = self.cliente(ip="2001:db8:abcd:12::1")
        a.sessao()
        self.relogio.avancar(200)
        b = self.cliente(ip="2001:db8:abcd:12:ffff:eeee:dddd:cccc")    # mesmo /64 (extensões de privacidade)
        self.assertEqual(b.sessao()["tempo_restante"], 400)

    def test_x_forwarded_for_falsificado_e_ignorado_sem_proxy_confiavel(self):
        c = self.cliente()
        c.sessao()
        self.relogio.avancar(300)
        novo = self.cliente()
        r = novo.http.get("/sessao", headers={"X-Forwarded-For": "8.8.8.8"})
        self.assertEqual(r.get_json()["tempo_restante"], 300)

    def test_depois_de_24_horas_o_visitante_ganha_novo_teste(self):
        c = self.cliente()
        c.sessao()
        self.relogio.avancar(700)
        self.assertTrue(c.sessao()["bloqueado"])
        self.relogio.avancar(86400 - 700 - 1)                           # 1 s antes de completar 24 h
        self.assertTrue(self.cliente().sessao()["bloqueado"])
        self.relogio.avancar(1)
        self.assertEqual(self.cliente().sessao()["tempo_restante"], 600)

    def test_relogio_do_servidor_andando_para_tras_nao_da_mais_que_600(self):
        c = self.cliente()
        c.sessao()
        self.relogio.avancar(-10_000)
        self.assertEqual(c.sessao()["tempo_restante"], 600)

    def test_banco_guarda_so_hmac_nunca_ip_ou_user_agent(self):
        self.cliente(ip="203.0.113.77", ua="Navegador Secreto/1.0").sessao()
        (linha,) = self.consulta("SELECT visitor_id, impressao FROM visitantes")
        self.assertRegex(linha[1], r"^[0-9a-f]{40}$")
        for valor in linha:
            self.assertNotIn("203.0.113", valor)
            self.assertNotIn("Navegador", valor)

    def test_cadastro_libera_o_visitante_bloqueado(self):
        c = self.cliente()
        c.sessao()
        self.relogio.avancar(601)
        self.assertEqual(c.responder("oi").status_code, 403)
        self.assertEqual(c.registrar("Maria Souza", "maria@example.com", SENHA_BOA).status_code, 200)
        corpo = c.responder("oi").get_json()
        self.assertTrue(corpo["autenticado"])
        self.assertIsNone(corpo["tempo_restante"])
        self.relogio.avancar(7200)                                      # 2 horas depois: segue sem limite
        self.assertEqual(c.responder("oi").status_code, 200)

    def test_login_libera_o_visitante_bloqueado(self):
        self.cliente(ip="192.0.2.1").registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        c = self.cliente()
        c.sessao()
        self.relogio.avancar(601)
        self.assertEqual(c.responder("oi").status_code, 403)
        self.assertEqual(c.login("maria@example.com").status_code, 200)
        self.assertEqual(c.responder("oi").status_code, 200)

    def test_sair_da_conta_nao_devolve_o_teste_gratuito(self):
        """Truque 'logar, deslogar, ganhar 10 minutos': não funciona; o relógio da impressão continua."""
        c = self.cliente()
        c.sessao()
        self.relogio.avancar(700)
        c.registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        c.logout()
        estado = c.sessao()
        self.assertFalse(estado["autenticado"])
        self.assertTrue(estado["bloqueado"])

    def test_visitante_que_nunca_esgotou_continua_de_onde_parou_apos_logout(self):
        c = self.cliente()
        c.sessao()
        self.relogio.avancar(100)
        c.registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        c.logout()
        self.assertEqual(c.sessao()["tempo_restante"], 500)


class TempoConfiguravelTest(XBotTestCase):
    env_extra = {"XBOT_GUEST_SECONDS": 30}

    def test_xbot_guest_seconds(self):
        c = self.cliente()
        self.assertEqual(c.sessao()["tempo_restante"], 30)
        self.relogio.avancar(30)
        self.assertTrue(c.sessao()["bloqueado"])


class VariasJanelasTest(XBotTestCase):
    """XBOT_GUEST_MAX_SESSIONS=2: duas janelas independentes por IP+navegador (demos em sala de aula)."""

    env_extra = {"XBOT_GUEST_MAX_SESSIONS": 2}

    def test_segunda_janela_e_independente_e_a_terceira_herda(self):
        a = self.cliente()
        a.sessao()
        self.relogio.avancar(300)
        b = self.cliente()
        self.assertEqual(b.sessao()["tempo_restante"], 600)            # janela própria
        self.relogio.avancar(100)
        self.assertEqual(a.sessao()["tempo_restante"], 200)
        self.assertEqual(b.sessao()["tempo_restante"], 500)
        c = self.cliente()
        self.assertEqual(c.sessao()["tempo_restante"], 200)            # sem vaga: herda a mais antiga


class PreviaParaVisitanteTest(XBotTestCase):
    def test_visitante_recebe_resposta_truncada_e_usuario_recebe_completa(self):
        visitante = self.cliente()
        previa = visitante.responder(PERGUNTA).get_json()["resposta"]
        usuario = self.cliente(ip="192.0.2.9")
        usuario.registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        completa = usuario.responder(PERGUNTA).get_json()["resposta"]

        self.assertIn("Essa é só uma prévia", previa)
        self.assertNotIn("Essa é só uma prévia", completa)
        self.assertGreater(len(completa), len(previa))
        corpo_previa = previa.split("\n\n🔒")[0]
        self.assertTrue(completa.startswith(corpo_previa[:60]))        # é o começo da mesma resposta

    def test_quiz_e_exercicio_nao_sao_cortados_para_visitante(self):
        c = self.cliente()
        quiz = c.responder("quiz python").get_json()
        self.assertEqual(quiz["fonte_resposta"], "quiz")
        self.assertNotIn("prévia", quiz["resposta"])
        self.assertIn("Quiz de Python", quiz["resposta"])
        exercicio = c.responder("exercício python").get_json()
        self.assertEqual(exercicio["fonte_resposta"], "exercicio")
        self.assertNotIn("prévia", exercicio["resposta"])


if __name__ == "__main__":
    unittest.main()
