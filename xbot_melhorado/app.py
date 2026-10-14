"""
app.py — XBot v0.3.0 Beta (aplicação ÚNICA)

Desde a revisão de segurança existe um só ponto de entrada. O que vivia no antigo
app_improved.py (quiz, exercícios, estatísticas de quiz) foi incorporado aqui, junto com
SQLite, motor de raciocínio, login/sessão e as proteções (CSRF, CORS restrito, limite de
visitante validado no servidor, bloqueio de tentativas de login).

    python app.py            # lê XBOT_* do ambiente / arquivo .env  (veja README e .env.example)
    python app_improved.py   # continua funcionando: apenas delega para este arquivo
    wsgi.py                  # entrada para waitress/gunicorn
"""

import datetime
import logging
import os
import random
import re
import sys
import threading
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from flask import Flask, g, jsonify, render_template, request, session
from flask.sessions import SecureCookieSessionInterface
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

import relogio
from config import Config, ConfigError
from historico import HistoricoConversas
from seguranca import (
    ErroRequisicao, campo_texto, impressao_do_cliente, ip_do_cliente,
    limpar_nome_exibicao, obter_json_objeto, registrar_seguranca,
    renovar_token_csrf, token_csrf,
)
from database import db as banco
from database import visitantes
from database.auth import autenticar, buscar_usuario_por_id, cadastrar
from database.bootstrap import inicializar_banco
from database.db import contar_registros, listar_tabelas
from database.reasoning import RaciocinioCognitivo

# O logging é configurado em main() (ou pelo servidor WSGI); aqui só pegamos o logger do módulo.
logger = logging.getLogger(__name__)

# Importar base de conhecimento (mantida como fallback)
try:
    from knowledge_base import KNOWLEDGE_BASE
    logger.info("Base de conhecimento carregada com sucesso")
except ImportError:
    logger.warning("Arquivo knowledge_base.py não encontrado, usando base de conhecimento integrada")
    KNOWLEDGE_BASE = {}

# Quiz e exercícios (vinham do antigo app_improved.py)
try:
    from knowledge_base_extended import QUIZ_QUESTIONS, EXERCICIOS_PRATICOS
except ImportError:
    logger.warning("knowledge_base_extended.py não encontrado: quiz e exercícios indisponíveis")
    QUIZ_QUESTIONS = {}
    EXERCICIOS_PRATICOS = {}

