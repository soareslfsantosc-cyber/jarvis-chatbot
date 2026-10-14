"""
database/audit_fix.py
XBot v0.3.0 Beta — Correções e Enriquecimento Final do Banco
XByte Games Studios

Operações baseadas na auditoria de qualidade:

FASE 1 — Deletar registros problemáticos (3)
  id:34  software sem licenciamento  → conteúdo completamente errado
  id:43  placas mae gigabyte         → muito específico (marca), longo demais
  id:71  protocolos e topologias de rede → duplicata de id:92

FASE 2 — Corrigir bugs reais (3)
  id:31  propriedade e licenca       → keyword "e" sozinha quebrando busca
  id:92  redes protocolos modernos   → absorver conteúdo único de id:71
  id:36  historia e evolucao         → condensar de 1552c para ~500c

FASE 3 — Enriquecer 18 registros rasos (200-270c)

FASE 4 — Inserir 3 registros novos
  software sem licenciamento (versão correta)
  placa mae (genérica, substituindo a de marca)
  barramentos e interfaces (arquitetura_computadores estava com só 2 registros)

Resultado esperado: 86 → 86 registros, todos íntegros e com conteúdo adequado para chatbot.
"""

import os, sys, logging
logger = logging.getLogger(__name__)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from database.db import get_connection, init_db, contar_registros


# ===========================================================================
# FASE 1 — IDs a deletar
# ===========================================================================

_IDS_DELETAR = [34, 43, 71]


# ===========================================================================
# FASE 2 — Correções de bugs (UPDATE por id)
# Formato: (id, titulo, categoria, palavras_chave, conteudo)
# ===========================================================================

_CORRECOES = [

    # id:31 — keywords com "e" sozinho quebravam a busca
    (
        31,
        "propriedade e licenca",
        "software",
        "propriedade,licença,licenca,software,direitos autorais,transferência,cópia,eula,contrato",
        "Na maioria dos contratos de software, o fabricante vende apenas o direito de uso, "
        "não a propriedade do programa. O usuário não é dono do software — é um licenciado. "
        "Consequências práticas: o software pode ser descontinuado pelo fabricante a qualquer "
        "momento, sem obrigação de continuidade; não é permitido vender, alugar, copiar ou "
        "redistribuir o software; atualizações podem ser pagas separadamente. "
        "Exceção: software open source transfere direitos mais amplos ao usuário, permitindo "
        "uso, modificação e redistribuição conforme a licença (MIT, GPL, Apache). "
        "EULA (End User License Agreement): contrato exibido na instalação que o usuário aceita "
        "ao clicar em 'Concordo'. Define todos os termos de uso, limitações e responsabilidades. "
        "Dica: sempre leia os termos principais antes de instalar software corporativo — "
        "em empresas, o descumprimento pode gerar multas e processos.",
    ),

    # id:92 — absorver conteúdo único de id:71 (dispositivos de rede + topologias)
    (
        92,
        "redes protocolos e dispositivos",
        "redes",
        "protocolo,rede,tcp,udp,http,https,dns,dhcp,ssh,vpn,firewall,osi,hub,switch,roteador,"
        "modem,topologia,estrela,anel,malha,ipv4,ipv6",
        "Protocolos definem regras de comunicação. Modelo OSI: 7 camadas "
        "(Física→Enlace→Rede→Transporte→Sessão→Apresentação→Aplicação). "
        "Protocolos principais: "
        "HTTP/HTTPS: páginas web (S = seguro via TLS). Métodos: GET, POST, PUT, DELETE. "
        "FTP: transferência de arquivos. SSH: acesso remoto seguro a servidores. "
        "DNS: traduz domínios (google.com) em IPs. DHCP: distribui IPs automaticamente. "
        "TCP: entrega garantida e ordenada (confiável, mais lento). "
        "UDP: sem confirmação, rápido (streaming, jogos online). "
        "IP: IPv4 (32 bits, ex: 192.168.1.1), IPv6 (128 bits, mais endereços). "
        "VPN: túnel criptografado sobre a internet. Firewall: bloqueia tráfego indesejado. "
        "Dispositivos de rede: "
        "Hub: envia dados para TODOS (obsoleto). Switch: envia só ao destinatário certo. "
        "Roteador: conecta redes diferentes e direciona tráfego. "
        "Modem: converte sinal digital↔analógico para transmissão. "
        "Topologias: estrela (todos num switch central), anel (dispositivos em círculo), "
        "malha (múltiplas conexões redundantes entre nós).",
    ),

    # id:36 — condensar de 1552c para ~500c
    (
        36,
        "historia e evolucao dos computadores",
        "historia_computacao",
        "história,computador,evolução,geração,mecânico,válvula,transistor,circuito integrado,"
        "microprocessador,abaco,pascal,babbage,ENIAC,ibm,moore",
        "Evolução dos computadores em 6 gerações: "
        "Geração 0 — Mecânica (até 1945): calculadoras mecânicas e eletromecânicas. "
        "Exemplos: ábaco, máquina de Pascal (1642), diferencial de Babbage (1837), relés. "
        "1ª Geração — Válvulas (1945-1955): ENIAC usava 19.000 válvulas, pesava 30 ton. "
        "Programação por cartões perfurados. Altíssimo consumo de energia. "
        "2ª Geração — Transistores (1955-1965): Bell Labs criou o transistor em 1948. "
        "1/200 do tamanho da válvula, 1/100 da energia. Surgem linguagens de alto nível. "
        "3ª Geração — Circuitos Integrados (1965-1980): múltiplos transistores em um chip. "
        "IBM 360 realizava 2 milhões de operações/segundo. Surgem os minicomputadores. "
        "4ª Geração — Microprocessadores (1970-atual): Intel concentrou a CPU em um chip (1971). "
        "Surgem os PCs, notebooks. Lei de Moore: dobra de transistores a cada ~2 anos. "
        "5ª Geração — IA e Nuvem (atual): inteligência artificial, IoT, computação quântica, "
        "cloud computing, interfaces de voz e processamento paralelo massivo.",
    ),

]


