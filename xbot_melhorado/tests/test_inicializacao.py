"""Inicialização única, seeds não destrutivos e preservação dos dados existentes (usuários e conhecimento)."""

import hashlib
import os
import shutil
import sqlite3
import tempfile
import unittest
from unittest import mock

from werkzeug.security import generate_password_hash

import app as xbot_app
from database import db as banco
from database.bootstrap import inicializar_banco

from . import PASTA_TEMP
from .base import SENHA_BOA, Cliente, banco_modelo, config_de_teste, RelogioFalso


class BancoTemporarioBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(dir=PASTA_TEMP)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.caminho = os.path.join(self.tmp, "t.db")
        banco.configurar_caminho(self.caminho)
        self.addCleanup(banco.configurar_caminho, None)

    def consulta(self, sql, params=()):
        with banco.get_connection() as conn:
            return [tuple(linha) for linha in conn.execute(sql, params).fetchall()]

    def copiar_modelo(self):
        shutil.copyfile(banco_modelo(), self.caminho)

    def foto_conhecimento(self):
        """Todas as linhas de knowledge, em ordem estável (para comparar antes/depois)."""
        return self.consulta("SELECT id, titulo, categoria, palavras_chave, conteudo, fonte FROM knowledge ORDER BY id")


class SeedUmaVezTest(BancoTemporarioBase):
    def test_banco_novo_e_semeado_e_a_segunda_inicializacao_nao_faz_nada(self):
        primeira = inicializar_banco()
        self.assertTrue(primeira["semeado"])
        self.assertGreater(primeira["registros"], 40)
        foto = self.foto_conhecimento()

        with mock.patch("database.seed.run_seed") as seed, \
                mock.patch("database.apostilas_seed.run_apostilas_seed") as apostilas:
            segunda = inicializar_banco()
            terceira = inicializar_banco()
        seed.assert_not_called()
        apostilas.assert_not_called()
        self.assertFalse(segunda["semeado"])
        self.assertFalse(terceira["semeado"])
        self.assertEqual(segunda["registros"], primeira["registros"])
        self.assertEqual(self.foto_conhecimento(), foto)

    def test_cada_create_app_em_banco_populado_nao_semeia(self):
        self.copiar_modelo()
        antes = self.foto_conhecimento()
        cfg = config_de_teste(self.caminho)
        with mock.patch("database.seed.run_seed") as seed, \
                mock.patch("database.apostilas_seed.run_apostilas_seed") as apostilas:
            xbot_app.create_app(cfg)
            xbot_app.create_app(cfg)
        seed.assert_not_called()
        apostilas.assert_not_called()
        self.assertEqual(self.foto_conhecimento(), antes)

    def test_edicoes_manuais_sobrevivem_ao_reinicio(self):
        """O bug de antes: a cada início o seed das apostilas reescrevia palavras-chave já refinadas."""
        self.copiar_modelo()
        with banco.get_connection() as conn:
            conn.execute("UPDATE knowledge SET palavras_chave = 'REFINADO-A-MAO' WHERE LOWER(titulo) = 'html'")
            apagado = conn.execute("SELECT id, titulo FROM knowledge WHERE LOWER(titulo) = 'python basico'").fetchone()
            conn.execute("DELETE FROM knowledge WHERE id = ?", (apagado[0],))
        antes = self.foto_conhecimento()

        cfg = config_de_teste(self.caminho)
        xbot_app.create_app(cfg)          # "reinício" do servidor
        xbot_app.create_app(cfg)

        depois = self.foto_conhecimento()
        self.assertEqual(depois, antes)                                       # nada mudou
        self.assertEqual(self.consulta("SELECT palavras_chave FROM knowledge WHERE LOWER(titulo)='html'")[0][0],
                         "REFINADO-A-MAO")
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM knowledge WHERE LOWER(titulo)='python basico'")[0][0], 0)

    def test_tabela_knowledge_vazia_mas_com_usuarios_semeia_sem_tocar_nos_usuarios(self):
        banco.init_db()
        from database.auth import init_auth_db

        init_auth_db()
        with banco.get_connection() as conn:
            conn.execute("INSERT INTO users (nome, email, senha_hash) VALUES (?, ?, ?)",
                         ("Existente", "existente@example.com", generate_password_hash("abc123", method="pbkdf2:sha256")))
        resumo = inicializar_banco()
        self.assertTrue(resumo["semeado"])
        self.assertEqual(resumo["usuarios"], 1)
        self.assertEqual(self.consulta("SELECT email FROM users"), [("existente@example.com",)])

    def test_banco_ilegivel_nao_e_tratado_como_vazio(self):
        """Contagem estrita: um arquivo corrompido faz o início FALHAR, em vez de semear por cima."""
        lixo = b"isto nao e um banco sqlite " * 40
        with open(self.caminho, "wb") as arquivo:
            arquivo.write(lixo)
        with self.assertRaises(sqlite3.DatabaseError):
            inicializar_banco()
        with open(self.caminho, "rb") as arquivo:
            self.assertEqual(arquivo.read(), lixo)                           # arquivo intacto


