"""Históricos de conversa: só o dono (usuário autenticado) lê e apaga; o nome na URL não dá acesso a nada."""

import threading
import unittest

from historico import HistoricoConversas

from .base import SENHA_BOA, XBotTestCase


class HistoricoConversasUnidadeTest(unittest.TestCase):
    """A estrutura em memória, sem Flask."""

    def test_donos_diferentes_com_o_mesmo_nome_nao_se_misturam(self):
        h = HistoricoConversas()
        h.adicionar("u:1", "Ana", {"usuario": "segredo do usuário 1"})
        h.adicionar("u:2", "Ana", {"usuario": "mensagem do usuário 2"})
        self.assertEqual([e["usuario"] for e in h.obter("u:1", "Ana")], ["segredo do usuário 1"])
        self.assertEqual([e["usuario"] for e in h.obter("u:2", "Ana")], ["mensagem do usuário 2"])
        self.assertEqual(h.obter("g:abc", "Ana"), [])

    def test_limpar_so_apaga_do_proprio_dono(self):
        h = HistoricoConversas()
        h.adicionar("u:1", "Ana", {"usuario": "a"})
        h.adicionar("u:2", "Ana", {"usuario": "b"})
        self.assertFalse(h.limpar("u:3", "Ana"))
        self.assertTrue(h.limpar("u:1", "Ana"))
        self.assertFalse(h.limpar("u:1", "Ana"))
        self.assertEqual(len(h.obter("u:2", "Ana")), 1)

    def test_obter_devolve_copia(self):
        h = HistoricoConversas()
        h.adicionar("u:1", "Ana", {"usuario": "a"})
        copia = h.obter("u:1", "Ana")
        copia.clear()
        self.assertEqual(len(h.obter("u:1", "Ana")), 1)

    def test_teto_de_mensagens_por_conversa(self):
        h = HistoricoConversas(max_mensagens=5)
        for i in range(12):
            h.adicionar("u:1", "Ana", {"n": i})
        self.assertEqual([e["n"] for e in h.obter("u:1", "Ana")], [7, 8, 9, 10, 11])

    def test_teto_de_nomes_por_dono_descarta_o_menos_recente(self):
        h = HistoricoConversas(max_nomes_por_dono=3)
        for nome in ("a", "b", "c", "d"):
            h.adicionar("u:1", nome, {"n": nome})
        self.assertEqual(h.obter("u:1", "a"), [])
        self.assertEqual(len(h.obter("u:1", "d")), 1)
        h.adicionar("u:2", "a", {"n": "outro dono"})                    # outro dono não é afetado
        self.assertEqual(len(h.obter("u:2", "a")), 1)

    def test_teto_global_de_conversas(self):
        h = HistoricoConversas(max_conversas=10, max_nomes_por_dono=5)
        for i in range(25):
            h.adicionar(f"g:{i}", "visitante", {"n": i})
        self.assertLessEqual(h.total_conversas(), 10)
        self.assertEqual(len(h.obter("g:24", "visitante")), 1)            # a mais recente fica
        self.assertEqual(h.obter("g:0", "visitante"), [])                # a mais antiga saiu

    def test_threads_simultaneas(self):
        h = HistoricoConversas()

        def escrever(n):
            for i in range(200):
                h.adicionar(f"u:{n}", "Ana", {"i": i})

        fios = [threading.Thread(target=escrever, args=(n,)) for n in range(8)]
        for fio in fios:
            fio.start()
        for fio in fios:
            fio.join()
        self.assertEqual(h.total_conversas(), 8)
        self.assertEqual(sum(len(h.obter(f"u:{n}", "Ana")) for n in range(8)), 8 * 100)  # teto de 100 cada


