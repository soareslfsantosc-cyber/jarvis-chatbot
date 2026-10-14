"""Cadastro, login, senha forte, bloqueio de tentativas repetidas e compatibilidade com contas antigas."""

import random
import unittest
from unittest import mock

from werkzeug.security import check_password_hash, generate_password_hash

from database import auth
from database.db import get_connection

from .base import SENHA_BOA, XBotTestCase


class PoliticaDeSenhaTest(unittest.TestCase):
    """validar_senha(): funções puras, sem banco."""

    def problema(self, senha, nome="Maria Souza", email="maria.souza@example.com"):
        return auth.validar_senha(senha, nome, email)

    def test_senhas_fracas_sao_recusadas(self):
        casos = {
            "curta": "Ab1!xyz",
            "so_numeros": "4829174650183",
            "so_letras": "umasenhasomenteletras",
            "sequencia_numerica": "abc1234567890",
            "sequencia_numerica_2": "1234567890-a",
            "sequencia_alfabetica": "abcdefghijkl!",
            "teclado": "qwertyuiop12",
            "repetida": "aaaaaaaaaa11",
            "padrao_repetido": "xyz9xyz9xyz9xyz9",
            "comum": "senha12345",
            "comum_com_sufixo": "senha2026!!",
            "comum_com_leet": "p4ssw0rd2026",
            "comum_com_simbolo": "Password!2026",
            "contem_nome": "Maria-1980-oi!",
            "contem_email": "maria.souza#2026",
            "nome_com_acento": "SOUZA_maria_7",
        }
        for rotulo, senha in casos.items():
            with self.subTest(rotulo):
                self.assertIsNotNone(self.problema(senha), f"{senha!r} deveria ser recusada")

    def test_mensagens_dizem_o_que_corrigir(self):
        self.assertIn("pelo menos 10", self.problema("Ab1!xyz"))
        self.assertIn("letra", self.problema("1029384756102"))
        self.assertIn("número, símbolo ou espaço", self.problema("somenteletrasminusculas"))
        self.assertIn("comum", self.problema("p4ssw0rd2026"))
        self.assertIn("nome", self.problema("Maria-1980-oi!"))

    def test_tamanho_maximo(self):
        sorteio = random.Random(7)
        alfabeto = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&*-_"
        senha = "".join(sorteio.choice(alfabeto) for _ in range(128))
        self.assertIsNone(auth.validar_senha(senha, "", ""))                       # exatamente 128: vale
        self.assertIn("muito longa", auth.validar_senha(senha + "a", "", ""))      # 129: recusada

    def test_senhas_boas_sao_aceitas(self):
        for senha in (SENHA_BOA, "cavalo-bateria-grampo-9", "Meu gato Tião mora em Jundiaí!",
                      "x7$Kp9!vQ2#mL", "correct-horse-qwerty-battery-9", "Casa-Amarela-2026!"):
            with self.subTest(senha):
                self.assertIsNone(self.problema(senha), senha)

    def test_tipos_invalidos(self):
        for valor in (None, 123456789012, ["a"], {"a": 1}, b"bytes-senha-12"):
            with self.subTest(valor=valor):
                self.assertEqual(auth.validar_senha(valor), "Senha inválida.")

    def test_nome_curto_nao_bloqueia_senha(self):
        # partes do nome com menos de 4 letras não contam (senão "Ana" proibiria "banana")
        self.assertIsNone(auth.validar_senha("banana-roxa-77!", "Ana Lu", "ana@example.com"))


