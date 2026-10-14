"""
database/apostilas_seed.py
XBot v0.3.0 Beta — Importador das Apostilas para SQLite
XByte Games Studios

Fonte: Apostilas  para o xbot/
Professores: Elenice Oliveira e Marcus Vinicius de Lima

Conteúdo extraído e condensado de:
  - Cursos de Desenvolvimento Web I (HTML5 + CSS3)
  - Web II (JavaScript Básico/Intermediário + JS para Jogos)
  - Apostila Python Completa + LPI Python
  - Montagem e Manutenção de Computadores
  - Redes de Computadores
  - Informática para o Trabalho
  - Ferramentas Digitais

Estratégia:
  mode="insert" → INSERT apenas se o título não existir (novo tópico)
  mode="update" → UPDATE do conteúdo se o título já existir (enriquece entradas rasas)

Uso:
  python database/apostilas_seed.py
  ou: from database.apostilas_seed import run_apostilas_seed
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_DIR)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from database.db import get_connection, init_db, contar_registros, contar_conhecimento, fazer_backup


# ===========================================================================
# DADOS DAS APOSTILAS
# Cada item: (titulo, categoria, palavras_chave, conteudo, fonte, mode)
# mode = "insert" → só insere se não existe
# mode = "update" → atualiza conteúdo e palavras-chave se já existe
# ===========================================================================

_DADOS = [

    # -----------------------------------------------------------------------
    # HTML / CSS — Apostilas Desenvolvimento Web I
    # -----------------------------------------------------------------------

    (
        "html historico e midia",
        "desenvolvimento_web",
        "html,historico,tim berners-lee,1991,html5,audio,video,mídia,w3c,whatwg",
        "O HTML foi criado por Tim Berners-Lee no CERN em 1991 para compartilhar "
        "documentos científicos. A evolução foi: HTML 1.0 (1991, ~20 tags), HTML 2.0 "
        "(1995, formulários), HTML 3.2 e 4.01 (1997-1999, tabelas, estilos, scripts), "
        "HTML5 (2014, padrão atual com suporte nativo a vídeo, áudio, gráficos e "
        "semântica sem plugins como Flash). "
        "Para incorporar mídia em HTML5: áudio usa <audio controls><source src='arquivo.mp3' "
        "type='audio/mp3'></audio>; vídeo usa <video width='640' height='360' controls>"
        "<source src='video.mp4' type='video/mp4'></video>. O atributo controls exibe os "
        "controles de reprodução. Múltiplos formatos podem ser declarados dentro de um "
        "mesmo elemento para garantir compatibilidade.",
        "apostila_html",
        "insert"
    ),

    (
        "css introducao",
        "desenvolvimento_web",
        "css,folha de estilo,seletor,propriedade,valor,declaração,cascata,regra css",
        "CSS (Cascading Style Sheets / Folhas de Estilo em Cascata) é a linguagem usada "
        "para estilizar páginas web — define cores, tamanhos, fontes, espaçamentos e "
        "posicionamento dos elementos HTML. Estrutura básica de uma regra CSS: "
        "seletor { propriedade: valor; } "
        "Seletor: o elemento HTML a ser estilizado. "
        "Propriedade: característica a ser alterada (ex: color, font-size, background-color). "
        "Valor: qualificação da propriedade (ex: red, 14px, black). "
        "Uma regra pode ter várias declarações separadas por ponto e vírgula: "
        "p { color: white; background-color: black; font-size: 14px; } "
        "Agrupamento de seletores: h2, p, ul { font-size: 18px; } aplica o mesmo estilo "
        "a múltiplos elementos de uma vez.",
        "apostila_css",
        "insert"
    ),

    (
        "css box model",
        "desenvolvimento_web",
        "css,box model,margin,padding,border,borda,margem,espaçamento,espessura",
        "O Box Model do CSS controla o espaçamento ao redor dos elementos. "
        "MARGIN: define as margens externas. Pode ser declarada individualmente "
        "(margin-top, margin-right, margin-bottom, margin-left) ou abreviada: "
        "margin: 20px 30px 5px 10px (topo direita baixo esquerda). "
        "Atalhos: margin: 20px (todos iguais); margin: 15px 10px (topo/baixo e esq/dir). "
        "PADDING: define o espaço entre o conteúdo e a borda. Mesma sintaxe do margin: "
        "padding: 20px 30px 5px 10px. "
        "BORDER: define largura, estilo e cor da borda. "
        "border-width: define espessura (ex: border-top-width: 2px). "
        "border-color: define a cor (ex: border-top-color: red). "
        "border-style: define o estilo (solid, dashed, dotted, double). "
        "Abreviação: border: 2px solid #000; (largura estilo cor). "
        "Dica: use * { box-sizing: border-box; } para que padding e border não aumentem "
        "o tamanho total do elemento.",
        "apostila_css",
        "insert"
    ),

    (
        "css cores e paletas",
        "desenvolvimento_web",
        "css,cores,rgb,hexadecimal,hex,hsl,color,paleta,vermelho,verde,azul",
        "CSS suporta três sistemas principais de cores: "
        "RGB: combina Vermelho (Red), Verde (Green) e Azul (Blue) com valores de 0 a 255. "
        "Ex: color: rgb(255, 0, 0) = vermelho; rgb(0, 0, 0) = preto; rgb(255, 255, 255) = branco. "
        "HEXADECIMAL: 6 dígitos hexadecimais (0-9, A-F) precedidos por #. "
        "Ex: #ff0000 = vermelho; #000000 = preto; #ffffff = branco; #00f = azul (abreviado). "
        "Regra de abreviação hex: se dois dígitos são iguais, pode-se usar apenas um "
        "(#ff0000 vira #f00). "
        "HSL: usa Hue (matiz 0-360°), Saturation (saturação %) e Lightness (luminosidade %). "
        "Ex: color: hsl(0, 100%, 50%) = vermelho; hsl(120, 100%, 50%) = verde. "
        "As 16 cores básicas do HTML são nomeadas: black, white, red, blue, green, etc.",
        "apostila_css",
        "insert"
    ),

    (
        "css seletores",
        "desenvolvimento_web",
        "css,seletor,universal,tipo,classe,id,atributo,especificidade,*",
        "Tipos de seletores CSS: "
        "Universal (*): aplica estilo a TODOS os elementos. Ex: * { box-sizing: border-box; }. "
        "Por tipo: seleciona por tag HTML. Ex: h1 { color: red; } "
        "Por classe (.): seleciona elementos com determinada classe. "
        "No HTML: <li class='criando'>; no CSS: .criando { color: blue; }. "
        "Por ID (#): seleciona elemento único por ID. No HTML: <div id='menu'>; "
        "no CSS: #menu { background: black; }. "
        "Agrupamento: h2, p, ul { font-size: 18px; } aplica estilo a múltiplos seletores. "
        "O seletor universal é especialmente útil para resetar margens e paddings: "
        "* { margin: 0; padding: 0; box-sizing: border-box; }",
        "apostila_css",
        "insert"
    ),

    (
        "css pseudo-classes",
        "desenvolvimento_web",
        "css,pseudo-classe,hover,active,disabled,focus,visited,nth-child,estado",
        "Pseudo-classes CSS são palavras-chave adicionadas aos seletores para especificar "
        "estados especiais do elemento. Sintaxe: seletor:pseudo-classe { propriedades }. "
        ":hover — ativa quando o mouse passa sobre o elemento: "
        ".btn:hover { background-color: green; color: white; } "
        ":active — ativa quando o elemento é clicado: "
        ".btn:active { background-color: gray; } "
        ":disabled — aplica estilo a elementos desabilitados (não recebem clique): "
        ".btn:disabled { opacity: 0.6; } "
        ":focus — ativa quando o elemento está em foco (ex: campo de texto selecionado). "
        ":visited — aplica estilo a links já visitados. "
        ":nth-child(n) — seleciona o n-ésimo filho de um elemento. "
        "São amplamente usadas para interatividade sem JavaScript.",
        "apostila_css",
        "insert"
    ),

    (
        "css pseudo-elementos",
        "desenvolvimento_web",
        "css,pseudo-elemento,first-line,first-letter,selection,marker,before,after,::,dom",
        "Pseudo-elementos CSS permitem estilizar partes específicas de um elemento. "
        "Sintaxe com dois colons (::): seletor::pseudo-elemento { propriedades }. "
        "::first-line — estiliza apenas a primeira linha de um parágrafo: "
        ".texto::first-line { font-weight: bold; font-size: 20px; color: blue; } "
        "::first-letter — estiliza apenas a primeira letra (efeito de capitular): "
        ".texto::first-letter { font-size: 50px; color: blue; text-decoration: underline; } "
        "::selection — muda a aparência do texto selecionado pelo usuário: "
        ".texto::selection { background-color: rgb(24, 214, 56); } "
        "::marker — estiliza os marcadores de listas: "
        "ul li::marker { content: '>'; } "
        "::before e ::after — inserem conteúdo antes/depois de um elemento sem adicionar HTML.",
        "apostila_css",
        "insert"
    ),

    (
        "css fontes e tipografia",
        "desenvolvimento_web",
        "css,fonte,tipografia,font-family,serif,sans-serif,google fonts,@import,link,text",
        "CSS permite importar e usar fontes personalizadas via Google Fonts (fonts.google.com). "
        "Dois métodos de importação: "
        "Via <link> no HTML: <link href='https://fonts.googleapis.com/css2?family=NomeDaFonte' "
        "rel='stylesheet'> — recomendado para uma página. "
        "Via @import no CSS: @import url('https://fonts.googleapis.com/...') — "
        "recomendado para projetos com múltiplas páginas. "
        "Uso no CSS: p { font-family: 'Nome da Fonte', sans-serif; font-size: 16px; } "
        "Diferença serif vs sans-serif: "
        "Serif (ex: Times New Roman): tem serifa (pequenos traços decorativos no final das letras). "
        "Sans-serif (ex: Arial): sem serifa, mais limpa e moderna. "
        "Propriedades de texto: font-size (tamanho), font-weight (bold/normal), "
        "font-style (italic), text-align (left/center/right), text-decoration (underline).",
        "apostila_css",
        "insert"
    ),

    (
        "css background imagens",
        "desenvolvimento_web",
        "css,background,imagem de fundo,background-image,background-size,cover,background-position,url",
        "CSS permite colocar imagens de fundo via propriedade background-image: "
        "body { background-image: url('imagem.jpg'); } "
        "Propriedades de controle: "
        "background-size: cover — faz a imagem cobrir todo o elemento mantendo proporção. "
        "background-size: 50% — define tamanho percentual. "
        "background-position: 380px 70px — posiciona a imagem no plano. "
        "background-repeat: no-repeat — evita que a imagem se repita. "
        "background-color — cor de fundo (usada quando a imagem não carrega). "
        "Para garantir altura mínima: html, body { min-height: 100%; } "
        "Exemplo completo: body { background-color: pink; background-image: url('img.png'); "
        "background-size: cover; background-repeat: no-repeat; background-position: center; }",
        "apostila_css",
        "insert"
    ),

    (
        "css estilos inline interno externo",
        "desenvolvimento_web",
        "css,inline,interno,externo,link,style,href,stylesheet,form de aplicar",
        "CSS pode ser aplicado de três formas: "
        "INLINE: diretamente na tag HTML com o atributo style. "
        "Ex: <p style='color: yellow; background: red; font-size: 18px;'>. "
        "Desvantagem: dificulta manutenção e perde o poder de reuso do CSS. "
        "INTERNO (Incorporado): estilos dentro da tag <style> no <head> do HTML. "
        "<head><style> body { background: pink; } h1 { color: blue; } </style></head>. "
        "Desvantagem: estilos valem apenas para aquela página. "
        "EXTERNO: arquivo separado com extensão .css vinculado ao HTML via <link>. "
        "<head><link rel='stylesheet' type='text/css' href='estilos.css'></head>. "
        "Vantagem: mesmo arquivo CSS pode ser reutilizado em todas as páginas do projeto, "
        "facilitando manutenção. Recomendado para projetos reais.",
        "apostila_css",
        "insert"
    ),

    (
        "html elementos semanticos",
        "desenvolvimento_web",
        "html,semântico,header,footer,nav,article,section,aside,main,div,estrutura",
        "Elementos semânticos do HTML5 descrevem seu propósito pelo próprio nome da tag, "
        "facilitando a leitura do código por desenvolvedores e por máquinas (SEO, acessibilidade). "
        "<header>: cabeçalho da página ou de uma seção (logotipo, menu, busca). "
        "<footer>: rodapé com direitos autorais, contatos, links úteis. "
        "<nav>: bloco de navegação/menu principal. "
        "<main>: conteúdo principal e único da página. "
        "<article>: conteúdo independente que faz sentido sozinho (postagem de blog, notícia). "
        "<section>: parte do conteúdo com tema específico (capítulo, aba, seção numerada). "
        "<aside>: conteúdo relacionado indiretamente ao principal (barra lateral, curiosidades). "
        "O Google analisou mais de 1 bilhão de sites para identificar padrões de layout "
        "ao criar esses elementos. Evitam o uso excessivo de <div> sem significado.",
        "apostila_html5",
        "insert"
    ),

    (
        "html container e div",
        "desenvolvimento_web",
        "html,div,container,bloco,box,overflow,display,block,caixa",
        "DIV (Division): elemento de nível de bloco usado como container genérico para outros "
        "elementos. Pode conter qualquer tipo de elemento em qualquer quantidade. "
        "Por si só não altera a renderização do conteúdo — sua utilidade vem com CSS. "
        "Container CSS: estrutura .container { width: 80%; max-width: 1200px; margin: 0 auto; "
        "background-color: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); } "
        "Um container centraliza e limita o conteúdo, tornando a página organizada. "
        "Elementos de nível de bloco: ocupam toda a largura disponível e quebram linha "
        "(div, p, h1-h6, ul, ol, table). "
        "Elementos inline: ocupam apenas o espaço do conteúdo (span, a, img, strong). "
        "overflow: define o que acontece quando conteúdo ultrapassa os limites da caixa "
        "(visible, hidden, scroll, auto).",
        "apostila_html5",
        "insert"
    ),

    (
        "html tabelas",
        "desenvolvimento_web",
        "html,tabela,table,tr,td,th,thead,tbody,tfoot,caption,colspan,rowspan",
        "Tags para criar tabelas em HTML: "
        "<table>: define a tabela. "
        "<tr> (table row): define uma linha. "
        "<td> (table data): define uma célula de dados. "
        "<th> (table header): define célula de cabeçalho (negrito e centralizado por padrão). "
        "<caption>: título geral da tabela. "
        "<thead>: agrupa as linhas do cabeçalho. "
        "<tbody>: agrupa as linhas do corpo. "
        "<tfoot>: agrupa as linhas do rodapé. "
        "colspan: mescla células horizontalmente. Ex: <td colspan='2'>. "
        "rowspan: mescla células verticalmente. Ex: <td rowspan='3'>. "
        "Estrutura básica: <table><thead><tr><th>Nome</th><th>Idade</th></tr></thead>"
        "<tbody><tr><td>Ana</td><td>25</td></tr></tbody></table>. "
        "Estilize com CSS: border-collapse: collapse elimina espaço duplo entre bordas.",
        "apostila_html5",
        "insert"
    ),

    (
        "html listas",
        "desenvolvimento_web",
        "html,lista,ul,ol,li,dl,dt,dd,ordenada,não ordenada,definição,marcador",
        "HTML tem três tipos de listas: "
        "LISTA NÃO ORDENADA (<ul>): exibida com marcadores (bullets). "
        "<ul><li>Item 1</li><li>Item 2</li></ul>. "
        "LISTA ORDENADA (<ol>): exibida com numeração automática. "
        "<ol><li>Primeiro</li><li>Segundo</li></ol>. "
        "LISTA DE DEFINIÇÃO (<dl>): usada para glossários e definições. "
        "Contém <dt> (termo) e <dd> (definição): "
        "<dl><dt>HTML</dt><dd>Linguagem de marcação para web</dd></dl>. "
        "CSS para listas: list-style-type define o marcador (disc, circle, square, none). "
        "list-style-position: inside/outside controla posição do marcador. "
        "Listas podem ser aninhadas colocando uma <ul> ou <ol> dentro de um <li>.",
        "apostila_html5",
        "insert"
    ),

    (
        "html formularios",
        "desenvolvimento_web",
        "html,formulário,form,input,type,placeholder,label,button,select,textarea,checkbox,radio",
        "Formulários HTML coletam dados do usuário. Tag principal: <form>. "
        "TAG <input>: campo de entrada autocontida (não requer fechamento). Tipos: "
        "text — campo de texto livre (padrão). "
        "password — esconde o que é digitado. "
        "email — valida formato de e-mail. "
        "url — valida formato de URL. "
        "number — campo numérico (min, max). "
        "range — controle deslizante. "
        "date/time/month/week — seletores de data e hora. "
        "radio — botão de opção única (marcar apenas uma). "
        "checkbox — caixa de seleção múltipla. "
        "color — seletor de cor. "
        "file — seleção de arquivo para upload. "
        "Atributos importantes: placeholder (texto informativo), id, name, required. "
        "<label for='id-do-campo'>: legenda que associa ao input via atributo for. "
        "<select>: lista suspensa. <textarea>: área de texto multilinha. "
        "<button type='submit'>: envia o formulário.",
        "apostila_html5",
        "insert"
    ),

    (
        "html imagens",
        "desenvolvimento_web",
        "html,imagem,img,src,alt,caminho,absoluto,relativo,rasterizada,pixel,jpg,png",
        "Tag de imagem HTML: <img src='caminho' alt='descrição'> (autocontida, sem fechamento). "
        "Atributo src: caminho para a imagem. "
        "Caminho absoluto: URL completa da internet. Ex: src='https://site.com/img.jpg'. "
        "Caminho relativo: arquivo local na mesma pasta ou em subpasta. "
        "Ex: src='img/foto.jpg' (imagem dentro da pasta img). "
        "Atributo alt: texto alternativo para acessibilidade e quando a imagem não carrega. "
        "Imagens rasterizadas: formadas por pixels (pontos coloridos). "
        "Quanto maior a resolução (mais pixels), melhor a qualidade. "
        "Formatos comuns: JPEG/JPG (fotos, compressão com perda), "
        "PNG (transparência, compressão sem perda), GIF (animações simples). "
        "Para criar subpasta de imagens: <img src='img/foto.jpg' alt='Foto'>. "
        "Dimensões: use width e height ou CSS para controlar tamanho. "
        "Dentro de uma div: <div><img src='foto.jpg' alt='x'></div> permite posicionamento.",
        "apostila_html5",
        "insert"
    ),

    # -----------------------------------------------------------------------
    # JAVASCRIPT — Apostila Web II JavaScript
    # -----------------------------------------------------------------------

    (
        "javascript basico",
        "programacao",
        "javascript,js,variável,tipo,ecmascript,ecma,netscape,função,dom,evento,client side",
        "JavaScript é a linguagem de programação da web, client-side por natureza. "
        "História: criado em 1995 pela Netscape com o nome Mocha/LiveScript. O nome "
        "'JavaScript' foi escolhido por marketing (Java era popular na época). Java e JS "
        "são diferentes — ambas baseadas em C, mas independentes. "
        "Padronização: ECMAScript (ECMA) é o JavaScript padronizado pela Associação Europeia "
        "de Fabricantes de Computadores. "
        "Papel na web: HTML = conteúdo, CSS = estilo, JS = interação. "
        "JS não pode ser programado em HTML nem CSS (essas são linguagens de marcação/estilo). "
        "Ordem de execução pelo navegador: 1) Script (JS), 2) CSS, 3) Conteúdo HTML. "
        "Variáveis: declaradas com var, let ou const. "
        "Tipos primitivos: string, number, boolean, null, undefined. "
        "Funções: function nomeFuncao() { ... } ou arrow function: () => { ... }. "
        "Ponto e vírgula no final de linha são opcionais em JS moderno.",
        "apostila_js",
        "insert"
    ),

    (
        "javascript para jogos",
        "programacao",
        "javascript,jogo,game,animação,css animation,keyframes,canvas,colisão,dinossauro",
        "JavaScript + CSS podem criar jogos simples no navegador sem frameworks externos. "
        "Estrutura básica: index.html (estrutura), style.css (visual), script.js (lógica). "
        "Animação com CSS: animation define uma animação em um objeto. "
        "@keyframes cria o deslocamento do objeto no plano cartesiano. "
        "Propriedades: 1s (tempo), infinite (sem limite), linear (constante). "
        "Controle via JS: adicionar/remover classes CSS dispara/para animações. "
        "Ex: personagem.classList.add('animar') e personagem.classList.remove('animar'). "
        "Detecção de colisão: comparar posições (getBoundingClientRect()) dos objetos. "
        "Eventos: addEventListener('click', funcao) captura interações do jogador. "
        "IDs e classes no CSS: IDs usam # (únicos), classes usam . (reutilizáveis). "
        "Coordenadas: position: absolute + top/left controlam posição de personagens. "
        "Projetos de exemplo: jogo do dinossauro, plataformer 2D simples.",
        "apostila_js",
        "insert"
    ),

    # -----------------------------------------------------------------------
    # PYTHON — Apostila Python Completa
    # -----------------------------------------------------------------------

    (
        "python flask e django",
        "programacao",
        "python,flask,django,web,framework,rota,route,api,rest,orm,template,backend",
        "Python tem dois frameworks web principais: "
        "FLASK (Microframework): fornece o essencial para aplicações web, deixando decisões "
        "arquiteturais para o desenvolvedor. Ideal para APIs RESTful e projetos menores. "
        "Exemplo básico: from flask import Flask; app = Flask(__name__); "
        "@app.route('/') def hello(): return '<p>Olá, Mundo!</p>'; app.run(debug=True). "
        "DJANGO (Framework completo): inclui ORM, autenticação, painel admin, sistema de "
        "templates e URL dispatcher prontos. Segue o padrão MTV (Model-Template-View). "
        "Características do Django: ORM mapeia Python para tabelas de banco sem SQL puro, "
        "Admin Site gerado automaticamente, sistema de autenticação integrado. "
        "Flask vs Django: Flask = mais controle e liberdade; Django = mais funcionalidades "
        "prontas, ideal para projetos grandes. "
        "Instalação Flask: pip install Flask. Executar: python app.py → http://127.0.0.1:5000/",
        "apostila_python",
        "insert"
    ),

    (
        "python bibliotecas populares",
        "programacao",
        "python,biblioteca,numpy,pandas,matplotlib,scikit-learn,data science,ia,machine learning",
        "O ecossistema de bibliotecas Python é um de seus maiores diferenciais: "
        "NumPy: computação numérica de alta performance. Fornece o ndarray (array N-dimensional) "
        "para operações matemáticas vetorizadas muito mais rápidas que loops Python. "
        "Exemplo: import numpy as np; arr = np.array([1,2,3]); print(arr * 2) → [2 4 6]. "
        "Pandas: manipulação e análise de dados tabulares (DataFrames). Essencial para "
        "ciência de dados, limpeza de dados e relatórios. "
        "Matplotlib / Seaborn: visualização de dados com gráficos de linha, barra, dispersão. "
        "Scikit-learn: machine learning clássico (regressão, classificação, clustering). "
        "TensorFlow / PyTorch: deep learning e redes neurais. "
        "Requests: requisições HTTP simples. "
        "OpenCV: visão computacional e processamento de imagens. "
        "SQLAlchemy: ORM para bancos de dados relacionais. "
        "A maioria é instalável via: pip install nome-da-biblioteca.",
        "apostila_python",
        "insert"
    ),

    # -----------------------------------------------------------------------
    # HARDWARE — Montagem e Manutenção de Computadores
    # -----------------------------------------------------------------------

    (
        "montagem e manutencao de computadores",
        "hardware",
        "montagem,manutenção,computador,componentes,gabinete,placa-mãe,fonte,hd,ssd,cooler",
        "Componentes essenciais de um sistema computacional para montagem: "
        "Gabinete (Case/Torre): estrutura física que abriga os componentes internos. "
        "IMPORTANTE: gabinete ≠ CPU. CPU é o microchip processador dentro do gabinete. "
        "Placa-mãe: componente central que conecta todos os outros (CPU, RAM, GPU, HD). "
        "Processador (CPU): realiza as instruções dos programas em operações binárias (0 e 1). "
        "Memória RAM: armazenamento temporário e volátil para dados em uso. "
        "HD/SSD: armazenamento permanente. SSD é mais rápido que HD mecânico. "
        "Fonte de alimentação: converte energia da tomada para voltagens dos componentes. "
        "Cooler/Dissipador: resfria o processador para evitar superaquecimento. "
        "GPU: processa gráficos (integrada na CPU ou placa de vídeo dedicada). "
        "Inicialização: ao energizar, o sistema busca o POST (Power-On Self-Test) via BIOS/UEFI, "
        "verifica componentes e carrega o sistema operacional.",
        "apostila_hardware",
        "insert"
    ),

    (
        "cpu versus gabinete",
        "hardware",
        "cpu,gabinete,torre,case,processador,microchip,confusão,equívoco,distinção",
        "Distinção técnica importante frequentemente confundida: "
        "CPU (Unidade Central de Processamento): é um MICROCHIP dentro do computador. "
        "Definição oficial: 'componente que realiza as instruções de um programa de computador, "
        "executa a aritmética básica orientado por padrão binário (0 e 1), possibilitando "
        "entrada, processamento e saída de dados. Funciona como o cérebro do computador.' "
        "Um microchip JAMAIS pode ser do tamanho de uma caixa! "
        "GABINETE (Case/Torre/Chassis): é o compartimento externo que CONTÉM os componentes. "
        "Definição: 'estrutura que abriga a maioria dos componentes internos de um computador.' "
        "Erro comum: chamar o gabinete de 'CPU'. Isso acontece porque nas décadas de 1980-90, "
        "o termo CPU foi popularizado metonimicamente para se referir ao conjunto todo. "
        "Correto: CPU = processador (chip). Gabinete = a caixa/torre.",
        "apostila_hardware",
        "insert"
    ),

    # -----------------------------------------------------------------------
    # REDES DE COMPUTADORES
    # -----------------------------------------------------------------------

    (
        "redes de computadores",
        "redes",
        "rede,computadores,arpanet,internet,protocolo,tcp,ip,topologia,lan,wan,roteador",
        "Redes de computadores surgiram de tecnologias anteriores como teleimpressores, "
        "modem e a Mondothèque de Paul Otlet. "
        "Marcos históricos: "
        "1940: George Stibitz enviou instruções via teletipo entre computadores em locais diferentes. "
        "1965: Lawrence Roberts e Thomas Merril conectaram dois centros de pesquisa via linha "
        "telefônica, num dos primeiros experimentos de rede entre computadores. "
        "1969: ARPANET conectou UCLA, Stanford, UCSB e Universidade de Utah — origem da Internet. "
        "A ARPANET transferia até 50 Kbps e usou comutação de pacotes (dados divididos em pacotes "
        "roteados independentemente). "
        "Conceitos fundamentais: "
        "LAN (Local Area Network): rede local (empresa, escola). "
        "WAN (Wide Area Network): rede de longa distância. "
        "Protocolo: conjunto de regras para comunicação entre dispositivos. "
        "TCP/IP: protocolo padrão da internet (Transmission Control Protocol / Internet Protocol). "
        "Roteador: direciona pacotes entre redes diferentes.",
        "apostila_redes",
        "insert"
    ),

    (
        "protocolos e topologias de rede",
        "redes",
        "protocolo,topologia,tcp,ip,http,https,ftp,dns,dhcp,rede,switch,hub,modem",
        "Protocolos de rede definem as regras de comunicação: "
        "TCP/IP: base da internet. TCP garante entrega ordenada dos pacotes; IP define endereçamento. "
        "HTTP/HTTPS: transferência de páginas web (S = criptografado/seguro). "
        "FTP: transferência de arquivos entre computadores. "
        "DNS: traduz nomes de domínio (ex: google.com) em endereços IP. "
        "DHCP: atribui IPs automaticamente a dispositivos na rede. "
        "Dispositivos de rede: "
        "Hub: distribui dados para TODOS os dispositivos da rede (obsoleto). "
        "Switch: distribui dados apenas para o destinatário correto (mais eficiente). "
        "Roteador: conecta diferentes redes e direciona o tráfego. "
        "Modem: converte sinal digital em analógico e vice-versa para transmissão. "
        "Topologias: estrela (todos conectados a um hub/switch central), "
        "anel (dispositivos em círculo), malha (múltiplas conexões entre nós).",
        "apostila_redes",
        "insert"
    ),

    # -----------------------------------------------------------------------
    # SISTEMA OPERACIONAL E INFORMÁTICA
    # -----------------------------------------------------------------------

    (
        "sistema operacional windows linux",
        "software",
        "sistema operacional,windows,linux,android,ios,so,path,diretório,extensão,arquivo",
        "Sistema Operacional (SO): software que administra e gerencia os recursos do hardware, "
        "estabelecendo a interface entre o computador e o usuário. "
        "Exemplos: Windows (Microsoft), Linux, macOS (Apple), Android, iOS, Solaris. "
        "Versões do Windows: MS-DOS → Windows 95/98 → XP → 7 → 8/8.1 → 10 → 11 (atual). "
        "PATH (caminho): especifica a localização de um arquivo no sistema de arquivos. "
        "Caminho absoluto: completo desde a raiz. Ex: C:\\Usuários\\Lucas\\Documentos\\arquivo.txt. "
        "Caminho relativo: relativo ao diretório atual. Ex: Documentos\\arquivo.txt. "
        "No Windows usa \\ como separador; no Linux/Mac usa /. "
        "Extensões de arquivo: sufixos que identificam o tipo e formato (.exe, .pdf, .jpg, "
        ".docx, .mp3, .zip). Cada extensão requer um software específico para abrir. "
        "UNC (Universal Naming Convention): padrão para recursos de rede: \\\\Servidor\\Pasta.",
        "apostila_informatica",
        "insert"
    ),

    # -----------------------------------------------------------------------
    # IMAGENS DIGITAIS E FERRAMENTAS
    # -----------------------------------------------------------------------

    (
        "imagens digitais e formatos",
        "design",
        "imagem,digital,pixel,vetor,raster,png,jpg,jpeg,bmp,gif,svg,rgb,canal alfa,resolução",
        "Tipos de imagens digitais: "
        "RASTERIZADAS (Bitmap): formadas por uma grade de pixels — pequenos pontos coloridos. "
        "Cada pixel armazena uma cor no sistema RGB. Quanto mais pixels, maior a resolução. "
        "Desvantagem: perdem qualidade ao ampliar (os pixels ficam visíveis). "
        "Formatos raster: JPG/JPEG (fotos, compressão com perda), PNG (transparência via canal "
        "alfa, compressão sem perda), BMP (sem compressão, arquivo grande), GIF (animações). "
        "VETORIAIS: geradas por descrições matemáticas de formas (curvas, polígonos). "
        "Vantagem: não perdem qualidade em nenhum tamanho. Mais leves que raster. "
        "Formato: SVG (Scalable Vector Graphics) para web. "
        "RGB: sistema de cores aditivas (Vermelho + Verde + Azul = 0 a 255 cada). "
        "Canal Alfa: define a opacidade de cada pixel (0 = transparente, 255 = opaco). "
        "PNG usa canal alfa para fundo transparente sem serrilhamento.",
        "apostila_ferramentas",
        "insert"
    ),

    (
        "kanban trello e gestao de projetos",
        "ferramentas_digitais",
        "kanban,trello,gestão,projeto,post-it,quadro,coluna,produção,agile,scrum,card",
        "Ferramentas de gestão visual de projetos: "
        "KANBAN: sistema de controle do fluxo de produção com cartões coloridos (post-its) "
        "em quadros com colunas que representam etapas do processo. "
        "Colunas típicas: A Fazer → Em Andamento → Revisão → Concluído. "
        "Também chamado de Gestão Visual por usar cores como sinalizadores de status. "
        "Origem na Toyota (sistema de produção japonês, anos 1940-50). "
        "TRELLO: ferramenta digital que implementa o Kanban em quadros online. "
        "Permite criar quadros, listas e cartões; adicionar membros, datas limite e "
        "checklists; integrar com outras ferramentas. Gratuito para uso básico. "
        "SCRUM: metodologia ágil que usa sprints (ciclos curtos de 1-4 semanas). "
        "Complementa o Kanban com reuniões diárias (daily) e revisões de sprint. "
        "Uso no desenvolvimento de software: organizar tarefas de features, bugs e melhorias.",
        "apostila_ferramentas",
        "insert"
    ),

    (
        "php formularios e banco de dados",
        "programacao",
        "php,banco de dados,mysql,sql,formulário,servidor,backend,web,pdo,crud",
        "PHP (Hypertext Preprocessor) é uma linguagem server-side para desenvolvimento web. "
        "Diferente de JavaScript (client-side), PHP roda no servidor e gera HTML dinâmico. "
        "Uso com formulários HTML: o atributo action do <form> aponta para um arquivo .php "
        "que processa os dados enviados. Ex: <form action='salvar.php' method='POST'>. "
        "Recebimento de dados em PHP: $_POST['nome'] para método POST, "
        "$_GET['parametro'] para método GET. "
        "Integração com banco de dados MySQL via PDO: "
        "$pdo = new PDO('mysql:host=localhost;dbname=meubanco', 'usuario', 'senha'); "
        "CRUD em PHP/MySQL: "
        "CREATE: INSERT INTO tabela (campo1, campo2) VALUES (?, ?); "
        "READ: SELECT * FROM tabela WHERE id = ?; "
        "UPDATE: UPDATE tabela SET campo = ? WHERE id = ?; "
        "DELETE: DELETE FROM tabela WHERE id = ?; "
        "PHP é amplamente usado em sistemas de cadastro, login e gerenciamento de dados.",
        "apostila_php",
        "insert"
    ),

    # -----------------------------------------------------------------------
    # ATUALIZAÇÕES — enriquecer entradas existentes com conteúdo das apostilas
    # -----------------------------------------------------------------------

    (
        "html",
        "desenvolvimento_web",
        "html,hipertext,markup,linguagem,tag,elemento,web,css,javascript,html5,w3c,whatwg",
        "HTML (HyperText Markup Language) é a linguagem padrão para criar páginas web. "
        "Criada em 1991 por Tim Berners-Lee no CERN para compartilhar documentos científicos. "
        "Estrutura de um documento HTML5: <!DOCTYPE html><html lang='pt-BR'><head>"
        "<meta charset='UTF-8'><title>Título</title></head><body>Conteúdo</body></html>. "
        "Tags essenciais: <h1>-<h6> (títulos), <p> (parágrafo), <a href=''> (link), "
        "<img src='' alt=''> (imagem), <ul>/<ol>/<li> (listas), <table>/<tr>/<td> (tabelas), "
        "<form>/<input> (formulários), <div> (container genérico). "
        "HTML5 introduziu: elementos semânticos (<header>, <nav>, <main>, <article>, "
        "<section>, <footer>), suporte nativo a <audio> e <video> sem plugins, "
        "APIs de armazenamento local e geolocalização. "
        "HTML define a ESTRUTURA. CSS define o ESTILO. JavaScript define a INTERAÇÃO. "
        "Atributo charset UTF-8: aceita caracteres especiais e acentos.",
        "apostila_html",
        "update"
    ),

    (
        "python basico",
        "programacao",
        "python,guido van rossum,1991,variável,tipo,if,for,while,função,def,indentação,alto nível",
        "Python é uma linguagem de programação de alto nível, interpretada, de propósito geral, "
        "criada por Guido van Rossum e lançada em 1991. Destaca-se pela legibilidade, sintaxe "
        "clara e concisa, tipagem dinâmica e grande ecossistema de bibliotecas. "
        "Muito usada em: desenvolvimento web (Flask, Django), ciência de dados (NumPy, Pandas), "
        "inteligência artificial, automação, scripts e ensino de programação. "
        "Variáveis: não precisam de declaração de tipo. Ex: nome = 'Lucas'; idade = 25. "
        "Tipos primitivos: str, int, float, bool, list, tuple, dict, set. "
        "Estruturas de controle: if/elif/else, for, while. "
        "Funções: def saudacao(nome): return f'Olá, {nome}!'. "
        "Indentação obrigatória (4 espaços) define blocos de código. "
        "Entrada e saída: input() para ler, print() para exibir. "
        "Instalação de pacotes: pip install nome-do-pacote. "
        "Grandes universidades substituíram Pascal pelo Python no currículo de TI.",
        "apostila_python",
        "update"
    ),

    (
        "desenvolvimento web",
        "desenvolvimento_web",
        "desenvolvimento web,html,css,javascript,frontend,backend,fullstack,responsivo,api",
        "Desenvolvimento web envolve três camadas fundamentais que trabalham juntas: "
        "HTML: define a ESTRUTURA e o CONTEÚDO (textos, imagens, links, formulários). "
        "CSS: define o ESTILO e o VISUAL (cores, fontes, espaçamentos, layout, animações). "
        "JavaScript: define a INTERAÇÃO e o COMPORTAMENTO (botões, formulários dinâmicos, "
        "animações, comunicação com servidores). "
        "Frontend: tudo o que o usuário vê e interage (HTML + CSS + JS). "
        "Backend: servidor, banco de dados e lógica de negócio (Python/Flask/Django, "
        "Node.js, PHP, etc.). "
        "Fullstack: combina frontend e backend. "
        "Responsividade: design que se adapta a qualquer tamanho de tela usando CSS Media Queries. "
        "REST API: padrão de comunicação entre frontend e backend via HTTP (GET, POST, PUT, DELETE). "
        "Ferramentas essenciais: VS Code (editor), Git (controle de versão), "
        "Chrome DevTools (debug), npm/pip (gerenciadores de pacotes).",
        "apostila_web",
        "update"
    ),

    (
        "design digital",
        "design",
        "design,digital,imagem,vetor,raster,pixel,rgb,cmyk,tipografia,ui,ux,cores,composição",
        "Design digital envolve criação de conteúdo visual para telas e mídias digitais. "
        "Fundamentos: "
        "Imagens rasterizadas (bitmap): formadas por pixels, cada um com cor RGB. "
        "Formatos: JPG (fotos, compressão com perda), PNG (transparência, sem perda), "
        "GIF (animações), BMP (sem compressão, arquivo grande). "
        "Imagens vetoriais: criadas com fórmulas matemáticas, não perdem qualidade ao ampliar. "
        "Formato: SVG para web, AI/EPS para impressão. "
        "RGB vs CMYK: RGB = telas (Vermelho, Verde, Azul); CMYK = impressão (Ciano, Magenta, "
        "Amarelo, Preto). "
        "Tipografia: escolha de fontes influencia percepção e legibilidade. "
        "Serif (Times New Roman) transmite formalidade; Sans-serif (Arial) transmite modernidade. "
        "Psicologia das cores: vermelho (urgência, paixão), azul (confiança, tecnologia), "
        "verde (natureza, crescimento), amarelo (atenção, otimismo). "
        "UI (User Interface): design visual dos elementos. "
        "UX (User Experience): experiência e usabilidade para o usuário.",
        "apostila_ferramentas",
        "update"
    ),

]


# ===========================================================================
# FUNÇÕES DE IMPORTAÇÃO
# ===========================================================================

def _get_existentes_com_conteudo(cursor) -> dict:
    """
    Retorna dict {titulo_lower: id} para todos os registros do banco.
    Usado para detectar duplicatas e decidir entre INSERT e UPDATE.
    """
    cursor.execute("SELECT id, LOWER(titulo) as titulo_lower FROM knowledge")
    return {row["titulo_lower"]: row["id"] for row in cursor.fetchall()}


def run_apostilas_seed() -> tuple:
    """
    Importa o conhecimento das apostilas para a tabela knowledge.

    Estratégia:
      mode='insert' → INSERT apenas se o título ainda não existe no banco.
      mode='update' → UPDATE do conteúdo e palavras-chave se já existe.

    Retorna:
      (encontrados, inseridos, atualizados, ignorados)
    """
    init_db()

    encontrados = 0
    inseridos   = 0
    atualizados = 0
    ignorados   = 0

    with get_connection() as conn:
        cursor = conn.cursor()
        existentes = _get_existentes_com_conteudo(cursor)

        for titulo, categoria, palavras_chave, conteudo, fonte, mode in _DADOS:
            encontrados += 1
            titulo_lower = titulo.lower().strip()

            if titulo_lower in existentes:
                if mode == "update":
                    registro_id = existentes[titulo_lower]
                    cursor.execute(
                        """
                        UPDATE knowledge
                        SET conteudo      = ?,
                            palavras_chave = ?,
                            categoria     = ?,
                            fonte         = ?
                        WHERE id = ?
                        """,
                        (conteudo, palavras_chave, categoria, fonte, registro_id)
                    )
                    atualizados += 1
                    logger.debug(f"  [↑] Atualizado: {titulo}")
                else:
                    ignorados += 1
                    logger.debug(f"  [=] Já existe (insert ignorado): {titulo}")
            else:
                cursor.execute(
                    """
                    INSERT INTO knowledge
                        (titulo, categoria, palavras_chave, conteudo, fonte)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (titulo, categoria, palavras_chave, conteudo, fonte)
                )
                existentes[titulo_lower] = cursor.lastrowid
                inseridos += 1
                logger.debug(f"  [+] Inserido: {titulo}")

    logger.info(
        f"[Apostilas] Concluído — Encontrados: {encontrados} | "
        f"Inseridos: {inseridos} | Atualizados: {atualizados} | Ignorados: {ignorados}"
    )
    return encontrados, inseridos, atualizados, ignorados


