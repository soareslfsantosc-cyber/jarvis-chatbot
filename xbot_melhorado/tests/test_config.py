"""Configuração: chave secreta, produção x desenvolvimento, debug, rede e CORS."""

import contextlib
import io
import os
import shutil
import tempfile
import unittest
from unittest import mock

import config
from config import Config, ConfigError, carregar_dotenv

from . import PASTA_TEMP
from .base import banco_modelo

CHAVE_BOA = "f3a9c1d27b8e4a06915d3c7e2b4f8a1d6e0c9b5a7d2f4e8c1a3b6d9e0f2a4c71"


def env(**kw):
    base = {"XBOT_DB_PATH": os.path.join(PASTA_TEMP, "cfg.db")}
    base.update(kw)
    return base


def ler(**kw) -> Config:
    return Config.from_env(env(**kw), dotenv_path=None)


class ChaveSecretaTest(unittest.TestCase):
    def test_producao_sem_chave_falha_com_mensagem_clara(self):
        with self.assertRaises(ConfigError) as ctx:
            ler()                                   # sem XBOT_ENV → produção
        mensagem = str(ctx.exception)
        self.assertIn("XBOT_SECRET_KEY", mensagem)
        self.assertIn("secrets.token_hex(32)", mensagem)    # diz como gerar uma
        self.assertIn(".env", mensagem)
        self.assertIn("XBOT_ENV=development", mensagem)    # e como seguir só para desenvolver

    def test_producao_explicita_sem_chave_ou_chave_em_branco_falha(self):
        for valor in (None, "", "   "):
            with self.subTest(valor=valor):
                extra = {} if valor is None else {"XBOT_SECRET_KEY": valor}
                with self.assertRaises(ConfigError):
                    ler(XBOT_ENV="production", **extra)

    def test_producao_rejeita_chave_curta(self):
        with self.assertRaisesRegex(ConfigError, "curta demais"):
            ler(XBOT_SECRET_KEY="abc123")

    def test_producao_rejeita_chave_de_exemplo(self):
        exemplos = (
            "dev-secret-key-trocar-em-producao",                  # o antigo valor padrão do projeto
            "troque-esta-chave-por-uma-bem-grande-123456",
            "a" * 40,                                              # sem variedade
            "my-super-secret-password-for-xbot-2026-ok",           # contém 'password'/'secret'...
        )
        for chave in exemplos:
            with self.subTest(chave=chave):
                with self.assertRaises(ConfigError):
                    ler(XBOT_SECRET_KEY=chave)

    def test_producao_aceita_chave_aleatoria(self):
        cfg = ler(XBOT_SECRET_KEY=CHAVE_BOA)
        self.assertTrue(cfg.producao)
        self.assertEqual(cfg.secret_key, CHAVE_BOA)
        self.assertFalse(cfg.secret_efemera)

    def test_desenvolvimento_sem_chave_gera_chave_temporaria(self):
        a = ler(XBOT_ENV="development")
        b = ler(XBOT_ENV="development")
        self.assertTrue(a.secret_efemera)
        self.assertGreaterEqual(len(a.secret_key), 32)
        self.assertNotEqual(a.secret_key, b.secret_key)             # nunca uma chave fixa
        self.assertTrue(any("TEMPORÁRIA" in aviso for aviso in a.avisos))

    def test_chave_nao_aparece_no_repr_nem_no_resumo(self):
        cfg = ler(XBOT_SECRET_KEY=CHAVE_BOA)
        self.assertNotIn(CHAVE_BOA, repr(cfg))
        self.assertNotIn(CHAVE_BOA, cfg.resumo())

    def test_ambiente_invalido(self):
        with self.assertRaisesRegex(ConfigError, "XBOT_ENV"):
            ler(XBOT_ENV="staging", XBOT_SECRET_KEY=CHAVE_BOA)