class CadastroTest(XBotTestCase):
    def test_cadastro_cria_usuario_e_ja_entra(self):
        c = self.cliente()
        antes = c.sessao()["csrf_token"]
        r = c.registrar("Maria Souza", "Maria@Example.com", SENHA_BOA)
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        corpo = r.get_json()
        self.assertTrue(corpo["sucesso"])
        self.assertEqual(corpo["usuario"]["nome"], "Maria Souza")
        self.assertEqual(corpo["usuario"]["email"], "maria@example.com")     # e-mail normalizado
        self.assertNotEqual(corpo["csrf_token"], antes)                      # token trocado no cadastro

        sessao = c.sessao()
        self.assertTrue(sessao["autenticado"])
        self.assertIsNone(sessao["tempo_restante"])
        self.assertFalse(sessao["bloqueado"])

    def test_senha_fica_so_como_hash(self):
        self.cliente().registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        (linha,) = self.consulta("SELECT senha_hash FROM users WHERE email = ?", ("maria@example.com",))
        hash_salvo = linha[0]
        self.assertNotIn(SENHA_BOA, hash_salvo)
        self.assertTrue(check_password_hash(hash_salvo, SENHA_BOA))
        self.assertFalse(check_password_hash(hash_salvo, SENHA_BOA + "x"))

    def test_resposta_nunca_devolve_hash_ou_senha(self):
        r = self.cliente().registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        texto = r.get_data(as_text=True)
        self.assertNotIn(SENHA_BOA, texto)
        self.assertNotIn("senha_hash", texto)
        self.assertNotIn("pbkdf2", texto)
        self.assertNotIn("scrypt", texto)

    def test_email_repetido_e_recusado_sem_diferenciar_maiusculas(self):
        self.cliente().registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        r = self.cliente().registrar("Outra Pessoa", "MARIA@EXAMPLE.COM", "Frase-Longa_Segura#77")
        corpo = self.assertJsonErro(r, 400, "email_em_uso")
        self.assertFalse(corpo["sucesso"])
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM users")[0][0], 1)

    def test_senha_fraca_via_endpoint(self):
        c = self.cliente()
        for senha, trecho in (("123456", "pelo menos 10"), ("senha12345", "comum"),
                              ("Maria-1980-oi!", "nome")):
            with self.subTest(senha):
                r = c.registrar("Maria Souza", "maria@example.com", senha)
                corpo = self.assertJsonErro(r, 400, "dados_invalidos")
                self.assertIn(trecho, corpo["erro"])
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM users")[0][0], 0)
        self.assertFalse(c.sessao()["autenticado"])

    def test_dados_invalidos(self):
        c = self.cliente()
        casos = [
            ({"nome": "A", "email": "a@example.com", "senha": SENHA_BOA}, "Nome"),
            ({"nome": "N" * 81, "email": "a@example.com", "senha": SENHA_BOA}, "longo"),
            ({"nome": "Maria", "email": "sem-arroba", "senha": SENHA_BOA}, "E-mail"),
            ({"nome": "Maria", "email": "a@b", "senha": SENHA_BOA}, "E-mail"),
            ({"nome": "Maria", "email": "a b@example.com", "senha": SENHA_BOA}, "E-mail"),
            ({"nome": "Maria", "email": ("x" * 250) + "@example.com", "senha": SENHA_BOA}, "mais de 320|E-mail|excede"),
        ]
        for dados, trecho in casos:
            with self.subTest(dados=str(dados)[:60]):
                r = c.post("/registrar", dados)
                self.assertEqual(r.status_code, 400, r.get_data(as_text=True))
                self.assertRegex(r.get_json()["erro"], trecho)
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM users")[0][0], 0)

    def test_nome_e_limpo_de_caracteres_de_controle(self):
        c = self.cliente()
        r = c.registrar("  Maria \t  Souza\x07 ", "maria@example.com", SENHA_BOA)
        self.assertEqual(r.get_json()["usuario"]["nome"], "Maria Souza")

    def test_cadastro_invalido_nao_gasta_o_limite_por_ip(self):
        c = self.cliente()
        for _ in range(15):                       # bem mais que XBOT_REGISTER_MAX_PER_HOUR (10)
            c.registrar("Maria Souza", "maria@example.com", "123456")
        r = c.registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))


class LimiteDeCadastroPorIpTest(XBotTestCase):
    env_extra = {"XBOT_REGISTER_MAX_PER_HOUR": 3}

    def test_excesso_de_cadastros_do_mesmo_ip(self):
        for i in range(3):
            r = self.cliente().registrar(f"Pessoa {i}x", f"p{i}@example.com", f"Frase-Segura_{i}{i}#Ok")
            self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        r = self.cliente().registrar("Pessoa Ex", "p9@example.com", "Frase-Segura_99#Ok")
        corpo = self.assertJsonErro(r, 429, "muitas_tentativas")
        self.assertGreater(int(r.headers["Retry-After"]), 0)
        self.assertEqual(corpo["retry_after"], int(r.headers["Retry-After"]))
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM users")[0][0], 3)

        # outro IP não é afetado
        r = self.cliente(ip="203.0.113.99").registrar("Pessoa Ok", "ok@example.com", "Frase-Segura_55#Ok")
        self.assertEqual(r.status_code, 200)

        # passada 1 hora, o IP volta a poder cadastrar
        self.relogio.avancar(3600 + 1)
        r = self.cliente().registrar("Pessoa Tv", "p10@example.com", "Frase-Segura_10#Ok")
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))