# ===========================================================================
# FASE 3 — Enriquecimento de registros rasos (UPDATE por id)
# ===========================================================================

_ENRIQUECIMENTOS = [

    (
        3,
        "software",
        "software",
        "software,programa,instrução,código,lógico,aplicativo,sistema,firmware,open source",
        "Software é o conjunto de instruções, programas e dados que dizem ao hardware o que "
        "fazer. Sem software, o hardware é apenas metal e silício inerte. "
        "Classificação por função: "
        "Software de Sistema: gerencia o hardware (sistemas operacionais, drivers, BIOS). "
        "Software Aplicativo: resolve tarefas do usuário (Word, Photoshop, jogos, apps). "
        "Software de Programação: ferramentas para criar outros softwares (IDEs, compiladores). "
        "Software Embarcado: controla dispositivos específicos (firmware de roteador, SW de carro). "
        "Classificação por licença: proprietário (pago/fechado), freeware (gratuito/fechado), "
        "open source (código aberto), domínio público (sem restrições). "
        "O termo 'software' foi cunhado por John Tukey em 1958 e popularizado nos anos 1960 "
        "como contraponto a 'hardware'. A Lei 9.609/98 protege o software no Brasil da mesma "
        "forma que obras literárias — a violação caracteriza crime.",
    ),

    (
        4,
        "programa de computador",
        "software",
        "programa,computador,instrução,sequência,código,compilado,interpretado,bytecode,executável",
        "Um programa de computador é uma sequência ordenada de instruções que o processador "
        "executa para realizar uma tarefa específica. "
        "Formas de execução: "
        "Compilado: o código-fonte é traduzido integralmente para linguagem de máquina antes "
        "de rodar. Resultado: arquivo executável (.exe, .bin). Ex: programas em C, C++, Rust. "
        "Vantagem: muito rápido na execução. "
        "Interpretado: o código é lido e executado linha a linha por um interpretador. "
        "Ex: Python, JavaScript, PHP, Ruby. Vantagem: flexível, fácil de testar. "
        "Bytecode: compilado para código intermediário e executado por uma VM. "
        "Ex: Java (JVM), Python (CPython). Equilíbrio entre velocidade e portabilidade. "
        "Todo programa, independente da linguagem, se transforma em instruções binárias "
        "(sequências de 0s e 1s) para que a CPU possa executar.",
    ),

    (
        5,
        "linguagens de programacao",
        "programacao",
        "linguagem,programação,java,c,c++,python,javascript,rust,go,kotlin,swift,paradigma",
        "Linguagem de programação é um sistema formal de comunicação com o computador, "
        "com sintaxe e semântica definidas. Permitem escrever programas em nível humano, "
        "que são então traduzidos para linguagem de máquina. "
        "Por paradigma: "
        "Imperativo/Procedural: instrui o computador passo a passo (C, Pascal). "
        "Orientado a Objetos (OOP): organiza código em classes e objetos (Java, Python, C++). "
        "Funcional: trata computação como funções matemáticas (Haskell, Elixir, Scala). "
        "Por nível: baixo nível (Assembly — próximo ao hardware), alto nível (Python, JS — "
        "próximo à linguagem humana). "
        "Mais usadas hoje: JavaScript (web front-end e back-end), Python (IA, dados, scripts), "
        "Java (enterprise, Android), C# (.NET, Unity), C/C++ (sistemas, jogos, embarcados), "
        "Kotlin (Android moderno), Swift (iOS), Rust (sistemas seguros), Go (servidores). "
        "Escolha da linguagem: depende do domínio, ecossistema, performance e preferência da equipe.",
    ),

    (
        6,
        "classes de software",
        "software",
        "classes,software,sistema,embarcado,aplicativo,programação,firmware,driver,so,ide",
        "Os softwares são agrupados em 4 classes principais segundo sua função: "
        "1. Software de Sistema: gerencia e controla os recursos de hardware. "
        "Inclui o Sistema Operacional (Windows, Linux, macOS, Android), drivers de dispositivos, "
        "firmware (BIOS/UEFI) e utilitários do sistema (antivírus, gerenciador de disco). "
        "2. Software Embarcado: projetado para operar dentro de um dispositivo específico, "
        "com recursos limitados e função fixa. Ex: firmware de roteador, SW de micro-ondas, "
        "sistema de freio ABS, controle de elevador. "
        "3. Software Aplicativo: voltado para tarefas do usuário final. "
        "Ex: editores de texto, planilhas, navegadores, jogos, aplicativos móveis, "
        "sistemas de gestão (ERP, CRM). "
        "4. Software de Programação: ferramentas para desenvolvedores criarem outros programas. "
        "Ex: IDEs (VS Code, IntelliJ), compiladores (GCC), interpretadores (Python), "
        "depuradores, frameworks, bibliotecas.",
    ),

    (
        8,
        "categorias de software por licenca",
        "software",
        "categoria,licença,software,proprietário,freeware,shareware,open source,adware,grátis",
        "Softwares são categorizados pelo modelo de licença e distribuição: "
        "Proprietário (Comercial): código fechado, uso mediante pagamento ou contrato. "
        "Ex: Windows, Adobe Photoshop, Microsoft Office, AutoCAD. "
        "Freeware: gratuito para uso, mas código permanece fechado. "
        "Ex: Google Chrome, Adobe Acrobat Reader, WinRAR, VLC. "
        "Shareware: versão de demonstração gratuita com funcionalidades limitadas ou por tempo. "
        "Para uso completo, é necessário pagar. Ex: versões trial de softwares profissionais. "
        "Adware: gratuito, mas exibe anúncios para financiar o desenvolvimento. "
        "Open Source (Código Aberto): código disponível publicamente — pode ser usado, "
        "modificado e redistribuído. Ex: Linux, Firefox, VS Code, LibreOffice, Python. "
        "Domínio Público: sem direitos autorais — totalmente livre, sem restrições. "
        "SaaS (Software como Serviço): acessado pela internet mediante assinatura. "
        "Ex: Google Workspace, Microsoft 365, Figma, Notion.",
    ),

    (
        9,
        "von neumann",
        "arquitetura_computadores",
        "von neumann,modelo,arquitetura,memória,ula,uc,cpu,barramento,programa armazenado,fetch",
        "John Von Neumann (1945) propôs a arquitetura que define os computadores até hoje. "
        "Conceito central: programa armazenado — instruções e dados ficam na MESMA memória. "
        "Antes de Von Neumann, os computadores eram reprogramados fisicamente (religando cabos). "
        "Os 5 componentes do modelo: "
        "Memória: armazena programas e dados em conjunto, acessível pela CPU. "
        "ULA (Unidade Aritmética e Lógica): realiza operações matemáticas e comparações. "
        "UC (Unidade de Controle): busca instruções na memória, decodifica e coordena a execução. "
        "Entrada: recebe dados do mundo externo (teclado, sensores). "
        "Saída: envia resultados para o mundo externo (monitor, impressora). "
        "ULA + UC formam a CPU. O ciclo básico é: Fetch (buscar instrução) → "
        "Decode (decodificar) → Execute (executar) → WriteBack (salvar resultado). "
        "Limitação: 'gargalo de Von Neumann' — a CPU fica ociosa esperando dados da memória, "
        "pois a mesma via é usada para instruções e dados.",
    ),

    (
        11,
        "primeira geração",
        "historia_computacao",
        "primeira geração,válvula,valvula,válvulas,eniac,colossus,edvac,1945,1955,cartão perfurado",
        "Primeira Geração (1945-1955) — Válvulas Eletrônicas: "
        "Componente base: válvula termiônica (tubo de vidro a vácuo que controla corrente elétrica). "
        "ENIAC (1945): primeiro computador eletrônico de propósito geral. 19.000 válvulas, "
        "30 toneladas, 167 m², consumia 200 kW. Realizava 5.000 operações/segundo. "
        "Colossus (1943): usado pelos britânicos para decifrar códigos nazistas na WWII. "
        "Programação: feita por cartões perfurados e painéis de conexões físicas. "
        "Sem sistema operacional — cada programa era inserido manualmente. "
        "Problemas críticos: válvulas queimavam com frequência (calor excessivo), "
        "ocupavam salas inteiras, altíssimo consumo de energia e refrigeração. "
        "Linguagem de máquina pura — sem linguagens de alto nível.",
    ),

    (
        12,
        "segunda geração",
        "historia_computacao",
        "segunda geração,transistor,bell labs,1955,1965,fortran,cobol,linguagem alto nível",
        "Segunda Geração (1955-1965) — Transistores: "
        "Transistor inventado na Bell Labs em 1947 (Shockley, Bardeen, Brattain — Nobel 1956). "
        "Vantagens sobre a válvula: 1/200 do tamanho, 1/100 do consumo elétrico, "
        "mais confiável, praticamente sem aquecimento, vida útil muito maior. "
        "Computadores como o IBM 7094 e o DEC PDP-1 marcaram essa era. "
        "Avanços além do hardware: surgem as primeiras linguagens de alto nível — "
        "FORTRAN (1957, cálculo científico) e COBOL (1959, negócios e bancos). "
        "Surgem os primeiros sistemas operacionais primitivos (batch processing). "
        "Memória de núcleos magnéticos substitui os tubos de Williams. "
        "Computadores ainda eram enormes e caríssimos — só governo e grandes empresas tinham acesso.",
    ),

    (
        13,
        "terceira geração",
        "historia_computacao",
        "terceira geração,circuito integrado,ci,chip,ibm 360,1965,1980,minicomputador,moore",
        "Terceira Geração (1965-1980) — Circuitos Integrados (CIs): "
        "Circuito Integrado: dezenas (depois milhares) de transistores gravados em um único chip "
        "de silício. Inventado por Jack Kilby (Texas Instruments) e Robert Noyce (Fairchild) — "
        "ambos receberam crédito pelo CI. "
        "IBM System/360 (1964): linha de computadores compatíveis entre si — revolução no mercado. "
        "Realizava mais de 2 milhões de adições por segundo. "
        "Lei de Moore (1965): Gordon Moore previu que o número de transistores em um chip "
        "dobraria a cada ~2 anos. Válida por décadas, ainda guia a indústria. "
        "Surgem os minicomputadores (DEC PDP-8): menores e mais baratos que os mainframes. "
        "Linguagens: BASIC (1964), C (1972), Pascal (1970). "
        "Sistemas operacionais evoluídos: UNIX surge em 1969 no Bell Labs.",
    ),

    (
        14,
        "quarta geração",
        "historia_computacao",
        "quarta geração,microprocessador,intel,4004,8086,1970,pc,computador pessoal,dos,windows",
        "Quarta Geração (1970-atual) — Microprocessadores: "
        "Intel 4004 (1971): primeiro microprocessador comercial — CPU inteira em um chip. "
        "Criado por Faggin, Hoff e Mazor para calculadoras, adaptado para computadores. "
        "Intel 8086 (1978): base da arquitetura x86, dominante até hoje em PCs. "
        "IBM PC (1981): popularizou o computador pessoal. Sistema operacional: MS-DOS. "
        "Apple Macintosh (1984): introduziu interface gráfica (GUI) para o público em geral. "
        "Windows (1985): GUI da Microsoft sobre o DOS, versão popular: Windows 3.1 (1992). "
        "Intel Pentium (1993): marco em performance para usuários domésticos. "
        "Lei de Moore aplicada: processadores evoluíam radicalmente a cada 2 anos. "
        "Técnica de litografia permite gravar transistores cada vez menores (de micrômetros "
        "para nanômetros). Hoje os chips têm bilhões de transistores em área de uma unha.",
    ),

    (
        15,
        "quinta geração",
        "historia_computacao",
        "quinta geração,ia,inteligência artificial,quântico,iot,nuvem,cloud,deep learning,llm",
        "Quinta Geração (2000s-atual) — Inteligência Artificial e Conectividade: "
        "Não definida por um componente único, mas por um conjunto de tecnologias emergentes. "
        "Inteligência Artificial: machine learning, deep learning e LLMs (GPT, Gemini, Claude) "
        "capazes de conversar, criar e raciocinar em linguagem natural. "
        "Internet das Coisas (IoT): bilhões de dispositivos conectados — casas inteligentes, "
        "wearables, sensores industriais, cidades inteligentes. "
        "Computação em Nuvem: processamento e armazenamento distribuídos globalmente "
        "(AWS, Google Cloud, Azure). Paga-se pelo uso, sem hardware próprio. "
        "Computação Quântica: qubits em superposição e emaranhamento prometem resolver "
        "problemas intratáveis para computadores clássicos (criptografia, simulações moleculares). "
        "Nanotecnologia: processos de 3nm e abaixo, chips com trilhões de transistores. "
        "Computação neuromórfica: chips inspirados no cérebro humano (Intel Loihi).",
    ),

    (
        16,
        "litografia",
        "hardware",
        "litografia,nanômetros,nm,transistor,tsmc,intel,amd,moore,gravação,chip,silício,EUV",
        "Litografia é o processo de gravação dos transistores no chip de silício usando "
        "luz (ou luz ultravioleta extrema — EUV). Quanto menor o número de nanômetros (nm), "
        "mais transistores cabem no chip — mais poder e eficiência. "
        "Evolução: 10µm (1971) → 1µm (anos 80) → 180nm (1999) → 90nm (2004) → "
        "14nm (2014, Intel Broadwell) → 7nm (2018, TSMC) → 5nm (2020) → 3nm (2022-2023). "
        "1 nanômetro = 1 bilionésimo de metro (menor que um vírus). "
        "Principais fabricantes (foundries): TSMC (Taiwan, líder mundial — fabrica chips "
        "da Apple, NVIDIA, AMD), Samsung (Coreia), Intel Foundry. "
        "EUV (Extreme Ultraviolet): tecnologia da ASML (Holanda) que usa luz de 13,5nm "
        "para gravar padrões ultrafinos — essencial abaixo de 7nm. "
        "Lei de Moore: número de transistores dobra a cada ~2 anos. "
        "O iPhone 15 Pro usa chip A17 Pro em 3nm com 19 bilhões de transistores.",
    ),

    (
        17,
        "futuro da tecnologia",
        "futuro_tecnologia",
        "futuro,nanotecnologia,computador óptico,fótonico,quântico,neuromórfico,dna,computação",
        "Próximas fronteiras da computação: "
        "Computação Quântica: qubits exploram superposição e emaranhamento para resolver "
        "problemas exponencialmente complexos. IBM Q, Google Sycamore, IonQ são líderes. "
        "Computação Fotônica/Óptica: usa fótons (luz) em vez de elétrons para transmitir dados. "
        "Velocidade da luz, sem resistência elétrica, praticamente sem calor. "
        "Computação Neuromórfica: chips que imitam a estrutura do cérebro — neurônios e "
        "sinapses artificiais. Intel Loihi 2, IBM TrueNorth. Eficientes em IA e reconhecimento. "
        "Computação em DNA: moléculas de DNA armazenam dados com densidade enorme — "
        "1 grama de DNA pode guardar 215 petabytes. "
        "Nanotecnologia: transistores atômicos (1-2 átomos de largura), materiais 2D "
        "como grafeno prometem ir além dos limites do silício. "
        "Brain-Computer Interface (BCI): Neuralink e similares conectam cérebro ao computador "
        "diretamente, abrindo possibilidades para deficientes e interfaces imersivas.",
    ),

    (
        19,
        "cpu",
        "hardware",
        "cpu,processador,ula,uc,núcleo,core,clock,ghz,cache,x86,arm,amd,intel,fetch,decode",
        "CPU (Central Processing Unit / Unidade Central de Processamento): componente que "
        "executa todas as instruções dos programas. Composta por: "
        "UC (Unidade de Controle): busca instruções na memória e coordena os demais componentes. "
        "ULA (Unidade Aritmética e Lógica): realiza cálculos e comparações. "
        "Registradores: memória ultrarrápida interna da CPU para dados em uso imediato. "
        "Cache L1/L2/L3: memória rápida hierárquica dentro do chip (L1 menor e mais rápida). "
        "Métricas de desempenho: "
        "Clock (GHz): frequência de operações por segundo. Ex: 3.5 GHz = 3,5 bilhões de ciclos/s. "
        "Núcleos (cores): CPUs modernas têm múltiplos núcleos para paralelismo. "
        "Ex: i9-14900K: 24 núcleos (8 P-cores + 16 E-cores). "
        "Threads: execuções simultâneas por núcleo (Hyper-Threading da Intel). "
        "Arquiteturas: x86/x64 (Intel e AMD, dominam PCs e servidores), "
        "ARM (Apple M-series, Snapdragon — eficiência energética, dominam mobile). "
        "Fabricantes: Intel (Core i, Xeon), AMD (Ryzen, EPYC), Apple (M1/M2/M3/M4).",
    ),

    (
        21,
        "transistor",
        "hardware",
        "transistor,silício,germânio,mosfet,interruptor,eletrônico,bell labs,bilhões,chip",
        "Transistor: componente semicondutor que funciona como interruptor ou amplificador elétrico. "
        "Inventado em 1947 na Bell Labs por Bardeen, Brattain e Shockley (Nobel de Física 1956). "
        "Substituiu as válvulas eletrônicas na 2ª geração — 1/200 do tamanho e 1/100 do consumo. "
        "Tipos: BJT (Bipolar Junction Transistor — amplificação), MOSFET (Metal-Oxide-Semiconductor "
        "Field-Effect Transistor — base dos chips digitais modernos). "
        "Funcionamento digital: o transistor MOSFET atua como chave — ligado (1) ou desligado (0). "
        "Bilhões deles formam os circuitos lógicos de qualquer processador moderno. "
        "Materiais: silício (mais comum), germânio (primeiros transistores), "
        "GaAs (arsenieto de gálio — alta frequência), GaN (nitreto de gálio — potência). "
        "Escala atual: transistores em chips modernos medem 3-5 nanômetros. "
        "O iPhone 15 Pro (A17 Pro, 3nm) contém 19 bilhões de transistores em uma área "
        "menor que uma moeda.",
    ),

    (
        23,
        "computacao quantica",
        "futuro_tecnologia",
        "computação quântica,quântico,quantico,qubit,superposição,emaranhamento,quantum,ibm,google",
        "Computação Quântica usa princípios da mecânica quântica para processar informação "
        "de formas impossíveis para computadores clássicos. "
        "Conceitos fundamentais: "
        "Qubit: unidade de informação quântica. Diferente do bit clássico (0 OU 1), "
        "o qubit pode estar em superposição — 0 E 1 simultaneamente — até ser medido. "
        "Superposição: o qubit existe em múltiplos estados ao mesmo tempo. "
        "Emaranhamento: dois qubits correlacionados — medir um afeta o outro instantaneamente, "
        "independente da distância. "
        "Interferência: amplifica caminhos corretos e cancela os incorretos. "
        "Aplicações potenciais: quebrar criptografia RSA atual (Shor's Algorithm), "
        "simular moléculas para descoberta de medicamentos, otimização logística, "
        "machine learning quântico. "
        "Estado atual (2024): computadores quânticos existem mas são limitados e propensos a erros "
        "(NISQ — Noisy Intermediate-Scale Quantum). "
        "Líderes: IBM (Eagle 127 qubits, Osprey 433 qubits), Google (Sycamore), IonQ, Quantinuum.",
    ),

    (
        27,
        "software aplicativo",
        "software",
        "software,aplicativo,app,usuário,tarefa,escritório,navegador,jogo,mobile,saas,word,chrome",
        "Software Aplicativo (ou simplesmente 'aplicativo' / 'app') é desenvolvido para resolver "
        "tarefas específicas do usuário final, rodando sobre o sistema operacional. "
        "Categorias de software aplicativo: "
        "Produtividade: Microsoft Office (Word, Excel, PowerPoint), LibreOffice, Google Docs. "
        "Navegadores: Chrome, Firefox, Edge, Safari — acesso à web. "
        "Comunicação: WhatsApp, Slack, Microsoft Teams, Gmail, Zoom. "
        "Entretenimento e jogos: Steam, Netflix, Spotify, jogos mobile e PC. "
        "Educacional: Duolingo, Khan Academy, apps de cursos online. "
        "Negócios: ERP (SAP, Totvs), CRM (Salesforce), sistemas de gestão. "
        "Criativo: Photoshop, Illustrator, Figma, DaVinci Resolve, Blender. "
        "Segurança: antivírus, gerenciadores de senha (Bitwarden, 1Password). "
        "Diferença do software de sistema: o aplicativo PRECISA do sistema operacional "
        "para funcionar — ele não gerencia hardware diretamente.",
    ),

]


