# Base de Conhecimento Expandida do XBot
# Inclui informações sobre HTML, CSS, Psicologia das Cores, Python e Arquitetura de Computadores

KNOWLEDGE_BASE_EXTENDED = {
    # Desenvolvimento Web - HTML
    "html": {
        "definicao": "HTML (HyperText Markup Language) é a linguagem de marcação padrão para criar páginas web. HTML5 é a versão mais recente.",
        "estrutura_basica": "Todo documento HTML possui: DOCTYPE (declara HTML5), elemento raiz <html>, cabeçalho <head> para configurações, e corpo <body> para conteúdo.",
        "elementos_principais": "HEAD contém configurações do site, BODY contém área de conteúdo, TITLE define o título da página, CHARSET serve para textos em português com acentos e cedilhas.",
        "titulos": "HTML possui 6 níveis de títulos: <h1> (principal), <h2> (subtítulo), <h3>, <h4>, <h5>, <h6> (menor).",
        "formatacao_texto": "Tags de formatação: <b> para negrito, <i> para itálico, <u> para sublinhado, <s> para riscado, <p> para parágrafos com quebra de linha, <span> para texto contínuo sem quebra.",
        "elementos_especiais": "Tag <hr> cria linha horizontal para separar conteúdo visualmente."
    },

    # Desenvolvimento Web - Visual Studio Code
    "visual_studio_code": {
        "instalacao": "Baixe o Visual Studio Code em https://code.visualstudio.com/ e instale para desenvolvimento web.",
        "configuracoes": "Configurações importantes: Word wrap (quebra de texto), Font size (tamanho da fonte, recomendado 15-20), Color theme (tema de cores), Auto Save (salvamento automático).",
        "idioma": "Para português: CTRL+SHIFT+P, escolha 'Configure Display Language', selecione Português.",
        "visualizacao": "Para aumentar fonte: CTRL+, para diminuir: CTRL-. Para executar: usar 'Executar, iniciar depuração' ou abrir arquivo HTML no navegador."
    },

    # Design - Psicologia das Cores
    "psicologia_cores": {
        "definicao": "Estudo que mostra como nosso cérebro identifica e transforma cores em sensações, influenciando comportamento, emoções e decisões.",
        "importancia": "Cores são elementos importantes na comunicação e têm grande influência no cotidiano, interferindo nos sentidos, emoções e decisões.",
        "cores_quentes": "Mais luminosas, colocam áreas em plano frontal. Sensações: vitalidade, energia, alegria, movimento, abrem apetite. Usadas em marcas de fast-food, filmes de ação.",
        "cores_frias": "Menos luminosas, colocam áreas em plano posterior. Sensações: calma, conforto, tranquilidade, mas também tédio, distância, lentidão. Usadas em hospitais para transmitir calma.",
        "marketing": "Cores têm grande poder no marketing. Cada marca cria identidade visual com paleta específica. Exemplos: Coca-Cola (vermelho - força, sedução), Nubank (roxo - transformação).",
        "design": "Na criação de identidade visual, a escolha de cores é crucial. Processo: entender proposta da marca, estudar cores adequadas, encontrar equilíbrio entre pesquisa e originalidade."
    },

    # Programação Python - Conceitos Básicos
    "python_basico": {
        "compilador": "Compilador é fundamental na programação, converte código fonte em código executável. Python usa interpretador que converte código em bytecode.",
        "codigo_aberto": "Python é open source (código aberto), permitindo modificação e distribuição livre. Outras linguagens open source: Java, C++, PHP, JavaScript.",
        "linguagens_nivel": "Linguagens de alto nível (Python, Java) são próximas à linguagem humana. Linguagens de baixo nível (Assembly) são próximas à linguagem de máquina.",
        "source_bytecode": "Source code é código escrito pelo programador. Bytecode é código intermediário gerado pelo compilador Python, executado pela máquina virtual Python.",
        "variaveis": "Regras para variáveis: não começar com número, não usar espaços, não usar caracteres especiais (exceto _). Exemplos válidos: numero, sal_func. Inválidos: 3num, nome produto.",
        "tipos_dados": "String (texto entre aspas), Integer (números inteiros), Float (números decimais). Exemplo: nome='João' (string), idade=25 (int), salario=1500.50 (float).",
        "comandos": "print() exibe informações na tela. input() faz pergunta e armazena resposta em variável. input() sempre retorna string, usar int() ou float() para converter."
    },

    # Programação Python - Estruturas de Controle
    "python_estruturas": {
        "comandos_selecao": "if/elif/else permitem execução condicional. Operadores: == (igual), != (diferente), > (maior), < (menor), >= (maior igual), <= (menor igual).",
        "comandos_repeticao": "for usado para repetições com quantidade definida. while usado para repetições com condição. range() gera sequência de números.",
        "funcoes": "Blocos de código reutilizáveis. Definidas com def nome_funcao():. Podem receber parâmetros e retornar valores.",
        "listas": "Estruturas que armazenam múltiplos valores. Criadas com colchetes []. Acesso por índice (começando em 0).",
        "operadores_logicos": "and (E lógico), or (OU lógico), not (NÃO lógico). Usados para combinar condições."
    },

    # Arquitetura de Computadores - Hardware Específico
    "placas_mae_gigabyte": {
        "smart_fan": "Tecnologia Smart Fan da Gigabyte gerencia ventoinhas do sistema, permitindo controle de velocidade para otimizar refrigeração e ruído.",
        "memoria_ddr5": "Placas-mãe Gigabyte atuais suportam DDR5, última geração de memória RAM com alta velocidade e maior eficiência energética.",
        "codec_audio": "Muitas placas Gigabyte usam codec ALC1220, oferecendo qualidade de áudio superior para aplicações profissionais e gaming.",
        "m2_pcie": "Slots M.2 PCIe 4.0 x4 suportam até 7000 MB/s de transferência, ideal para SSDs de alta performance.",
        "uc_bios": "Interface UC BIOS da Gigabyte é intuitiva e fácil de usar, permitindo configurações avançadas do sistema.",
        "conectores_alimentacao": "Gigabyte usa conectores ATX 12V, EPS 12V e PCIe 8-pin para energia estável e eficiente.",
        "perfdrive": "Tecnologia PerfDrive permite overclocking seguro, ajustando configurações para melhor desempenho.",
        "wifi_6e": "Wi-Fi 6E suporta velocidades até 9,6 Gbps, oferecendo conectividade sem fio ultra-rápida.",
        "lan_gigabit": "Suporte a 2,5 GbE LAN oferece velocidades superiores ao Gigabit Ethernet padrão.",
        "protecao_tensao": "Overvoltage Protection protege componentes contra sobretensão, aumentando durabilidade do sistema."
    },

    # Conceitos de Programação Avançados
    "programacao_avancada": {
        "estruturas_dados": "Arrays, listas, pilhas, filas, árvores, grafos são estruturas fundamentais para organizar dados eficientemente.",
        "algoritmos": "Sequências de passos para resolver problemas. Incluem algoritmos de ordenação, busca, recursão.",
        "paradigmas": "Programação procedural, orientada a objetos, funcional, cada uma com características específicas.",
        "debugging": "Processo de encontrar e corrigir erros no código. Ferramentas incluem debuggers, logs, testes unitários.",
        "versionamento": "Git é sistema de controle de versão mais usado, permitindo rastrear mudanças e colaboração.",
        "boas_praticas": "Código limpo, comentários úteis, nomes descritivos, funções pequenas, testes automatizados."
    },

    # História da Computação
    "historia_computacao": {
        "descobrimento_brasil": "Pedro Álvares Cabral descobriu o Brasil em 22 de abril de 1500, navegando com caravelas.",
        "guerra_100_anos": "Durou 116 anos (1337-1453), série de conflitos entre Inglaterra e França, com vitória francesa.",
        "primeiro_presidente": "Marechal Deodoro da Fonseca foi o primeiro presidente do Brasil, assumindo em 15 de novembro de 1889.",
        "evolucao_tecnologica": "Da computação mecânica aos computadores quânticos, a tecnologia evoluiu exponencialmente.",
        "pioneiros": "Figuras como Von Neumann, Turing, Ada Lovelace foram fundamentais para a computação moderna."
    },

    # Desenvolvimento Web Avançado
    "desenvolvimento_web": {
        "frontend": "HTML estrutura conteúdo, CSS estiliza apresentação, JavaScript adiciona interatividade.",
        "backend": "Servidor processa requisições, banco de dados armazena informações, APIs conectam sistemas.",
        "frameworks": "React, Vue, Angular para frontend. Node.js, Python Flask/Django, PHP Laravel para backend.",
        "responsividade": "Design que se adapta a diferentes tamanhos de tela usando media queries CSS.",
        "acessibilidade": "Práticas para tornar sites usáveis por pessoas com deficiências, usando ARIA, semântica HTML.",
        "performance": "Otimização de carregamento, compressão de imagens, minificação de código, CDN."
    },

    # Conceitos de Design
    "design_digital": {
        "ui_ux": "UI (Interface do Usuário) foca na aparência. UX (Experiência do Usuário) foca na usabilidade.",
        "tipografia": "Escolha de fontes impacta legibilidade e personalidade do design.",
        "layout": "Organização visual dos elementos usando grids, alinhamento, hierarquia.",
        "branding": "Criação de identidade visual consistente para marcas, incluindo logo, cores, tipografia.",
        "prototipagem": "Criação de versões preliminares para testar conceitos antes da implementação final."
    }
}

