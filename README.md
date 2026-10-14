# Jarvis Chatbot + XBot v0.3.0 Beta

Este repositório reúne **dois projetos distintos**: o Jarvis original, executado no navegador, e o XBot educacional, com backend Python/Flask. O XBot v0.3.0 adiciona contas, persistência SQLite e uma revisão ampla de segurança.

## Projetos e branches

| Projeto | Branch | Localização | Guia |
|---|---|---|---|
| Jarvis original | [`main`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/main) | arquivos web na raiz | [README do Jarvis](README_JARVIS_ORIGINAL.md) |
| XBot v0.3.0 Beta | [`xbot-atual`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/xbot-atual) | `xbot_melhorado/` | [Guia do XBot v0.3.0](README_XBOT_V0.3.0.md) |

## Comparativo

| Aspecto | Jarvis original (`main`) | XBot v0.3.0 (`xbot-atual`) |
|---|---|---|
| Execução | HTML, CSS e JavaScript no navegador | Aplicação Python/Flask com interface web |
| Respostas | Comandos e lógica locais; voz via APIs do navegador | Motor local de raciocínio e busca em conhecimento SQLite; sem API externa de IA generativa |
| Foco | Assistente geral, comandos e conversa por voz | Arquitetura de computadores, programação e web design; quizzes e exercícios |
| Contas e acesso | Perfil e configurações guardados no `localStorage` do navegador | Cadastro e login; visitantes recebem uma prévia de 10 minutos |
| Persistência | Preferências e histórico local no navegador | SQLite para usuários, conhecimento e limites; histórico do chat e quizzes ativos ficam na memória do processo |
| Segurança | Recursos dependem do navegador e do armazenamento local | Chave obrigatória em produção, hash de senhas, limites de login/cadastro, CSRF, CORS por allowlist, validação de entradas e cabeçalhos de segurança |

## O que mudou no XBot

A versão 0.3.0 Beta substitui o servidor anterior por uma aplicação Flask única e acrescenta:

- autenticação com política de senha, bloqueio de tentativas repetidas e limite de cadastros;
- limite de uso de visitantes acompanhado no servidor, não apenas por cookie;
- armazenamento SQLite de contas, conhecimento e controles de abuso;
- proteção CSRF e validação de `Origin`/`Referer`, CORS limitado a origens configuradas e cookies `HttpOnly`/`SameSite`;
- chave secreta obrigatória em produção, debug restrito a desenvolvimento local e orientação WSGI para publicação;
- testes automatizados de rotas, sessão, autenticação, segurança e inicialização.

**Validação desta publicação:** os 306 testes da suíte passaram em ambiente isolado. O Jarvis original continua na branch `main`; nenhum código do Jarvis foi substituído.

## Executar localmente

### Jarvis original

Na branch `main`, na raiz:

```bash
python3 -m http.server 8000
```

Abra <http://localhost:8000>. O uso de voz depende do suporte e da permissão de microfone do navegador.

### XBot v0.3.0 — desenvolvimento local

Na branch `xbot-atual`:

```bash
cd xbot_melhorado
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
pip install -r requirements.txt
XBOT_ENV=development python app.py
```

No Windows PowerShell, ative com `.venv\Scripts\Activate.ps1` e defina `$env:XBOT_ENV = "development"` antes de executar `python app.py`. Acesse <http://127.0.0.1:5000>.

Para produção, configure `XBOT_SECRET_KEY`, use `wsgi.py` com Waitress ou Gunicorn e coloque HTTPS/proxy à frente. **Não exponha o servidor de desenvolvimento/debug.** Consulte o [guia detalhado do XBot](README_XBOT_V0.3.0.md).

## Documentação

- [Jarvis original](README_JARVIS_ORIGINAL.md)
- [XBot v0.3.0 Beta — comparativo, instalação, API e segurança](README_XBOT_V0.3.0.md)
- [README v0.3.0 incluído no projeto](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/blob/xbot-atual/xbot_melhorado/README_V0.3.0.md)
- `README_XBOT_V2.md` — documentação histórica da versão 2.1.
- `xbot_melhorado/README.md` — README existente preservado como estava antes da atualização.
