"""Entradas malformadas: sempre erro controlado (400/413/415) em JSON — nunca exceção 500."""

import json
import unittest
from unittest import mock

from .base import SENHA_BOA, XBotTestCase

JSON = {"Content-Type": "application/json"}


class CorpoJsonTest(XBotTestCase):
    """Corpos que não são o JSON esperado, em TODAS as rotas que leem JSON."""

    ROTAS = [
        ("/responder", {"mensagem": "oi"}),
        ("/login", {"email": "a@example.com", "senha": "qualquer-coisa-1"}),
        ("/registrar", {"nome": "Maria Souza", "email": "maria@example.com", "senha": SENHA_BOA}),
        ("/quiz/arquitetura", {"nome_usuario": "Ana"}),
        ("/raciocinio_debug", {"mensagem": "cpu"}),
    ]

    def setUp(self):
        super().setUp()
        self.c = self.cliente()
        self.c.sessao()
        # logado, para a rota de diagnóstico (fechada fora de development) chegar à validação
        self.dono = self.cliente(ip="192.0.2.99")
        self.dono.registrar("Maria Souza", "dono@example.com", SENHA_BOA)

    def cliente_da(self, url):
        return self.dono if url == "/raciocinio_debug" else self.c

    def enviar(self, url, **kw):
        c = self.cliente_da(url)
        return c.post(url, **kw)

    def test_content_type_que_nao_e_json_da_415(self):
        for url, _ in self.ROTAS:
            for tipo in ("text/plain", "application/x-www-form-urlencoded", "multipart/form-data"):
                with self.subTest(url=url, tipo=tipo):
                    r = self.enviar(url, data='{"mensagem": "oi"}', headers={"Content-Type": tipo})
                    self.assertJsonErro(r, 415, "tipo_nao_suportado")

    def test_sem_corpo_e_sem_content_type(self):
        for url, _ in self.ROTAS:
            with self.subTest(url=url):
                self.assertJsonErro(self.enviar(url), 415, "tipo_nao_suportado")

    def test_json_quebrado_ou_vazio_da_400(self):
        corpos = ["{oops", "", "   ", "{'aspas': 'simples'}", '{"a": }', "nul", "{", '{"a":1}}', "﻿{}x"]
        for url, _ in self.ROTAS:
            for corpo in corpos:
                with self.subTest(url=url, corpo=corpo[:15]):
                    r = self.enviar(url, data=corpo, headers=JSON)
                    self.assertJsonErro(r, 400, "json_invalido")

    def test_utf8_invalido_da_400(self):
        for url, _ in self.ROTAS:
            with self.subTest(url=url):
                r = self.enviar(url, data=b'{"mensagem": "\xff\xfe\xfa"}', headers=JSON)
                self.assertJsonErro(r, 400, "json_invalido")

    def test_corpo_json_que_nao_e_objeto_da_400(self):
        for url, _ in self.ROTAS:
            for corpo in ("[]", "[1, 2]", '"texto"', "123", "true", "null", '[{"mensagem": "oi"}]'):
                with self.subTest(url=url, corpo=corpo):
                    r = self.enviar(url, data=corpo, headers=JSON)
                    self.assertJsonErro(r, 400, "json_invalido")

    def test_json_absurdamente_aninhado_nao_estoura_a_pilha(self):
        # Abaixo do limite de 16 KB: aqui se testa o aninhamento, não o tamanho.
        for url, _ in self.ROTAS:
            with self.subTest(url=url, forma="lista"):
                r = self.enviar(url, data="[" * 5000 + "]" * 5000, headers=JSON)
                self.assertJsonErro(r, 400, "json_invalido")           # não é um objeto (ou estourou a pilha)
            with self.subTest(url=url, forma="objeto"):
                r = self.enviar(url, data='{"a":' * 2500 + "1" + "}" * 2500, headers=JSON)
                # Python novo aguenta 2500 níveis (objeto válido, sem os campos pedidos); Python antigo
                # estoura a pilha e o servidor devolve 400. O que NUNCA pode acontecer é um erro 5xx.
                self.assertLess(r.status_code, 500, r.get_data(as_text=True)[:200])
                self.assertIsInstance(r.get_json(), dict)

    def test_corpo_grande_demais_da_413(self):
        grande = json.dumps({"mensagem": "a" * 20000})              # limite padrão: 16384 bytes
        for url, _ in self.ROTAS:
            with self.subTest(url=url):
                r = self.enviar(url, data=grande, headers=JSON)
                self.assertJsonErro(r, 413)

    def test_toda_resposta_de_erro_e_json_e_sem_vazar_detalhes(self):
        textos = []
        for url, _ in self.ROTAS:
            for corpo in ("{oops", "[1]", "null"):
                r = self.enviar(url, data=corpo, headers=JSON)
                textos.append(r.get_data(as_text=True))
                self.assertEqual(r.mimetype, "application/json")
        for texto in textos:
            for vazamento in ("Traceback", "File \"", "werkzeug", "JSONDecodeError", "Expecting"):
                self.assertNotIn(vazamento, texto)


