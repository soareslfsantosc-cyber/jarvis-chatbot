"""
database/refine.py
XBot v0.3.0 Beta — Refinamento do Banco de Conhecimento
XByte Games Studios

Operações:
  FASE 1 — Remover 6 duplicatas e stubs cobertos por registros mais ricos
  FASE 2 — Enriquecer 7 registros rasos (< 200 chars ou desatualizados)
  FASE 3 — Inserir 16 novos tópicos que faltam no banco

Resultado esperado: 75 → 85 registros limpos e sem redundância.

Uso:
  python database/refine.py
"""

import os, sys, logging
logger = logging.getLogger(__name__)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from database.db import get_connection, init_db, contar_registros


# ===========================================================================
# FASE 1 — IDs a remover (duplicatas e stubs absorvidos por outros registros)
# ===========================================================================
# id:1  sistema computacional    → coberto por id:24 sistemas computacionais
# id:7  licenciamento            → coberto por id:30 licenciamento de software
# id:18 dispositivos entrada saída→ coberto por id:37 dispositivos de entrada e saida
# id:32 tempo de validade licenca → conteúdo já está em id:30
# id:33 vantagens licenciamento  → conteúdo já está em id:30
# id:45 historia computacao      → coberto por id:36 historia e evolucao (1552c)

_IDS_REMOVER = [1, 7, 18, 32, 33, 45]


# ===========================================================================
# FASE 2 — Registros a enriquecer (UPDATE)
# Formato: (id, titulo, categoria, palavras_chave, conteudo, fonte)
# ===========================================================================