class XBotIA:
    """Classe principal do chatbot XBot com IA conversacional melhorada"""
    
    def __init__(self, raciocinio: Optional[RaciocinioCognitivo] = None):
        # Motor de raciocínio injetado pelo app (um por aplicação, cada um com seu cache do SQLite)
        self.raciocinio = raciocinio
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
            'arquitetura_computadores': r'\b(arquitetura|computador|hardware|software|cpu|processador|memória|sistema computacional|von neumann|transistor|válvula|circuito integrado|microprocessador|geração|história|evolução|dispositivos|entrada|saída|licença|programa|linguagem|máquina|eniac|intel|pentium|nanotecnologia)\b',
            # Categorias do antigo app_improved.py. Ficam DEPOIS das demais para não mudar a
            # categoria de nenhuma mensagem que já era reconhecida ('pergunta' e 'questão'
            # ficaram de fora: são comuns demais para sugerir um quiz).
            'quiz': r'\b(quiz|teste|desafio|avaliar|testar)\b',
            'exercicios': r'\b(exercício|exercicio|prática|pratica|exemplo|código|programar)\b'
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
        
        # v0.3.0 Beta: rastrear origem da última resposta (sqlite ou fallback_python)
        self.ultima_fonte      = "indefinido"
        self.ultima_confianca  = "indefinido"   # alta/media/baixa/nenhuma
        self.ultimos_relacionados = []           # tópicos correlacionados
        self.ultimas_sugestoes    = []           # próximas perguntas sugeridas
        self.ultimo_titulo_kb     = None         # título do último conhecimento usado

        # v0.3.0 (unificação com o antigo app_improved.py): quiz e exercícios
        self.quiz_questions = QUIZ_QUESTIONS
        self.exercicios = EXERCICIOS_PRATICOS
        self.user_quiz_state: "OrderedDict[str, Dict]" = OrderedDict()   # chave = dono da sessão
        self._max_quizzes_ativos = 1000                                   # teto de memória

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
    
    # ------------------------------------------------------------------
    # Quiz e exercícios (portados do antigo app_improved.py).
    # O estado do quiz é do DONO da sessão (u:<id> / g:<visitante>), não do nome digitado:
    # duas pessoas com o mesmo nome não misturam quizzes nem leem o andamento uma da outra.
    # ------------------------------------------------------------------

    def _quiz_ativo(self, dono: str) -> bool:
        estado = self.user_quiz_state.get(dono)
        return bool(estado and estado['ativo'])

    def iniciar_quiz(self, categoria: str, dono: str, nome_usuario: str) -> str:
        """Inicia um quiz para o dono da sessão"""
        if categoria not in self.quiz_questions:
            return f"Desculpe {nome_usuario}, não tenho quiz sobre {categoria[:40]}. Categorias disponíveis: {', '.join(self.quiz_questions.keys())}"

        questions = self.quiz_questions[categoria]
        if not questions:
            return f"Não há perguntas disponíveis para {categoria}, {nome_usuario}."

        # Inicializar estado do quiz
        self.user_quiz_state[dono] = {
            'categoria': categoria,
            'questoes': questions.copy(),
            'questao_atual': 0,
            'pontuacao': 0,
            'ativo': True
        }
        self.user_quiz_state.move_to_end(dono)
        while len(self.user_quiz_state) > self._max_quizzes_ativos:
            self.user_quiz_state.popitem(last=False)

        primeira_questao = questions[0]
        opcoes_texto = "\n".join([f"{i+1}. {opcao}" for i, opcao in enumerate(primeira_questao['opcoes'])])

        return f"""🎯 Quiz de {categoria.title()} iniciado, {nome_usuario}!

Questão 1/{len(questions)}:
{primeira_questao['pergunta']}

{opcoes_texto}

Digite o número da sua resposta (1-{len(primeira_questao['opcoes'])})"""

    def processar_resposta_quiz(self, resposta: str, dono: str, nome_usuario: str) -> str:
        """Processa resposta do quiz"""
        if not self._quiz_ativo(dono):
            return f"Você não está em um quiz ativo, {nome_usuario}. Digite 'quiz' para começar!"

        estado = self.user_quiz_state[dono]
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
            return f"Não tenho exercícios para {categoria[:40]}, {nome_usuario}. Categorias disponíveis: {', '.join(self.exercicios.keys())}"

        exercicios_categoria = self.exercicios[categoria]
        exercicio = random.choice(exercicios_categoria)

        return f"""💻 Exercício: {exercicio['titulo']}

📝 Descrição:
{exercicio['descricao']}

💡 Exemplo de código:
```python{exercicio['codigo_exemplo']}```

Tente implementar sua própria versão, {nome_usuario}!"""

    def _comando_quiz(self, mensagem_lower: str, dono: str, nome_usuario: str) -> str:
        """Mensagem que cita 'quiz': inicia o quiz do tema pedido ou lista os temas."""
        if 'arquitetura' in mensagem_lower or 'hardware' in mensagem_lower:
            return self.iniciar_quiz('arquitetura', dono, nome_usuario)
        elif 'python' in mensagem_lower or 'programação' in mensagem_lower:
            return self.iniciar_quiz('python', dono, nome_usuario)
        elif 'web' in mensagem_lower or 'html' in mensagem_lower:
            return self.iniciar_quiz('web', dono, nome_usuario)
        return f"""🎯 Quizzes disponíveis, {nome_usuario}:

1. **Arquitetura de Computadores** - Digite: "quiz arquitetura"
2. **Python** - Digite: "quiz python"
3. **Desenvolvimento Web** - Digite: "quiz web"

Qual você gostaria de fazer?"""

    def _comando_exercicio(self, mensagem_lower: str, nome_usuario: str) -> str:
        """Mensagem que cita 'exercício': entrega um exercício de Python ou lista os temas."""
        if 'python' in mensagem_lower:
            return self.obter_exercicio('python_basico', nome_usuario)
        return f"""💻 Exercícios disponíveis, {nome_usuario}:

1. **Python Básico** - Digite: "exercício python"

Qual você gostaria de praticar?"""

    # ------------------------------------------------------------------
    # Geração de resposta
    # ------------------------------------------------------------------

    def _zerar_metadados(self):
        """
        Zera os metadados da última resposta. Sem isso, um caminho que não define
        confiança/relacionados (fallback, resposta padrão, quiz) herdava os valores da
        resposta ANTERIOR — que podia ter sido de outro usuário.
        """
        self.ultima_fonte = "indefinido"
        self.ultima_confianca = "indefinido"
        self.ultimos_relacionados = []
        self.ultimas_sugestoes = []
        self.ultimo_titulo_kb = None

    def gerar_resposta(self, mensagem: str, nome_usuario: str = "usuário",
                       historico_sessao: Optional[List[Dict]] = None,
                       dono: Optional[str] = None) -> str:
        """
        Gera resposta baseada na mensagem e contexto.

        Fluxo v0.3.0 Beta:
          0. Quiz/exercício (comandos explícitos, vindos do antigo app_improved.py)
          1. Motor de raciocínio sobre o SQLite
          2. Se não encontrou → fallback: lógica Python original
          3. Sem nada → resposta padrão da categoria

        `historico_sessao` e `dono` são definidos pelo SERVIDOR (sessão validada); o nome
        digitado pelo usuário serve apenas para tratá-lo pelo nome.
        """
        self._zerar_metadados()
        historico_sessao = historico_sessao or []
        dono = dono or f"n:{nome_usuario}"
        categoria = self.detectar_categoria(mensagem)
        mensagem_lower = mensagem.lower()

        # ================================================================
        # Quiz e exercícios
        # ================================================================
        if self._quiz_ativo(dono) and mensagem.strip().isdigit():
            self.ultima_fonte = "quiz"
            return self.processar_resposta_quiz(mensagem.strip(), dono, nome_usuario)
        if 'quiz' in mensagem_lower:
            self.ultima_fonte = "quiz"
            return self._comando_quiz(mensagem_lower, dono, nome_usuario)
        if 'exercício' in mensagem_lower or 'exercicio' in mensagem_lower:
            self.ultima_fonte = "exercicio"
            return self._comando_exercicio(mensagem_lower, nome_usuario)

        # ================================================================
        # v0.3.0 Beta — MOTOR DE RACIOCÍNIO COGNITIVO (prioridade máxima)
        # ================================================================
        try:
            resultado_r = (
                self.raciocinio.analisar(mensagem, historico_sessao)
                if self.raciocinio is not None else None
            )

            if resultado_r is not None and resultado_r.nivel_confianca in ('alta', 'media', 'baixa'):
                self.ultima_fonte         = "reasoning"
                self.ultima_confianca     = resultado_r.nivel_confianca
                self.ultimos_relacionados = resultado_r.topicos_relacionados
                self.ultimas_sugestoes    = resultado_r.sugestoes_proximas
                self.ultimo_titulo_kb     = resultado_r.vencedor.titulo
                logger.info(
                    f"[Reasoning] '{resultado_r.vencedor.titulo}' | "
                    f"conf={resultado_r.nivel_confianca} | "
                    f"margem={resultado_r.margem_lideranca:.1f}"
                )
                resposta_final = resultado_r.resposta_construida
                if resultado_r.nivel_confianca == 'baixa':
                    resposta_final += f"\n\nSe quiser mais detalhes, {nome_usuario}, pode reformular a pergunta!"
                else:
                    resposta_final += f"\n\nPosso explicar mais alguma coisa, {nome_usuario}?"
                return resposta_final

        except Exception as e:
            logger.warning(
                f"[XBot] Falha no Reasoning Engine, usando fallback: {e}"
            )
        # ================================================================
        # FALLBACK — base de conhecimento Python original
        # ================================================================

        # Primeiro, verifica se é uma pergunta sobre arquitetura de computadores
        if categoria == 'arquitetura_computadores':
            conhecimento = self.buscar_conhecimento_arquitetura(mensagem)
            if conhecimento:
                self.ultima_fonte = "fallback_python"
                return f"{conhecimento}\n\nPosso explicar mais alguma coisa sobre arquitetura de computadores, {nome_usuario}?"

        # Busca conhecimento mesmo se não foi categorizado como arquitetura
        conhecimento = self.buscar_conhecimento_arquitetura(mensagem)
        if conhecimento:
            self.ultima_fonte = "fallback_python"
            return f"{conhecimento}\n\nEssa informação foi útil, {nome_usuario}? Posso esclarecer mais alguma dúvida?"

        # Se não encontrou conhecimento específico, usa as respostas padrão
        self.ultima_fonte = "resposta_padrao"
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
            "categorias": list(self.padroes.keys()),
            "quiz_categorias": list(self.quiz_questions.keys()),
            "exercicio_categorias": list(self.exercicios.keys())
        }


