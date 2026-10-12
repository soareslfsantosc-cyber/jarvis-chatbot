from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import random
import datetime
import re
import logging
from typing import Dict, List, Optional, Any

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Permitir CORS para todas as rotas

# Importar base de conhecimento
try:
    from knowledge_base import KNOWLEDGE_BASE
    logger.info("Base de conhecimento carregada com sucesso")
except ImportError:
    logger.warning("Arquivo knowledge_base.py não encontrado, usando base de conhecimento integrada")
    KNOWLEDGE_BASE = {}

class XBotIA:
    """Classe principal do chatbot XBot com IA conversacional melhorada"""
    
    def __init__(self):
        self.respostas = {
            'saudacoes': [
                "Olá, {nome}! É um prazer falar com você! Em que posso ajudar?",
                "Oi, {nome}! Bem-vindo de volta! Como posso ser útil hoje?",
                "Olá! Sou o XBot da XByte Games Studios. Como posso ajudá-lo, {nome}?",
                "Oi, {nome}! Espero que esteja tendo um ótimo dia! O que posso fazer por você?",
                "Saudações, {nome}! Estou aqui para ajudar. Qual é sua dúvida?"
            ],
            'despedidas': [
                "Até logo, {nome}! Foi um prazer conversar com você!",
                "Tchau, {nome}! Volte sempre que precisar!",
                "Até mais, {nome}! Tenha um excelente dia!",
                "Nos vemos em breve, {nome}! Cuide-se!",
                "Adeus, {nome}! Estarei aqui quando precisar!"
            ],
            'agradecimentos': [
                "De nada, {nome}! Fico feliz em ajudar!",
                "Por nada! Estou aqui sempre que precisar!",
                "É um prazer ajudar, {nome}!",
                "Disponha sempre, {nome}!",
                "Que bom que pude ser útil, {nome}!"
            ],
            'xbyte_games': [
                "A XByte Games Studios é uma empresa inovadora focada em desenvolvimento de jogos e tecnologia!",
                "Somos a XByte Games Studios, criadores de experiências digitais incríveis!",
                "A XByte Games Studios está sempre na vanguarda da tecnologia de jogos!",
                "Nossa missão na XByte Games Studios é criar entretenimento de qualidade!",
                "Na XByte Games Studios, combinamos criatividade e tecnologia para criar jogos únicos!"
            ],
            'jogos': [
                "Adoramos falar sobre jogos! Qual é o seu gênero favorito?",
                "Jogos são nossa paixão na XByte Games Studios! Tem algum favorito?",
                "O mundo dos games é fascinante! Que tipo de jogo você mais gosta?",
                "Games são arte interativa! Qual foi o último jogo que você jogou?",
                "Desenvolvimento de jogos é nossa especialidade! Quer saber mais sobre algum aspecto?"
            ],
            'tecnologia': [
                "A tecnologia está sempre evoluindo! É empolgante acompanhar essas mudanças.",
                "Na XByte Games Studios, usamos as tecnologias mais avançadas!",
                "Tecnologia é o que nos move! Sempre buscamos inovação.",
                "O futuro da tecnologia é promissor! Estamos animados para fazer parte dele.",
                "Tecnologia e criatividade andam juntas em nossos projetos!"
            ],
            'problemas': [
                "Sinto muito por isso, {nome}. Pode me dar mais detalhes sobre o problema?",
                "Que chato, {nome}! Vamos ver como posso ajudar a resolver isso.",
                "Compreendo sua frustração, {nome}. Como posso ser útil?",
                "Lamento ouvir isso, {nome}. Conte-me mais sobre a situação.",
                "Vamos resolver isso juntos, {nome}! Qual é exatamente o problema?"
            ],
            'humor': [
                "Haha! Gosto do seu senso de humor, {nome}!",
                "😄 Você é engraçado, {nome}!",
                "Adoro uma boa piada! Você me fez sorrir, {nome}!",
                "Humor é sempre bem-vindo! Obrigado pela risada, {nome}!",
                "Que bom que mantém o bom humor, {nome}!"
            ],
            'elogios': [
                "Muito obrigado pelo elogio, {nome}! Isso me motiva a ajudar ainda mais!",
                "Que gentil da sua parte, {nome}! Fico feliz em ser útil!",
                "Obrigado, {nome}! Estou sempre me esforçando para melhorar!",
                "Suas palavras são muito importantes para mim, {nome}!"
            ],
            'default': [
                "Interessante, {nome}! Pode me contar mais sobre isso?",
                "Hmm, não tenho certeza sobre isso, {nome}. Pode reformular?",
                "Desculpe, {nome}, não entendi completamente. Pode explicar melhor?",
                "Essa é uma pergunta interessante, {nome}! Pode dar mais detalhes?",
                "Preciso de mais informações para ajudar melhor, {nome}. Pode elaborar?"
            ]
        }
        
        self.padroes = {
            'saudacoes': r'\b(oi|olá|ola|hey|e aí|eai|bom dia|boa tarde|boa noite|salve|hello|hi)\b',
            'despedidas': r'\b(tchau|bye|até logo|até mais|falou|adeus|nos vemos|goodbye)\b',
            'agradecimentos': r'\b(obrigad[oa]|valeu|thanks|brigad[oa]|grato|grata)\b',
            'xbyte_games': r'\b(xbyte|empresa|estúdio|studio|quem são|sobre vocês|desenvolvedores)\b',
            'jogos': r'\b(jogo|game|gaming|jogar|gamer|gameplay|videogame)\b',
            'tecnologia': r'\b(tecnologia|tech|programação|código|desenvolvimento|dev|software|hardware)\b',
            'problemas': r'\b(problema|erro|bug|não funciona|ajuda|socorro|dificuldade)\b',
            'humor': r'\b(haha|kkkk|rsrs|lol|engraçado|piada|risos)\b',
            'elogios': r'\b(legal|bacana|incrível|ótimo|excelente|perfeito|maravilhoso|fantástico)\b',
            'arquitetura_computadores': r'\b(arquitetura|computador|hardware|software|cpu|processador|memória|sistema computacional|von neumann|transistor|válvula|circuito integrado|microprocessador|geração|história|evolução|dispositivos|entrada|saída|licença|programa|linguagem|máquina|eniac|intel|pentium|nanotecnologia)\b'
        }
        
        # Base de conhecimento sobre Arquitetura de Computadores (integrada + externa)
        self.conhecimento_arquitetura = {
            'sistema computacional': "Um sistema computacional consiste em um conjunto de dispositivos eletrônicos, denominado hardware, capazes de processar informações de acordo com um programa, denominado software. Os componentes principais são hardware e software.",
            
            'hardware': "Hardware é a parte física de computadores e outros sistemas microeletrônicos, incluindo CPU, memória e dispositivos de entrada e saída. É um termo geral que se refere aos componentes físicos dos computadores.",
            
            'software': "Software é a parte lógica, o conjunto de instruções e dados processados pelos circuitos eletrônicos do hardware. É a camada que torna o computador útil para o ser humano. O termo foi criado na década de 1940 como um trocadilho com 'hardware'.",
            
            'programa de computador': "Um programa de computador é composto por uma sequência de instruções, que podem ser em linguagem natural ou codificada, interpretada e executada por um processador ou máquina virtual. Quando está em linguagem de máquina, pode ser executado diretamente pelo processador.",
            
            'linguagens de programação': "Programas são geralmente escritos em linguagens de programação como Java, Visual Basic, C, C++, PHP, Python, JavaScript, que se aproximam das linguagens humanas. Raramente se usa linguagem de máquina diretamente.",
            
            'classes de software': "As principais classes são: Software de Sistema (firmware, drivers, SO), Software Embarcado (para máquinas específicas), Software Aplicativo (tarefas específicas do usuário) e Software de Programação (ferramentas para desenvolvedores).",
            
            'licenciamento': "Uma licença de software define e restringe como se pode utilizar o software. Tipos incluem: temporárias, permanentes, por quantidade de uso, de rede/virtuais, perpétuas, do tipo chaves e hard lock. Software não licenciado pode causar problemas legais e de desempenho.",
            
            'categorias de software': "Software Proprietário (uso restrito), Domínio Público (gratuito, sem direitos autorais), Adware (com publicidade), Freeware (gratuito), Shareware (teste gratuito, depois pago), Código Aberto (open source).",
            
            'von neumann': "John Von Neumann propôs o modelo fundamental dos computadores modernos, composto por: memória física (para programas e dados), Unidade Aritmética e Lógica (ULA), Unidade de Controle (UC) e equipamentos de entrada e saída. A ULA e UC formam a CPU.",
            
            'gerações de computadores': "Geração Zero (1645-1945): computadores mecânicos. Primeira Geração (1945-1955): válvulas eletrônicas. Segunda Geração (1955-1965): transistores. Terceira Geração (1965-1980): circuitos integrados. Quarta Geração (1970-atualidade): microprocessadores. Quinta Geração (atual): IA e computação quântica.",
            
            'primeira geração': "Computadores com válvulas eletrônicas (1945-1955). Exemplo: ENIAC com 19.000 válvulas, pesava 30 toneladas, consumia 200 quilowatts. Entrada de dados por cartões perfurados. Problemas: queima frequente de válvulas, alto consumo de energia.",
            
            'segunda geração': "Transistores substituíram válvulas (1955-1965). Transistor desenvolvido pela Bell Labs em 1948. Vantagens: 1/200 do tamanho de uma válvula, consumo 1/100 da energia, mais confiável, aquecimento mínimo.",
            
            'terceira geração': "Circuitos Integrados (1965-1980). CIs incorporam inúmeros transistores em um único chip. Vantagens: maior confiabilidade, muito menores, baixo consumo, custo menor. Exemplo: IBM 360 realizava 2 milhões de adições por segundo.",
            
            'quarta geração': "Microprocessadores (1970-atualidade). Intel lançou o primeiro microprocessador em 1970, concentrando CPU, controladores de memória e E/S. Evolução da miniaturização com técnicas como litografia. Intel Pentium foi revolucionário nos anos 90.",
            
            'quinta geração': "Era atual da computação, caracterizada por: Inteligência Artificial, computação quântica, nanotecnologia, Internet das Coisas (IoT), computação em nuvem, processamento paralelo massivo e interfaces naturais de usuário.",
            
            'litografia': "Técnica de construção dos componentes internos do processador que permite colocar milhares de transistores em um chip pequeno. Refere-se ao tamanho de cada transistor, medido em nanômetros (bilionésima parte do metro). Atualmente temos processos de 3nm.",
            
            'futuro da tecnologia': "Nanotecnologia permite miniaturização extrema. Computadores ópticos usam feixes de luz em cubos ópticos. Computadores quânticos usam átomos como transistores, com unidades de informação que podem assumir qualquer valor entre 0 e 1 (qubits).",
            
            'dispositivos entrada saída': "Elementos de interface entre usuário e computador. Funções: receber/enviar informações ao meio exterior e converter informações para forma inteligível. Categorias: entrada (teclado, mouse), saída (monitor, impressora), entrada e saída (pen drive, HD externo).",
            
            'cpu': "Unidade Central de Processamento, formada pela ULA (Unidade Aritmética e Lógica) e UC (Unidade de Controle), junto com registradores. É responsável por buscar instruções na memória e executá-las. Moderna CPUs têm múltiplos núcleos.",
            
            'memória': "Armazena programas e dados em formato binário (0s e 1s). A CPU busca instruções e dados diretamente da memória para processamento. Tipos: RAM (volátil), ROM (não-volátil), cache (ultra-rápida).",
            
            'transistor': "Dispositivo que substituiu as válvulas na segunda geração. Função básica: interruptor eletrônico para operações lógicas. Materiais: silício, germânio, gálio e óxidos. Muito menor e mais eficiente que válvulas. Base de toda eletrônica moderna.",
            
            'inteligencia artificial': "Campo da ciência da computação que busca criar máquinas capazes de realizar tarefas que normalmente requerem inteligência humana. Inclui machine learning, deep learning, processamento de linguagem natural e visão computacional.",
            
            'computacao quantica': "Paradigma de computação que utiliza fenômenos quânticos como superposição e emaranhamento para processar informações. Qubits podem existir em múltiplos estados simultaneamente, oferecendo potencial para resolver problemas complexos exponencialmente mais rápido."
        }
        
        # Integrar conhecimento externo se disponível
        if KNOWLEDGE_BASE:
            self._integrate_external_knowledge()
    
    def _integrate_external_knowledge(self):
        """Integra conhecimento da base externa"""
        try:
            for topic, content in KNOWLEDGE_BASE.items():
                if isinstance(content, dict):
                    # Combinar informações do dicionário
                    combined_info = []
                    for key, value in content.items():
                        if isinstance(value, str):
                            combined_info.append(value)
                    
                    if combined_info:
                        self.conhecimento_arquitetura[topic] = " ".join(combined_info)
            
            logger.info(f"Integrados {len(KNOWLEDGE_BASE)} tópicos da base externa")
        except Exception as e:
            logger.error(f"Erro ao integrar base de conhecimento externa: {e}")
    
    def detectar_categoria(self, mensagem: str) -> str:
        """Detecta a categoria da mensagem usando regex"""
        mensagem_lower = mensagem.lower()
        
        for categoria, padrao in self.padroes.items():
            if re.search(padrao, mensagem_lower, re.IGNORECASE):
                return categoria
        
        return 'default'
    
    def buscar_conhecimento_arquitetura(self, mensagem: str) -> Optional[str]:
        """Busca conhecimento específico sobre arquitetura de computadores"""
        mensagem_lower = mensagem.lower()
        
        # Busca direta por palavras-chave
        for palavra_chave, conhecimento in self.conhecimento_arquitetura.items():
            # Busca por palavra-chave completa ou partes dela
            if palavra_chave in mensagem_lower:
                return conhecimento
            
            # Busca por palavras individuais da chave
            palavras_chave = palavra_chave.split()
            if len(palavras_chave) > 1:
                if all(palavra in mensagem_lower for palavra in palavras_chave):
                    return conhecimento
        
        # Busca por sinônimos e termos relacionados
        sinonimos = {
            'válvula': 'primeira geração',
            'valvula': 'primeira geração',
            'eniac': 'primeira geração',
            'transistor': 'segunda geração',
            'ci': 'terceira geração',
            'circuito integrado': 'terceira geração',
            'ibm 360': 'terceira geração',
            'microprocessador': 'quarta geração',
            'intel': 'quarta geração',
            'pentium': 'quarta geração',
            'nanotecnologia': 'futuro da tecnologia',
            'quântico': 'computacao quantica',
            'quantico': 'computacao quantica',
            'óptico': 'futuro da tecnologia',
            'optico': 'futuro da tecnologia',
            'teclado': 'dispositivos entrada saída',
            'mouse': 'dispositivos entrada saída',
            'monitor': 'dispositivos entrada saída',
            'impressora': 'dispositivos entrada saída',
            'ia': 'inteligencia artificial',
            'ai': 'inteligencia artificial',
            'machine learning': 'inteligencia artificial',
            'deep learning': 'inteligencia artificial'
        }
        
        for termo, chave in sinonimos.items():
            if termo in mensagem_lower and chave in self.conhecimento_arquitetura:
                return self.conhecimento_arquitetura[chave]
        
        return None
    
    def gerar_resposta(self, mensagem: str, nome_usuario: str = "usuário") -> str:
        """Gera resposta baseada na mensagem e contexto"""
        categoria = self.detectar_categoria(mensagem)
        
        # Primeiro, verifica se é uma pergunta sobre arquitetura de computadores
        if categoria == 'arquitetura_computadores':
            conhecimento = self.buscar_conhecimento_arquitetura(mensagem)
            if conhecimento:
                return f"{conhecimento}\n\nPosso explicar mais alguma coisa sobre arquitetura de computadores, {nome_usuario}?"
        
        # Busca conhecimento mesmo se não foi categorizado como arquitetura
        conhecimento = self.buscar_conhecimento_arquitetura(mensagem)
        if conhecimento:
            return f"{conhecimento}\n\nEssa informação foi útil, {nome_usuario}? Posso esclarecer mais alguma dúvida?"
        
        # Se não encontrou conhecimento específico, usa as respostas padrão
        respostas_categoria = self.respostas.get(categoria, self.respostas['default'])
        resposta = random.choice(respostas_categoria)
        
        # Personalizar com o nome do usuário
        resposta = resposta.format(nome=nome_usuario)
        
        return resposta
    
    def get_available_topics(self) -> List[str]:
        """Retorna lista de tópicos disponíveis"""
        return list(self.conhecimento_arquitetura.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do bot"""
        return {
            "total_respostas_padrao": sum(len(respostas) for respostas in self.respostas.values()),
            "total_padroes": len(self.padroes),
            "total_conhecimento": len(self.conhecimento_arquitetura),
            "categorias": list(self.padroes.keys())
        }

# Instância do bot
xbot = XBotIA()

# Histórico de conversas (em produção, usar banco de dados)
historico_conversas: Dict[str, List[Dict]] = {}
estatisticas_uso: Dict[str, Any] = {
    "total_mensagens": 0,
    "usuarios_unicos": set(),
    "inicio_servico": datetime.datetime.now()
}

@app.route("/")
def home():
    """Página principal do chatbot"""
    return render_template("index.html")

@app.route("/responder", methods=["POST"])
def resposta():
    """Endpoint principal para processar mensagens"""
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({"erro": "Dados JSON inválidos"}), 400
        
        mensagem = dados.get("mensagem", "").strip()
        nome_usuario = dados.get("nome_usuario", "usuário").strip()
        
        if not mensagem:
            return jsonify({"resposta": "Por favor, digite uma mensagem!"})
        
        if len(mensagem) > 500:
            return jsonify({"resposta": "Mensagem muito longa! Máximo de 500 caracteres."})
        
        # Gerar resposta usando a IA do bot
        resposta_bot = xbot.gerar_resposta(mensagem, nome_usuario)
        
        # Atualizar estatísticas
        estatisticas_uso["total_mensagens"] += 1
        estatisticas_uso["usuarios_unicos"].add(nome_usuario)
        
        # Salvar no histórico
        timestamp = datetime.datetime.now().isoformat()
        if nome_usuario not in historico_conversas:
            historico_conversas[nome_usuario] = []
        
        historico_conversas[nome_usuario].append({
            'timestamp': timestamp,
            'usuario': mensagem,
            'bot': resposta_bot,
            'categoria': xbot.detectar_categoria(mensagem)
        })
        
        # Limitar histórico por usuário (últimas 100 mensagens)
        if len(historico_conversas[nome_usuario]) > 100:
            historico_conversas[nome_usuario] = historico_conversas[nome_usuario][-100:]
        
        logger.info(f"Mensagem processada para {nome_usuario}: {mensagem[:50]}...")
        
        return jsonify({
            "resposta": resposta_bot,
            "timestamp": timestamp,
            "categoria": xbot.detectar_categoria(mensagem)
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        return jsonify({
            "resposta": "Desculpe, ocorreu um erro interno. Tente novamente.",
            "erro": str(e)
        }), 500

@app.route("/historico/<nome_usuario>", methods=["GET"])
def obter_historico(nome_usuario: str):
    """Endpoint para obter histórico de conversas de um usuário"""
    try:
        historico = historico_conversas.get(nome_usuario, [])
        return jsonify({
            "historico": historico,
            "total_mensagens": len(historico)
        })
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}")
        return jsonify({"erro": "Erro ao obter histórico"}), 500

@app.route("/status", methods=["GET"])
def status():
    """Endpoint para verificar status do bot"""
    try:
        uptime = datetime.datetime.now() - estatisticas_uso["inicio_servico"]
        
        return jsonify({
            "status": "online",
            "versao": "2.1",
            "desenvolvedor": "XByte Games Studios",
            "usuarios_ativos": len(historico_conversas),
            "usuarios_unicos": len(estatisticas_uso["usuarios_unicos"]),
            "total_mensagens": estatisticas_uso["total_mensagens"],
            "conhecimento": "Arquitetura de Computadores integrada",
            "uptime_segundos": int(uptime.total_seconds()),
            "uptime_formatado": str(uptime).split('.')[0],
            "estatisticas_bot": xbot.get_statistics()
        })
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        return jsonify({"erro": "Erro ao obter status"}), 500

@app.route("/conhecimento", methods=["GET"])
def listar_conhecimento():
    """Endpoint para listar tópicos de conhecimento disponíveis"""
    try:
        topicos = xbot.get_available_topics()
        return jsonify({
            "topicos_disponiveis": sorted(topicos),
            "total_topicos": len(topicos),
            "categorias_resposta": list(xbot.padroes.keys())
        })
    except Exception as e:
        logger.error(f"Erro ao listar conhecimento: {e}")
        return jsonify({"erro": "Erro ao listar conhecimento"}), 500

@app.route("/estatisticas", methods=["GET"])
def obter_estatisticas():
    """Endpoint para obter estatísticas detalhadas"""
    try:
        uptime = datetime.datetime.now() - estatisticas_uso["inicio_servico"]
        
        # Estatísticas por categoria
        categorias_count = {}
        for historico in historico_conversas.values():
            for msg in historico:
                categoria = msg.get('categoria', 'unknown')
                categorias_count[categoria] = categorias_count.get(categoria, 0) + 1
        
        return jsonify({
            "uptime": {
                "segundos": int(uptime.total_seconds()),
                "formatado": str(uptime).split('.')[0]
            },
            "usuarios": {
                "total_unicos": len(estatisticas_uso["usuarios_unicos"]),
                "com_historico": len(historico_conversas)
            },
            "mensagens": {
                "total": estatisticas_uso["total_mensagens"],
                "por_categoria": categorias_count
            },
            "bot": xbot.get_statistics(),
            "inicio_servico": estatisticas_uso["inicio_servico"].isoformat()
        })
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({"erro": "Erro ao obter estatísticas"}), 500

@app.route("/limpar_historico/<nome_usuario>", methods=["DELETE"])
def limpar_historico_usuario(nome_usuario: str):
    """Endpoint para limpar histórico de um usuário específico"""
    try:
        if nome_usuario in historico_conversas:
            del historico_conversas[nome_usuario]
            return jsonify({"mensagem": f"Histórico de {nome_usuario} limpo com sucesso"})
        else:
            return jsonify({"mensagem": "Usuário não encontrado"}), 404
    except Exception as e:
        logger.error(f"Erro ao limpar histórico: {e}")
        return jsonify({"erro": "Erro ao limpar histórico"}), 500

@app.errorhandler(404)
def not_found(error):
    """Handler para erro 404"""
    return jsonify({"erro": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para erro 500"""
    return jsonify({"erro": "Erro interno do servidor"}), 500

if __name__ == "__main__":
    logger.info("Iniciando XBot v2.1...")
    logger.info(f"Tópicos de conhecimento carregados: {len(xbot.get_available_topics())}")
    
    # Configuração para produção vs desenvolvimento
    debug_mode = True  # Alterar para False em produção
    
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=debug_mode,
        threaded=True
    )