class LoginTest(XBotTestCase):
    EMAIL = "maria@example.com"

    def setUp(self):
        super().setUp()
        self.cliente().registrar("Maria Souza", self.EMAIL, SENHA_BOA)

    def test_login_correto(self):
        c = self.cliente()
        antes = c.sessao()["csrf_token"]
        r = c.login("  MARIA@example.com ", SENHA_BOA)                 # e-mail normalizado
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        corpo = r.get_json()
        self.assertTrue(corpo["sucesso"])
        self.assertEqual(corpo["usuario"]["email"], self.EMAIL)
        self.assertNotEqual(corpo["csrf_token"], antes)
        self.assertTrue(c.sessao()["autenticado"])

    def test_senha_errada_e_email_inexistente_sao_indistinguiveis(self):
        c = self.cliente()
        errada = c.login(self.EMAIL, "senha-errada-123")
        inexistente = c.login("ninguem@example.com", "senha-errada-123")
        self.assertEqual(errada.status_code, 401)
        self.assertEqual(inexistente.status_code, 401)
        self.assertEqual(errada.get_json()["erro"], inexistente.get_json()["erro"])
        self.assertEqual(errada.get_json()["erro"], "E-mail ou senha incorretos.")
        self.assertFalse(c.sessao()["autenticado"])

    def test_email_inexistente_tambem_calcula_hash(self):
        """Mesmo trabalho nos dois casos: o tempo de resposta não revela se o e-mail existe."""
        with mock.patch("database.auth.check_password_hash", wraps=check_password_hash) as chamada:
            self.cliente().login(self.EMAIL, "senha-errada-123")
            self.cliente().login("ninguem@example.com", "senha-errada-123")
        self.assertEqual(chamada.call_count, 2)

    def test_campos_obrigatorios(self):
        c = self.cliente()
        self.assertEqual(c.post("/login", {"email": self.EMAIL}).status_code, 400)
        self.assertEqual(c.post("/login", {"senha": SENHA_BOA}).status_code, 400)
        self.assertEqual(c.post("/login", {"email": "", "senha": ""}).status_code, 400)

    def test_entradas_gigantes_nao_viram_trabalho_de_hash(self):
        c = self.cliente()
        with mock.patch("database.auth.check_password_hash") as chamada:
            r = c.post("/login", {"email": self.EMAIL, "senha": "x" * 257})
            self.assertEqual(r.status_code, 400)                     # recusado já na borda (campo muito longo)
            chamada.assert_not_called()

    def test_conta_antiga_com_hash_pbkdf2_e_senha_curta_continua_entrando(self):
        """Dados existentes: a política nova vale só para NOVOS cadastros."""
        antigo = generate_password_hash("abc123", method="pbkdf2:sha256")
        with get_connection() as conn:
            conn.execute("INSERT INTO users (nome, email, senha_hash) VALUES (?, ?, ?)",
                         ("Conta Antiga", "antiga@example.com", antigo))
        c = self.cliente()
        r = c.login("antiga@example.com", "abc123")
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        self.assertEqual(r.get_json()["usuario"]["nome"], "Conta Antiga")
        # …mas a mesma senha fraca é recusada num cadastro novo
        r = self.cliente().registrar("Nova Pessoa", "nova@example.com", "abc123")
        self.assertEqual(r.status_code, 400)

    def test_hash_em_formato_desconhecido_nao_derruba_o_login(self):
        with get_connection() as conn:
            conn.execute("INSERT INTO users (nome, email, senha_hash) VALUES (?, ?, ?)",
                         ("Hash Estranho", "estranho@example.com", "formato-que-ninguem-conhece"))
        r = self.cliente().login("estranho@example.com", "qualquer-coisa-123")
        self.assertEqual(r.status_code, 401)

    def test_login_nao_registra_email_nem_senha_nos_logs(self):
        with self.assertLogs(level="DEBUG") as logs:
            c = self.cliente()
            c.login(self.EMAIL, "senha-errada-123")
            c.login(self.EMAIL, SENHA_BOA)
            c.registrar("Joao Pereira", "joao.pereira@example.com", "Outra-Frase_Segura#12")
        texto = "\n".join(logs.output)
        for segredo in (self.EMAIL, "joao.pereira", "senha-errada-123", SENHA_BOA, "Outra-Frase_Segura"):
            self.assertNotIn(segredo, texto)