# ============================================================================
# v0.3.0 Beta — PRÉVIA PARA VISITANTES
# ============================================================================

def _truncar_para_guest(texto: str, limite: int = 220) -> str:
    """
    Trunca a resposta do XBot para visitantes não cadastrados, cortando em
    fim de frase sempre que possível, e acrescenta uma chamada para cadastro.
    Remove rodapés (relacionados/sugestões/pergunta de fechamento) do corpo
    antes de truncar, para não cortar no meio deles.
    """
    corpo = texto
    for marcador in ('\n\n📚', '\n\n💡', '\n\nPosso explicar', '\n\nSe quiser mais'):
        corpo = corpo.split(marcador)[0]

    if len(corpo) <= limite:
        trecho = corpo
    else:
        trecho = corpo[:limite]
        ultimo_ponto = trecho.rfind('. ')
        trecho = trecho[:ultimo_ponto + 1] if ultimo_ponto > 50 else trecho.rstrip() + '...'

    return trecho + "\n\n🔒 Essa é só uma prévia. Cadastre-se gratuitamente para ver a explicação completa e sem limites!"


# ============================================================================
# Aplicação Flask (fábrica)
# ============================================================================

class _SessaoXBot(SecureCookieSessionInterface):
    """Cookie de sessão com Secure automático: só marca Secure quando a requisição chegou por HTTPS."""

    def get_cookie_secure(self, app):
        configurado = app.config["XBOT"].cookie_secure
        return request.is_secure if configurado is None else configurado