# ===========================================================================
# ENTRY POINT — execução direta como script
# ===========================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    print("=" * 60)
    print("  XBot — Importador das Apostilas (apostilas_seed.py)")
    print("=" * 60)

    # Trava: as apostilas já foram importadas e depois REFINADAS à mão. O modo "update" reescreve
    # palavras-chave e o "insert" recria tópicos que a auditoria apagou de propósito.
    # Só com --forcar (e com backup antes).
    init_db()
    total_antes = contar_conhecimento()
    if total_antes > 0:
        if "--forcar" not in sys.argv[1:]:
            print(f"\nO banco já tem {total_antes} registros de conhecimento. apostilas_seed.py NÃO foi executado:")
            print("reaplicá-lo pode sobrescrever palavras-chave refinadas e recriar tópicos apagados de propósito.")
            print("O servidor já semeia sozinho um banco NOVO (vazio); você não precisa rodar isto à mão.")
            print("Se realmente quiser reaplicar, rode de novo com --forcar (um backup é feito antes).")
            sys.exit(1)
        print(f"\nBackup criado antes de alterar: {fazer_backup('antes-das-apostilas')}")

    print(f"\nRegistros no banco antes: {total_antes}")
    print("\nImportando apostilas...\n")

    enc, ins, upd, ign = run_apostilas_seed()

    total_depois = contar_registros()

    print("\n" + "=" * 60)
    print("  RESULTADO")
    print("=" * 60)
    print(f"  Encontrados nas apostilas : {enc}")
    print(f"  Inseridos (novos tópicos) : {ins}")
    print(f"  Atualizados (enriquecidos): {upd}")
    print(f"  Ignorados (já existiam)   : {ign}")
    print(f"  Total no banco agora      : {total_depois}")
    print("=" * 60)

    if ins + upd > 0:
        print(f"\n✓ Apostilas importadas com sucesso!")
    else:
        print(f"\n✓ Banco já estava atualizado. Nenhuma alteração necessária.")