class HistoricoHttpTest(XBotTestCase):
    def setUp(self):
        super().setUp()
        self.ana = self.cliente(ip="198.51.100.11")
        self.ana.registrar("Ana Lima", "ana@example.com", SENHA_BOA)
        self.beto = self.cliente(ip="198.51.100.12")
        self.beto.registrar("Beto Dias", "beto@example.com", "Outra-Frase_Segura#12")

    def mensagens(self, cliente, nome="Ana"):
        r = cliente.get(f"/historico/{nome}")
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        return [entrada["usuario"] for entrada in r.get_json()["historico"]]

    # -- exige login ---------------------------------------------------------------------
    def test_visitante_nao_le_nem_apaga_historico(self):
        visitante = self.cliente()
        visitante.responder("mensagem do visitante", nome="Ana")
        self.assertJsonErro(visitante.get("/historico/Ana"), 401, "nao_autenticado")
        self.assertJsonErro(visitante.delete("/limpar_historico/Ana"), 401, "nao_autenticado")

    def test_sem_nenhuma_sessao_tambem_nao(self):
        anonimo = self.cliente()
        self.assertEqual(anonimo.get("/historico/Ana").status_code, 401)
        self.assertEqual(anonimo.get("/historico/Beto").status_code, 401)

    # -- propriedade -----------------------------------------------------------------------
    def test_dono_le_o_proprio_historico(self):
        self.ana.responder("primeira pergunta da Ana", nome="Ana")
        self.ana.responder("segunda pergunta da Ana", nome="Ana")
        r = self.ana.get("/historico/Ana")
        corpo = r.get_json()
        self.assertEqual(corpo["total_mensagens"], 2)
        self.assertEqual([e["usuario"] for e in corpo["historico"]],
                         ["primeira pergunta da Ana", "segunda pergunta da Ana"])
        self.assertTrue(all(e["bot"] for e in corpo["historico"]))

    def test_o_nome_na_url_nao_da_acesso_ao_historico_de_outra_pessoa(self):
        self.ana.responder("assunto particular da Ana", nome="Ana")
        # Beto pede /historico/Ana: o nome bate, mas o DONO não — vem vazio
        self.assertEqual(self.mensagens(self.beto, "Ana"), [])
        r = self.beto.get("/historico/Ana")
        self.assertNotIn("particular", r.get_data(as_text=True))

    def test_o_nome_enviado_no_chat_nao_cola_a_conversa_no_nome_de_outra_pessoa(self):
        self.ana.responder("assunto particular da Ana", nome="Ana")
        self.beto.responder("Beto fingindo ser Ana", nome="Ana")
        self.assertEqual(self.mensagens(self.ana), ["assunto particular da Ana"])
        self.assertEqual(self.mensagens(self.beto), ["Beto fingindo ser Ana"])

    def test_nome_de_exibicao_so_escolhe_qual_conversa_do_proprio_dono(self):
        self.ana.responder("pergunta 1", nome="Ana")
        self.ana.responder("pergunta 2", nome="Aninha")
        self.assertEqual(self.mensagens(self.ana, "Ana"), ["pergunta 1"])
        self.assertEqual(self.mensagens(self.ana, "Aninha"), ["pergunta 2"])
        self.assertEqual(self.mensagens(self.ana, "Beto"), [])

    def test_conversa_de_visitante_nao_aparece_para_usuario_logado(self):
        visitante = self.cliente(ip="192.0.2.31")
        visitante.responder("conversa do visitante", nome="Ana")
        self.assertEqual(self.mensagens(self.ana, "Ana"), [])
        # e o visitante que depois se cadastra começa limpo (a conversa anônima não migra)
        resposta = visitante.registrar("Carla Reis", "carla@example.com", "Frase-Segura_Zeta#55")
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        self.assertEqual(self.mensagens(visitante, "Ana"), [])

    def test_historico_sobrevive_a_sair_e_entrar_de_novo(self):
        self.ana.responder("lembre disto", nome="Ana")
        self.ana.logout()
        self.assertEqual(self.ana.get("/historico/Ana").status_code, 401)
        self.ana.login("ana@example.com")
        self.assertEqual(self.mensagens(self.ana), ["lembre disto"])

    # -- exclusão ----------------------------------------------------------------------------
    def test_apagar_o_proprio_historico(self):
        self.ana.responder("apague-me", nome="Ana")
        r = self.ana.delete("/limpar_historico/Ana")
        self.assertEqual(r.status_code, 200)
        self.assertIn("limpo com sucesso", r.get_json()["mensagem"])
        self.assertEqual(self.mensagens(self.ana), [])
        self.assertEqual(self.ana.delete("/limpar_historico/Ana").status_code, 404)    # já não existe

    def test_nao_da_para_apagar_o_historico_de_outra_pessoa(self):
        self.ana.responder("a Ana quer guardar isto", nome="Ana")
        r = self.beto.delete("/limpar_historico/Ana")
        self.assertEqual(r.status_code, 404)                           # Beto não tem conversa "Ana"
        self.assertEqual(self.mensagens(self.ana), ["a Ana quer guardar isto"])

    def test_apagar_so_afeta_o_dono_mesmo_com_conversas_de_mesmo_nome(self):
        self.ana.responder("da Ana", nome="Ana")
        self.beto.responder("do Beto", nome="Ana")
        self.assertEqual(self.beto.delete("/limpar_historico/Ana").status_code, 200)
        self.assertEqual(self.mensagens(self.ana), ["da Ana"])
        self.assertEqual(self.mensagens(self.beto), [])

    def test_apagar_exige_csrf(self):
        self.ana.responder("continua aqui", nome="Ana")
        self.assertJsonErro(self.ana.delete("/limpar_historico/Ana", token=None), 403, "csrf")
        self.assertJsonErro(self.ana.delete("/limpar_historico/Ana", token="token-errado"), 403, "csrf")
        self.assertEqual(self.mensagens(self.ana), ["continua aqui"])

    def test_token_de_outra_sessao_nao_serve(self):
        self.ana.responder("continua aqui", nome="Ana")
        r = self.ana.delete("/limpar_historico/Ana", token=self.beto.token)
        self.assertJsonErro(r, 403, "csrf")
        self.assertEqual(self.mensagens(self.ana), ["continua aqui"])

    # -- robustez ----------------------------------------------------------------------------
    def test_metodos_errados(self):
        self.assertJsonErro(self.ana.post("/historico/Ana", {}), 405)
        self.assertJsonErro(self.ana.get("/limpar_historico/Ana"), 405)

    def test_nomes_estranhos_nunca_viram_erro_500(self):
        nomes = ["x" * 300, "%E2%9C%93%20ok", "a%00b", "%20%20", "..", "%2E%2E", "<script>alert(1)</script>",
                 "Jo%C3%A3o", "a%0Ab", "%F0%9F%A4%96"]
        for nome in nomes:
            with self.subTest(nome=nome[:25]):
                r = self.ana.get(f"/historico/{nome}")
                self.assertIn(r.status_code, (200, 404), r.get_data(as_text=True)[:200])
                self.assertIsInstance(r.get_json(), dict)

    def test_barra_no_nome_nao_escapa_da_rota(self):
        for nome in ("..%2F..%2Fetc%2Fpasswd", "a%2Fb", "%2F"):
            with self.subTest(nome=nome):
                r = self.ana.get(f"/historico/{nome}")
                self.assertEqual(r.status_code, 404)
                self.assertEqual(r.get_json()["erro"], "Endpoint não encontrado")

    def test_historico_traz_so_o_necessario(self):
        self.ana.responder("o que é uma CPU?", nome="Ana")
        entrada = self.ana.get("/historico/Ana").get_json()["historico"][0]
        self.assertEqual(set(entrada), {"timestamp", "usuario", "bot", "categoria",
                                        "titulo_conhecimento", "categoria_respondida"})

    def test_o_dono_do_historico_nunca_aparece_na_resposta(self):
        self.ana.responder("oi", nome="Ana")
        texto = self.ana.get("/historico/Ana").get_data(as_text=True)
        self.assertNotIn("u:1", texto)
        self.assertNotIn("g:", texto)


if __name__ == "__main__":
    unittest.main()