class _Estado:
    """Tudo que muda durante a execução, preso à instância do app (nada de globais soltas)."""

    def __init__(self):
        self.raciocinio = RaciocinioCognitivo()      # cache próprio dos registros do SQLite
        self.bot = XBotIA(self.raciocinio)
        self.historico = HistoricoConversas()
        # O XBotIA guarda "última fonte/confiança/relacionados" em atributos da instância:
        # gerar a resposta e ler esses atributos acontece sob esta trava, para duas requisições
        # simultâneas não misturarem metadados.
        self.trava = threading.RLock()
        self.estatisticas: Dict[str, Any] = {
            "total_mensagens": 0,
            "usuarios_unicos": set(),
            "quizzes_realizados": 0,
            "exercicios_solicitados": 0,
            "inicio_servico": datetime.datetime.now(),
        }


def create_app(config: Optional[Config] = None, *, inicializar: bool = True) -> Flask:
    """
    Cria a aplicação. Sem `config`, lê XBOT_* do ambiente/.env (e FALHA com mensagem clara
    se faltar a chave secreta em produção). `inicializar=False` pula a criação das tabelas
    e os seeds — usado pelo processo "pai" do recarregador do Flask, que só vigia arquivos.
    """
    cfg = config or Config.from_env()

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=cfg.secret_key,
        DEBUG=cfg.debug,                        # só a configuração do XBot decide; FLASK_DEBUG do ambiente não liga o debug
        MAX_CONTENT_LENGTH=cfg.max_body_bytes,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE=cfg.cookie_samesite,
        XBOT=cfg,
    )
    app.session_interface = _SessaoXBot()
    if cfg.trusted_proxies:
        n = cfg.trusted_proxies
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=n, x_proto=n, x_host=n)

    banco.configurar_caminho(cfg.db_path)
    if inicializar:
        inicializar_banco()

    estado = _Estado()
    estado.raciocinio.invalidar_cache()   # garantir que o Reasoning Engine use dados frescos
    app.extensions["xbot"] = estado

    if cfg.allowed_origins:
        CORS(
            app,
            origins=list(cfg.allowed_origins),       # lista exata — nunca "*" com cookies
            supports_credentials=True,
            allow_headers=["Content-Type", "X-CSRF-Token"],
            methods=["GET", "POST", "DELETE", "OPTIONS"],
            max_age=600,
        )
    registrar_seguranca(app)
    _registrar_rotas(app, estado)
    return app