_ATUALIZACOES = [

    (
        24,
        "sistema computacional",
        "arquitetura_computadores",
        "sistema computacional,hardware,software,processamento,entrada,saída,memória,cpu",
        "Um sistema computacional é o conjunto integrado de hardware e software capaz de "
        "receber dados, processá-los e produzir resultados. Modelo de Von Neumann define os "
        "quatro componentes fundamentais: Unidade de Entrada (teclado, mouse, sensores), "
        "Memória (armazena programas e dados), UCP/CPU (processa as instruções) e "
        "Unidade de Saída (monitor, impressora, alto-falante). "
        "O hardware é a parte física (circuitos, chips, cabos). "
        "O software é a parte lógica (programas, sistemas operacionais, dados). "
        "Sem software, o hardware é inútil; sem hardware, o software não tem onde rodar. "
        "Ciclo básico de processamento: Entrada → Processamento → Saída → Armazenamento. "
        "Exemplos de sistemas computacionais: computador pessoal, smartphone, servidor, "
        "console de videogame, caixa eletrônico, sistema embarcado em automóveis.",
        "refine"
    ),

    (
        25,
        "software de sistema",
        "software",
        "software de sistema,sistema operacional,driver,firmware,bios,uefi,kernel,so",
        "Software de Sistema é o conjunto de programas que controlam e gerenciam os recursos "
        "do hardware, servindo de base para os demais softwares. Tipos principais: "
        "Sistema Operacional (SO): gerencia hardware e fornece interface ao usuário. "
        "Exemplos: Windows 11, Linux (Ubuntu, Debian), macOS, Android, iOS. "
        "Kernel: núcleo do SO, responsável por gerenciar processos, memória e dispositivos. "
        "Drivers: programas que permitem ao SO comunicar-se com dispositivos específicos "
        "(impressora, placa de vídeo, pen drive). Sem driver correto, o dispositivo não funciona. "
        "Firmware: software gravado na memória ROM do hardware (BIOS/UEFI da placa-mãe, "
        "firmware de roteador). Inicializa o hardware antes do SO carregar. "
        "BIOS/UEFI: programa que realiza o POST (Power-On Self-Test) ao ligar o computador, "
        "verifica componentes e carrega o sistema operacional do HD/SSD.",
        "refine"
    ),

    (
        26,
        "software embarcado",
        "software",
        "software embarcado,embedded,firmware,microcontrolador,arduino,raspberry,iot,dispositivo",
        "Software Embarcado (Embedded Software) é desenvolvido para executar funções específicas "
        "em dispositivos dedicados, geralmente com recursos de hardware limitados. "
        "Características: tamanho reduzido, executado diretamente no hardware sem SO completo, "
        "extremamente confiável e otimizado para uma única função. "
        "Exemplos no dia a dia: controle de uma geladeira smart, sistema de freio ABS de carro, "
        "firmware de roteador Wi-Fi, software de micro-ondas digital, "
        "sistema de controle de elevador, marcapassos cardíacos. "
        "Plataformas comuns: Arduino (microcontrolador para prototipagem), "
        "Raspberry Pi (mini computador Linux), ESP32 (Wi-Fi + Bluetooth integrados). "
        "Linguagens usadas: C, C++, MicroPython, Assembly. "
        "Diferença do software aplicativo: o software embarcado controla hardware específico, "
        "enquanto o aplicativo roda sobre um SO de propósito geral.",
        "refine"
    ),

    (
        28,
        "software de programacao",
        "software",
        "software de programação,ide,compilador,interpretador,depurador,vscode,intellij,eclipse",
        "Software de Programação são as ferramentas usadas por desenvolvedores para criar "
        "outros programas. Categorias principais: "
        "IDE (Ambiente de Desenvolvimento Integrado): editor de código + depurador + terminal "
        "integrados. Exemplos: VS Code (gratuito, mais usado no mundo), IntelliJ IDEA "
        "(Java/Kotlin), PyCharm (Python), Eclipse, Android Studio. "
        "Compilador: traduz código-fonte para linguagem de máquina de uma vez. "
        "Ex: GCC (C/C++), javac (Java). O programa compilado roda sem o compilador instalado. "
        "Interpretador: executa o código linha a linha em tempo real. "
        "Ex: Python, JavaScript (Node.js), PHP. Mais flexível, porém geralmente mais lento. "
        "Depurador (Debugger): permite pausar o programa, inspecionar variáveis e "
        "encontrar erros (bugs) passo a passo. "
        "Controle de versão: Git + GitHub/GitLab para rastrear mudanças no código.",
        "refine"
    ),

    (
        29,
        "software como servico",
        "software",
        "saas,software como serviço,nuvem,assinatura,cloud,google workspace,microsoft 365,netflix",
        "SaaS (Software as a Service / Software como Serviço) é um modelo de distribuição "
        "onde o software é acessado pela internet, sem instalação local. "
        "O usuário paga uma assinatura mensal ou anual e acessa tudo pelo navegador ou app. "
        "Vantagens: sem instalação, atualizações automáticas, acesso de qualquer dispositivo, "
        "escalável conforme a necessidade, backups automáticos na nuvem. "
        "Desvantagens: depende de internet, dados ficam em servidores de terceiros, "
        "custo recorrente (enquanto pagar, tem acesso). "
        "Exemplos populares: Google Workspace (Docs, Sheets, Gmail), Microsoft 365 "
        "(Word, Excel online), Netflix, Spotify, Figma, Notion, Slack, Zoom, GitHub. "
        "Diferença dos modelos: SaaS (software na nuvem), PaaS (plataforma para desenvolver), "
        "IaaS (infraestrutura — servidores virtuais).",
        "refine"
    ),

    (
        20,
        "memória",
        "hardware",
        "memória,ram,rom,cache,l1,l2,l3,ddr4,ddr5,volátil,armazenamento,byte,gb",
        "Memória é o componente que armazena dados e instruções para processamento. Tipos: "
        "RAM (Random Access Memory): memória volátil de trabalho — perde os dados ao desligar. "
        "Quanto mais RAM, mais programas podem rodar simultaneamente sem lentidão. "
        "Gerações: DDR4 (atual nos PCs mais comuns), DDR5 (mais rápida, plataformas novas). "
        "ROM (Read-Only Memory): memória não-volátil gravada de fábrica — armazena firmware/BIOS. "
        "Cache: memória ultrarrápida dentro do próprio processador, dividida em níveis: "
        "L1 (menor e mais rápida, por núcleo), L2 (média), L3 (maior, compartilhada entre núcleos). "
        "O processador busca dados na ordem: L1 → L2 → L3 → RAM → HD/SSD. "
        "VRAM: RAM dedicada da placa de vídeo para armazenar texturas e frames renderizados. "
        "Unidades: 1 Byte = 8 bits; 1 KB = 1024 B; 1 MB = 1024 KB; 1 GB = 1024 MB.",
        "refine"
    ),

    (
        2,
        "hardware",
        "hardware",
        "hardware,físico,componentes,placa-mãe,cpu,ram,hd,ssd,gpu,fonte,gabinete,periférico",
        "Hardware é o conjunto de componentes físicos e eletrônicos de um sistema computacional. "
        "Componentes internos principais: "
        "Processador (CPU): cérebro do computador, executa todas as instruções. "
        "Memória RAM: armazenamento temporário e rápido para dados em uso. "
        "Placa-mãe: conecta todos os componentes entre si (CPU, RAM, GPU, HD, fonte). "
        "HD (Hard Disk): armazenamento mecânico, mais barato por GB, mais lento. "
        "SSD (Solid State Drive): armazenamento em chips flash, muito mais rápido que HD. "
        "GPU (Placa de Vídeo): processa gráficos. Pode ser integrada à CPU ou dedicada. "
        "Fonte de Alimentação: converte corrente alternada (tomada) em tensões para os componentes. "
        "Gabinete: estrutura que abriga os componentes internos. "
        "Periféricos de Entrada: teclado, mouse, webcam, microfone, scanner. "
        "Periféricos de Saída: monitor, impressora, caixas de som, projetor. "
        "E/S (Entrada e Saída): pen drive, HD externo, leitor de cartão.",
        "refine"
    ),

    (
        22,
        "inteligencia artificial",
        "ia",
        "ia,inteligência artificial,machine learning,deep learning,nlp,llm,gpt,neural,dados",
        "Inteligência Artificial (IA) é o campo da computação que desenvolve sistemas capazes "
        "de realizar tarefas que normalmente requerem inteligência humana. Subáreas: "
        "Machine Learning (ML): algoritmos que aprendem padrões a partir de dados sem serem "
        "explicitamente programados para cada caso. Tipos: supervisionado, não-supervisionado, "
        "por reforço. "
        "Deep Learning: ML usando redes neurais com múltiplas camadas (deep neural networks). "
        "Base dos sistemas modernos de visão computacional e linguagem. "
        "NLP (Processamento de Linguagem Natural): permite que máquinas entendam e gerem texto. "
        "Base de chatbots, tradutores automáticos e assistentes virtuais. "
        "LLMs (Large Language Models): modelos de linguagem treinados em enormes quantidades "
        "de texto. Exemplos: GPT (OpenAI), Gemini (Google), Claude (Anthropic), LLaMA (Meta). "
        "Aplicações práticas: reconhecimento facial, recomendações (Netflix, Spotify), "
        "diagnóstico médico, veículos autônomos, geração de imagens (DALL-E, Midjourney).",
        "refine"
    ),

    (
        30,
        "licenciamento de software",
        "software",
        "licença,licenciamento,software,uso,pirataria,eula,proprietário,open source,creative commons",
        "Licença de software é um contrato legal que define como o programa pode ser usado, "
        "copiado, modificado e distribuído. Principais tipos: "
        "Proprietária/Comercial: o código-fonte é fechado. O usuário compra o direito de uso, "
        "não o software. Exemplos: Windows, Photoshop, Microsoft Office. "
        "Freeware: gratuito para uso, mas código fechado. Ex: WinRAR, Adobe Acrobat Reader. "
        "Shareware: versão de teste gratuita por tempo limitado. Ex: versões trial de softwares. "
        "Open Source: código aberto, geralmente gratuito. Permite estudar e modificar. "
        "Exemplos: Linux, Firefox, VS Code, Python, LibreOffice. "
        "Licenças open source: MIT (muito permissiva), GPL (derivados devem ser open source), "
        "Apache 2.0, BSD. "
        "EULA (End User License Agreement): contrato que o usuário aceita ao instalar o software. "
        "Pirataria: uso sem licença válida — ilegal no Brasil (Lei 9.609/98) e no mundo. "
        "Software pirata pode conter vírus, não recebe atualizações de segurança e "
        "pode gerar multas e processos para empresas.",
        "refine"
    ),

]


