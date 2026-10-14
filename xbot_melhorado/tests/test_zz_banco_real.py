"""
Último teste da suíte (o "zz" no nome o deixa por último na ordem alfabética do `discover`):
o xbot.db REAL — o seu banco de verdade, se existir — não pode ter sido tocado por nenhum teste.
"""

import glob
import os
import unittest

from database import db as banco

from . import ASSINATURA_BANCO_REAL_INICIAL, BANCO_REAL, PASTA_TEMP, assinatura_arquivo


class BancoRealIntactoTest(unittest.TestCase):
    def test_xbot_db_real_nao_mudou_durante_os_testes(self):
        self.assertEqual(
            assinatura_arquivo(BANCO_REAL), ASSINATURA_BANCO_REAL_INICIAL,
            "O xbot.db real foi criado, apagado ou modificado durante a suíte de testes!",
        )

    def test_nao_surgiram_arquivos_auxiliares_ao_lado_do_banco_real(self):
        if ASSINATURA_BANCO_REAL_INICIAL is None:
            self.assertFalse(os.path.exists(BANCO_REAL), "um xbot.db apareceu durante os testes")
        for sufixo in ("-journal", "-wal", "-shm"):
            self.assertFalse(os.path.exists(BANCO_REAL + sufixo), sufixo)
        self.assertEqual(glob.glob(BANCO_REAL + ".*.bak"), [], "backup inesperado ao lado do banco real")

    def test_o_banco_padrao_dos_testes_e_temporario(self):
        caminho = os.path.abspath(os.environ["XBOT_DB_PATH"])
        self.assertEqual(os.path.commonpath([caminho, PASTA_TEMP]), PASTA_TEMP)
        # nenhum teste deixa um banco "configurado" para trás; e o caminho de reserva também é temporário
        self.assertIsNone(banco._caminho_ativo)
        self.assertNotEqual(os.path.abspath(banco.caminho_banco()), os.path.abspath(BANCO_REAL))


if __name__ == "__main__":
    unittest.main()