def _registrar_rotas(app: Flask, estado: _Estado) -> None:
    cfg: Config = app.config["XBOT"]
    bot = estado.bot

    # ------------------------------------------------------------------
    # Sessão: quem é "dono" desta requisição?
    # ------------------------------------------------------------------

    def usuario_logado() -> Optional[dict]:
        """Usuário da sessão (conferido no banco). Cookie com id inexistente é descartado."""
        if hasattr(g, "usuario_xbot"):
            return g.usuario_xbot
        usuario = buscar_usuario_por_id(session.get("user_id"))
        if usuario is None and "user_id" in session:
            session.pop("user_id", None)           # conta apagada ou cookie adulterado
        g.usuario_xbot = usuario
        return usuario

    def status_sessao() -> dict:
        """
        Logado → ilimitado. Visitante → relógio de XBOT_GUEST_SECONDS (padrão 10 min) mantido
        NO SERVIDOR, preso a IP + navegador (apagar o cookie não zera). `dono` identifica o
        histórico/quiz desta pessoa e nunca sai do servidor.
        """
        if hasattr(g, "status_xbot"):
            return g.status_xbot
        usuario = usuario_logado()
        if usuario:
            status = {"autenticado": True, "usuario": usuario, "tempo_restante": None,
                      "bloqueado": False, "dono": f"u:{usuario['id']}"}
        else:
            visitante = visitantes.consultar(
                session.get("visitor_id"), impressao_do_cliente(),
                agora=relogio.agora(), limite=cfg.guest_seconds,
                cooldown=cfg.guest_cooldown_seconds, max_sessoes=cfg.guest_max_sessions,
            )
            if session.get("visitor_id") != visitante.visitor_id:
                session["visitor_id"] = visitante.visitor_id
            status = {"autenticado": False, "usuario": None, "tempo_restante": visitante.restante,
                      "bloqueado": visitante.bloqueado, "dono": f"g:{visitante.visitor_id}"}
        g.status_xbot = status
        return status

    def trocar_sessao_para(usuario: dict) -> str:
        """Login/cadastro: sessão nova (evita fixação) e novo token CSRF."""
        session.clear()
        session["user_id"] = usuario["id"]
        token = renovar_token_csrf()
        g.usuario_xbot = usuario
        g.pop("status_xbot", None)
        return token

    def exigir_login() -> dict:
        usuario = usuario_logado()
        if not usuario:
            raise ErroRequisicao("É preciso entrar na sua conta para acessar esta função.",
                                 401, "nao_autenticado")
        return usuario

    def exigir_diagnostico() -> None:
        """Rotas de diagnóstico: abertas só se XBOT_DIAGNOSTICS=1 (padrão: development)."""
        if not cfg.diagnostics_open:
            exigir_login()

    def resposta_bloqueada():
        resposta = jsonify({
            "resposta": (
                "⏰ Seu tempo de teste gratuito acabou! "
                "Cadastre-se gratuitamente para continuar conversando com o XBot sem limites."
            ),
            "bloqueado": True,
            "autenticado": False,
            "tempo_restante": 0,
            "codigo": "limite_visitante",
        })
        resposta.status_code = 403
        return resposta

    def falha_de_autenticacao(resultado: dict, status_http: int):
        if resultado.get("codigo") == "muitas_tentativas":
            status_http = 429
        resposta = jsonify(resultado)
        resposta.status_code = status_http
        if "retry_after" in resultado:
            resposta.headers["Retry-After"] = str(resultado["retry_after"])
        return resposta

    # ------------------------------------------------------------------
    # Autenticação
    # ------------------------------------------------------------------

    @app.route("/registrar", methods=["POST"])
    def registrar():
        """Cria uma nova conta e já autentica o usuário (login automático)."""
        dados = obter_json_objeto()
        nome = campo_texto(dados, "nome", obrigatorio=True, max_len=200)
        email = campo_texto(dados, "email", obrigatorio=True, max_len=320)
        senha = campo_texto(dados, "senha", obrigatorio=True, strip=False, max_len=256)
        resultado = cadastrar(nome, email, senha, ip=ip_do_cliente(), cfg=cfg)
        if resultado["sucesso"]:
            token = trocar_sessao_para(resultado["usuario"])
            return jsonify({**resultado, "csrf_token": token})
        return falha_de_autenticacao(resultado, 400)

    @app.route("/login", methods=["POST"])
    def login():
        """Autentica um usuário existente por e-mail e senha."""
        dados = obter_json_objeto()
        email = campo_texto(dados, "email", obrigatorio=True, max_len=320)
        senha = campo_texto(dados, "senha", obrigatorio=True, strip=False, max_len=256)
        resultado = autenticar(email, senha, ip=ip_do_cliente(), cfg=cfg)
        if resultado["sucesso"]:
            token = trocar_sessao_para(resultado["usuario"])
            return jsonify({**resultado, "csrf_token": token})
        return falha_de_autenticacao(resultado, 401)

    @app.route("/logout", methods=["POST"])
    def logout():
        """Encerra a sessão atual (login ou contagem de visitante)."""
        session.clear()
        g.pop("usuario_xbot", None)
        g.pop("status_xbot", None)
        return jsonify({"sucesso": True, "csrf_token": renovar_token_csrf()})

    @app.route("/sessao", methods=["GET"])
    def sessao():
        """Status da sessão para o frontend decidir a UI (+ token CSRF para as próximas requisições)."""
        status = status_sessao()
        corpo = {chave: status[chave] for chave in ("autenticado", "usuario", "tempo_restante", "bloqueado")}
        corpo["csrf_token"] = token_csrf()
        return jsonify(corpo)

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    @app.route("/")
    def home():
        """Página principal do chatbot"""
        return render_template("index.html")

    @app.route("/responder", methods=["POST"])
    def resposta():
        """Endpoint principal para processar mensagens"""
        try:
            status = status_sessao()

            if status["bloqueado"]:
                return resposta_bloqueada()

            dados = obter_json_objeto()
            if not dados:
                raise ErroRequisicao("Dados JSON inválidos", 400, "json_invalido")

            mensagem = campo_texto(dados, "mensagem", padrao="")
            nome_usuario = limpar_nome_exibicao(campo_texto(dados, "nome_usuario", padrao=""))

            if not mensagem:
                return jsonify({"resposta": "Por favor, digite uma mensagem!"})

            if len(mensagem) > 500:
                return jsonify({"resposta": "Mensagem muito longa! Máximo de 500 caracteres."})

            dono = status["dono"]

            # Gerar resposta usando a IA do bot (e ler os metadados dela) sob a trava
            with estado.trava:
                historico_sessao = estado.historico.obter(dono, nome_usuario)
                resposta_bot = bot.gerar_resposta(
                    mensagem, nome_usuario, historico_sessao=historico_sessao, dono=dono
                )
                fonte = bot.ultima_fonte
                confianca = bot.ultima_confianca
                relacionados = list(bot.ultimos_relacionados)
                sugestoes = list(bot.ultimas_sugestoes)
                titulo_kb = bot.ultimo_titulo_kb
                categoria = bot.detectar_categoria(mensagem)

            # v0.3.0 Beta: visitantes não cadastrados recebem prévia truncada
            # (quiz e exercícios são interativos: truncar quebraria o fluxo, e já estão
            # limitados pelos 10 minutos do visitante)
            if not status["autenticado"] and fonte not in ("quiz", "exercicio"):
                resposta_bot = _truncar_para_guest(resposta_bot)

            # Atualizar estatísticas
            minuscula = mensagem.lower()
            with estado.trava:
                estatisticas = estado.estatisticas
                estatisticas["total_mensagens"] += 1
                if len(estatisticas["usuarios_unicos"]) < 10000:      # teto de memória
                    estatisticas["usuarios_unicos"].add(nome_usuario)
                if 'quiz' in minuscula:
                    estatisticas["quizzes_realizados"] += 1
                if 'exercício' in minuscula or 'exercicio' in minuscula:
                    estatisticas["exercicios_solicitados"] += 1

            # Salvar no histórico (do DONO da sessão; o nome só escolhe a conversa)
            timestamp = datetime.datetime.now().isoformat()
            estado.historico.adicionar(dono, nome_usuario, {
                'timestamp': timestamp,
                'usuario': mensagem,
                'bot': resposta_bot,
                'categoria': categoria,
                # Metadados de contexto para o Reasoning Engine
                'titulo_conhecimento': titulo_kb,
                'categoria_respondida': fonte if fonte == 'resposta_padrao' else categoria,
            })

            logger.info(
                "Mensagem processada (%s, %d caracteres, fonte=%s)",
                "usuário" if status["autenticado"] else "visitante", len(mensagem), fonte,
            )

            return jsonify({
                "resposta": resposta_bot,
                "timestamp": timestamp,
                "categoria": categoria,
                "fonte_resposta": fonte,
                # ── Campos do Reasoning Engine (v0.3.0 Beta) ──
                "nivel_confianca": confianca,
                "topicos_relacionados": relacionados,
                "sugestoes_proximas": sugestoes,
                # ── Campos de sessão/autenticação (v0.3.0 Beta) ──
                "autenticado": status['autenticado'],
                "tempo_restante": status['tempo_restante'],
                "bloqueado": False,
            })

        except (ErroRequisicao, HTTPException):
            raise          # 400/413/415... já têm tratador próprio (JSON com o status certo)
        except Exception:
            logger.exception("Erro ao processar mensagem")
            erro = jsonify({
                "resposta": "Desculpe, ocorreu um erro interno. Tente novamente.",
                "erro": "Erro interno do servidor",
            })
            erro.status_code = 500
            return erro

    @app.route("/quiz/<categoria>", methods=["POST"])
    def iniciar_quiz_endpoint(categoria: str):
        """Endpoint para iniciar quiz específico (vindo do antigo app_improved.py)"""
        status = status_sessao()
        if status["bloqueado"]:
            return resposta_bloqueada()
        dados = obter_json_objeto()
        nome_usuario = limpar_nome_exibicao(campo_texto(dados, "nome_usuario", padrao=""))
        with estado.trava:
            texto = bot.iniciar_quiz(categoria, status["dono"], nome_usuario)
            estado.estatisticas["quizzes_realizados"] += 1
        return jsonify({"resposta": texto})

    @app.route("/exercicio/<categoria>", methods=["GET"])
    def obter_exercicio_endpoint(categoria: str):
        """Endpoint para obter exercício (vindo do antigo app_improved.py)"""
        status = status_sessao()
        if status["bloqueado"]:
            return resposta_bloqueada()
        nome_usuario = limpar_nome_exibicao(request.args.get("usuario", ""))
        with estado.trava:
            texto = bot.obter_exercicio(categoria, nome_usuario)
            estado.estatisticas["exercicios_solicitados"] += 1
        return jsonify({"resposta": texto})

    # ------------------------------------------------------------------
    # Históricos — SÓ do próprio usuário autenticado
    # ------------------------------------------------------------------

    @app.route("/historico/<nome_usuario>", methods=["GET"])
    def obter_historico(nome_usuario: str):
        """
        Histórico de uma conversa do PRÓPRIO usuário logado. O nome na URL apenas escolhe
        qual das conversas dele; quem é o dono vem da sessão, nunca da URL.
        """
        usuario = exigir_login()
        historico = estado.historico.obter(f"u:{usuario['id']}", limpar_nome_exibicao(nome_usuario))
        return jsonify({
            "historico": historico,
            "total_mensagens": len(historico)
        })

    @app.route("/limpar_historico/<nome_usuario>", methods=["DELETE"])
    def limpar_historico_usuario(nome_usuario: str):
        """Limpa uma conversa do PRÓPRIO usuário logado (nunca de outro)."""
        usuario = exigir_login()
        nome = limpar_nome_exibicao(nome_usuario)
        if estado.historico.limpar(f"u:{usuario['id']}", nome):
            return jsonify({"mensagem": f"Histórico de {nome} limpo com sucesso"})
        return jsonify({"mensagem": "Usuário não encontrado"}), 404

    # ------------------------------------------------------------------
    # Informações gerais
    # ------------------------------------------------------------------

    @app.route("/status", methods=["GET"])
    def status_bot():
        """Endpoint para verificar status do bot"""
        with estado.trava:
            estatisticas = dict(estado.estatisticas)
            unicos = len(estatisticas["usuarios_unicos"])
        uptime = datetime.datetime.now() - estatisticas["inicio_servico"]
        return jsonify({
            "status": "online",
            "versao": "2.1",
            "desenvolvedor": "XByte Games Studios",
            "usuarios_ativos": estado.historico.total_conversas(),
            "usuarios_unicos": unicos,
            "total_mensagens": estatisticas["total_mensagens"],
            "quizzes_realizados": estatisticas["quizzes_realizados"],
            "exercicios_solicitados": estatisticas["exercicios_solicitados"],
            "conhecimento": "Arquitetura de Computadores integrada",
            "uptime_segundos": int(uptime.total_seconds()),
            "uptime_formatado": str(uptime).split('.')[0],
            "estatisticas_bot": bot.get_statistics()
        })

    @app.route("/conhecimento", methods=["GET"])
    def listar_conhecimento():
        """Endpoint para listar tópicos de conhecimento disponíveis"""
        topicos = bot.get_available_topics()
        return jsonify({
            "topicos_disponiveis": sorted(topicos),
            "total_topicos": len(topicos),
            "categorias_resposta": list(bot.padroes.keys()),
            "quiz_categorias": list(bot.quiz_questions.keys()),
            "exercicio_categorias": list(bot.exercicios.keys())
        })

    # ------------------------------------------------------------------
    # Diagnóstico (abertos só em development; senão exigem login)
    # ------------------------------------------------------------------

    @app.route("/estatisticas", methods=["GET"])
    def obter_estatisticas():
        """Endpoint para obter estatísticas detalhadas"""
        exigir_diagnostico()
        with estado.trava:
            estatisticas = dict(estado.estatisticas)
            unicos = len(estatisticas["usuarios_unicos"])
        uptime = datetime.datetime.now() - estatisticas["inicio_servico"]

        # Estatísticas por categoria
        categorias_count: Dict[str, int] = {}
        for msg in estado.historico.todas_as_entradas():
            categoria = msg.get('categoria', 'unknown')
            categorias_count[categoria] = categorias_count.get(categoria, 0) + 1

        return jsonify({
            "uptime": {
                "segundos": int(uptime.total_seconds()),
                "formatado": str(uptime).split('.')[0]
            },
            "usuarios": {
                "total_unicos": unicos,
                "com_historico": estado.historico.total_conversas()
            },
            "mensagens": {
                "total": estatisticas["total_mensagens"],
                "por_categoria": categorias_count
            },
            "interacoes": {
                "quizzes_realizados": estatisticas["quizzes_realizados"],
                "exercicios_solicitados": estatisticas["exercicios_solicitados"]
            },
            "bot": bot.get_statistics(),
            "inicio_servico": estatisticas["inicio_servico"].isoformat()
        })

    @app.route("/raciocinio_debug", methods=["POST"])
    def raciocinio_debug():
        """Endpoint de debug do Reasoning Engine — mostra parâmetros e scores"""
        exigir_diagnostico()
        dados = obter_json_objeto()
        mensagem = campo_texto(dados, "mensagem", padrao="", max_len=500)
        if not mensagem:
            raise ErroRequisicao('Campo mensagem obrigatório', 400, "campo_obrigatorio")
        with estado.trava:                      # o motor compartilha cache com o chat
            resultado = estado.raciocinio.analisar(mensagem, [])
        candidatos_info = []
        for c in resultado.todos_candidatos[:5]:
            candidatos_info.append({
                'titulo': c.titulo,
                'categoria': c.categoria,
                'score': round(c.score_final, 2),
                'evidencias': c.keywords_que_batem[:6],
                'parametros': {
                    k: round(v, 3) for k, v in c.valores_param.items() if v != 0
                },
            })
        return jsonify({
            'mensagem': mensagem,
            'tipo_pergunta': resultado.analise.tipo_pergunta,
            'categoria_detectada': resultado.analise.categoria_detectada,
            'termos_extraidos': resultado.analise.termos,
            'nivel_confianca': resultado.nivel_confianca,
            'margem_lideranca': round(resultado.margem_lideranca, 2),
            'vencedor': resultado.vencedor.titulo if resultado.vencedor else None,
            'relacionados': resultado.topicos_relacionados,
            'sugestoes': resultado.sugestoes_proximas,
            'top5_candidatos': candidatos_info,
            'explicacao': resultado.explicacao_debug,
        })

    @app.route("/db_status", methods=["GET"])
    def db_status():
        """Endpoint de diagnóstico do banco SQLite (v0.3.0 Beta)"""
        exigir_diagnostico()
        try:
            tabelas = listar_tabelas()
            total_registros = contar_registros()
            return jsonify({
                "banco": os.path.basename(cfg.db_path),
                "status": "ok",
                "tabelas": tabelas,
                "knowledge_registros": total_registros
            })
        except Exception:
            logger.exception("Erro ao verificar banco")
            return jsonify({"status": "erro", "detalhe": "Falha ao consultar o banco de dados"}), 500