# ===========================================================================
# FASE 3 — Novos registros (INSERT)
# Formato: (titulo, categoria, palavras_chave, conteudo, fonte)
# ===========================================================================

_NOVOS = [

    # --- CSS Layout Moderno ---
    (
        "css flexbox",
        "desenvolvimento_web",
        "css,flexbox,flex,display flex,justify-content,align-items,flex-direction,layout",
        "Flexbox (Flexible Box Layout) é o modelo CSS para criar layouts unidimensionais "
        "(linha ou coluna) de forma simples e responsiva. "
        "Ativar: display: flex; no container pai — os filhos viram flex items automaticamente. "
        "Propriedades do container (pai): "
        "flex-direction: row (padrão, horizontal) | column (vertical). "
        "justify-content: alinhamento no eixo principal — flex-start, center, flex-end, "
        "space-between, space-around. "
        "align-items: alinhamento no eixo cruzado — flex-start, center, flex-end, stretch. "
        "flex-wrap: nowrap (padrão) | wrap (quebra linha se não couber). "
        "gap: espaço entre os itens. Ex: gap: 16px; "
        "Propriedades dos itens (filhos): "
        "flex: 1 → o item ocupa todo o espaço disponível igualmente. "
        "flex-grow, flex-shrink, flex-basis controlam crescimento, encolhimento e tamanho base. "
        "align-self: sobrescreve align-items para um item específico. "
        "Caso de uso clássico: centralizar um elemento na tela: "
        "body { display: flex; justify-content: center; align-items: center; min-height: 100vh; }",
        "refine"
    ),

    (
        "css grid",
        "desenvolvimento_web",
        "css,grid,display grid,grid-template-columns,grid-area,layout,bidimensional,rows",
        "CSS Grid é o sistema de layout bidimensional (linhas E colunas) do CSS. "
        "Ativar: display: grid; no container. "
        "Propriedades do container: "
        "grid-template-columns: define as colunas. "
        "Ex: grid-template-columns: 200px 1fr 1fr; (1 fixa + 2 flexíveis). "
        "repeat(3, 1fr) → 3 colunas iguais. "
        "grid-template-rows: define as linhas. "
        "gap / column-gap / row-gap: espaço entre células. "
        "grid-template-areas: nomeia áreas do layout visualmente: "
        "grid-template-areas: 'header header' 'sidebar main' 'footer footer'; "
        "Propriedades dos itens: "
        "grid-area: nomeia o item para encaixar no template. "
        "grid-column: 1 / 3 → item ocupa da coluna 1 até a 3. "
        "grid-row: 1 / 2 → item ocupa da linha 1 até a 2. "
        "Flexbox vs Grid: Flexbox = 1 dimensão (menus, botões, cards em linha). "
        "Grid = 2 dimensões (layout completo da página, dashboards, galerias).",
        "refine"
    ),

    (
        "css responsivo e media queries",
        "desenvolvimento_web",
        "css,responsivo,media query,mobile,breakpoint,viewport,rem,em,vw,vh,mobile-first",
        "Design responsivo adapta o layout a qualquer tamanho de tela (mobile, tablet, desktop). "
        "Media Queries: regras CSS que se aplicam apenas quando certas condições são verdadeiras. "
        "Sintaxe: @media (max-width: 768px) { /* estilos para telas até 768px */ } "
        "Breakpoints mais comuns: "
        "< 480px → smartphones pequenos. "
        "< 768px → tablets e smartphones grandes. "
        "< 1024px → tablets landscape e laptops pequenos. "
        "> 1200px → desktops e monitores. "
        "Mobile-first: escrever estilos base para mobile e usar min-width para escalar. "
        "Ex: @media (min-width: 768px) { .container { max-width: 960px; } } "
        "Unidades relativas: rem (relativo ao root), em (relativo ao pai), "
        "vw (% da largura da viewport), vh (% da altura). "
        "viewport meta tag obrigatória no HTML: "
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>. "
        "Imagens responsivas: img { max-width: 100%; height: auto; }",
        "refine"
    ),

    (
        "css variaveis customizadas",
        "desenvolvimento_web",
        "css,variáveis,custom properties,var,root,tema,dark mode,reutilização",
        "Variáveis CSS (Custom Properties) permitem definir valores reutilizáveis no CSS, "
        "facilitando manutenção e criação de temas. "
        "Definição: variáveis são declaradas com dois hífens (--) dentro de :root "
        "(disponível para todo o documento): "
        ":root { --cor-primaria: #2563eb; --cor-fundo: #ffffff; --tamanho-fonte: 16px; } "
        "Uso: color: var(--cor-primaria); background: var(--cor-fundo); "
        "Valor fallback (caso a variável não exista): color: var(--cor-primaria, blue); "
        "Sobrescrever em escopo específico: "
        ".card { --cor-primaria: #10b981; } → só afeta elementos dentro de .card. "
        "Dark mode com variáveis: "
        "@media (prefers-color-scheme: dark) { :root { --cor-fundo: #1a1a1a; --cor-texto: #fff; } } "
        "Atualização via JavaScript: "
        "document.documentElement.style.setProperty('--cor-primaria', '#ff0000'); "
        "Vantagem: mudar um tema inteiro alterando apenas as variáveis no :root.",
        "refine"
    ),

    # --- JavaScript Avançado ---
    (
        "javascript dom",
        "programacao",
        "javascript,dom,document object model,querySelector,getElementById,innerHTML,createElement",
        "DOM (Document Object Model) é a representação em árvore do HTML acessível via JavaScript. "
        "Cada tag HTML vira um nó (node) que o JS pode ler e modificar em tempo real. "
        "Selecionar elementos: "
        "document.getElementById('meuId') → busca pelo atributo id. "
        "document.querySelector('.minhaClasse') → busca pelo seletor CSS (retorna o primeiro). "
        "document.querySelectorAll('p') → retorna todos os <p> como NodeList. "
        "Ler e alterar conteúdo: "
        "elemento.innerHTML = '<b>novo</b>'; → altera HTML interno. "
        "elemento.textContent = 'texto'; → altera apenas o texto (mais seguro). "
        "Alterar estilos: elemento.style.color = 'red'; "
        "Alterar classes: elemento.classList.add('ativo'); .remove('ativo'); .toggle('ativo'); "
        "Criar e inserir elementos: "
        "const div = document.createElement('div'); "
        "div.textContent = 'novo'; "
        "document.body.appendChild(div); "
        "Remover: elemento.remove(); ",
        "refine"
    ),

    (
        "javascript eventos e funcoes",
        "programacao",
        "javascript,evento,addEventListener,click,submit,keydown,function,arrow function,callback",
        "Eventos permitem que o JavaScript reaja às ações do usuário e do navegador. "
        "Adicionar evento: elemento.addEventListener('tipo', funcao); "
        "Eventos comuns: click, dblclick, mouseover, mouseout, keydown, keyup, "
        "submit (formulário), change (input), load (página carregada). "
        "Exemplo: "
        "btn.addEventListener('click', function() { alert('Clicado!'); }); "
        "Arrow function (sintaxe moderna): "
        "btn.addEventListener('click', () => { console.log('clicado'); }); "
        "event.target: referência ao elemento que disparou o evento. "
        "event.preventDefault(): cancela o comportamento padrão (ex: impede submit do form). "
        "Funções: "
        "function somar(a, b) { return a + b; } → declaração tradicional. "
        "const somar = (a, b) => a + b; → arrow function. "
        "Callback: função passada como argumento para outra função. "
        "setTimeout(() => console.log('depois'), 1000); → executa após 1 segundo. "
        "setInterval(() => atualizar(), 5000); → executa a cada 5 segundos.",
        "refine"
    ),

    # --- Desenvolvimento / Ferramentas ---
    (
        "git e controle de versao",
        "programacao",
        "git,github,gitlab,controle de versão,commit,branch,merge,push,pull,clone,repositório",
        "Git é o sistema de controle de versão distribuído mais usado no mundo. "
        "Registra o histórico de mudanças do código, permitindo voltar a versões anteriores "
        "e colaborar com outros desenvolvedores. "
        "Comandos essenciais: "
        "git init → inicializa um repositório na pasta atual. "
        "git clone URL → baixa um repositório remoto. "
        "git add . → adiciona todas as mudanças para o próximo commit. "
        "git commit -m 'mensagem' → salva um snapshot com descrição. "
        "git push origin main → envia commits para o repositório remoto (GitHub/GitLab). "
        "git pull → baixa e mescla mudanças do repositório remoto. "
        "git branch nome → cria uma nova branch (ramificação). "
        "git checkout nome → muda para outra branch. "
        "git merge nome → mescla outra branch na atual. "
        "git status → mostra arquivos modificados. "
        "git log → histórico de commits. "
        "GitHub: plataforma online para hospedar repositórios Git e colaborar em equipe. "
        "Pull Request: proposta de mesclar mudanças de uma branch em outra.",
        "refine"
    ),

    (
        "banco de dados e sql",
        "programacao",
        "banco de dados,sql,select,insert,update,delete,where,join,tabela,sqlite,mysql,postgresql",
        "Banco de dados é um sistema organizado para armazenar e recuperar dados de forma eficiente. "
        "SQL (Structured Query Language) é a linguagem padrão para trabalhar com bancos relacionais. "
        "Operações CRUD: "
        "CREATE (criar): INSERT INTO tabela (col1, col2) VALUES (val1, val2); "
        "READ (ler): SELECT * FROM tabela WHERE condicao ORDER BY coluna LIMIT 10; "
        "UPDATE (atualizar): UPDATE tabela SET coluna = valor WHERE id = 1; "
        "DELETE (excluir): DELETE FROM tabela WHERE id = 1; "
        "Filtros e combinações: "
        "WHERE: filtra registros. Ex: WHERE idade > 18 AND cidade = 'Rio'. "
        "JOIN: combina dados de duas tabelas. Ex: SELECT * FROM pedidos JOIN clientes ON "
        "pedidos.cliente_id = clientes.id; "
        "GROUP BY: agrupa resultados. SELECT cidade, COUNT(*) FROM clientes GROUP BY cidade; "
        "Bancos populares: SQLite (arquivo local, sem servidor — ideal para apps pequenos), "
        "MySQL/MariaDB (web, gratuito), PostgreSQL (robusto, open source), "
        "MongoDB (NoSQL, documentos JSON).",
        "refine"
    ),

    (
        "acessibilidade web",
        "desenvolvimento_web",
        "acessibilidade,aria,a11y,alt,screen reader,teclado,wcag,contraste,foco,semântico",
        "Acessibilidade web (a11y) garante que sites funcionem para pessoas com deficiências "
        "visuais, motoras, auditivas ou cognitivas. "
        "Boas práticas fundamentais: "
        "Alt em imagens: <img src='foto.jpg' alt='Descrição da foto'> → lido por leitores de tela. "
        "Imagens decorativas: alt='' (vazio) para que leitores de tela as ignorem. "
        "HTML semântico: usar <button> para botões (não <div>) — navegável por teclado. "
        "<nav>, <main>, <header> ajudam leitores de tela a identificar regiões da página. "
        "ARIA (Accessible Rich Internet Applications): atributos que adicionam semântica: "
        "aria-label='descrição', aria-hidden='true', role='dialog'. "
        "Contraste: texto e fundo devem ter contraste suficiente (WCAG recomenda 4.5:1 para texto). "
        "Navegação por teclado: todos os elementos interativos devem ser acessíveis com Tab. "
        "Foco visível: nunca remover outline sem substituir por indicador visual alternativo. "
        "WCAG (Web Content Accessibility Guidelines): padrão internacional de acessibilidade "
        "com três níveis: A (mínimo), AA (recomendado), AAA (avançado).",
        "refine"
    ),

    # --- Python ---
    (
        "python orientado a objetos",
        "programacao",
        "python,oop,orientado a objetos,classe,objeto,herança,encapsulamento,polimorfismo,__init__",
        "Programação Orientada a Objetos (OOP) organiza o código em classes e objetos. "
        "Classe: modelo/molde que define atributos e comportamentos. "
        "Objeto (instância): criado a partir de uma classe. "
        "Definição básica: "
        "class Pessoa: "
        "    def __init__(self, nome, idade):  # construtor "
        "        self.nome = nome              # atributo "
        "        self.idade = idade "
        "    def saudacao(self):               # método "
        "        return f'Olá, sou {self.nome}' "
        "p = Pessoa('Lucas', 25)              # instância "
        "print(p.saudacao())                  # → Olá, sou Lucas "
        "Os 4 pilares da OOP: "
        "Encapsulamento: ocultar detalhes internos (atributos privados com __). "
        "Herança: uma classe filha herda atributos e métodos da classe pai. "
        "class Dev(Pessoa): def __init__(self, nome, linguagem): super().__init__(nome, 0) "
        "Polimorfismo: objetos diferentes respondem ao mesmo método de formas diferentes. "
        "Abstração: expor apenas o necessário, esconder complexidade interna.",
        "refine"
    ),

    (
        "typescript basico",
        "programacao",
        "typescript,ts,tipagem,interface,type,compilador,javascript,angular,react,strong typing",
        "TypeScript é um superset do JavaScript que adiciona tipagem estática opcional. "
        "Código TypeScript é transpilado para JavaScript antes de rodar no navegador. "
        "Por que usar: detecta erros em tempo de desenvolvimento (não em produção), "
        "melhora o autocomplete nas IDEs e facilita manutenção em projetos grandes. "
        "Instalação: npm install -g typescript. Compilar: tsc arquivo.ts "
        "Tipos básicos: "
        "let nome: string = 'Lucas'; "
        "let idade: number = 25; "
        "let ativo: boolean = true; "
        "let lista: number[] = [1, 2, 3]; "
        "Inferência: TypeScript deduz o tipo automaticamente — let x = 10 já é number. "
        "Interface: contrato que define a estrutura de um objeto: "
        "interface Usuario { nome: string; idade: number; email?: string; } "
        "O ? indica campo opcional. "
        "Type: similar à interface, mas mais flexível para uniões e interseções: "
        "type ID = string | number; "
        "Usado em frameworks modernos: Angular (obrigatório), React, Vue, Node.js.",
        "refine"
    ),

    # --- IA e Futuro ---
    (
        "machine learning basico",
        "ia",
        "machine learning,ml,aprendizado de máquina,supervisionado,não supervisionado,modelo,treino",
        "Machine Learning (ML) é a subárea de IA onde algoritmos aprendem padrões a partir "
        "de dados, sem serem explicitamente programados para cada situação. "
        "Tipos de aprendizado: "
        "Supervisionado: treinado com dados rotulados (entrada + resposta correta). "
        "Ex: classificar e-mails como spam ou não-spam, prever preço de imóvel. "
        "Não-supervisionado: encontra padrões em dados sem rótulos. "
        "Ex: agrupar clientes por comportamento (clustering), detectar anomalias. "
        "Por reforço: o modelo aprende por tentativa e erro, recebendo recompensas. "
        "Ex: jogos de xadrez, robótica, carros autônomos. "
        "Conceitos fundamentais: "
        "Dataset: conjunto de dados para treino e teste. "
        "Features: variáveis de entrada (características dos dados). "
        "Label: variável de saída (o que queremos prever). "
        "Overfitting: modelo memoriza os dados de treino, mas falha em dados novos. "
        "Underfitting: modelo muito simples, não aprende os padrões. "
        "Bibliotecas: scikit-learn (ML clássico), TensorFlow, PyTorch (deep learning).",
        "refine"
    ),

    (
        "cloud computing e computacao em nuvem",
        "futuro_tecnologia",
        "cloud,nuvem,aws,azure,google cloud,iaas,paas,saas,servidor,escalabilidade,aws ec2,s3",
        "Computação em Nuvem (Cloud Computing) é o fornecimento de recursos computacionais "
        "(servidores, armazenamento, bancos de dados, rede) via internet, sob demanda. "
        "Modelos de serviço: "
        "IaaS (Infrastructure as a Service): infraestrutura virtual — aluga servidores, "
        "armazenamento e rede. Ex: AWS EC2, Google Compute Engine, Azure VMs. "
        "PaaS (Platform as a Service): plataforma para desenvolver e hospedar apps sem "
        "gerenciar servidores. Ex: Heroku, Google App Engine, Vercel, Railway. "
        "SaaS (Software as a Service): software acessado via browser. Ex: Gmail, Notion, Figma. "
        "Provedores principais: AWS (Amazon Web Services — líder de mercado), "
        "Google Cloud Platform (GCP), Microsoft Azure. "
        "Vantagens: sem custo de hardware físico, escala automaticamente conforme demanda, "
        "pague apenas o que usar, alta disponibilidade (99.99% uptime). "
        "Serviços comuns: armazenamento (S3), banco de dados (RDS), funções serverless "
        "(Lambda), CDN para distribuição de conteúdo.",
        "refine"
    ),

    (
        "iot internet das coisas",
        "futuro_tecnologia",
        "iot,internet das coisas,sensor,arduino,raspberry,mqtt,smart home,wearable,edge computing",
        "IoT (Internet of Things / Internet das Coisas) é a rede de dispositivos físicos "
        "conectados à internet que coletam e compartilham dados automaticamente. "
        "Exemplos no dia a dia: lâmpadas inteligentes (Philips Hue), termostatos smart "
        "(Nest), smartwatches (Apple Watch, Fitbit), geladeiras conectadas, fechaduras "
        "inteligentes, rastreadores de veículos, sensores industriais. "
        "Componentes típicos de um projeto IoT: "
        "Sensor: coleta dados do ambiente (temperatura, umidade, movimento, luminosidade). "
        "Microcontrolador: processa os dados (Arduino, ESP32, Raspberry Pi Pico). "
        "Conectividade: Wi-Fi, Bluetooth, LoRa, Zigbee, 4G/5G. "
        "Cloud: armazena e analisa os dados coletados. "
        "Aplicação: interface para o usuário visualizar e controlar. "
        "Protocolo MQTT: lightweight pub/sub para comunicação entre dispositivos IoT. "
        "Desafios: segurança (dispositivos com software desatualizado), privacidade "
        "(dados coletados continuamente), interoperabilidade entre fabricantes.",
        "refine"
    ),

    (
        "seguranca web",
        "desenvolvimento_web",
        "segurança,https,ssl,tls,xss,sql injection,csrf,hash,bcrypt,owasp,vulnerabilidade",
        "Segurança web protege aplicações e usuários contra ataques e vulnerabilidades. "
        "Vulnerabilidades mais comuns (OWASP Top 10): "
        "SQL Injection: inserção de código SQL malicioso em campos de formulário. "
        "Prevenção: sempre use queries parametrizadas (prepared statements) — nunca concatene "
        "strings com dados do usuário: cursor.execute('SELECT * FROM users WHERE id=?', (id,)). "
        "XSS (Cross-Site Scripting): injeção de scripts maliciosos em páginas web. "
        "Prevenção: escapar/sanitizar todo conteúdo gerado pelo usuário antes de exibir no HTML. "
        "CSRF (Cross-Site Request Forgery): requisições forjadas em nome do usuário. "
        "Prevenção: tokens CSRF únicos por sessão. "
        "HTTPS: criptografa a comunicação entre cliente e servidor via TLS. "
        "Nunca transmita senhas ou dados sensíveis em HTTP. "
        "Senhas: NUNCA armazene em texto puro. Use hash + salt: bcrypt, argon2. "
        "Ex em Python: bcrypt.hashpw(senha.encode(), bcrypt.gensalt()). "
        "Princípio do mínimo privilégio: cada parte do sistema acessa só o que precisa.",
        "refine"
    ),

    (
        "algoritmos e logica de programacao",
        "programacao",
        "algoritmo,lógica,complexidade,big o,ordenação,busca,recursão,estrutura de dados",
        "Algoritmo é uma sequência finita e bem definida de passos para resolver um problema. "
        "Toda programação se baseia em algoritmos e lógica. "
        "Estruturas de controle fundamentais: "
        "Sequência: instruções executadas em ordem. "
        "Seleção: if/else, switch — decisões baseadas em condições. "
        "Repetição: for, while — executar código múltiplas vezes. "
        "Complexidade de tempo (Big O): mede como o tempo de execução cresce com a entrada. "
        "O(1) constante → melhor caso. Ex: acessar índice de lista. "
        "O(n) linear → percorrer uma lista. "
        "O(n²) quadrático → loops aninhados. "
        "O(log n) logarítmico → busca binária. "
        "Algoritmos de ordenação clássicos: Bubble Sort, Selection Sort, Insertion Sort "
        "(simples, O(n²)), Quick Sort e Merge Sort (eficientes, O(n log n)). "
        "Recursão: função que chama a si mesma. Requer condição de parada (base case). "
        "Ex clássico: fatorial(n) = n * fatorial(n-1); fatorial(0) = 1. "
        "Estruturas de dados: lista, pilha (stack), fila (queue), árvore, grafo, hash table.",
        "refine"
    ),

    (
        "redes protocolos modernos",
        "redes",
        "http,https,tcp,udp,ip,dns,dhcp,ftp,ssh,vpn,firewall,protocolo,camada,osi",
        "Protocolos de rede definem as regras de comunicação entre dispositivos. Modelo OSI: "
        "7 camadas (Física → Enlace → Rede → Transporte → Sessão → Apresentação → Aplicação). "
        "Camada de Aplicação (mais próxima do usuário): "
        "HTTP/HTTPS: páginas web (S = seguro via TLS). Métodos: GET, POST, PUT, DELETE. "
        "FTP: transferência de arquivos. SSH: acesso remoto seguro a servidores. "
        "DNS: traduz domínios (google.com) em IPs (142.250.x.x). "
        "DHCP: distribui endereços IP automaticamente na rede. "
        "Camada de Transporte: "
        "TCP: garante entrega ordenada e confirmada dos pacotes (confiável, mais lento). "
        "UDP: envia pacotes sem confirmação (rápido, usado em streaming e jogos online). "
        "Camada de Rede: IP (IPv4 — 32 bits, ex: 192.168.1.1; IPv6 — 128 bits). "
        "Segurança: Firewall bloqueia tráfego indesejado. VPN cria túnel criptografado. "
        "HTTPS usa TLS para criptografar a comunicação cliente-servidor.",
        "refine"
    ),

]


