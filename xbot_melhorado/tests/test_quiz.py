"""Quiz e exercícios (vieram do antigo app_improved.py): fluxo pelo chat, endpoints e isolamento por dono."""

import unittest

import knowledge_base_extended as base_extra

from .base import SENHA_BOA, XBotTestCase

QUIZ = base_extra.QUIZ_QUESTIONS
TITULOS_EXERCICIOS = {e["titulo"] for e in base_extra.EXERCICIOS_PRATICOS["python_basico"]}


def texto(resposta) -> str:
    return resposta.get_json()["resposta"]


def certa(categoria: str, indice: int) -> str:
    """O número (1-based) da alternativa correta da questão `indice` (0-based) — lido dos dados, não decorado."""
    return str(QUIZ[categoria][indice]["resposta_correta"] + 1)


def errada(categoria: str, indice: int) -> str:
    return "1" if QUIZ[categoria][indice]["resposta_correta"] != 0 else "2"


class QuizPeloChatTest(XBotTestCase):
    def setUp(self):
        super().setUp()
        self.v = self.cliente()

    def test_os_dados_do_quiz_estao_la(self):
        self.assertEqual(set(QUIZ), {"arquitetura", "python", "web"})
        self.assertEqual(len(QUIZ["arquitetura"]), 3)

    def test_quiz_do_inicio_ao_fim_com_nota_maxima(self):
        r = self.v.responder("quiz arquitetura", nome="Ana")
        self.assertEqual(r.status_code, 200)
        corpo = r.get_json()
        self.assertEqual(corpo["fonte_resposta"], "quiz")
        self.assertIn("Quiz de Arquitetura iniciado, Ana!", corpo["resposta"])
        self.assertIn("Questão 1/3", corpo["resposta"])
        self.assertIn(QUIZ["arquitetura"][0]["pergunta"], corpo["resposta"])

        for indice, proxima in ((0, "Questão 2/3"), (1, "Questão 3/3")):
            corpo = self.v.responder(certa("arquitetura", indice), nome="Ana").get_json()
            self.assertEqual(corpo["fonte_resposta"], "quiz")
            self.assertIn("✅ Correto, Ana!", corpo["resposta"])
            self.assertIn(proxima, corpo["resposta"])

        final = self.v.responder(certa("arquitetura", 2), nome="Ana").get_json()["resposta"]
        self.assertIn("Quiz finalizado, Ana!", final)
        self.assertIn("Pontuação: 3/3 (100.0%)", final)
        self.assertIn("🏆", final)
        self.assertNotIn("prévia", final)            # quiz de visitante não é truncado

    def test_nota_zero_e_nota_media(self):
        self.v.responder("quiz arquitetura")
        self.v.responder(errada("arquitetura", 0))
        self.v.responder(errada("arquitetura", 1))
        resposta = texto(self.v.responder(errada("arquitetura", 2)))
        self.assertIn("Pontuação: 0/3 (0.0%)", resposta)
        self.assertIn("📚", resposta)
        self.assertIn("Continue estudando!", resposta)

        outro = self.cliente(ip="198.51.100.40", ua="Outro-Navegador/1.0")
        outro.responder("quiz arquitetura")
        outro.responder(certa("arquitetura", 0))
        outro.responder(certa("arquitetura", 1))
        resposta = texto(outro.responder(errada("arquitetura", 2)))
        self.assertIn("Pontuação: 2/3 (66.7%)", resposta)
        self.assertIn("👏", resposta)

    def test_resposta_errada_mostra_a_correta(self):
        self.v.responder("quiz python")
        resposta = texto(self.v.responder(errada("python", 0)))
        correta = QUIZ["python"][0]["opcoes"][QUIZ["python"][0]["resposta_correta"]]
        self.assertIn("❌ Incorreto", resposta)
        self.assertIn(correta, resposta)
        self.assertIn("Questão 2/2", resposta)

    def test_resposta_invalida_nao_avanca_a_questao(self):
        self.v.responder("quiz python")
        for entrada in ("9", "0", "99999999999999999999"):
            with self.subTest(entrada=entrada):
                resposta = texto(self.v.responder(entrada))
                self.assertIn("Resposta inválida", resposta)
        resposta = texto(self.v.responder(certa("python", 0)))        # continua na questão 1
        self.assertIn("✅ Correto", resposta)
        self.assertIn("Questão 2/2", resposta)

    def test_digitos_estranhos_durante_o_quiz_nunca_dao_500(self):
        # "²" e "①" passam em str.isdigit() mas não em int(): já foi uma exceção 500 em potencial
        for entrada in ("²", "①", "٣", "１", "9" * 400, "9" * 501, "0", "００"):
            with self.subTest(entrada=entrada[:12]):
                self.v.responder("quiz web")
                r = self.v.responder(entrada)
                self.assertEqual(r.status_code, 200, r.get_data(as_text=True)[:200])
                self.assertIsInstance(r.get_json()["resposta"], str)

    def test_digito_sem_quiz_ativo_segue_o_fluxo_normal(self):
        r = self.v.responder("1")
        self.assertEqual(r.status_code, 200)
        self.assertNotEqual(r.get_json()["fonte_resposta"], "quiz")

    def test_quiz_terminado_nao_aceita_mais_respostas(self):
        self.v.responder("quiz python")
        self.v.responder(certa("python", 0))
        self.assertIn("Quiz finalizado", texto(self.v.responder(certa("python", 1))))
        r = self.v.responder("1")
        self.assertNotEqual(r.get_json()["fonte_resposta"], "quiz")

    def test_pedir_outro_quiz_no_meio_recomeca(self):
        self.v.responder("quiz arquitetura")
        self.v.responder(certa("arquitetura", 0))
        self.assertIn("Quiz de Python iniciado", texto(self.v.responder("quiz python")))
        resposta = texto(self.v.responder(certa("python", 0)))
        self.assertIn("Questão 2/2", resposta)                          # é a questão 1 do quiz de Python

    def test_temas_e_listagem(self):
        self.assertIn("Quiz de Python iniciado", texto(self.v.responder("quiz python")))
        self.assertIn("Quiz de Web iniciado", texto(self.v.responder("quiz web")))
        self.assertIn("Quiz de Web iniciado", texto(self.v.responder("quiz html")))
        self.assertIn("Quiz de Arquitetura iniciado", texto(self.v.responder("quiz hardware")))
        listagem = texto(self.v.responder("quiz"))
        self.assertIn("Quizzes disponíveis", listagem)
        self.assertIn('"quiz python"', listagem)

    def test_quiz_bloqueado_depois_do_tempo_do_visitante(self):
        self.v.responder("quiz python")
        self.relogio.avancar(601)
        r = self.v.responder(certa("python", 0))
        self.assertEqual(r.status_code, 403)
        self.assertTrue(r.get_json()["bloqueado"])