# ===========================================================================
# FASE 4 — Novos registros (INSERT)
# ===========================================================================

_NOVOS = [

    (
        "software sem licenciamento",
        "software",
        "pirataria,software,sem licença,ilegal,lei 9609,crime,multa,virus,segurança,BSA,ABES",
        "Software sem licenciamento é o uso de software sem autorização legal do titular dos "
        "direitos — popularmente chamado de pirataria. "
        "No Brasil, é crime tipificado na Lei 9.609/98 (Lei de Software) e Lei 9.610/98 "
        "(Direitos Autorais). Penas: detenção de 6 meses a 2 anos + multa para pessoas físicas. "
        "Para empresas: multa de até R$ 20.000 por cópia ilegal + ação cível por danos. "
        "Riscos além do legal: "
        "Software pirata frequentemente contém vírus, ransomware e spyware embutidos. "
        "Sem atualizações de segurança — vulnerabilidades ficam sem correção. "
        "Instabilidade e incompatibilidades que afetam a produtividade. "
        "Fiscalização: BSA (Business Software Alliance) e ABES (Associação Brasileira das "
        "Empresas de Software) realizam auditorias em empresas. Denúncias anônimas são aceitas. "
        "Alternativas legais gratuitas: LibreOffice (Word/Excel), GIMP (Photoshop), "
        "DaVinci Resolve (Premiere), VS Code (IDE), Linux (Windows/macOS).",
        "refine"
    ),

    (
        "placa mae",
        "hardware",
        "placa-mãe,motherboard,socket,slot,chipset,bios,uefi,ddr5,pcie,atx,asus,msi,gigabyte",
        "Placa-mãe (Motherboard): componente central que interliga todos os outros componentes "
        "do computador. Tudo se conecta a ela direta ou indiretamente. "
        "Componentes na placa-mãe: "
        "Socket da CPU: encaixe do processador. Cada geração tem socket diferente. "
        "Ex: LGA1700 (Intel 12ª-13ª gen), AM5 (AMD Ryzen 7000). "
        "Slots de RAM: para os módulos de memória (DDR4 ou DDR5). "
        "Slot PCIe x16: para placa de vídeo dedicada. "
        "Slots M.2 e SATA: para SSDs e HDs. "
        "Chipset: controla a comunicação entre CPU, RAM, armazenamento e periféricos. "
        "BIOS/UEFI: firmware de inicialização — configura boot, voltagens e overclock. "
        "Conectores de alimentação: 24 pinos (energia geral) + 8 pinos (CPU). "
        "Portas traseiras: USB, HDMI, Ethernet, áudio. "
        "Formatos: ATX (30,5×24,4cm — padrão), Micro-ATX (menor, menos slots), "
        "Mini-ITX (17×17cm — builds compactos). "
        "Fabricantes: ASUS ROG/TUF, MSI, Gigabyte AORUS, ASRock.",
        "refine"
    ),

    (
        "barramentos e interfaces",
        "arquitetura_computadores",
        "barramento,bus,pcie,usb,sata,nvme,hdmi,displayport,interface,largura de banda,protocolo",
        "Barramento (Bus) é o canal de comunicação que transfere dados entre componentes do "
        "computador. Tipos por função: "
        "Barramento de Dados: transporta os dados em si entre CPU, memória e periféricos. "
        "Barramento de Endereços: indica onde na memória os dados devem ser lidos ou escritos. "
        "Barramento de Controle: transporta sinais de controle (leitura, escrita, interrupção). "
        "Interfaces modernas de armazenamento e expansão: "
        "PCIe (Peripheral Component Interconnect Express): barramento serial de alta velocidade. "
        "PCIe 4.0 x16: até 32 GB/s (placas de vídeo). PCIe 5.0: dobra para 64 GB/s. "
        "NVMe (via PCIe M.2): SSDs ultrarrápidos — PCIe 4.0 NVMe atinge 7.000 MB/s leitura. "
        "SATA III: SSDs e HDs mais antigos — limite de 600 MB/s. "
        "Interfaces de conexão externa: "
        "USB 3.2 Gen2: 10 Gbps. USB4/Thunderbolt 4: 40 Gbps. "
        "HDMI 2.1: 48 Gbps para 4K 144Hz e 8K 60Hz. "
        "DisplayPort 2.1: até 80 Gbps para monitores de alta resolução e taxa.",
        "refine"
    ),

]