# ===========================================================================
# FUNÇÕES PRINCIPAIS
# ===========================================================================

def run_refine() -> dict:
    """
    Executa as 3 fases de refinamento do banco.
    Retorna dict com contagens de cada operação.
    """
    init_db()
    resultado = {"removidos": 0, "atualizados": 0, "inseridos": 0, "erros": 0}

    with get_connection() as conn:
        c = conn.cursor()

        # ------------------------------------------------------------------
        # FASE 1 — Remoção de duplicatas e stubs
        # ------------------------------------------------------------------
        for id_del in _IDS_REMOVER:
            c.execute("SELECT titulo FROM knowledge WHERE id = ?", (id_del,))
            row = c.fetchone()
            if row:
                c.execute("DELETE FROM knowledge WHERE id = ?", (id_del,))
                resultado["removidos"] += 1
                logger.info(f"  [−] Removido id:{id_del} — {row['titulo']}")
            else:
                logger.debug(f"  [?] id:{id_del} não encontrado (já removido?)")

        # ------------------------------------------------------------------
        # FASE 2 — Enriquecimento de registros existentes
        # ------------------------------------------------------------------
        for id_upd, titulo, categoria, palavras_chave, conteudo, fonte in _ATUALIZACOES:
            c.execute("SELECT titulo FROM knowledge WHERE id = ?", (id_upd,))
            row = c.fetchone()
            if row:
                c.execute(
                    """UPDATE knowledge
                       SET titulo=?, categoria=?, palavras_chave=?, conteudo=?, fonte=?
                       WHERE id=?""",
                    (titulo, categoria, palavras_chave, conteudo, fonte, id_upd)
                )
                resultado["atualizados"] += 1
                logger.info(f"  [↑] Enriquecido id:{id_upd} — {titulo}")
            else:
                logger.warning(f"  [!] id:{id_upd} não encontrado para atualização")
                resultado["erros"] += 1

        # ------------------------------------------------------------------
        # FASE 3 — Inserção de novos tópicos
        # ------------------------------------------------------------------
        c.execute("SELECT LOWER(titulo) FROM knowledge")
        existentes = {row[0] for row in c.fetchall()}

        for titulo, categoria, palavras_chave, conteudo, fonte in _NOVOS:
            if titulo.lower() in existentes:
                logger.debug(f"  [=] Já existe: {titulo}")
                continue
            c.execute(
                """INSERT INTO knowledge
                   (titulo, categoria, palavras_chave, conteudo, fonte)
                   VALUES (?, ?, ?, ?, ?)""",
                (titulo, categoria, palavras_chave, conteudo, fonte)
            )
            existentes.add(titulo.lower())
            resultado["inseridos"] += 1
            logger.info(f"  [+] Inserido: {titulo}")

    return resultado


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    print("=" * 60)
    print("  XBot — Refinamento do Banco (refine.py)")
    print("=" * 60)

    antes = contar_registros()
    print(f"\nRegistros antes: {antes}")
    print("\nExecutando refinamento...\n")

    res = run_refine()

    depois = contar_registros()

    print("\n" + "=" * 60)
    print("  RESULTADO")
    print("=" * 60)
    print(f"  Duplicatas/stubs removidos : {res['removidos']}")
    print(f"  Registros enriquecidos     : {res['atualizados']}")
    print(f"  Novos tópicos inseridos    : {res['inseridos']}")
    print(f"  Erros                      : {res['erros']}")
    print(f"  Registros antes            : {antes}")
    print(f"  Registros depois           : {depois}")
    print(f"  Variação                   : {'+' if depois > antes else ''}{depois - antes}")
    print("=" * 60)