# Questões e Respostas para Quiz Interativo
QUIZ_QUESTIONS = {
    "arquitetura": [
        {
            "pergunta": "Qual o nome da tecnologia de gerenciamento das ventoinhas da Gigabyte?",
            "opcoes": ["Smart Fan", "Fan Control", "Cooling System", "Smart Cooling", "Expert Fan"],
            "resposta_correta": 0,
            "explicacao": "A Gigabyte usa a tecnologia Smart Fan para gerenciar as ventoinhas do sistema, permitindo controle de velocidade."
        },
        {
            "pergunta": "Qual tipo de memória RAM as placas-mãe atuais da Gigabyte suportam?",
            "opcoes": ["DDR4", "DDR6", "DDR2", "DDR5", "DDR3"],
            "resposta_correta": 3,
            "explicacao": "As placas-mãe da Gigabyte mais recentes suportam DDR5, oferecendo alta velocidade e eficiência energética."
        },
        {
            "pergunta": "Qual codec de áudio é utilizado em muitas placas-mãe Gigabyte?",
            "opcoes": ["ALC1150", "Realtek HD Audio", "ALC1220", "Creative Sound Amplificator", "Creative Sound Blaster"],
            "resposta_correta": 2,
            "explicacao": "Muitas placas-mãe da Gigabyte usam o ALC1220, que oferece qualidade de áudio superior."
        }
    ],
    "python": [
        {
            "pergunta": "Qual a importância de um compilador na programação?",
            "opcoes": ["Apenas formatar código", "Converter código fonte em executável", "Criar interfaces", "Gerenciar memória", "Conectar à internet"],
            "resposta_correta": 1,
            "explicacao": "O compilador é fundamental para converter código fonte em código executável que o computador pode entender."
        },
        {
            "pergunta": "Qual dessas variáveis Python é válida?",
            "opcoes": ["3numero", "nome produto", "sal_func", "num-val", "class"],
            "resposta_correta": 2,
            "explicacao": "sal_func é válida pois não começa com número, não tem espaços nem caracteres especiais (exceto _)."
        }
    ],
    "web": [
        {
            "pergunta": "O que significa DOCTYPE em HTML?",
            "opcoes": ["Tipo de documento", "Declara HTML5", "Define charset", "Configura CSS", "Importa JavaScript"],
            "resposta_correta": 1,
            "explicacao": "DOCTYPE declara que o documento está usando HTML5, a versão mais recente do HTML."
        },
        {
            "pergunta": "Qual tag HTML cria uma linha horizontal?",
            "opcoes": ["<line>", "<hr>", "<br>", "<div>", "<span>"],
            "resposta_correta": 1,
            "explicacao": "A tag <hr> cria uma linha horizontal para separar visualmente o conteúdo."
        }
    ]
}

# Exercícios Práticos
EXERCICIOS_PRATICOS = {
    "python_basico": [
        {
            "titulo": "Calculadora Simples",
            "descricao": "Crie um programa que leia dois números e realize operações básicas",
            "codigo_exemplo": """
num1 = float(input('Digite o primeiro número: '))
num2 = float(input('Digite o segundo número: '))
print(f'Soma: {num1 + num2}')
print(f'Subtração: {num1 - num2}')
print(f'Multiplicação: {num1 * num2}')
if num2 != 0:
    print(f'Divisão: {num1 / num2}')
else:
    print('Divisão por zero não é possível')
"""
        },
        {
            "titulo": "Sistema de Notas",
            "descricao": "Programa que calcula média de notas e determina aprovação",
            "codigo_exemplo": """
nome = input('Nome do aluno: ')
nota1 = float(input('Primeira nota: '))
nota2 = float(input('Segunda nota: '))
nota3 = float(input('Terceira nota: '))
media = (nota1 + nota2 + nota3) / 3
print(f'Aluno: {nome}')
print(f'Média: {media:.2f}')
if media >= 7:
    print('Aprovado!')
elif media >= 5:
    print('Recuperação')
else:
    print('Reprovado')
"""
        }
    ]
}