class QuizIsoladoPorDonoTest(XBotTestCase):
    """O quiz é de quem está logado/da janela do visitante — o nome digitado NÃO decide de quem é."""

    def estado(self):
        return self.app.extensions["xbot"].bot

    def test_visitantes_com_o_mesmo_nome_nao_misturam_quizzes(self):
        a = self.cliente(ip="198.51.100.21", ua="Navegador-A")
        b = self.cliente(ip="198.51.100.22", ua="Navegador-B")
        a.responder("quiz arquitetura", nome="Ana")
        self.assertIn("Questão 2/3", texto(a.responder(certa("arquitetura", 0), nome="Ana")))

        # B também se chama "Ana", mas não está em quiz nenhum: a resposta "1" não é do quiz da A
        r = b.responder("1", nome="Ana")
        self.assertNotEqual(r.get_json()["fonte_resposta"], "quiz")
        self.assertNotIn("Questão", r.get_json()["resposta"])

        # B inicia o dele e começa do zero, sem herdar o andamento da A
        self.assertIn("Questão 1/3", texto(b.responder("quiz arquitetura", nome="Ana")))
        # e a A continua exatamente de onde parou
        self.assertIn("Questão 3/3", texto(a.responder(certa("arquitetura", 1), nome="Ana")))

    def test_mesmo_ip_e_navegador_com_cookies_diferentes_tambem_nao_misturam(self):
        """Sala de aula: vários alunos atrás do mesmo IP e navegador dividem o RELÓGIO, mas não o quiz."""
        a = self.cliente(ip="198.51.100.30", ua="Mesmo-Navegador")
        b = self.cliente(ip="198.51.100.30", ua="Mesmo-Navegador")
        a.responder("quiz python", nome="Aluno")
        self.assertIn("Questão 2/2", texto(a.responder(certa("python", 0), nome="Aluno")))
        r = b.responder("2", nome="Aluno")
        self.assertNotEqual(r.get_json()["fonte_resposta"], "quiz")

    def test_usuario_e_visitante_com_o_mesmo_nome(self):
        ana = self.cliente(ip="198.51.100.23")
        self.assertEqual(ana.registrar("Ana Lima", "ana@example.com", SENHA_BOA).status_code, 200)
        ana.responder("quiz web", nome="Ana")

        visitante = self.cliente(ip="198.51.100.24", ua="Navegador-V")
        r = visitante.responder("2", nome="Ana")
        self.assertNotEqual(r.get_json()["fonte_resposta"], "quiz")

        # a resposta da Ana continua valendo para a Ana
        self.assertIn("Questão 2/2", texto(ana.responder("2", nome="Ana")))

    def test_o_nome_digitado_nao_muda_de_quem_e_o_quiz(self):
        ana = self.cliente()
        ana.registrar("Ana Lima", "ana@example.com", SENHA_BOA)
        ana.responder("quiz web", nome="Ana")
        # mesma pessoa logada, outro "nome de exibição": o quiz dela continua (e ninguém mais o enxerga)
        self.assertIn("Questão 2/2", texto(ana.responder("2", nome="Aninha")))

    def test_o_quiz_sobrevive_a_sair_e_entrar(self):
        ana = self.cliente()
        ana.registrar("Ana Lima", "ana@example.com", SENHA_BOA)
        ana.responder("quiz web", nome="Ana")
        ana.logout()
        ana.login("ana@example.com")
        self.assertIn("Questão 2/2", texto(ana.responder("2", nome="Ana")))

    def test_chaves_do_estado_sao_donos_e_nunca_nomes(self):
        a = self.cliente(ip="198.51.100.21", ua="Navegador-A")
        ana = self.cliente(ip="198.51.100.25")
        ana.registrar("Ana Lima", "ana@example.com", SENHA_BOA)
        a.responder("quiz web", nome="Ana")
        ana.responder("quiz web", nome="Ana")
        chaves = list(self.estado().user_quiz_state)
        self.assertEqual(len(chaves), 2)
        self.assertTrue(all(c.startswith(("u:", "g:")) for c in chaves), chaves)
        self.assertNotIn("Ana", chaves)

    def test_teto_de_quizzes_ativos_descarta_os_mais_antigos(self):
        bot = self.estado()
        bot._max_quizzes_ativos = 3
        for i in range(5):
            bot.iniciar_quiz("python", f"g:{i}", "x")
        self.assertEqual(list(bot.user_quiz_state), ["g:2", "g:3", "g:4"])
        bot.iniciar_quiz("python", "g:2", "x")                       # recomeçar traz o dono para o fim da fila
        bot.iniciar_quiz("python", "g:5", "x")
        self.assertEqual(list(bot.user_quiz_state), ["g:4", "g:2", "g:5"])

    def test_processar_resposta_sem_quiz_nao_quebra(self):
        bot = self.estado()
        self.assertIn("não está em um quiz ativo", bot.processar_resposta_quiz("1", "g:nunca-vi", "Ana"))


