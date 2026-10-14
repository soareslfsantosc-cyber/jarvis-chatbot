"""
database/seed.py
XBot v0.3.0 Beta — Importador de Dados para SQLite
XByte Games Studios

Responsabilidade:
  Migrar os dados das bases de conhecimento Python (knowledge_base.py,
  knowledge_base_extended.py e os dados internos do app.py) para a tabela
  'knowledge' do SQLite.

Segurança:
  Pode ser executado MÚLTIPLAS VEZES sem duplicar dados.
  Estratégia: antes de cada INSERT, verifica se o titulo já existe no banco.

Uso:
  # Executar manualmente pela linha de comando:
  python database/seed.py

  # Ou importar e chamar programaticamente (sem circular import):
  from database.seed import run_seed
  encontrados, inseridos, duplicados = run_seed()

Fontes importadas (em ordem):
  1. conhecimento_arquitetura do app.py   → 23 registros base
  2. KNOWLEDGE_BASE de knowledge_base.py  → 17 registros (3 duplicatas esperadas)
  3. KNOWLEDGE_BASE_EXTENDED              → 10 registros novos
  Total esperado: 50 encontrados / 47 inseridos / 3 duplicados
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Garantir que a pasta raiz do projeto está no sys.path.
# Isso permite importar database.db, knowledge_base e knowledge_base_extended
# quando seed.py é executado diretamente como script (python database/seed.py).
# ---------------------------------------------------------------------------
_SEED_DIR = os.path.dirname(os.path.abspath(__file__))      # .../database/
_ROOT_DIR = os.path.dirname(_SEED_DIR)                       # .../xbot_melhorado/
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from database.db import get_connection, init_db, contar_registros, contar_conhecimento, fazer_backup


# ===========================================================================
# FONTE 1 — Conhecimento interno do app.py (conhecimento_arquitetura)
#
# Definidos diretamente aqui para evitar importar app.py (que inicializaria
# Flask, rotas etc.) e criar dependência circular futura.
#
# As palavras_chave incluem os sinônimos usados no método
# buscar_conhecimento_arquitetura() do app.py, garantindo que o SQLite cubra
# os mesmos termos que a lógica Python original.
# ===========================================================================

_DADOS_APP = [
    (
        "sistema computacional",
        "arquitetura_computadores",
        "sistema computacional,hardware,software,computador,eletrônico,dispositivos",
        "Um sistema computacional consiste em um conjunto de dispositivos "
        "eletrônicos, denominado hardware, capazes de processar informações de "
        "acordo com um programa, denominado software. Os componentes principais "
        "são hardware e software.",
        "app.py"
    ),
    (
        "hardware",
        "hardware",
        "hardware,físico,componentes,cpu,memória,processador,parte física",
        "Hardware é a parte física de computadores e outros sistemas "
        "microeletrônicos, incluindo CPU, memória e dispositivos de entrada e "
        "saída. É um termo geral que se refere aos componentes físicos dos "
        "computadores.",
        "app.py"
    ),
    (
        "software",
        "software",
        "software,programa,instrução,código,lógico,linguagem,aplicativo",
        "Software é a parte lógica, o conjunto de instruções e dados processados "
        "pelos circuitos eletrônicos do hardware. É a camada que torna o "
        "computador útil para o ser humano. O termo foi criado na década de 1940 "
        "como um trocadilho com 'hardware'.",
        "app.py"
    ),
    (
        "programa de computador",
        "software",
        "programa,computador,instrução,sequência,linguagem de máquina,código de máquina",
        "Um programa de computador é composto por uma sequência de instruções, "
        "que podem ser em linguagem natural ou codificada, interpretada e "
        "executada por um processador ou máquina virtual. Quando está em "
        "linguagem de máquina, pode ser executado diretamente pelo processador.",
        "app.py"
    ),
    (
        "linguagens de programação",
        "software",
        "linguagem,programação,java,c++,python,javascript,visual basic,php,código",
        "Programas são geralmente escritos em linguagens de programação como "
        "Java, Visual Basic, C, C++, PHP, Python, JavaScript, que se aproximam "
        "das linguagens humanas. Raramente se usa linguagem de máquina "
        "diretamente.",
        "app.py"
    ),
    (
        "classes de software",
        "software",
        "classes,software,sistema,embarcado,aplicativo,programação,firmware,driver",
        "As principais classes são: Software de Sistema (firmware, drivers, SO), "
        "Software Embarcado (para máquinas específicas), Software Aplicativo "
        "(tarefas específicas do usuário) e Software de Programação (ferramentas "
        "para desenvolvedores).",
        "app.py"
    ),
    (
        "licenciamento",
        "software",
        "licença,licenciamento,software,uso,propriedade,pirataria,temporária,perpétua",
        "Uma licença de software define e restringe como se pode utilizar o "
        "software. Tipos incluem: temporárias, permanentes, por quantidade de "
        "uso, de rede/virtuais, perpétuas, do tipo chaves e hard lock. Software "
        "não licenciado pode causar problemas legais e de desempenho.",
        "app.py"
    ),
    (
        "categorias de software",
        "software",
        "categorias,software,proprietário,freeware,shareware,open source,domínio público,adware",
        "Software Proprietário (uso restrito), Domínio Público (gratuito, sem "
        "direitos autorais), Adware (com publicidade), Freeware (gratuito), "
        "Shareware (teste gratuito, depois pago), Código Aberto (open source).",
        "app.py"
    ),
    (
        "von neumann",
        "arquitetura_computadores",
        "von neumann,modelo,memória,ula,uc,cpu,arquitetura,unidade de controle,aritmética",
        "John Von Neumann propôs o modelo fundamental dos computadores modernos, "
        "composto por: memória física (para programas e dados), Unidade "
        "Aritmética e Lógica (ULA), Unidade de Controle (UC) e equipamentos de "
        "entrada e saída. A ULA e UC formam a CPU.",
        "app.py"
    ),
    (
        "gerações de computadores",
        "historia_computacao",
        "gerações,computadores,história,válvulas,transistores,circuitos integrados,microprocessadores,evolução",
        "Geração Zero (1645-1945): computadores mecânicos. Primeira Geração "
        "(1945-1955): válvulas eletrônicas. Segunda Geração (1955-1965): "
        "transistores. Terceira Geração (1965-1980): circuitos integrados. "
        "Quarta Geração (1970-atualidade): microprocessadores. Quinta Geração "
        "(atual): IA e computação quântica.",
        "app.py"
    ),
    (
        "primeira geração",
        "historia_computacao",
        "primeira geração,válvula,valvula,válvulas,eniac,1945,1955,cartão perfurado,relé",
        "Computadores com válvulas eletrônicas (1945-1955). Exemplo: ENIAC com "
        "19.000 válvulas, pesava 30 toneladas, consumia 200 quilowatts. Entrada "
        "de dados por cartões perfurados. Problemas: queima frequente de "
        "válvulas, alto consumo de energia.",
        "app.py"
    ),
    (
        "segunda geração",
        "historia_computacao",
        "segunda geração,transistor,bell labs,1955,1965,válvula substituída",
        "Transistores substituíram válvulas (1955-1965). Transistor desenvolvido "
        "pela Bell Labs em 1948. Vantagens: 1/200 do tamanho de uma válvula, "
        "consumo 1/100 da energia, mais confiável, aquecimento mínimo.",
        "app.py"
    ),
    (
        "terceira geração",
        "historia_computacao",
        "terceira geração,circuito integrado,ci,ibm 360,1965,1980,chip,transistores integrados",
        "Circuitos Integrados (1965-1980). CIs incorporam inúmeros transistores "
        "em um único chip. Vantagens: maior confiabilidade, muito menores, baixo "
        "consumo, custo menor. Exemplo: IBM 360 realizava 2 milhões de adições "
        "por segundo.",
        "app.py"
    ),
    (
        "quarta geração",
        "historia_computacao",
        "quarta geração,microprocessador,intel,1970,pentium,litografia,miniaturização",
        "Microprocessadores (1970-atualidade). Intel lançou o primeiro "
        "microprocessador em 1970, concentrando CPU, controladores de memória "
        "e E/S. Evolução da miniaturização com técnicas como litografia. Intel "
        "Pentium foi revolucionário nos anos 90.",
        "app.py"
    ),
    (
        "quinta geração",
        "historia_computacao",
        "quinta geração,ia,inteligência artificial,quântico,iot,nuvem,atual,computação em nuvem",
        "Era atual da computação, caracterizada por: Inteligência Artificial, "
        "computação quântica, nanotecnologia, Internet das Coisas (IoT), "
        "computação em nuvem, processamento paralelo massivo e interfaces "
        "naturais de usuário.",
        "app.py"
    ),
    (
        "litografia",
        "hardware",
        "litografia,nanômetros,nanometro,transistor,chip,processador,miniaturização,3nm",
        "Técnica de construção dos componentes internos do processador que "
        "permite colocar milhares de transistores em um chip pequeno. Refere-se "
        "ao tamanho de cada transistor, medido em nanômetros (bilionésima parte "
        "do metro). Atualmente temos processos de 3nm.",
        "app.py"
    ),
    (
        "futuro da tecnologia",
        "futuro_tecnologia",
        "futuro,nanotecnologia,computador óptico,óptico,optico,quântico,quantico,qubits",
        "Nanotecnologia permite miniaturização extrema. Computadores ópticos "
        "usam feixes de luz em cubos ópticos. Computadores quânticos usam átomos "
        "como transistores, com unidades de informação que podem assumir qualquer "
        "valor entre 0 e 1 (qubits).",
        "app.py"
    ),
    (
        "dispositivos entrada saída",
        "hardware",
        "dispositivos,entrada,saída,teclado,mouse,monitor,impressora,pen drive,webcam,hd externo",
        "Elementos de interface entre usuário e computador. Funções: "
        "receber/enviar informações ao meio exterior e converter informações para "
        "forma inteligível. Categorias: entrada (teclado, mouse), saída "
        "(monitor, impressora), entrada e saída (pen drive, HD externo).",
        "app.py"
    ),
    (
        "cpu",
        "hardware",
        "cpu,processador,ula,uc,núcleo,unidade central de processamento,registrador",
        "Unidade Central de Processamento, formada pela ULA (Unidade Aritmética "
        "e Lógica) e UC (Unidade de Controle), junto com registradores. É "
        "responsável por buscar instruções na memória e executá-las. Modernas "
        "CPUs têm múltiplos núcleos.",
        "app.py"
    ),
    (
        "memória",
        "hardware",
        "memória,ram,rom,cache,armazenamento,binário,volátil,não volátil",
        "Armazena programas e dados em formato binário (0s e 1s). A CPU busca "
        "instruções e dados diretamente da memória para processamento. Tipos: "
        "RAM (volátil), ROM (não-volátil), cache (ultra-rápida).",
        "app.py"
    ),
    (
        "transistor",
        "hardware",
        "transistor,silício,germânio,interruptor,eletrônico,válvula,segunda geração",
        "Dispositivo que substituiu as válvulas na segunda geração. Função "
        "básica: interruptor eletrônico para operações lógicas. Materiais: "
        "silício, germânio, gálio e óxidos. Muito menor e mais eficiente que "
        "válvulas. Base de toda eletrônica moderna.",
        "app.py"
    ),
    (
        "inteligencia artificial",
        "ia",
        "ia,inteligência artificial,ai,machine learning,deep learning,nlp,visão computacional",
        "Campo da ciência da computação que busca criar máquinas capazes de "
        "realizar tarefas que normalmente requerem inteligência humana. Inclui "
        "machine learning, deep learning, processamento de linguagem natural e "
        "visão computacional.",
        "app.py"
    ),
    (
        "computacao quantica",
        "futuro_tecnologia",
        "computação quântica,quântico,quantico,qubit,superposição,emaranhamento,quantum",
        "Paradigma de computação que utiliza fenômenos quânticos como "
        "superposição e emaranhamento para processar informações. Qubits podem "
        "existir em múltiplos estados simultaneamente, oferecendo potencial para "
        "resolver problemas complexos exponencialmente mais rápido.",
        "app.py"
    ),
]


# ===========================================================================
# FONTE 2 — knowledge_base.py
# Importado dinamicamente para não duplicar dados.
# ===========================================================================

def _importar_knowledge_base() -> list:
    """
    Lê KNOWLEDGE_BASE de knowledge_base.py e converte para lista de registros.

    Estratégia de conteúdo:
      Combina todos os valores string de cada sub-dicionário com ' | '.
      Ex: {"definicao": "...", "exemplos": "..."} → "definicao: ... | exemplos: ..."

    Retorna lista de tuplas (titulo, categoria, palavras_chave, conteudo, fonte).
    """
    try:
        from knowledge_base import KNOWLEDGE_BASE
    except ImportError:
        logger.warning("[Seed] knowledge_base.py não encontrado. Pulando fonte 2.")
        return []

    # Mapeamento de categoria por tópico
    _CATEGORIAS = {
        "sistemas computacionais": "arquitetura_computadores",
        "hardware":                "hardware",
        "software":                "software",
        "software de sistema":     "software",
        "software embarcado":      "software",
        "software aplicativo":     "software",
        "software de programacao": "software",
        "software como servico":   "software",
        "licenciamento de software": "software",
        "propriedade e licenca":   "software",
        "tempo de validade licenca": "software",
        "vantagens licenciamento": "software",
        "categorias de software":  "software",
        "software sem licenciamento": "software",
        "leis sobre software":     "software",
        "historia e evolucao":     "historia_computacao",
        "dispositivos de entrada e saida": "hardware",
    }

    registros = []
    for topico, conteudo_dict in KNOWLEDGE_BASE.items():
        # Combinar todos os valores string em um único bloco de conteúdo
        partes = []
        for chave, valor in conteudo_dict.items():
            if isinstance(valor, str) and valor.strip():
                partes.append(valor.strip())

        if not partes:
            continue

        conteudo = " | ".join(partes)

        # Palavras-chave: o tópico em si + cada palavra individual
        palavras_set = {topico}
        palavras_set.update(topico.replace("_", " ").split())
        palavras_chave = ",".join(sorted(palavras_set))

        categoria = _CATEGORIAS.get(topico, "geral")

        registros.append((topico, categoria, palavras_chave, conteudo, "knowledge_base.py"))

    return registros


# ===========================================================================
# FONTE 3 — knowledge_base_extended.py (apenas KNOWLEDGE_BASE_EXTENDED)
# QUIZ_QUESTIONS e EXERCICIOS_PRATICOS são ignorados nesta etapa.
# ===========================================================================

def _importar_knowledge_base_extended() -> list:
    """
    Lê KNOWLEDGE_BASE_EXTENDED de knowledge_base_extended.py.
    Ignora QUIZ_QUESTIONS e EXERCICIOS_PRATICOS (estrutura incompatível).

    Retorna lista de tuplas (titulo, categoria, palavras_chave, conteudo, fonte).
    """
    try:
        from knowledge_base_extended import KNOWLEDGE_BASE_EXTENDED
    except ImportError:
        logger.warning("[Seed] knowledge_base_extended.py não encontrado. Pulando fonte 3.")
        return []

    _CATEGORIAS = {
        "html":                "desenvolvimento_web",
        "visual_studio_code":  "desenvolvimento_web",
        "psicologia_cores":    "design",
        "python_basico":       "programacao",
        "python_estruturas":   "programacao",
        "placas_mae_gigabyte": "hardware",
        "programacao_avancada":"programacao",
        "historia_computacao": "historia_computacao",
        "desenvolvimento_web": "desenvolvimento_web",
        "design_digital":      "design",
    }

    registros = []
    for chave_original, conteudo_dict in KNOWLEDGE_BASE_EXTENDED.items():
        # Normalizar o titulo: underscore → espaço
        titulo = chave_original.replace("_", " ").strip()

        partes = []
        for sub_chave, valor in conteudo_dict.items():
            if isinstance(valor, str) and valor.strip():
                partes.append(valor.strip())

        if not partes:
            continue

        conteudo = " | ".join(partes)

        # Palavras-chave incluem: chave original, titulo normalizado, palavras individuais
        palavras_set = {chave_original, titulo}
        palavras_set.update(titulo.split())
        palavras_chave = ",".join(sorted(palavras_set))

        categoria = _CATEGORIAS.get(chave_original, "geral")

        registros.append((titulo, categoria, palavras_chave, conteudo, "knowledge_base_extended.py"))

    return registros


# ===========================================================================
# LÓGICA CENTRAL DE IMPORTAÇÃO
# ===========================================================================

def _carregar_existentes(cursor) -> set:
    """
    Carrega do banco todos os títulos já existentes, normalizados para
    minúsculo. Retorna um set para lookup O(1).
    """
    cursor.execute("SELECT LOWER(titulo) FROM knowledge")
    return {row[0] for row in cursor.fetchall()}


def _inserir_se_novo(cursor,
                     titulo: str,
                     categoria: str,
                     palavras_chave: str,
                     conteudo: str,
                     fonte: str,
                     existentes: set) -> bool:
    """
    Insere um registro se seu título (normalizado) não estiver em `existentes`.
    Atualiza `existentes` in-place quando insere.

    Retorna True se inseriu, False se era duplicado.
    """
    titulo_norm = titulo.lower().strip()

    if titulo_norm in existentes:
        return False   # duplicado — pula

    cursor.execute(
        """
        INSERT INTO knowledge (titulo, categoria, palavras_chave, conteudo, fonte)
        VALUES (?, ?, ?, ?, ?)
        """,
        (titulo, categoria, palavras_chave, conteudo, fonte)
    )
    existentes.add(titulo_norm)
    return True


def run_seed() -> tuple:
    """
    Executa a importação completa das três fontes para o SQLite.

    Garante que o banco e a tabela existam antes de inserir.
    É idempotente: pode ser chamado múltiplas vezes sem duplicar dados.

    Retorna:
        (encontrados, inseridos, duplicados)  — todos inteiros
    """
    # Garantir banco e tabela criados
    init_db()

    encontrados = 0
    inseridos   = 0
    duplicados  = 0

    with get_connection() as conn:
        cursor = conn.cursor()

        # Carregar títulos já existentes UMA VEZ (eficiente)
        existentes = _carregar_existentes(cursor)
        logger.info(f"[Seed] Títulos já no banco antes da importação: {len(existentes)}")

        # ------------------------------------------------------------------
        # FONTE 1 — dados internos do app.py (23 registros)
        # ------------------------------------------------------------------
        logger.info("[Seed] Importando Fonte 1: app.py (conhecimento_arquitetura)...")
        for titulo, categoria, palavras_chave, conteudo, fonte in _DADOS_APP:
            encontrados += 1
            if _inserir_se_novo(cursor, titulo, categoria, palavras_chave, conteudo, fonte, existentes):
                inseridos += 1
                logger.debug(f"  [+] Inserido: {titulo}")
            else:
                duplicados += 1
                logger.debug(f"  [=] Duplicado ignorado: {titulo}")

        # ------------------------------------------------------------------
        # FONTE 2 — knowledge_base.py (17 registros, ~3 duplicatas esperadas)
        # ------------------------------------------------------------------
        logger.info("[Seed] Importando Fonte 2: knowledge_base.py...")
        for registro in _importar_knowledge_base():
            titulo, categoria, palavras_chave, conteudo, fonte = registro
            encontrados += 1
            if _inserir_se_novo(cursor, titulo, categoria, palavras_chave, conteudo, fonte, existentes):
                inseridos += 1
                logger.debug(f"  [+] Inserido: {titulo}")
            else:
                duplicados += 1
                logger.debug(f"  [=] Duplicado ignorado: {titulo}")

        # ------------------------------------------------------------------
        # FONTE 3 — knowledge_base_extended.py (10 registros, 0 duplicatas)
        # ------------------------------------------------------------------
        logger.info("[Seed] Importando Fonte 3: knowledge_base_extended.py...")
        for registro in _importar_knowledge_base_extended():
            titulo, categoria, palavras_chave, conteudo, fonte = registro
            encontrados += 1
            if _inserir_se_novo(cursor, titulo, categoria, palavras_chave, conteudo, fonte, existentes):
                inseridos += 1
                logger.debug(f"  [+] Inserido: {titulo}")
            else:
                duplicados += 1
                logger.debug(f"  [=] Duplicado ignorado: {titulo}")

    logger.info(
        f"[Seed] Concluído — Encontrados: {encontrados} | "
        f"Inseridos: {inseridos} | Duplicados ignorados: {duplicados}"
    )
    return encontrados, inseridos, duplicados


# ===========================================================================
# ENTRY POINT — execução direta como script
# ===========================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s"
    )

    print("=" * 55)
    print("  XBot v0.3.0 Beta — Importador SQLite (seed.py)")
    print("=" * 55)

    # Trava: estes dados já foram refinados à mão (palavras-chave, duplicatas removidas). Reaplicar o
    # seed num banco populado reescreve/reinsere registros. Só com --forcar (e com backup antes).
    init_db()
    total_antes = contar_conhecimento()
    if total_antes > 0:
        if "--forcar" not in sys.argv[1:]:
            print(f"\nO banco já tem {total_antes} registros de conhecimento. {"seed.py"} NÃO foi executado:")
            print("reaplicá-lo pode sobrescrever palavras-chave refinadas e recriar tópicos apagados de propósito.")
            print("O servidor já semeia sozinho um banco NOVO (vazio); você não precisa rodar isto à mão.")
            print("Se realmente quiser reaplicar, rode de novo com --forcar (um backup é feito antes).")
            sys.exit(1)
        print(f"\nBackup criado antes de alterar: {fazer_backup('antes-do-seed')}")

    print(f"\nRegistros existentes antes da importação: {total_antes}")
    print("\nExecutando importação...\n")

    encontrados, inseridos, duplicados = run_seed()

    total_depois = contar_registros()

    print("\n" + "=" * 55)
    print("  RESULTADO")
    print("=" * 55)
    print(f"  Registros encontrados nas fontes : {encontrados}")
    print(f"  Registros inseridos no SQLite    : {inseridos}")
    print(f"  Duplicados ignorados             : {duplicados}")
    print(f"  Total na tabela knowledge agora  : {total_depois}")
    print("=" * 55)

    if inseridos > 0:
        print(f"\n✓ Importação concluída com sucesso!")
    else:
        print(f"\n✓ Banco já estava populado. Nenhuma duplicata inserida.")