class DebugERedeTest(unittest.TestCase):
    def test_producao_tem_debug_desligado_e_escuta_so_em_localhost(self):
        cfg = ler(XBOT_SECRET_KEY=CHAVE_BOA)
        self.assertFalse(cfg.debug)
        self.assertEqual(cfg.host, "127.0.0.1")
        self.assertFalse(cfg.host_na_rede)

    def test_debug_em_producao_e_recusado(self):
        for valor in ("1", "true", "sim"):
            with self.subTest(valor=valor):
                with self.assertRaisesRegex(ConfigError, "XBOT_DEBUG"):
                    ler(XBOT_SECRET_KEY=CHAVE_BOA, XBOT_DEBUG=valor)

    def test_debug_no_ambiente_de_teste_tambem_e_recusado(self):
        with self.assertRaises(ConfigError):
            ler(XBOT_ENV="testing", XBOT_DEBUG="1")

    def test_desenvolvimento_liga_debug_so_em_loopback(self):
        cfg = ler(XBOT_ENV="development")
        self.assertTrue(cfg.debug)
        self.assertFalse(cfg.host_na_rede)

    def test_desenvolvimento_na_rede_desliga_o_debug_sozinho(self):
        cfg = ler(XBOT_ENV="development", XBOT_HOST="0.0.0.0")
        self.assertFalse(cfg.debug)
        self.assertTrue(any("Debug desativado" in aviso for aviso in cfg.avisos))
        self.assertTrue(any("rede" in aviso for aviso in cfg.avisos))

    def test_debug_pedido_explicitamente_na_rede_e_recusado(self):
        with self.assertRaisesRegex(ConfigError, "depurador"):
            ler(XBOT_ENV="development", XBOT_HOST="0.0.0.0", XBOT_DEBUG="1")

    def test_debug_pode_ser_desligado_em_desenvolvimento(self):
        self.assertFalse(ler(XBOT_ENV="development", XBOT_DEBUG="0").debug)

    def test_loopback_ipv6_e_localhost_contam_como_local(self):
        for host in ("localhost", "::1", "127.0.0.5"):
            with self.subTest(host=host):
                self.assertFalse(ler(XBOT_ENV="development", XBOT_HOST=host).host_na_rede)

    def test_valores_invalidos(self):
        with self.assertRaises(ConfigError):
            ler(XBOT_SECRET_KEY=CHAVE_BOA, XBOT_PORT="abc")
        with self.assertRaises(ConfigError):
            ler(XBOT_SECRET_KEY=CHAVE_BOA, XBOT_PORT="70000")
        with self.assertRaises(ConfigError):
            ler(XBOT_ENV="development", XBOT_DEBUG="talvez")


class CorsECookiesTest(unittest.TestCase):
    def test_padrao_nao_libera_nenhuma_origem(self):
        self.assertEqual(ler(XBOT_SECRET_KEY=CHAVE_BOA).allowed_origins, ())

    def test_asterisco_e_recusado(self):
        for valor in ("*", "https://a.com, *"):
            with self.subTest(valor=valor):
                with self.assertRaisesRegex(ConfigError, r"não aceita '\*'"):
                    ler(XBOT_SECRET_KEY=CHAVE_BOA, XBOT_ALLOWED_ORIGINS=valor)

    def test_origens_sao_normalizadas(self):
        cfg = ler(XBOT_SECRET_KEY=CHAVE_BOA,
                  XBOT_ALLOWED_ORIGINS=" https://Meu.Site/ ,http://localhost:5173,https://meu.site")
        self.assertEqual(cfg.allowed_origins, ("https://meu.site", "http://localhost:5173"))

    def test_origem_malformada_e_recusada(self):
        for valor in ("meu.site", "https://meu.site/caminho", "ftp://x.com", "https://"):
            with self.subTest(valor=valor):
                with self.assertRaises(ConfigError):
                    ler(XBOT_SECRET_KEY=CHAVE_BOA, XBOT_ALLOWED_ORIGINS=valor)

    def test_samesite_none_exige_cookie_secure(self):
        cfg = ler(XBOT_SECRET_KEY=CHAVE_BOA, XBOT_COOKIE_SAMESITE="none")
        self.assertEqual(cfg.cookie_samesite, "None")
        self.assertTrue(cfg.cookie_secure)
        with self.assertRaises(ConfigError):
            ler(XBOT_SECRET_KEY=CHAVE_BOA, XBOT_COOKIE_SAMESITE="None", XBOT_COOKIE_SECURE="0")

    def test_padroes_de_cookie(self):
        cfg = ler(XBOT_SECRET_KEY=CHAVE_BOA)
        self.assertEqual(cfg.cookie_samesite, "Lax")
        self.assertIsNone(cfg.cookie_secure)        # automático: Secure quando a requisição é HTTPS