class BloqueioDeTentativasTest(XBotTestCase):
    """5 falhas por e-mail em 15 minutos (padrões) → 429 com Retry-After."""

    EMAIL = "maria@example.com"

    def setUp(self):
        super().setUp()
        self.cliente(ip="198.51.100.50").registrar("Maria Souza", self.EMAIL, SENHA_BOA)
        self.atacante = self.cliente(ip="203.0.113.5")

    def falhar(self, vezes, email=None, cliente=None):
        cliente = cliente or self.atacante
        return [cliente.login(email or self.EMAIL, f"errada-{i}-xyz") for i in range(vezes)]

    def test_apos_cinco_falhas_bloqueia_ate_a_senha_certa(self):
        respostas = self.falhar(5)
        self.assertTrue(all(r.status_code == 401 for r in respostas))
        r = self.atacante.login(self.EMAIL, SENHA_BOA)                 # a senha CERTA, mas já bloqueado
        corpo = self.assertJsonErro(r, 429, "muitas_tentativas")
        self.assertIn("Tente novamente", corpo["erro"])
        espera = int(r.headers["Retry-After"])
        self.assertTrue(1 <= espera <= 900, espera)
        self.assertFalse(self.atacante.sessao()["autenticado"])

    def test_quarta_falha_ainda_permite_a_quinta_tentativa(self):
        self.falhar(4)
        r = self.atacante.login(self.EMAIL, SENHA_BOA)
        self.assertEqual(r.status_code, 200)

    def test_bloqueio_vale_de_qualquer_ip_para_aquele_email(self):
        self.falhar(5)
        outro_ip = self.cliente(ip="192.0.2.77")
        self.assertEqual(outro_ip.login(self.EMAIL, SENHA_BOA).status_code, 429)

    def test_dono_da_conta_so_volta_depois_da_janela(self):
        self.falhar(5)
        dono = self.cliente(ip="198.51.100.50")
        self.assertEqual(dono.login(self.EMAIL, SENHA_BOA).status_code, 429)
        self.relogio.avancar(899)
        self.assertEqual(dono.login(self.EMAIL, SENHA_BOA).status_code, 429)
        self.relogio.avancar(2)                                        # 901 s depois da 1ª falha
        self.assertEqual(dono.login(self.EMAIL, SENHA_BOA).status_code, 200)

    def test_tentativas_durante_o_bloqueio_nao_prolongam_o_bloqueio(self):
        self.falhar(5)
        for _ in range(10):
            self.relogio.avancar(60)
            self.atacante.login(self.EMAIL, "tentando-de-novo-1")
        # 600 s passados + 1: ainda bloqueado; depois de 900 s da primeira falha, livre
        self.relogio.avancar(400)
        self.assertEqual(self.cliente(ip="198.51.100.50").login(self.EMAIL, SENHA_BOA).status_code, 200)

    def test_sucesso_zera_o_contador_do_email(self):
        self.falhar(4)
        self.assertEqual(self.cliente(ip="198.51.100.50").login(self.EMAIL, SENHA_BOA).status_code, 200)
        self.falhar(4)                                                 # recomeça do zero: ainda livre
        self.assertEqual(self.cliente(ip="198.51.100.50").login(self.EMAIL, SENHA_BOA).status_code, 200)

    def test_emails_diferentes_tem_contadores_proprios(self):
        self.cliente(ip="198.51.100.51").registrar("Joao Pereira", "joao.p@example.com", "Outra-Frase_Segura#12")
        self.falhar(5)
        r = self.cliente(ip="198.51.100.51").login("joao.p@example.com", "Outra-Frase_Segura#12")
        self.assertEqual(r.status_code, 200)

    def test_inexistente_e_existente_bloqueiam_do_mesmo_jeito(self):
        """Sem enumeração de contas: e-mail que não existe também chega ao 429, com a mesma mensagem."""
        existente = self.falhar(5)
        inexistente = self.falhar(5, email="fantasma@example.com", cliente=self.cliente(ip="192.0.2.8"))
        self.assertEqual([r.status_code for r in existente], [r.status_code for r in inexistente])
        r1 = self.atacante.login(self.EMAIL, "x-qualquer-1")
        r2 = self.cliente(ip="192.0.2.8").login("fantasma@example.com", "x-qualquer-1")
        self.assertEqual(r1.status_code, 429)
        self.assertEqual(r2.status_code, 429)
        self.assertEqual(r1.get_json()["erro"].split(".")[0], r2.get_json()["erro"].split(".")[0])

    def test_contador_sobrevive_ao_reinicio_do_servidor(self):
        from app import create_app

        self.falhar(5)
        novo_app = create_app(self.cfg)                                 # "reinício": app novo, mesmo banco
        c = self.cliente()
        c.app = novo_app
        c.http = novo_app.test_client()
        c.http.environ_base["REMOTE_ADDR"] = "192.0.2.200"
        self.assertEqual(c.login(self.EMAIL, SENHA_BOA).status_code, 429)

    def test_banco_guarda_apenas_hmac_nao_email_nem_ip(self):
        self.falhar(2)
        linhas = self.consulta("SELECT acao, chave FROM auth_tentativas")
        self.assertTrue(linhas)
        for _acao, chave in linhas:
            self.assertNotIn("maria", chave)
            self.assertNotIn("203.0.113.5", chave)
            self.assertRegex(chave, r"^[0-9a-f]{40}$")

    def test_tentativas_antigas_sao_apagadas(self):
        self.falhar(2)
        self.relogio.avancar(25 * 3600)
        self.falhar(1)
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM auth_tentativas WHERE quando < ?",
                                       (self.relogio.t - 24 * 3600,))[0][0], 0)