# ============================================================================
# Execução
# ============================================================================

def deve_inicializar(cfg: Config, environ=None) -> bool:
    """
    O recarregador do Werkzeug (modo debug) executa este script DUAS vezes: um processo "pai",
    que só vigia os arquivos, e um "filho" (WERKZEUG_RUN_MAIN=true), que atende as requisições.
    Só o filho — ou qualquer execução sem recarregador — deve criar tabelas e rodar seeds;
    antes, tudo rodava duas vezes.
    """
    environ = os.environ if environ is None else environ
    return not (cfg.debug and environ.get("WERKZEUG_RUN_MAIN") != "true")


def main() -> int:
    try:
        cfg = Config.from_env()
    except ConfigError as erro:
        print(f"\n[XBot] Não foi possível iniciar — configuração inválida:\n\n{erro}\n", file=sys.stderr)
        return 2

    if cfg.producao and cfg.host_na_rede:
        # `python app.py` usa o servidor de DESENVOLVIMENTO do Flask: em produção ele só atende em localhost.
        print(
            f"\n[XBot] XBOT_HOST={cfg.host} em modo produção colocaria o servidor de desenvolvimento do "
            "Flask na rede, e ele não foi feito para isso.\n"
            "  - Uso local: deixe XBOT_HOST=127.0.0.1 (padrão).\n"
            "  - Para atender a rede/Internet: use um servidor de produção com o wsgi.py, por exemplo\n"
            "        waitress-serve --listen=0.0.0.0:8000 wsgi:app\n"
            "    com um proxy HTTPS na frente (veja o README).\n"
            "  - Só para testar na rede local: rode com XBOT_ENV=development.\n",
            file=sys.stderr,
        )
        return 2

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    servindo = deve_inicializar(cfg)

    if cfg.secret_efemera and cfg.debug and "WERKZEUG_RUN_MAIN" not in os.environ:
        # chave temporária de desenvolvimento: o processo filho do recarregador herda a MESMA,
        # para os logins sobreviverem aos recarregamentos de código
        os.environ["XBOT_SECRET_KEY"] = cfg.secret_key

    app = create_app(cfg, inicializar=servindo)

    if servindo:
        logger.info("Iniciando XBot v0.3.0 Beta... (%s)", cfg.resumo())
        for aviso in cfg.avisos:
            logger.warning(aviso)
        logger.info("Tópicos de conhecimento carregados: %d",
                    len(app.extensions["xbot"].bot.get_available_topics()))
        endereco = "localhost" if cfg.host in ("0.0.0.0", "::") else cfg.host
        logger.info("Acesse: http://%s:%d", endereco, cfg.port)

    app.run(host=cfg.host, port=cfg.port, debug=cfg.debug, use_reloader=cfg.debug, threaded=True)
    return 0


_app_padrao: Optional[Flask] = None


def __getattr__(nome: str):
    """
    `from app import app` (gunicorn app:app, flask --app app run) cria a aplicação sob demanda.
    Importar este módulo NÃO toca no banco nem exige a chave — por isso os testes e
    ferramentas podem importar `create_app` à vontade.
    """
    global _app_padrao
    if nome == "app":
        if _app_padrao is None:
            _app_padrao = create_app()
        return _app_padrao
    raise AttributeError(f"module {__name__!r} has no attribute {nome!r}")


if __name__ == "__main__":
    sys.exit(main())