class LimitesTest(unittest.TestCase):
    def test_padroes_preservam_a_regra_de_10_minutos(self):
        cfg = ler(XBOT_SECRET_KEY=CHAVE_BOA)
        self.assertEqual(cfg.guest_seconds, 600)
        self.assertEqual(cfg.guest_cooldown_seconds, 86400)
        self.assertEqual(cfg.guest_max_sessions, 1)
        self.assertEqual(cfg.login_max_failures_email, 5)
        self.assertEqual(cfg.login_window_seconds, 900)
        self.assertFalse(cfg.diagnostics_open)      # diagnóstico fechado fora de development

    def test_diagnostico_aberto_so_em_desenvolvimento_ou_se_pedido(self):
        self.assertTrue(ler(XBOT_ENV="development").diagnostics_open)
        self.assertTrue(ler(XBOT_SECRET_KEY=CHAVE_BOA, XBOT_DIAGNOSTICS="1").diagnostics_open)

    def test_espera_nao_pode_ser_menor_que_o_teste(self):
        with self.assertRaises(ConfigError):
            ler(XBOT_SECRET_KEY=CHAVE_BOA, XBOT_GUEST_SECONDS="600", XBOT_GUEST_COOLDOWN_SECONDS="100")

    def test_limites_fora_do_intervalo(self):
        for nome, valor in (("XBOT_GUEST_SECONDS", "1"), ("XBOT_LOGIN_MAX_FAILURES_EMAIL", "0"),
                            ("XBOT_MAX_BODY_BYTES", "10")):
            with self.subTest(nome=nome):
                with self.assertRaises(ConfigError):
                    ler(XBOT_SECRET_KEY=CHAVE_BOA, **{nome: valor})

    def test_banco_invalido(self):
        with self.assertRaisesRegex(ConfigError, "pasta"):
            Config.from_env({"XBOT_SECRET_KEY": CHAVE_BOA, "XBOT_DB_PATH": PASTA_TEMP}, dotenv_path=None)
        with self.assertRaises(ConfigError):
            Config.from_env({"XBOT_SECRET_KEY": CHAVE_BOA, "XBOT_DB_PATH": ":memory:"}, dotenv_path=None)
        with self.assertRaises(ConfigError):
            Config.from_env({"XBOT_SECRET_KEY": CHAVE_BOA,
                             "XBOT_DB_PATH": os.path.join(PASTA_TEMP, "nao", "existe", "x.db")}, dotenv_path=None)


class DotenvTest(unittest.TestCase):
    def escrever(self, texto: str, encoding="utf-8") -> str:
        pasta = tempfile.mkdtemp(dir=PASTA_TEMP)
        caminho = os.path.join(pasta, ".env")
        with open(caminho, "w", encoding=encoding, newline="") as arquivo:
            arquivo.write(texto)
        return caminho

    def test_formato_basico(self):
        caminho = self.escrever(
            "# comentário\n\nXBOT_SECRET_KEY=abc\nXBOT_PORT = 8080\nexport XBOT_HOST=0.0.0.0\n"
            "XBOT_ALLOWED_ORIGINS=\"https://a.com\"\nXBOT_X='aspas simples'\nXBOT_Y=valor # comentário\n"
            "OUTRA_COISA=ignorada\nlinha sem igual\n"
        )
        valores = carregar_dotenv(caminho)
        self.assertEqual(valores["XBOT_SECRET_KEY"], "abc")
        self.assertEqual(valores["XBOT_PORT"], "8080")
        self.assertEqual(valores["XBOT_HOST"], "0.0.0.0")
        self.assertEqual(valores["XBOT_ALLOWED_ORIGINS"], "https://a.com")
        self.assertEqual(valores["XBOT_X"], "aspas simples")
        self.assertEqual(valores["XBOT_Y"], "valor")
        self.assertNotIn("OUTRA_COISA", valores)          # só variáveis XBOT_*

    def test_bom_do_bloco_de_notas_e_fim_de_linha_windows(self):
        caminho = self.escrever("﻿XBOT_PORT=7000\r\nXBOT_HOST=127.0.0.1\r\n")
        valores = carregar_dotenv(caminho)
        self.assertEqual(valores, {"XBOT_PORT": "7000", "XBOT_HOST": "127.0.0.1"})

    def test_arquivo_ausente_e_vazio(self):
        self.assertEqual(carregar_dotenv(os.path.join(PASTA_TEMP, "nao-existe.env")), {})

    def test_variavel_de_ambiente_vence_o_arquivo(self):
        caminho = self.escrever(f"XBOT_SECRET_KEY={CHAVE_BOA}\nXBOT_PORT=8080\nXBOT_DB_PATH={PASTA_TEMP}/d.db\n")
        with mock.patch.dict(os.environ, {"XBOT_PORT": "9090"}, clear=True):
            cfg = Config.from_env(dotenv_path=caminho)
        self.assertEqual(cfg.port, 9090)                  # ambiente real vence
        self.assertEqual(cfg.secret_key, CHAVE_BOA)       # veio do .env

    def test_env_explicito_ignora_arquivo_e_ambiente(self):
        caminho = self.escrever(f"XBOT_SECRET_KEY={CHAVE_BOA}\n")
        with mock.patch.dict(os.environ, {"XBOT_SECRET_KEY": CHAVE_BOA}, clear=True):
            with self.assertRaises(ConfigError):
                Config.from_env(env(), dotenv_path=caminho)       # dicionário explícito = só ele