class DadosExistentesTest(BancoTemporarioBase):
    """Um banco no formato do que acompanha o projeto (só knowledge + users) é atualizado sem perdas."""

    def setUp(self):
        super().setUp()
        self.copiar_modelo()
        with banco.get_connection() as conn:
            conn.execute("DROP TABLE visitantes")
            conn.execute("DROP TABLE auth_tentativas")
            conn.execute("INSERT INTO users (nome, email, senha_hash) VALUES (?, ?, ?)",
                         ("Maria Antiga", "maria@example.com", generate_password_hash("abc123", method="pbkdf2:sha256")))
            conn.execute("INSERT INTO users (nome, email, senha_hash) VALUES (?, ?, ?)",
                         ("João Antigo", "joao@example.com", generate_password_hash(SENHA_BOA, method="pbkdf2:sha256")))
        self.usuarios_antes = self.consulta("SELECT id, nome, email, senha_hash, criado_em FROM users ORDER BY id")
        self.conhecimento_antes = self.foto_conhecimento()

    def test_inicializar_so_acrescenta_tabelas(self):
        self.assertNotIn("visitantes", [t[0] for t in self.consulta("SELECT name FROM sqlite_master WHERE type='table'")])
        xbot_app.create_app(config_de_teste(self.caminho))
        tabelas = {t[0] for t in self.consulta("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"knowledge", "users", "visitantes", "auth_tentativas"} <= tabelas)
        self.assertEqual(self.consulta("SELECT id, nome, email, senha_hash, criado_em FROM users ORDER BY id"),
                         self.usuarios_antes)
        self.assertEqual(self.foto_conhecimento(), self.conhecimento_antes)

    def test_esquema_da_tabela_users_nao_muda(self):
        antes = self.consulta("PRAGMA table_info(users)")
        xbot_app.create_app(config_de_teste(self.caminho))
        self.assertEqual(self.consulta("PRAGMA table_info(users)"), antes)
        self.assertEqual([c[1] for c in antes], ["id", "nome", "email", "senha_hash", "criado_em"])

    def test_contas_antigas_continuam_entrando_inclusive_com_senha_curta(self):
        relogio = RelogioFalso()
        with mock.patch("relogio.agora", relogio.agora):
            app = xbot_app.create_app(config_de_teste(self.caminho))
            c = Cliente(app)
            r = c.login("maria@example.com", "abc123")                       # senha de 6 caracteres, política antiga
            self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
            self.assertEqual(r.get_json()["usuario"]["nome"], "Maria Antiga")
            c2 = Cliente(app, ip="192.0.2.50")
            self.assertEqual(c2.login("joao@example.com", SENHA_BOA).status_code, 200)

    def test_novos_cadastros_recebem_ids_seguintes(self):
        relogio = RelogioFalso()
        with mock.patch("relogio.agora", relogio.agora):
            app = xbot_app.create_app(config_de_teste(self.caminho))
            r = Cliente(app).registrar("Nova Pessoa", "nova@example.com", "Frase-Segura_Zeta#55")
        self.assertEqual(r.get_json()["usuario"]["id"], 3)


class SemInicializarTest(BancoTemporarioBase):
    def test_create_app_sem_inicializar_nao_cria_nem_toca_no_banco(self):
        """É o que o processo 'pai' do recarregador faz: só vigia arquivos."""
        cfg = config_de_teste(self.caminho)
        xbot_app.create_app(cfg, inicializar=False)
        self.assertFalse(os.path.exists(self.caminho))

    def test_importar_o_modulo_nao_cria_app_nem_banco(self):
        import subprocess
        import sys

        from . import RAIZ

        ambiente = {k: v for k, v in os.environ.items() if not k.startswith("XBOT_")}
        ambiente["XBOT_DB_PATH"] = os.path.join(self.tmp, "nao_deve_existir.db")
        resultado = subprocess.run(
            [sys.executable, "-c", "import app, app_improved; print('importou')"],
            cwd=RAIZ, env=ambiente, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("importou", resultado.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "nao_deve_existir.db")))


class ScriptsDeSeedManuaisTest(BancoTemporarioBase):
    """database/seed.py e database/apostilas_seed.py recusam rodar em banco já populado (sem --forcar)."""

    def rodar(self, script, *args):
        import subprocess
        import sys

        from . import RAIZ

        ambiente = {k: v for k, v in os.environ.items() if not k.startswith("XBOT_")}
        ambiente["XBOT_DB_PATH"] = self.caminho
        ambiente["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run([sys.executable, os.path.join(RAIZ, "database", script), *args],
                              cwd=RAIZ, env=ambiente, capture_output=True, text=True, timeout=120)

    def hash_banco(self):
        with open(self.caminho, "rb") as arquivo:
            return hashlib.sha256(arquivo.read()).hexdigest()

    def test_recusam_banco_populado(self):
        self.copiar_modelo()
        antes = self.hash_banco()
        for script in ("seed.py", "apostilas_seed.py"):
            with self.subTest(script=script):
                r = self.rodar(script)
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn("--forcar", r.stdout)
                self.assertEqual(self.hash_banco(), antes)                   # nem um byte mudou
        self.assertEqual(os.listdir(self.tmp), ["t.db"])                    # e nenhum backup foi criado à toa

    def test_com_forcar_faz_backup_antes(self):
        self.copiar_modelo()
        r = self.rodar("apostilas_seed.py", "--forcar")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        backups = [n for n in os.listdir(self.tmp) if n.endswith(".bak")]
        self.assertEqual(len(backups), 1)
        self.assertIn("antes-das-apostilas", backups[0])

    def test_aceitam_banco_novo(self):
        r = self.rodar("seed.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertGreater(self.consulta("SELECT COUNT(*) FROM knowledge")[0][0], 40)


class ReparoOpcionalTest(BancoTemporarioBase):
    """database/reparar_refinamento.py: mostra por padrão; só altera com --aplicar (e com backup)."""

    def rodar(self, *args):
        import subprocess
        import sys

        from . import RAIZ

        ambiente = {k: v for k, v in os.environ.items() if not k.startswith("XBOT_")}
        ambiente["XBOT_DB_PATH"] = self.caminho
        ambiente["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run([sys.executable, os.path.join(RAIZ, "database", "reparar_refinamento.py"), *args],
                              cwd=RAIZ, env=ambiente, capture_output=True, text=True, timeout=120)

    def estragar(self):
        """Reproduz o que o seed a cada início fazia com o banco refinado."""
        with banco.get_connection() as conn:
            conn.execute("UPDATE knowledge SET palavras_chave = 'das,apostilas' WHERE LOWER(titulo) = 'html'")
            conn.execute("INSERT INTO knowledge (titulo, categoria, palavras_chave, conteudo, fonte) "
                         "VALUES ('protocolos e topologias de rede', 'redes', 'x', 'y', 'apostila_redes')")
            conn.execute("INSERT INTO knowledge (titulo, categoria, palavras_chave, conteudo, fonte) "
                         "VALUES ('redes protocolos e dispositivos', 'redes', 'x', 'y', 'refine')")

    def test_mostrar_nao_altera_nada(self):
        shutil.copyfile(banco_modelo(), self.caminho)
        self.estragar()
        with open(self.caminho, "rb") as arquivo:
            antes = hashlib.sha256(arquivo.read()).hexdigest()
        r = self.rodar()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("restaurar as palavras-chave", r.stdout)
        self.assertIn("remover duplicata", r.stdout)
        with open(self.caminho, "rb") as arquivo:
            self.assertEqual(hashlib.sha256(arquivo.read()).hexdigest(), antes)
        self.assertEqual(os.listdir(self.tmp), ["t.db"])

    def test_aplicar_faz_backup_e_corrige_so_o_necessario(self):
        shutil.copyfile(banco_modelo(), self.caminho)
        self.estragar()
        refinados = "('html', 'python basico', 'design digital')"
        outros_antes = self.consulta(
            f"SELECT id, titulo, palavras_chave FROM knowledge WHERE LOWER(titulo) NOT IN {refinados} "
            "AND LOWER(titulo) <> 'protocolos e topologias de rede' ORDER BY id")
        r = self.rodar("--aplicar")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len([n for n in os.listdir(self.tmp) if n.endswith(".bak")]), 1)
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM knowledge WHERE LOWER(titulo)='protocolos e topologias de rede'")[0][0], 0)
        self.assertNotEqual(self.consulta("SELECT palavras_chave FROM knowledge WHERE LOWER(titulo)='html'")[0][0], "das,apostilas")
        outros_depois = self.consulta(
            f"SELECT id, titulo, palavras_chave FROM knowledge WHERE LOWER(titulo) NOT IN {refinados} "
            "AND LOWER(titulo) <> 'protocolos e topologias de rede' ORDER BY id")
        self.assertEqual(outros_depois, outros_antes)
        # rodar de novo: nada a fazer
        self.assertIn("Nada a corrigir", self.rodar().stdout)

    def test_nao_remove_a_duplicata_sem_o_registro_que_a_absorveu(self):
        shutil.copyfile(banco_modelo(), self.caminho)
        contagem = "SELECT COUNT(*) FROM knowledge WHERE LOWER(titulo)='protocolos e topologias de rede'"
        with banco.get_connection() as conn:
            conn.execute("INSERT INTO knowledge (titulo, categoria, palavras_chave, conteudo, fonte) "
                         "VALUES ('protocolos e topologias de rede', 'redes', 'x', 'y', 'apostila_redes')")
        antes = self.consulta(contagem)[0][0]
        self.assertEqual(self.consulta(
            "SELECT COUNT(*) FROM knowledge WHERE LOWER(titulo)='redes protocolos e dispositivos'")[0][0], 0)
        self.rodar("--aplicar")
        self.assertEqual(self.consulta(contagem)[0][0], antes)        # sem o registro que absorveu: não apaga nada


if __name__ == "__main__":
    unittest.main()