class CamposTest(XBotTestCase):
    """Campos com tipo errado, nulos, gigantes ou com caracteres proibidos."""

    def setUp(self):
        super().setUp()
        self.c = self.cliente()
        self.c.sessao()

    def test_responder_mensagem_com_tipo_errado(self):
        for valor in (123, 1.5, True, [], ["oi"], {"a": 1}):
            with self.subTest(valor=valor):
                r = self.c.post("/responder", {"mensagem": valor})
                self.assertJsonErro(r, 400, "tipo_invalido")

    def test_responder_nome_usuario_com_tipo_errado(self):
        for valor in (123, [], {"a": 1}, False):
            with self.subTest(valor=valor):
                r = self.c.post("/responder", {"mensagem": "oi", "nome_usuario": valor})
                self.assertJsonErro(r, 400, "tipo_invalido")

    def test_responder_campos_nulos_ou_ausentes_tem_resposta_amigavel(self):
        for corpo in ({"mensagem": None}, {"mensagem": ""}, {"mensagem": "   "}, {"nome_usuario": "Ana"}):
            with self.subTest(corpo=corpo):
                r = self.c.post("/responder", corpo)
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.get_json()["resposta"], "Por favor, digite uma mensagem!")

    def test_responder_objeto_vazio_e_recusado(self):
        self.assertJsonErro(self.c.post("/responder", {}), 400, "json_invalido")

    def test_responder_mensagem_longa_mantem_o_aviso_amigavel_de_antes(self):
        r = self.c.post("/responder", {"mensagem": "a" * 501})
        self.assertEqual(r.status_code, 200)
        self.assertIn("Máximo de 500", r.get_json()["resposta"])
        self.assertEqual(self.c.post("/responder", {"mensagem": "a" * 500}).status_code, 200)

    def test_caractere_nul_e_recusado(self):
        for corpo in ({"mensagem": "oi\u0000tchau"}, {"mensagem": "oi", "nome_usuario": "A\u0000na"}):
            with self.subTest(corpo=corpo):
                self.assertJsonErro(self.c.post("/responder", corpo), 400, "caractere_invalido")
        self.assertJsonErro(self.c.post("/login", {"email": "a@example.com\u0000", "senha": "x1"}), 400, "caractere_invalido")
        self.assertJsonErro(self.c.post("/registrar", {"nome": "A\u0000b", "email": "a@example.com", "senha": SENHA_BOA}),
                            400, "caractere_invalido")

    def test_surrogate_solto_e_recusado_em_todos_os_campos_de_texto(self):
        """O JSON aceita "\\ud800" (metade de um par UTF-16), mas isso não é texto válido: nunca pode virar 500."""
        casos = [
            ("/responder", {"mensagem": "oi \ud800 cpu"}),
            ("/responder", {"mensagem": "oi", "nome_usuario": "\ud800Ana"}),
            ("/login", {"email": "\ud800@example.com", "senha": "qualquer-coisa-1"}),
            ("/login", {"email": "a@example.com", "senha": "abc\udfff"}),
            ("/registrar", {"nome": "\ud800Maria", "email": "maria@example.com", "senha": SENHA_BOA}),
            ("/registrar", {"nome": "Maria Souza", "email": "m\udc00@example.com", "senha": SENHA_BOA}),
            ("/registrar", {"nome": "Maria Souza", "email": "maria@example.com", "senha": SENHA_BOA + "\ud800"}),
            ("/quiz/arquitetura", {"nome_usuario": "\ud800"}),
        ]
        for url, corpo in casos:
            # Corpo montado à mão, com o escape literal "\ud800" no JSON (independe do serializador do cliente de teste).
            bruto = json.dumps(corpo, ensure_ascii=True).encode("ascii")
            self.assertIn(b"\\ud", bruto.lower())
            with self.subTest(url=url, campos=sorted(corpo)):
                self.assertJsonErro(self.c.post(url, data=bruto, headers=JSON), 400, "caractere_invalido")
        # o mesmo na rota de diagnóstico (que exige login fora de development)
        dono = self.cliente(ip="192.0.2.77")
        dono.registrar("Maria Souza", "dono2@example.com", SENHA_BOA)
        bruto = json.dumps({"mensagem": "\ud800"}, ensure_ascii=True).encode("ascii")
        self.assertJsonErro(dono.post("/raciocinio_debug", data=bruto, headers=JSON), 400, "caractere_invalido")

    def test_surrogate_solto_no_login_nao_conta_como_tentativa_nem_vira_500(self):
        """Era o caso que estourava: o e-mail entrava no HMAC do limitador de login antes de qualquer validação."""
        bruto = json.dumps({"email": "\ud800@example.com", "senha": "qualquer-coisa-1"}, ensure_ascii=True).encode("ascii")
        for _ in range(8):                                  # mais que o limite de 5 por e-mail: segue 400, nunca 429/500
            self.assertJsonErro(self.c.post("/login", data=bruto, headers=JSON), 400, "caractere_invalido")
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM auth_tentativas")[0][0], 0)

    def test_acentos_emoji_e_pares_validos_continuam_aceitos(self):
        """A checagem de UTF-8 não pode barrar texto legítimo: acentos, emoji (par de surrogates válido em JSON)."""
        for texto in ("Olá, não sei o que é CPU", "ação coração 日本語", "oi 😀 cpu"):
            bruto = json.dumps({"mensagem": texto}, ensure_ascii=True).encode("ascii")        # emoji vira 😀
            with self.subTest(texto=texto):
                self.assertEqual(self.c.post("/responder", data=bruto, headers=JSON).status_code, 200)

    def test_nome_de_exibicao_e_normalizado(self):
        r = self.c.post("/responder", {"mensagem": "oi", "nome_usuario": "  Ana\t\n  Maria\x07 " + "z" * 100})
        self.assertEqual(r.status_code, 200)
        # o nome só serve para tratar a pessoa pelo nome: sem controle, espaços normalizados, até 40 caracteres
        self.assertNotIn("\x07", r.get_json()["resposta"])
        self.assertNotIn("z" * 41, r.get_json()["resposta"])

    def test_nome_so_com_espacos_vira_o_padrao(self):
        r = self.c.post("/responder", {"mensagem": "quiz", "nome_usuario": "   "})
        self.assertIn("usuário", r.get_json()["resposta"])

    def test_unicode_e_emoji_funcionam(self):
        r = self.c.post("/responder", {"mensagem": "olá 🤖 ção ñ 日本語", "nome_usuario": "Zoë 😀"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["resposta"])

    def test_login_e_cadastro_com_tipos_errados(self):
        casos = [
            ("/login", {"email": 1, "senha": "x"}), ("/login", {"email": "a@example.com", "senha": 123456}),
            ("/login", {"email": ["a@example.com"], "senha": "x"}), ("/login", {"email": "a@example.com", "senha": {"a": 1}}),
            ("/login", {"email": None, "senha": "x"}), ("/login", {"email": "a@example.com", "senha": None}),
            ("/registrar", {"nome": 5, "email": "a@example.com", "senha": SENHA_BOA}),
            ("/registrar", {"nome": "Maria", "email": 5, "senha": SENHA_BOA}),
            ("/registrar", {"nome": "Maria", "email": "a@example.com", "senha": 5}),
            ("/registrar", {"nome": "Maria", "email": "a@example.com", "senha": [SENHA_BOA]}),
            ("/registrar", {"nome": None, "email": "a@example.com", "senha": SENHA_BOA}),
            ("/registrar", {"nome": "Maria", "email": "a@example.com"}),
            ("/registrar", {}),
        ]
        for url, corpo in casos:
            with self.subTest(url=url, corpo=str(corpo)[:50]):
                r = self.c.post(url, corpo)
                self.assertEqual(r.status_code, 400, r.get_data(as_text=True))
                self.assertIn(r.get_json()["codigo"], ("tipo_invalido", "campo_obrigatorio", "json_invalido"))
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM users")[0][0], 0)

    def test_campos_gigantes_em_login_e_cadastro(self):
        casos = [("/login", {"email": "a" * 400 + "@example.com", "senha": "x"}),
                 ("/login", {"email": "a@example.com", "senha": "x" * 300}),
                 ("/registrar", {"nome": "n" * 300, "email": "a@example.com", "senha": SENHA_BOA}),
                 ("/registrar", {"nome": "Maria", "email": "a" * 400 + "@example.com", "senha": SENHA_BOA}),
                 ("/registrar", {"nome": "Maria", "email": "a@example.com", "senha": "S1-" + "x" * 300})]
        for url, corpo in casos:
            with self.subTest(url=url, corpo=str(corpo)[:40]):
                self.assertEqual(self.c.post(url, corpo).status_code, 400)

    def test_campos_extras_sao_ignorados(self):
        r = self.c.post("/responder", {"mensagem": "oi", "admin": True, "dono": "u:1", "bloqueado": False,
                                       "autenticado": True, "tempo_restante": 99999})
        self.assertEqual(r.status_code, 200)
        corpo = r.get_json()
        self.assertFalse(corpo["autenticado"])                          # o cliente não decide quem ele é
        self.assertLessEqual(corpo["tempo_restante"], 600)

    def test_injecao_sql_nos_campos_nao_faz_nada(self):
        r = self.c.post("/login", {"email": "' OR '1'='1' --", "senha": "' OR '1'='1"})
        self.assertEqual(r.status_code, 401)
        r = self.c.post("/registrar", {"nome": "Robert'); DROP TABLE users;--", "email": "bobby@example.com",
                                       "senha": "Frase-Segura_Zeta#55"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM users")[0][0], 1)
        self.assertEqual(self.consulta("SELECT nome FROM users")[0][0], "Robert'); DROP TABLE users;--")
        self.assertEqual(self.c.post("/responder", {"mensagem": "'; DROP TABLE knowledge; --"}).status_code, 200)
        self.assertGreater(self.consulta("SELECT COUNT(*) FROM knowledge")[0][0], 40)


class RotasEUrlsTest(XBotTestCase):
    def test_quiz_e_exercicio_com_categorias_estranhas(self):
        c = self.cliente()
        c.sessao()
        for categoria in ("x" * 500, "%E2%9C%93", "a%20b", "..", "%00", "<b>"):
            with self.subTest(categoria=categoria[:20]):
                r = c.post(f"/quiz/{categoria}", {"nome_usuario": "Ana"})
                self.assertIn(r.status_code, (200, 404), r.get_data(as_text=True)[:200])
                self.assertIsInstance(r.get_json(), dict)
                r = c.get(f"/exercicio/{categoria}?usuario=Ana")
                self.assertIn(r.status_code, (200, 404))
                if r.status_code == 200:
                    self.assertLess(len(r.get_json()["resposta"]), 600)         # categoria ecoada é cortada

    def test_quiz_pelo_endpoint_sem_corpo_json_da_415(self):
        c = self.cliente()
        c.sessao()
        self.assertJsonErro(c.post("/quiz/arquitetura"), 415)

    def test_parametro_usuario_do_exercicio_e_limpo(self):
        c = self.cliente()
        r = c.get("/exercicio/python_basico?usuario=" + "A" * 500)
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("A" * 41, r.get_json()["resposta"])

    def test_rota_inexistente_e_metodo_errado_respondem_json(self):
        c = self.cliente()
        r = c.get("/nao-existe")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json()["erro"], "Endpoint não encontrado")
        r = c.http.get("/responder")
        self.assertJsonErro(r, 405)
        self.assertIn("POST", r.headers.get("Allow", ""))
        # PUT/PATCH/DELETE em rota que não os aceita: sem token o CSRF recusa antes (403); com token, 405
        self.assertJsonErro(c.http.put("/responder", json={}), 403, "csrf")
        c.sessao()
        self.assertJsonErro(c.http.put("/responder", json={}, headers={"X-CSRF-Token": c.token}), 405)

    def test_erro_interno_nao_vaza_a_causa(self):
        """Falha inesperada no bot: 500 controlado, mensagem genérica; o detalhe fica só no log."""
        c = self.cliente()
        c.sessao()
        estado = self.app.extensions["xbot"]
        with mock.patch.object(estado.bot, "gerar_resposta", side_effect=RuntimeError("segredo-interno-123")):
            with self.assertLogs("app", level="ERROR") as logs:
                r = c.responder("oi")
        self.assertEqual(r.status_code, 500)
        corpo = r.get_json()
        self.assertEqual(corpo["erro"], "Erro interno do servidor")
        self.assertIn("ocorreu um erro interno", corpo["resposta"])
        self.assertNotIn("segredo-interno-123", r.get_data(as_text=True))
        self.assertTrue(any("segredo-interno-123" in linha for linha in logs.output))   # …mas está no log

    def test_erro_inesperado_em_outras_rotas_tambem_e_generico(self):
        c = self.cliente()
        with mock.patch("app.listar_tabelas", side_effect=RuntimeError("detalhe-do-banco-xyz")):
            self.dono = self.cliente(ip="192.0.2.77")
            self.dono.registrar("Maria Souza", "maria@example.com", SENHA_BOA)
            with self.assertLogs("app", level="ERROR"):
                r = self.dono.get("/db_status")
        self.assertEqual(r.status_code, 500)
        self.assertNotIn("detalhe-do-banco-xyz", r.get_data(as_text=True))
        # rota qualquer que estoure fora do try/except: o handler global também não vaza
        with mock.patch.object(self.app.extensions["xbot"].bot, "get_available_topics",
                               side_effect=RuntimeError("vazamento-global-abc")):
            with self.assertLogs(self.app.logger.name, level="ERROR"):
                r = c.get("/conhecimento")
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.get_json()["erro"], "Erro interno do servidor")
        self.assertNotIn("vazamento-global-abc", r.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
