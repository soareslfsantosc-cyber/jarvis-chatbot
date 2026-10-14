"""
database/reparar_refinamento.py — reparo OPCIONAL do conhecimento refinado
XBot v0.3.0 Beta

Por que existe
--------------
Até esta versão o servidor executava `run_apostilas_seed()` a CADA início. No modo "update" esse
seed reescreve as palavras-chave de registros que já tinham sido refinados à mão e reinsere um
tópico que a auditoria havia apagado de propósito. Se o seu banco rodou em versões antigas, ele
pode estar assim:

  * `html`, `python basico` e `design digital` com as palavras-chave das apostilas (não as refinadas);
  * `protocolos e topologias de rede` de volta (duplicata de `redes protocolos e dispositivos`).

O que faz
---------
  python database/reparar_refinamento.py             # SÓ MOSTRA o que mudaria (não altera nada)
  python database/reparar_refinamento.py --aplicar   # faz um backup do banco e aplica a correção

  * restaura as palavras-chave dos 3 registros refinados (valores do banco refinado do pacote);
  * remove a duplicata ressuscitada, e só se o registro que absorveu o conteúdo dela existir.

Não toca em nenhum outro registro, nem em usuários. Usa o banco de XBOT_DB_PATH (ou o xbot.db padrão).
"""

import os
import sqlite3
import sys

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from config import carregar_dotenv, DOTENV_PADRAO  # noqa: E402
from database import db  # noqa: E402

# Palavras-chave refinadas (as do banco que acompanhava o projeto: 86 registros).
PALAVRAS_CHAVE_REFINADAS = {
    'html': 'hipertext,markup,linguagem,elemento,html5,w3c,whatwg,hypertext markup,linguagem marcacao,pagina web,estrutura web,tag html',
    'python basico': 'python,guido van rossum,1991,variável,tipo,if,for,while,função,def,indentação,alto nível,introducao python,python iniciante,o que e python,linguagem python basica,aprender python,python overview,python geral',
    'design digital': 'design,digital,vetor,raster,pixel,rgb,cmyk,tipografia,ui,ux,cores,composição,design grafico,ui design,ux design,composicao visual,user experience,user interface',
}

# Duplicata apagada de propósito na auditoria (audit_fix.py, fase 1) e o registro que a absorveu.
DUPLICATA_APAGADA = ('protocolos e topologias de rede', 'apostila_redes')
REGISTRO_QUE_ABSORVEU = 'redes protocolos e dispositivos'


def planejar(conn) -> list:
    """Lista de correções: ('atualizar', id, titulo, novas_palavras) ou ('apagar', id, titulo, None)."""
    plano = []

    for titulo, esperado in PALAVRAS_CHAVE_REFINADAS.items():
        linhas = conn.execute(
            "SELECT id, palavras_chave FROM knowledge WHERE LOWER(titulo) = ?", (titulo,)
        ).fetchall()
        if len(linhas) != 1:
            print(f"  [pulado] '{titulo}': esperado 1 registro, encontrado {len(linhas)}")
            continue
        registro_id, atuais = linhas[0]
        if atuais != esperado:
            plano.append(("atualizar", registro_id, titulo, esperado))

    titulo_dup, fonte_dup = DUPLICATA_APAGADA
    existe_absorvedor = conn.execute(
        "SELECT 1 FROM knowledge WHERE LOWER(titulo) = ?", (REGISTRO_QUE_ABSORVEU,)
    ).fetchone()
    if existe_absorvedor:
        for registro_id, in conn.execute(
            "SELECT id FROM knowledge WHERE LOWER(titulo) = ? AND fonte = ?", (titulo_dup, fonte_dup)
        ).fetchall():
            plano.append(("apagar", registro_id, titulo_dup, None))
    return plano


def main(argv) -> int:
    aplicar = "--aplicar" in argv[1:]

    # mesmo critério de banco do servidor: XBOT_DB_PATH do ambiente ou do arquivo .env
    caminho_env = os.environ.get("XBOT_DB_PATH") or carregar_dotenv(DOTENV_PADRAO).get("XBOT_DB_PATH")
    if caminho_env:
        db.configurar_caminho(caminho_env)
    caminho = db.caminho_banco()
    if not os.path.isfile(caminho):
        print(f"Banco não encontrado: {caminho}\nNada a reparar.")
        return 1

    print(f"Banco: {caminho}")
    # leitura somente-leitura para planejar: o modo "mostrar" não consegue alterar nada
    uri = "file:" + caminho.replace("\\", "/").replace("?", "%3f").replace("#", "%23") + "?mode=ro"
    try:
        leitura = sqlite3.connect(uri, uri=True, timeout=10)
    except sqlite3.Error as erro:
        print(f"Não foi possível abrir o banco: {erro}")
        return 1
    try:
        total = leitura.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        plano = planejar(leitura)
    except sqlite3.Error as erro:
        print(f"Não foi possível ler a tabela knowledge: {erro}")
        return 1
    finally:
        leitura.close()

    print(f"Registros de conhecimento: {total}")
    if not plano:
        print("\nNada a corrigir: o conhecimento refinado está íntegro.")
        return 0

    print("\nCorreções necessárias:")
    for acao, registro_id, titulo, _novo in plano:
        if acao == "atualizar":
            print(f"  - id {registro_id} '{titulo}': restaurar as palavras-chave refinadas")
        else:
            print(f"  - id {registro_id} '{titulo}': remover duplicata (o conteúdo já está em '{REGISTRO_QUE_ABSORVEU}')")

    if not aplicar:
        print("\nNada foi alterado. Para aplicar (com backup automático):")
        print("    python database/reparar_refinamento.py --aplicar")
        return 0

    backup = db.fazer_backup("pre-reparo")
    print(f"\nBackup criado: {backup}")
    with db.get_connection() as conn:               # uma transação só: tudo ou nada
        for acao, registro_id, _titulo, novo in plano:
            if acao == "atualizar":
                conn.execute("UPDATE knowledge SET palavras_chave = ? WHERE id = ?", (novo, registro_id))
            else:
                conn.execute("DELETE FROM knowledge WHERE id = ?", (registro_id,))
    print(f"Correções aplicadas: {len(plano)}. (Reinicie o servidor para ele recarregar o conhecimento.)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