class FuncaoMainETest(unittest.TestCase):
    """main() — o que `python app.py` faz — sem subir o servidor de verdade."""

    def rodar_main(self, ambiente: dict, banco_pronto: bool = False):
        import app as xbot_app

        if banco_pronto:        # evita refazer o seed (lento) a cada teste
            shutil.copyfile(banco_modelo(), ambiente["XBOT_DB_PATH"])
        saida = io.StringIO()
        with mock.patch.dict(os.environ, ambiente, clear=True), \
                mock.patch.object(config, "carregar_dotenv", return_value={}), \
                mock.patch("flask.Flask.run") as executar, \
                mock.patch("logging.basicConfig"), \
                contextlib.redirect_stderr(saida):
            codigo = xbot_app.main()
        return codigo, saida.getvalue(), executar

    def test_sem_chave_em_producao_nao_inicia_e_explica(self):
        codigo, erro, executar = self.rodar_main({"XBOT_DB_PATH": os.path.join(PASTA_TEMP, "m1.db")})
        self.assertEqual(codigo, 2)
        self.assertIn("XBOT_SECRET_KEY", erro)
        self.assertIn("secrets.token_hex", erro)
        executar.assert_not_called()
        self.assertFalse(os.path.exists(os.path.join(PASTA_TEMP, "m1.db")))   # nem tocou no banco

    def test_producao_na_rede_recusa_o_servidor_de_desenvolvimento(self):
        codigo, erro, executar = self.rodar_main({
            "XBOT_SECRET_KEY": CHAVE_BOA, "XBOT_HOST": "0.0.0.0",
            "XBOT_DB_PATH": os.path.join(PASTA_TEMP, "m2.db"),
        })
        self.assertEqual(codigo, 2)
        self.assertIn("waitress", erro)
        executar.assert_not_called()
        self.assertFalse(os.path.exists(os.path.join(PASTA_TEMP, "m2.db")))

    def test_producao_local_roda_sem_debug_e_sem_recarregador(self):
        banco_tmp = os.path.join(PASTA_TEMP, "m3.db")
        codigo, _erro, executar = self.rodar_main(
            {"XBOT_SECRET_KEY": CHAVE_BOA, "XBOT_DB_PATH": banco_tmp}, banco_pronto=True)
        self.assertEqual(codigo, 0)
        executar.assert_called_once()
        kwargs = executar.call_args.kwargs
        self.assertEqual(kwargs["host"], "127.0.0.1")
        self.assertIs(kwargs["debug"], False)
        self.assertIs(kwargs["use_reloader"], False)

    def test_desenvolvimento_local_liga_debug(self):
        codigo, _erro, executar = self.rodar_main({
            "XBOT_ENV": "development", "XBOT_DB_PATH": os.path.join(PASTA_TEMP, "m4.db"),
        })
        self.assertEqual(codigo, 0)
        kwargs = executar.call_args.kwargs
        self.assertEqual(kwargs["host"], "127.0.0.1")
        self.assertIs(kwargs["debug"], True)

    def test_desenvolvimento_na_rede_nunca_liga_debug(self):
        codigo, _erro, executar = self.rodar_main({
            "XBOT_ENV": "development", "XBOT_HOST": "0.0.0.0",
            "XBOT_DB_PATH": os.path.join(PASTA_TEMP, "m5.db"),
        }, banco_pronto=True)
        self.assertEqual(codigo, 0)
        self.assertIs(executar.call_args.kwargs["debug"], False)


class ReloaderTest(unittest.TestCase):
    def test_deve_inicializar(self):
        import app as xbot_app

        dev = ler(XBOT_ENV="development")                  # debug=True → recarregador ligado
        prod = ler(XBOT_SECRET_KEY=CHAVE_BOA)
        # processo "pai" do recarregador: só vigia arquivos, não inicializa
        self.assertFalse(xbot_app.deve_inicializar(dev, environ={}))
        # processo "filho" (o que atende): inicializa
        self.assertTrue(xbot_app.deve_inicializar(dev, environ={"WERKZEUG_RUN_MAIN": "true"}))
        # sem recarregador: sempre inicializa
        self.assertTrue(xbot_app.deve_inicializar(prod, environ={}))

    def test_chave_temporaria_de_desenvolvimento_vai_para_o_processo_filho(self):
        """O recarregador reexecuta o script: o filho precisa herdar a MESMA chave temporária."""
        import app as xbot_app

        saida = io.StringIO()
        ambiente = {"XBOT_ENV": "development", "XBOT_DB_PATH": os.path.join(PASTA_TEMP, "r1.db")}
        with mock.patch.dict(os.environ, ambiente, clear=True), \
                mock.patch.object(config, "carregar_dotenv", return_value={}), \
                mock.patch("flask.Flask.run"), mock.patch("logging.basicConfig"), \
                contextlib.redirect_stderr(saida):
            xbot_app.main()
            self.assertGreaterEqual(len(os.environ.get("XBOT_SECRET_KEY", "")), 32)


if __name__ == "__main__":
    unittest.main()
