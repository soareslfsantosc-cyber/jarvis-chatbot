from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import random
import datetime
import re
import logging
import json
from typing import Dict, List, Optional, Any

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Permitir CORS para todas as rotas

# Importar bases de conhecimento
try:
    from knowledge_base import KNOWLEDGE_BASE
    logger.info("Base de conhecimento original carregada")
except ImportError:
    logger.warning("knowledge_base.py não encontrado")
    KNOWLEDGE_BASE = {}

try:
    from knowledge_base_extended import KNOWLEDGE_BASE_EXTENDED, QUIZ_QUESTIONS, EXERCICIOS_PRATICOS
    logger.info("Base de conhecimento expandida carregada")
except ImportError:
    logger.warning("knowledge_base_extended.py não encontrado")
    KNOWLEDGE_BASE_EXTENDED = {}
    QUIZ_QUESTIONS = {}
    EXERCICIOS_PRATICOS = {}

class XBotIA:
    """Classe principal do chatbot XBot com IA conversacional melhorada e expandida"""
    
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
            'quiz': [
                "Que tal testarmos seus conhecimentos, {nome}? Posso criar um quiz sobre arquitetura de computadores, Python ou desenvolvimento web!",
                "Adoro desafios! Quer fazer um quiz comigo, {nome}? Tenho perguntas sobre vários temas!",
                "Vamos testar o que você aprendeu, {nome}? Posso fazer perguntas sobre tecnologia!",
                "Quiz time, {nome}! Escolha um tema: arquitetura, programação ou web design!"
            ],
            'exercicios': [
                "Quer praticar programação, {nome}? Tenho vários exercícios de Python!",
                "Prática leva à perfeição! Posso sugerir exercícios de programação, {nome}!",
                "Que tal alguns exercícios práticos, {nome}? Tenho desafios de diferentes níveis!",
                "Vamos colocar a mão na massa, {nome}! Posso propor exercícios interessantes!"
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
            'quiz': r'\b(quiz|teste|pergunta|questão|desafio|avaliar|testar)\b',
            'exercicios': r'\b(exercício|exercicio|prática|pratica|exemplo|código|programar)\b',
            'arquitetura_computadores': r'\b(arquitetura|computador|hardware|software|cpu|processador|memória|sistema computacional|von neumann|transistor|válvula|circuito integrado|microprocessador|geração|história|evolução|dispositivos|entrada|saída|licença|programa|linguagem|máquina|eniac|intel|pentium|nanotecnologia|gigabyte|placa mãe|ddr5|smart fan)\b',
            'python': r'\b(python|programação|variável|função|if|else|for|while|lista|string|int|float|input|print|compilador|código aberto|bytecode)\b',
            'web_design': r'\b(html|css|javascript|web|site|página|design|cor|psicologia|visual studio|vscode|frontend|backend|responsivo)\b'
        }
        
        # Base de conhecimento integrada
        self.conhecimento_completo = {}
        self._integrar_conhecimento()
        
        # Quiz e exercícios
        self.quiz_questions = QUIZ_QUESTIONS
        self.exercicios = EXERCICIOS_PRATICOS
        
        # Estado do usuário para quiz
        self.user_quiz_state = {}
    
    def _integrar_conhecimento(self):
        """Integra todas as bases de conhecimento"""
        # Base original
        if KNOWLEDGE_BASE:
            for topic, content in KNOWLEDGE_BASE.items():
                if isinstance(content, dict):
                    combined_info = []
                    for key, value in content.items():
                        if isinstance(value, str):
                            combined_info.append(value)
                    if combined_info:
                        self.conhecimento_completo[topic] = " ".join(combined_info)
        
        # Base expandida
        if KNOWLEDGE_BASE_EXTENDED:
            for topic, content in KNOWLEDGE_BASE_EXTENDED.items():
                if isinstance(content, dict):
                    combined_info = []
                    for key, value in content.items():
                        if isinstance(value, str):
                            combined_info.append(f"{key}: {value}")
                    if combined_info:
                        self.conhecimento_completo[topic] = " ".join(combined_info)
                else:
                    self.conhecimento_completo[topic] = str(content)
        
        logger.info(f"Base de conhecimento integrada: {len(self.conhecimento_completo)} tópicos")
    
    def detectar_categoria(self, mensagem: str) -> str:
        """Detecta a categoria da mensagem usando regex"""
        mensagem_lower = mensagem.lower()
        
        for categoria, padrao in self.padroes.items():
            if re.search(padrao, mensagem_lower, re.IGNORECASE):
                return categoria
        
        return 'default'
    
    def buscar_conhecimento(self, mensagem: str) -> Optional[str]:
        """Busca conhecimento em toda a base integrada"""
        mensagem_lower = mensagem.lower()
        
        # Busca direta por tópicos
        for topico, conhecimento in self.conhecimento_completo.items():
            if topico.lower() in mensagem_lower:
                return conhecimento
            
            # Busca por palavras-chave do tópico
            palavras_topico = topico.replace('_', ' ').split()
            if all(palavra.lower() in mensagem_lower for palavra in palavras_topico):
                return conhecimento
        
        # Busca por palavras-chave específicas
        palavras_chave_especificas = {
            'html': ['html', 'html5', 'markup', 'tag', 'elemento'],
            'css': ['css', 'estilo', 'cor', 'design', 'layout'],
            'python': ['python', 'programação', 'código', 'variável', 'função'],
            'javascript': ['javascript', 'js', 'interativo', 'frontend'],
            'visual_studio_code': ['vscode', 'visual studio', 'editor', 'ide'],
            'psicologia_cores': ['cor', 'cores', 'psicologia', 'marketing', 'design'],
            'placas_mae_gigabyte': ['gigabyte', 'placa mãe', 'motherboard', 'hardware'],
            'arquitetura': ['arquitetura', 'computador', 'hardware', 'cpu', 'processador']
        }
        
        for topico, palavras in palavras_chave_especificas.items():
            if any(palavra in mensagem_lower for palavra in palavras):
                if topico in self.conhecimento_completo:
                    return self.conhecimento_completo[topico]
        
        return None
    
    def iniciar_quiz(self, categoria: str, nome_usuario: str) -> str:
        """Inicia um quiz para o usuário"""
        if categoria not in self.quiz_questions:
            return f"Desculpe {nome_usuario}, não tenho quiz sobre {categoria}. Categorias disponíveis: {', '.join(self.quiz_questions.keys())}"
        
        questions = self.quiz_questions[categoria]
        if not questions:
            return f"Não há perguntas disponíveis para {categoria}, {nome_usuario}."
        
        # Inicializar estado do quiz
        self.user_quiz_state[nome_usuario] = {
            'categoria': categoria,
            'questoes': questions.copy(),
            'questao_atual': 0,
            'pontuacao': 0,
            'ativo': True
        }
        
        primeira_questao = questions[0]
        opcoes_texto = "\n".join([f"{i+1}. {opcao}" for i, opcao in enumerate(primeira_questao['opcoes'])])
        
        return f"""🎯 Quiz de {categoria.title()} iniciado, {nome_usuario}!

Questão 1/{len(questions)}:
{primeira_questao['pergunta']}

{opcoes_texto}

Digite o número da sua resposta (1-{len(primeira_questao['opcoes'])})"""
    
    def processar_resposta_quiz(self, resposta: str, nome_usuario: str) -> str:
        """Processa resposta do quiz"""
        if nome_usuario not in self.user_quiz_state or not self.user_quiz_state[nome_usuario]['ativo']:
            return f"Você não está em um quiz ativo, {nome_usuario}. Digite 'quiz' para começar!"
        
        estado = self.user_quiz_state[nome_usuario]
        questao_atual = estado['questoes'][estado['questao_atual']]
        
        try:
            resposta_num = int(resposta) - 1
            if resposta_num < 0 or resposta_num >= len(questao_atual['opcoes']):
                return f"Resposta inválida, {nome_usuario}. Digite um número entre 1 e {len(questao_atual['opcoes'])}."
        except ValueError:
            return f"Por favor digite apenas o número da resposta, {nome_usuario}."
        
        # Verificar resposta
        resultado = ""
        if resposta_num == questao_atual['resposta_correta']:
            estado['pontuacao'] += 1
            resultado = f"✅ Correto, {nome_usuario}!\n{questao_atual['explicacao']}\n\n"
        else:
            resposta_correta = questao_atual['opcoes'][questao_atual['resposta_correta']]
            resultado = f"❌ Incorreto, {nome_usuario}. A resposta correta é: {resposta_correta}\n{questao_atual['explicacao']}\n\n"
        
        # Próxima questão ou fim do quiz
        estado['questao_atual'] += 1
        
        if estado['questao_atual'] >= len(estado['questoes']):
            # Fim do quiz
            pontuacao_final = estado['pontuacao']
            total_questoes = len(estado['questoes'])
            percentual = (pontuacao_final / total_questoes) * 100
            
            estado['ativo'] = False
            
            if percentual >= 80:
                emoji = "🏆"
                comentario = "Excelente!"
            elif percentual >= 60:
                emoji = "👏"
                comentario = "Muito bem!"
            else:
                emoji = "📚"
                comentario = "Continue estudando!"
            
            return f"""{resultado}{emoji} Quiz finalizado, {nome_usuario}!
Pontuação: {pontuacao_final}/{total_questoes} ({percentual:.1f}%)
{comentario}

Digite 'quiz' para fazer outro quiz!"""
        
        else:
            # Próxima questão
            proxima_questao = estado['questoes'][estado['questao_atual']]
            opcoes_texto = "\n".join([f"{i+1}. {opcao}" for i, opcao in enumerate(proxima_questao['opcoes'])])
            
            return f"""{resultado}Questão {estado['questao_atual'] + 1}/{len(estado['questoes'])}:
{proxima_questao['pergunta']}

{opcoes_texto}

Digite o número da sua resposta (1-{len(proxima_questao['opcoes'])})"""
    
    def obter_exercicio(self, categoria: str, nome_usuario: str) -> str:
        """Retorna um exercício prático"""
        if categoria not in self.exercicios:
            return f"Não tenho exercícios para {categoria}, {nome_usuario}. Categorias disponíveis: {', '.join(self.exercicios.keys())}"
        
        exercicios_categoria = self.exercicios[categoria]
        exercicio = random.choice(exercicios_categoria)
        
        return f"""💻 Exercício: {exercicio['titulo']}

📝 Descrição:
{exercicio['descricao']}

💡 Exemplo de código:
```python{exercicio['codigo_exemplo']}```

Tente implementar sua própria versão, {nome_usuario}!"""
    
    def gerar_resposta(self, mensagem: str, nome_usuario: str = "usuário") -> str:
        """Gera resposta baseada na mensagem e contexto"""
        # Verificar se está em quiz ativo
        if nome_usuario in self.user_quiz_state and self.user_quiz_state[nome_usuario]['ativo']:
            # Se a mensagem é um número, processar como resposta do quiz
            if mensagem.strip().isdigit():
                return self.processar_resposta_quiz(mensagem.strip(), nome_usuario)
        
        categoria = self.detectar_categoria(mensagem)
        mensagem_lower = mensagem.lower()
        
        # Comandos especiais
        if 'quiz' in mensagem_lower:
            if 'arquitetura' in mensagem_lower or 'hardware' in mensagem_lower:
                return self.iniciar_quiz('arquitetura', nome_usuario)
            elif 'python' in mensagem_lower or 'programação' in mensagem_lower:
                return self.iniciar_quiz('python', nome_usuario)
            elif 'web' in mensagem_lower or 'html' in mensagem_lower:
                return self.iniciar_quiz('web', nome_usuario)
            else:
                return f"""🎯 Quizzes disponíveis, {nome_usuario}:

1. **Arquitetura de Computadores** - Digite: "quiz arquitetura"
2. **Python** - Digite: "quiz python"  
3. **Desenvolvimento Web** - Digite: "quiz web"

Qual você gostaria de fazer?"""
        
        if 'exercício' in mensagem_lower or 'exercicio' in mensagem_lower:
            if 'python' in mensagem_lower:
                return self.obter_exercicio('python_basico', nome_usuario)
            else:
                return f"""💻 Exercícios disponíveis, {nome_usuario}:

1. **Python Básico** - Digite: "exercício python"

Qual você gostaria de praticar?"""
        
        # Buscar conhecimento específico
        conhecimento = self.buscar_conhecimento(mensagem)
        if conhecimento:
            return f"{conhecimento}\n\nPosso esclarecer mais alguma dúvida sobre este tópico, {nome_usuario}?"
        
        # Respostas padrão por categoria
        respostas_categoria = self.respostas.get(categoria, self.respostas['default'])
        resposta = random.choice(respostas_categoria)
        
        # Personalizar com o nome do usuário
        resposta = resposta.format(nome=nome_usuario)
        
        return resposta
    
    def get_available_topics(self) -> List[str]:
        """Retorna lista de tópicos disponíveis"""
        return list(self.conhecimento_completo.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do bot"""
        return {
            "total_respostas_padrao": sum(len(respostas) for respostas in self.respostas.values()),
            "total_padroes": len(self.padroes),
            "total_conhecimento": len(self.conhecimento_completo),
            "categorias": list(self.padroes.keys()),
            "quiz_categorias": list(self.quiz_questions.keys()),
            "exercicio_categorias": list(self.exercicios.keys())
        }

# Instância do bot
xbot = XBotIA()

# Histórico de conversas e estatísticas
historico_conversas: Dict[str, List[Dict]] = {}
estatisticas_uso: Dict[str, Any] = {
    "total_mensagens": 0,
    "usuarios_unicos": set(),
    "quizzes_realizados": 0,
    "exercicios_solicitados": 0,
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
        
        if 'quiz' in mensagem.lower():
            estatisticas_uso["quizzes_realizados"] += 1
        if 'exercício' in mensagem.lower() or 'exercicio' in mensagem.lower():
            estatisticas_uso["exercicios_solicitados"] += 1
        
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
        
        # Limitar histórico por usuário
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

@app.route("/quiz/<categoria>", methods=["POST"])
def iniciar_quiz_endpoint(categoria: str):
    """Endpoint para iniciar quiz específico"""
    try:
        dados = request.get_json()
        nome_usuario = dados.get("nome_usuario", "usuário")
        
        resposta = xbot.iniciar_quiz(categoria, nome_usuario)
        estatisticas_uso["quizzes_realizados"] += 1
        
        return jsonify({"resposta": resposta})
    except Exception as e:
        logger.error(f"Erro ao iniciar quiz: {e}")
        return jsonify({"erro": "Erro ao iniciar quiz"}), 500

@app.route("/exercicio/<categoria>", methods=["GET"])
def obter_exercicio_endpoint(categoria: str):
    """Endpoint para obter exercício"""
    try:
        nome_usuario = request.args.get("usuario", "usuário")
        resposta = xbot.obter_exercicio(categoria, nome_usuario)
        estatisticas_uso["exercicios_solicitados"] += 1
        
        return jsonify({"resposta": resposta})
    except Exception as e:
        logger.error(f"Erro ao obter exercício: {e}")
        return jsonify({"erro": "Erro ao obter exercício"}), 500

@app.route("/historico/<nome_usuario>", methods=["GET"])
def obter_historico(nome_usuario: str):
    """Endpoint para obter histórico de conversas"""
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
            "quizzes_realizados": estatisticas_uso["quizzes_realizados"],
            "exercicios_solicitados": estatisticas_uso["exercicios_solicitados"],
            "conhecimento": "Base expandida com HTML, CSS, Python, Arquitetura",
            "uptime_segundos": int(uptime.total_seconds()),
            "uptime_formatado": str(uptime).split('.')[0],
            "estatisticas_bot": xbot.get_statistics()
        })
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        return jsonify({"erro": "Erro ao obter status"}), 500

@app.route("/conhecimento", methods=["GET"])
def listar_conhecimento():
    """Endpoint para listar tópicos de conhecimento"""
    try:
        topicos = xbot.get_available_topics()
        return jsonify({
            "topicos_disponiveis": sorted(topicos),
            "total_topicos": len(topicos),
            "categorias_resposta": list(xbot.padroes.keys()),
            "quiz_categorias": list(xbot.quiz_questions.keys()),
            "exercicio_categorias": list(xbot.exercicios.keys())
        })
    except Exception as e:
        logger.error(f"Erro ao listar conhecimento: {e}")
        return jsonify({"erro": "Erro ao listar conhecimento"}), 500

@app.route("/estatisticas", methods=["GET"])
def obter_estatisticas():
    """Endpoint para estatísticas detalhadas"""
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
            "interacoes": {
                "quizzes_realizados": estatisticas_uso["quizzes_realizados"],
                "exercicios_solicitados": estatisticas_uso["exercicios_solicitados"]
            },
            "bot": xbot.get_statistics(),
            "inicio_servico": estatisticas_uso["inicio_servico"].isoformat()
        })
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({"erro": "Erro ao obter estatísticas"}), 500

@app.errorhandler(404)
def not_found(error):
    """Handler para erro 404"""
    return jsonify({"erro": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para erro 500"""
    return jsonify({"erro": "Erro interno do servidor"}), 500

if __name__ == "__main__":
    logger.info("Iniciando XBot v2.1 Expandido...")
    logger.info(f"Tópicos de conhecimento: {len(xbot.get_available_topics())}")
    logger.info(f"Categorias de quiz: {list(xbot.quiz_questions.keys())}")
    logger.info(f"Categorias de exercícios: {list(xbot.exercicios.keys())}")
    
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=True,
        threaded=True
    )

