"""Rotas informativas e de diagnóstico: o que é público, o que exige login e o que nunca vaza."""

import json
import os
import unittest
from unittest import mock

from .base import SENHA_BOA, XBotTestCase

DIAGNOSTICO = (("GET", "/estatisticas"), ("GET", "/db_status"), ("POST", "/raciocinio_debug"))


def chamar(cliente, metodo, rota):
    if metodo == "GET":
        return cliente.get(rota)
    return cliente.post(rota, {"mensagem": "o que é uma cpu?"})


class DiagnosticoFechadoTest(XBotTestCase):
    """Padrão (qualquer ambiente que não seja development): diagnóstico só para quem está logado."""

    def setUp(self):
        super().setUp()
        self.ana = self.cliente(ip="198.51.100.61")
        self.assertEqual(self.ana.registrar("Ana Lima", "ana@example.com", SENHA_BOA).status_code, 200)

    def test_visitante_recebe_401_e_nenhum_dado(self):
        visitante = self.cliente(ip="198.51.100.62", ua="Outro-UA")
        for metodo, rota in DIAGNOSTICO:
            with self.subTest(rota=rota):
                r = chamar(visitante, metodo, rota)
                self.assertJsonErro(r, 401, "nao_autenticado")
                corpo = r.get_data(as_text=True)
                for informacao in ("knowledge", "tabelas", "uptime", "candidatos"):
                    self.assertNotIn(informacao, corpo)

    def test_quem_nunca_abriu_sessao_tambem_recebe_401(self):
        anonimo = self.cliente(ip="198.51.100.63", ua="Anonimo")
        self.assertJsonErro(anonimo.get("/db_status"), 401, "nao_autenticado")
        self.assertJsonErro(anonimo.get("/estatisticas"), 401, "nao_autenticado")

    def test_post_de_diagnostico_sem_csrf_e_403(self):
        self.assertJsonErro(self.ana.post("/raciocinio_debug", {"mensagem": "cpu"}, token=None), 403, "csrf")

    def test_usuario_logado_acessa(self):
        for metodo, rota in DIAGNOSTICO:
            with self.subTest(rota=rota):
                r = chamar(self.ana, metodo, rota)
                self.assertEqual(r.status_code, 200, r.get_data(as_text=True)[:200])

    def test_depois_de_sair_volta_a_ser_negado(self):
        self.ana.logout()
        for metodo, rota in DIAGNOSTICO:
            with self.subTest(rota=rota):
                self.assertJsonErro(chamar(self.ana, metodo, rota), 401, "nao_autenticado")

    # -- /db_status -----------------------------------------------------------------------------
    def test_db_status_mostra_so_o_nome_do_arquivo(self):
        resposta = self.ana.get("/db_status")
        corpo = resposta.get_json()
        self.assertEqual(corpo["banco"], "t.db")                       # só o nome, sem a pasta
        self.assertNotIn(self.tmp, resposta.get_data(as_text=True))
        self.assertEqual(corpo["status"], "ok")
        reais = [linha[0] for linha in self.consulta("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        self.assertEqual(corpo["tabelas"], reais)
        for tabela in ("knowledge", "users", "visitantes", "auth_tentativas"):
            self.assertIn(tabela, corpo["tabelas"])
        self.assertEqual(corpo["knowledge_registros"], self.consulta("SELECT COUNT(*) FROM knowledge")[0][0])

    def test_db_status_nao_vaza_o_texto_da_excecao(self):
        with mock.patch("app.contar_registros", side_effect=RuntimeError("segredo-interno /var/lib/xbot.db")):
            r = self.ana.get("/db_status")
        self.assertEqual(r.status_code, 500)
        corpo = r.get_data(as_text=True)
        self.assertIn("Falha ao consultar o banco de dados", corpo)
        self.assertNotIn("segredo-interno", corpo)
        self.assertNotIn("/var/lib", corpo)

    # -- /estatisticas --------------------------------------------------------------------------
    def test_estatisticas_contam_o_que_aconteceu_sem_dados_pessoais(self):
        self.ana.responder("o que é uma CPU?", nome="Ana")
        self.ana.responder("o que é memória RAM?", nome="Ana")
        r = self.ana.get("/estatisticas")
        corpo = r.get_json()
        self.assertEqual(set(corpo), {"uptime", "usuarios", "mensagens", "interacoes", "bot", "inicio_servico"})
        self.assertEqual(corpo["mensagens"]["total"], 2)
        self.assertEqual(sum(corpo["mensagens"]["por_categoria"].values()), 2)
        self.assertEqual(corpo["usuarios"], {"total_unicos": 1, "com_historico": 1})
        texto = r.get_data(as_text=True)
        self.assertNotIn("ana@example.com", texto)
        self.assertNotIn("o que é uma CPU", texto)                    # nunca o conteúdo das conversas

    # -- /raciocinio_debug --------------------------------------------------------------------
    def test_raciocinio_debug_devolve_a_analise(self):
        corpo = self.ana.post("/raciocinio_debug", {"mensagem": "o que é uma cpu?"}).get_json()
        for chave in ("mensagem", "tipo_pergunta", "categoria_detectada", "termos_extraidos", "nivel_confianca",
                      "margem_lideranca", "vencedor", "relacionados", "sugestoes", "top5_candidatos", "explicacao"):
            self.assertIn(chave, corpo)
        self.assertLessEqual(len(corpo["top5_candidatos"]), 5)

    def test_raciocinio_debug_valida_o_corpo(self):
        casos = [
            ({}, 400, "campo_obrigatorio"),
            ({"mensagem": ""}, 400, "campo_obrigatorio"),
            ({"mensagem": "   "}, 400, "campo_obrigatorio"),
            ({"mensagem": 123}, 400, "tipo_invalido"),
            ({"mensagem": ["cpu"]}, 400, "tipo_invalido"),
            ({"mensagem": {"a": 1}}, 400, "tipo_invalido"),
            ({"mensagem": True}, 400, "tipo_invalido"),
            ({"mensagem": "a" * 501}, 400, "campo_muito_longo"),
            ({"mensagem": "a\x00b"}, 400, "caractere_invalido"),
            (["cpu"], 400, "json_invalido"),
        ]
        for corpo, status, codigo in casos:
            with self.subTest(corpo=str(corpo)[:30]):
                self.assertJsonErro(self.ana.post("/raciocinio_debug", corpo), status, codigo)
        self.assertJsonErro(self.ana.post("/raciocinio_debug", data="cpu"), 415, "tipo_nao_suportado")

    def test_raciocinio_debug_com_entradas_hostis_nunca_da_500(self):
        antes = self.consulta("SELECT COUNT(*) FROM knowledge")[0][0]
        for mensagem in ("'; DROP TABLE knowledge; --", "%" * 50, "😀" * 100, "\n\n\n x", "_" * 400,
                         "\\", "\"'`", "<script>alert(1)</script>", "NULL", "1 OR 1=1"):
            with self.subTest(mensagem=mensagem[:20]):
                r = self.ana.post("/raciocinio_debug", {"mensagem": mensagem})
                self.assertEqual(r.status_code, 200, r.get_data(as_text=True)[:200])
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM knowledge")[0][0], antes)


class DiagnosticoAbertoPorConfiguracaoTest(XBotTestCase):
    """Quem administra o servidor pode abrir de propósito: XBOT_DIAGNOSTICS=1."""

    env_extra = {"XBOT_DIAGNOSTICS": "1"}

    def test_visitante_acessa(self):
        v = self.cliente()
        for metodo, rota in DIAGNOSTICO:
            with self.subTest(rota=rota):
                self.assertEqual(chamar(v, metodo, rota).status_code, 200)

    def test_o_post_continua_exigindo_csrf(self):
        v = self.cliente()
        self.assertJsonErro(v.post("/raciocinio_debug", {"mensagem": "cpu"}, token=None), 403, "csrf")


class DiagnosticoEmDesenvolvimentoTest(XBotTestCase):
    env_extra = {"XBOT_ENV": "development", "XBOT_DEBUG": "0"}

    def test_aberto_por_padrao(self):
        v = self.cliente()
        for metodo, rota in DIAGNOSTICO:
            with self.subTest(rota=rota):
                self.assertEqual(chamar(v, metodo, rota).status_code, 200)


class DiagnosticoEmDesenvolvimentoFechadoTest(XBotTestCase):
    env_extra = {"XBOT_ENV": "development", "XBOT_DEBUG": "0", "XBOT_DIAGNOSTICS": "0"}

    def test_da_para_fechar_mesmo_em_desenvolvimento(self):
        self.assertJsonErro(self.cliente().get("/db_status"), 401, "nao_autenticado")


class RotasPublicasTest(XBotTestCase):
    def test_status_e_publico(self):
        r = self.cliente().get("/status")
        self.assertEqual(r.status_code, 200)
        corpo = r.get_json()
        self.assertEqual(corpo["status"], "online")
        self.assertEqual(corpo["desenvolvedor"], "XByte Games Studios")
        for chave in ("versao", "usuarios_ativos", "usuarios_unicos", "total_mensagens", "quizzes_realizados",
                      "exercicios_solicitados", "uptime_segundos", "uptime_formatado", "estatisticas_bot"):
            self.assertIn(chave, corpo)

    def test_status_nao_revela_caminhos_nem_chaves(self):
        texto = self.cliente().get("/status").get_data(as_text=True)
        self.assertNotIn(self.tmp, texto)
        self.assertNotIn(self.cfg.secret_key, texto)
        self.assertNotIn("t.db", texto)

    def test_status_acompanha_o_uso(self):
        ana = self.cliente()
        ana.responder("oi", nome="Ana")
        ana.responder("oi", nome="Ana")
        corpo = self.cliente(ip="198.51.100.99", ua="Outro").get("/status").get_json()
        self.assertEqual(corpo["total_mensagens"], 2)
        self.assertEqual(corpo["usuarios_unicos"], 1)
        self.assertEqual(corpo["usuarios_ativos"], 1)

    def test_conhecimento_lista_os_topicos(self):
        corpo = self.cliente().get("/conhecimento").get_json()
        self.assertEqual(corpo["total_topicos"], len(corpo["topicos_disponiveis"]))
        self.assertEqual(corpo["topicos_disponiveis"], sorted(corpo["topicos_disponiveis"]))
        self.assertGreaterEqual(corpo["total_topicos"], 20)
        self.assertEqual(corpo["quiz_categorias"], ["arquitetura", "python", "web"])
        self.assertEqual(corpo["exercicio_categorias"], ["python_basico"])
        self.assertIn("quiz", corpo["categorias_resposta"])

    def test_rotas_informativas_nao_dependem_do_relogio_do_visitante(self):
        v = self.cliente()
        v.sessao()
        self.relogio.avancar(601)
        self.assertTrue(v.sessao()["bloqueado"])
        for rota in ("/", "/status", "/conhecimento", "/sessao"):
            with self.subTest(rota=rota):
                self.assertEqual(v.get(rota).status_code, 200)

    def test_erros_sao_json(self):
        c = self.cliente()
        r = c.get("/nao-existe")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json()["erro"], "Endpoint não encontrado")
        self.assertJsonErro(c.get("/responder"), 405)
        self.assertJsonErro(c.post("/status", {}), 405)

    def test_cabecalhos_de_seguranca_em_todas_as_respostas(self):
        c = self.cliente()
        for rota in ("/", "/status", "/nao-existe", "/sessao"):
            with self.subTest(rota=rota):
                cab = c.get(rota).headers
                self.assertEqual(cab.get("X-Content-Type-Options"), "nosniff")
                self.assertIn("default-src 'self'", cab.get("Content-Security-Policy", ""))
                self.assertIn(cab.get("X-Frame-Options"), ("DENY", "SAMEORIGIN"))

    def test_respostas_json_nao_contem_a_chave_secreta(self):
        c = self.cliente()
        c.registrar("Ana Lima", "ana@example.com", SENHA_BOA)
        c.responder("oi", nome="Ana")
        for rota in ("/sessao", "/status", "/conhecimento", "/historico/Ana", "/db_status", "/estatisticas"):
            with self.subTest(rota=rota):
                texto = c.get(rota).get_data(as_text=True)
                self.assertNotIn(self.cfg.secret_key, texto)
                self.assertNotIn("senha_hash", texto)
                self.assertNotIn("pbkdf2", texto)
                self.assertNotIn("scrypt", texto)
        json.loads(c.get("/status").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
