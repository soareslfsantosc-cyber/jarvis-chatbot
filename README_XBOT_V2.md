# XBot v2.1 — assistente educacional

**Branch:** [`xbot-atual`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/xbot-atual)

**Diretório:** `xbot_melhorado/`

**Interface:** <https://github.com/soareslfsantosc-cyber/jarvis-chatbot/blob/xbot-atual/xbot_melhorado/templates/index.html>

O XBot é uma aplicação web com backend Python/Flask e interface HTML, CSS e JavaScript. Diferentemente do Jarvis original, ele organiza as respostas com regras/expressões regulares e bases de conhecimento locais; o código atual não usa um serviço de IA generativa externo.

## O que foi acrescentado

- Backend Flask com API para conversa, status, conhecimento, estatísticas, quiz, exercícios e histórico.
- Base de conhecimento em Python sobre arquitetura de computadores, hardware/Gigabyte, história da computação, HTML/CSS, design e cores, desenvolvimento web e programação Python.
- Quizzes educativos para arquitetura, Python e web, com pontuação e explicações.
- Exercícios práticos de Python com exemplos de código.
- Interface responsiva com alternância de tema, controles de conversa e limite de 500 caracteres por mensagem.
- Registro de atividade, estatísticas de uso e histórico por usuário mantidos em memória durante a execução do servidor.

## Estrutura

```text
xbot_melhorado/
├── app.py
├── app_improved.py
├── knowledge_base.py
├── knowledge_base_extended.py
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    ├── script.js
    └── style.css
```

`app_improved.py` é a entrada recomendada pela documentação do XBot e carrega a base estendida e os recursos de quiz/exercícios. Os arquivos `README.md`, `README_COMPLETO.md` e `CHANGELOG.md` existentes dentro de `xbot_melhorado/` continuam como documentação complementar.

## Instalação e execução

Requer Python e as dependências listadas em `requirements.txt` (Flask, Flask-CORS e Werkzeug):

```bash
cd xbot_melhorado
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# No Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app_improved.py
```

Acesse <http://localhost:5000>.

## Endpoints da API

- `POST /responder` — recebe JSON com `mensagem` e, opcionalmente, `nome_usuario`.
- `GET /status` — estado e informações de uso do bot.
- `GET /conhecimento` — tópicos e categorias disponíveis.
- `GET /estatisticas` — métricas da execução atual.
- `POST /quiz/<categoria>` — iniciar quiz (`arquitetura`, `python` ou `web`).
- `GET /exercicio/<categoria>` — obter exercício.
- `GET /historico/<nome_usuario>` — consultar histórico em memória do usuário.

A execução atual guarda histórico e métricas em estruturas na memória, sem banco de dados; esses dados são reiniciados quando o processo Flask é encerrado. `app_improved.py` inicia com modo de depuração habilitado para desenvolvimento local; antes de expor o serviço publicamente, configure um servidor de produção e desative o modo debug.

## Diferença em relação ao Jarvis original

O Jarvis, na branch [`main`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/main), é um frontend de assistente com voz do navegador, perfil, comandos personalizados e armazenamento local. O XBot 2.1 acrescenta uma camada de servidor Python/Flask, conteúdo educacional, quizzes e exercícios.

O XBot 2.1 permanece em [`xbot-atual`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/xbot-atual). A versão mais nova, [XBot v0.3.0 Beta](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/xbot-v0.3.0), está em branch separada e acrescenta contas, SQLite, teste de visitante e proteções de segurança. Veja o [guia v0.3.0](README_XBOT_V0.3.0.md) e o [comparativo dos três projetos](README.md).