class LimitePorIpTest(XBotTestCase):
    """Um IP testando muitas contas diferentes também é bloqueado (aqui o limite é 4 falhas)."""

    env_extra = {"XBOT_LOGIN_MAX_FAILURES_IP": 4}

    def test_ip_que_testa_varias_contas_e_bloqueado(self):
        self.cliente(ip="198.51.100.50").registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        atacante = self.cliente(ip="203.0.113.5")
        for i in range(4):
            self.assertEqual(atacante.login(f"alvo{i}@example.com", "errada-123-xyz").status_code, 401)
        # 5ª tentativa, com e-mail inédito (cujo contador próprio está em zero): bloqueada pelo IP
        self.assertEqual(atacante.login("alvo99@example.com", "errada-123-xyz").status_code, 429)
        # nem a conta verdadeira abre a partir deste IP enquanto durar o bloqueio
        self.assertEqual(atacante.login("maria@example.com", SENHA_BOA).status_code, 429)
        # outro IP segue normal
        self.assertEqual(self.cliente(ip="198.51.100.50").login("maria@example.com", SENHA_BOA).status_code, 200)
        # e depois da janela (15 min) o IP volta
        self.relogio.avancar(901)
        self.assertEqual(atacante.login("maria@example.com", SENHA_BOA).status_code, 200)


class LimitesConfiguraveisTest(XBotTestCase):
    env_extra = {"XBOT_LOGIN_MAX_FAILURES_EMAIL": 2, "XBOT_LOGIN_WINDOW_SECONDS": 60}

    def test_limites_vem_da_configuracao(self):
        c = self.cliente()
        c.registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        c.logout()
        for i in range(2):
            c.login("maria@example.com", f"errada-{i}-xyz")
        self.assertEqual(c.login("maria@example.com", SENHA_BOA).status_code, 429)
        self.relogio.avancar(61)
        self.assertEqual(c.login("maria@example.com", SENHA_BOA).status_code, 200)


class BuscarUsuarioTest(XBotTestCase):
    def test_id_invalido_nao_quebra(self):
        for valor in (None, "1", 1.0, True, [], {}, -1, 10**12):
            with self.subTest(valor=valor):
                self.assertIsNone(auth.buscar_usuario_por_id(valor))

    def test_id_valido(self):
        self.cliente().registrar("Maria Souza", "maria@example.com", SENHA_BOA)
        usuario = auth.buscar_usuario_por_id(1)
        self.assertEqual(usuario, {"id": 1, "nome": "Maria Souza", "email": "maria@example.com"})


if __name__ == "__main__":
    unittest.main()