# ===========================================================================
# EXECUÇÃO
# ===========================================================================

def run_audit_fix() -> dict:
    init_db()
    res = {"deletados": 0, "corrigidos": 0, "enriquecidos": 0, "inseridos": 0, "erros": 0}

    with get_connection() as conn:
        c = conn.cursor()

        # FASE 1
        for id_ in _IDS_DELETAR:
            c.execute("SELECT titulo FROM knowledge WHERE id=?", (id_,))
            row = c.fetchone()
            if row:
                c.execute("DELETE FROM knowledge WHERE id=?", (id_,))
                res["deletados"] += 1
                logger.info(f"  [−] Deletado id:{id_} — {row['titulo']}")

        # FASE 2
        for id_, titulo, cat, kw, conteudo in _CORRECOES:
            c.execute("SELECT titulo FROM knowledge WHERE id=?", (id_,))
            if c.fetchone():
                c.execute(
                    "UPDATE knowledge SET titulo=?, categoria=?, palavras_chave=?, conteudo=? WHERE id=?",
                    (titulo, cat, kw, conteudo, id_)
                )
                res["corrigidos"] += 1
                logger.info(f"  [✓] Corrigido id:{id_} — {titulo}")

        # FASE 3
        for id_, titulo, cat, kw, conteudo in _ENRIQUECIMENTOS:
            c.execute("SELECT titulo FROM knowledge WHERE id=?", (id_,))
            if c.fetchone():
                c.execute(
                    "UPDATE knowledge SET titulo=?, categoria=?, palavras_chave=?, conteudo=? WHERE id=?",
                    (titulo, cat, kw, conteudo, id_)
                )
                res["enriquecidos"] += 1
                logger.info(f"  [↑] Enriquecido id:{id_} — {titulo}")

        # FASE 4
        c.execute("SELECT LOWER(titulo) FROM knowledge")
        existentes = {row[0] for row in c.fetchall()}
        for titulo, cat, kw, conteudo, fonte in _NOVOS:
            if titulo.lower() in existentes:
                logger.debug(f"  [=] Já existe: {titulo}")
                continue
            c.execute(
                "INSERT INTO knowledge (titulo, categoria, palavras_chave, conteudo, fonte) VALUES (?,?,?,?,?)",
                (titulo, cat, kw, conteudo, fonte)
            )
            res["inseridos"] += 1
            logger.info(f"  [+] Inserido: {titulo}")

    return res


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    print("=" * 60)
    print("  XBot — Auditoria e Correção Final (audit_fix.py)")
    print("=" * 60)
    antes = contar_registros()
    print(f"\nRegistros antes: {antes}\n")

    res = run_audit_fix()

    depois = contar_registros()
    print(f"\n{'='*60}")
    print("  RESULTADO")
    print(f"{'='*60}")
    print(f"  Deletados              : {res['deletados']}")
    print(f"  Bugs corrigidos        : {res['corrigidos']}")
    print(f"  Registros enriquecidos : {res['enriquecidos']}")
    print(f"  Novos inseridos        : {res['inseridos']}")
    print(f"  Erros                  : {res['erros']}")
    print(f"  Total antes            : {antes}")
    print(f"  Total depois           : {depois}")
    print("=" * 60)