class QuizEEndpointsTest(XBotTestCase):
    def setUp(self):
        super().setUp()
        self.v = self.cliente()

    # -- /quiz/<categoria> ----------------------------------------------------------------
    def test_iniciar_quiz_pelo_endpoint_e_continuar_pelo_chat(self):
        r = self.v.post("/quiz/python", {"nome_usuario": "Ana"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("Quiz de Python iniciado, Ana!", texto(r))
        self.assertIn("Questão 2/2", texto(self.v.responder(certa("python", 0), nome="Ana")))

    def test_categoria_desconhecida_lista_as_disponiveis(self):
        resposta = texto(self.v.post("/quiz/astrologia", {"nome_usuario": "Ana"}))
        self.assertIn("não tenho quiz sobre astrologia", resposta)
        for categoria in QUIZ:
            self.assertIn(categoria, resposta)

    def test_categoria_gigante_e_cortada_na_resposta(self):
        resposta = texto(self.v.post("/quiz/" + "a" * 500, {"nome_usuario": "Ana"}))
        self.assertIn("não tenho quiz sobre", resposta)
        self.assertNotIn("a" * 41, resposta)

    def test_categorias_estranhas_nunca_dao_500(self):
        for categoria in ("%00", "%E2%9C%93", "__proto__", "..", "a%20b", "%F0%9F%A4%96", "<script>"):
            with self.subTest(categoria=categoria):
                r = self.v.post(f"/quiz/{categoria}", {"nome_usuario": "Ana"})
                self.assertIn(r.status_code, (200, 404), r.get_data(as_text=True)[:200])
                self.assertIsInstance(r.get_json(), dict)

    def test_nome_do_endpoint_e_limpo_como_no_chat(self):
        resposta = texto(self.v.post("/quiz/web", {"nome_usuario": "  Ana\n\tLima  "}))
        self.assertIn("Quiz de Web iniciado, Ana Lima!", resposta)
        resposta = texto(self.v.post("/quiz/web", {}))
        self.assertIn("Quiz de Web iniciado, usuário!", resposta)

    def test_quiz_exige_csrf_e_json_valido(self):
        self.assertJsonErro(self.v.post("/quiz/python", {"nome_usuario": "Ana"}, token=None), 403, "csrf")
        self.assertJsonErro(self.v.post("/quiz/python", [1, 2]), 400, "json_invalido")
        self.assertJsonErro(self.v.post("/quiz/python", {"nome_usuario": 123}), 400, "tipo_invalido")
        self.assertJsonErro(self.v.post("/quiz/python", {"nome_usuario": ["x"]}), 400, "tipo_invalido")
        self.assertJsonErro(self.v.post("/quiz/python", data="não é json"), 415, "tipo_nao_suportado")
        self.assertEqual(self.v.get("/quiz/python").status_code, 405)

    def test_endpoints_bloqueados_depois_do_tempo_do_visitante(self):
        self.v.sessao()                                               # abre o relógio de 10 minutos
        self.relogio.avancar(601)
        r = self.v.post("/quiz/python", {"nome_usuario": "Ana"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.get_json()["codigo"], "limite_visitante")
        r = self.v.get("/exercicio/python_basico")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.get_json()["codigo"], "limite_visitante")

    def test_usuario_logado_nunca_e_bloqueado_nos_endpoints(self):
        ana = self.cliente(ip="198.51.100.50")
        ana.registrar("Ana Lima", "ana@example.com", SENHA_BOA)
        self.relogio.avancar(100_000)
        self.assertEqual(ana.post("/quiz/python", {"nome_usuario": "Ana"}).status_code, 200)
        self.assertEqual(ana.get("/exercicio/python_basico").status_code, 200)

    # -- /exercicio/<categoria> --------------------------------------------------------------
    def test_exercicio_python_basico(self):
        r = self.v.get("/exercicio/python_basico?usuario=Ana")
        self.assertEqual(r.status_code, 200)
        resposta = texto(r)
        self.assertIn("💻 Exercício:", resposta)
        self.assertTrue(any(titulo in resposta for titulo in TITULOS_EXERCICIOS), resposta[:200])
        self.assertIn("Tente implementar sua própria versão, Ana!", resposta)

    def test_exercicio_desconhecido(self):
        resposta = texto(self.v.get("/exercicio/astrologia"))
        self.assertIn("Não tenho exercícios para astrologia", resposta)
        self.assertIn("python_basico", resposta)
        resposta = texto(self.v.get("/exercicio/" + "b" * 500))
        self.assertNotIn("b" * 41, resposta)

    def test_exercicio_nome_estranho_na_query(self):
        for nome in ("%00", "%E2%9C%93", "%0A%0D", "<b>x</b>"):
            with self.subTest(nome=nome[:10]):
                r = self.v.get(f"/exercicio/python_basico?usuario={nome}")
                self.assertEqual(r.status_code, 200)
                self.assertIn("💻 Exercício:", texto(r))
        # nome gigante é cortado em 40 caracteres, como no chat
        resposta = texto(self.v.get("/exercicio/python_basico?usuario=" + "x" * 5000))
        self.assertIn("x" * 40, resposta)
        self.assertNotIn("x" * 41, resposta)
        # caracteres de controle somem; sem nome sobra o padrão
        self.assertIn("Tente implementar sua própria versão, usuário!", texto(self.v.get("/exercicio/python_basico?usuario=%00")))

    def test_exercicio_pelo_chat_nao_e_truncado_para_visitante(self):
        r = self.v.responder("exercício python", nome="Ana")
        corpo = r.get_json()
        self.assertEqual(corpo["fonte_resposta"], "exercicio")
        self.assertIn("Tente implementar sua própria versão, Ana!", corpo["resposta"])
        self.assertNotIn("prévia", corpo["resposta"])
        self.assertIn("Exercícios disponíveis", texto(self.v.responder("exercicio")))

    # -- contadores ----------------------------------------------------------------------------
    def test_contadores_de_quiz_e_exercicio_no_status(self):
        self.v.post("/quiz/python", {"nome_usuario": "Ana"})
        self.v.responder("quiz web")
        self.v.get("/exercicio/python_basico")
        self.v.responder("exercício python")
        corpo = self.v.get("/status").get_json()
        self.assertEqual(corpo["quizzes_realizados"], 2)
        self.assertEqual(corpo["exercicios_solicitados"], 2)
        self.assertEqual(corpo["estatisticas_bot"]["quiz_categorias"], list(QUIZ))
        self.assertEqual(corpo["estatisticas_bot"]["exercicio_categorias"], ["python_basico"])


class PadroesDeCategoriaTest(XBotTestCase):
    """O quiz e os exercícios entram por último na lista de padrões e 'pergunta'/'questão' não disparam quiz."""

    def bot(self):
        return self.app.extensions["xbot"].bot

    def test_quiz_e_exercicios_ficam_depois_dos_demais_padroes(self):
        self.assertEqual(list(self.bot().padroes)[-2:], ["quiz", "exercicios"])

    def test_palavras_comuns_nao_viram_quiz(self):
        bot = self.bot()
        for frase in ("tenho uma pergunta", "uma questão importante", "qual é a pergunta?"):
            with self.subTest(frase=frase):
                self.assertNotEqual(bot.detectar_categoria(frase), "quiz")

    def test_palavras_de_quiz_continuam_funcionando(self):
        bot = self.bot()
        for frase in ("quero um quiz", "vamos fazer um teste", "me dê um desafio"):
            with self.subTest(frase=frase):
                self.assertEqual(bot.detectar_categoria(frase), "quiz")


if __name__ == "__main__":
    unittest.main()
