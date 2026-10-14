# Jarvis Chatbot e XBot v2.1

Este repositório reúne **dois projetos relacionados, mas com arquiteturas e objetivos diferentes**. O Jarvis original é um assistente executado no navegador; o XBot v2.1 acrescenta um backend Flask e recursos educativos.

## Projetos e branches

| Projeto | Branch | Localização | Documentação |
|---|---|---|---|
| Jarvis original | [`main`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/main) | arquivos web na raiz | [README do Jarvis](README_JARVIS_ORIGINAL.md) |
| XBot v2.1 | [`xbot-atual`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/xbot-atual) | `xbot_melhorado/` | [README do XBot](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/blob/xbot-atual/README_XBOT_V2.md) |

## Diferenças principais

| Aspecto | Jarvis original (`main`) | XBot v2.1 (`xbot-atual`) |
|---|---|---|
| Execução | HTML, CSS e JavaScript no navegador | Python/Flask no servidor e frontend web |
| Respostas | Comandos e lógica locais; reconhecimento e síntese de voz do navegador | Regras/regex e base de conhecimento temática local |
| Conteúdo | Assistente geral, comandos rápidos e personalizados | Arquitetura de computadores, hardware, web, design e Python |
| Recursos próprios | Perfil, temas, voz, busca e histórico no `localStorage` | Quizzes, exercícios, endpoints de API, estatísticas e histórico em memória |
| Dependências de servidor | Não requer Python/Flask | Requer Python e dependências de `xbot_melhorado/requirements.txt` |

## Modificações que o XBot acrescenta

Na branch `xbot-atual`, o diretório `xbot_melhorado/` adiciona dois backends Flask (`app.py` e `app_improved.py`), bases de conhecimento em Python, quizzes e exercícios, templates HTML e arquivos estáticos próprios. A interface XBot também inclui alternância de tema, exportação e limite de 500 caracteres por mensagem. O Jarvis original continua disponível em `main`; o XBot não substitui essa branch.

O XBot responde por regras e conteúdo local; o código atual não integra um serviço externo de IA generativa. Histórico e métricas do backend são mantidos em memória e não persistem após reiniciar o servidor.

## Executar localmente

### Jarvis original

Na branch `main`, na raiz do repositório:

```bash
python3 -m http.server 8000
```

Abra <http://localhost:8000>. O uso de voz depende do suporte do navegador e da permissão do microfone.

### XBot v2.1

Na branch `xbot-atual`:

```bash
cd xbot_melhorado
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
pip install -r requirements.txt
python app_improved.py
```

Abra <http://localhost:5000>. Consulte o [guia detalhado do XBot](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/blob/xbot-atual/README_XBOT_V2.md) para endpoints e detalhes.

## Documentação complementar

- [Detalhes do Jarvis original](README_JARVIS_ORIGINAL.md)
- [Detalhes do XBot v2.1](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/blob/xbot-atual/README_XBOT_V2.md)
- `xbot_melhorado/README.md`, `README_COMPLETO.md` e `CHANGELOG.md` — documentação existente do XBot, preservada na branch `xbot-atual`.
