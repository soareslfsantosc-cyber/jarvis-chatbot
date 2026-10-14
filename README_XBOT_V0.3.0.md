# XBot v0.3.0 Beta — guia atual

**Branch:** [`xbot-atual`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/xbot-atual)
**Código:** `xbot_melhorado/`
**Documentação completa incluída no projeto:** [`xbot_melhorado/README_V0.3.0.md`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/blob/xbot-atual/xbot_melhorado/README_V0.3.0.md)

O XBot é um chatbot educacional sobre arquitetura de computadores, programação e web design. A v0.3.0 Beta combina Flask e SQLite com um motor local de raciocínio e base de conhecimento; não há integração com API externa de IA generativa no código recebido.

## Recursos e arquitetura

- Base de conhecimento e motor de raciocínio local com busca de tópicos, quizzes e exercícios.
- Cadastro, login e uma prévia de 10 minutos para visitantes; contas registradas removem o limite de tempo.
- SQLite guarda contas, conhecimento, tentativas de autenticação e controles de sessão de visitantes.
- Históricos de conversa e andamento de quizzes ficam na memória do processo e são perdidos quando ele reinicia; mantenha um processo se esses estados temporários forem importantes.
- Interface HTML/CSS/JavaScript; `app.py` é o entrypoint principal. `app_improved.py` delega à mesma aplicação para compatibilidade.

## Segurança implementada

- `XBOT_SECRET_KEY` aleatória, obrigatória em produção; nenhum segredo padrão no código.
- Senhas hasheadas com Werkzeug, política para novos cadastros e proteção contra tentativas repetidas de login/cadastro.
- CSRF nas operações que alteram dados e verificação de `Origin`/`Referer`.
- CORS fechado por padrão e limitado a origens explicitamente configuradas; `*` é recusado.
- Cookies `HttpOnly`, `SameSite` e `Secure` automático em HTTPS; cabeçalhos de segurança e respostas JSON sem cache.
- Validação de payloads/tipos/tamanho, limites de corpo e rotas diagnósticas restritas fora do modo de desenvolvimento.
- Em produção, o servidor embutido fica em `127.0.0.1`; use WSGI atrás de proxy HTTPS para acesso pela rede.

Esses controles não substituem configuração segura do ambiente e revisão antes de uma implantação pública. O projeto também documenta limitações, incluindo ausência de verificação de e-mail e armazenamento temporário de histórico/quizzes.

## Instalação e execução local

Requer Python 3.11+ e as dependências fixadas em `xbot_melhorado/requirements.txt` (Flask, Flask-CORS e Werkzeug):

```bash
cd xbot_melhorado
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
pip install -r requirements.txt
XBOT_ENV=development python app.py
```

No Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
$env:XBOT_ENV = "development"
python app.py
```

Acesse <http://127.0.0.1:5000>. `development` usa chave temporária quando necessário e ativa debug apenas no loopback; use somente para desenvolvimento local.

### Produção

Gere uma chave com `python -c "import secrets; print(secrets.token_hex(32))"`, defina-a em `XBOT_SECRET_KEY`, mantenha `XBOT_ENV=production` e use `wsgi.py` com Waitress ou Gunicorn. Configure um proxy HTTPS e `XBOT_TRUSTED_PROXIES` conforme o ambiente. Veja `xbot_melhorado/README_V0.3.0.md` para as variáveis, valores padrão e comandos completos.

## API principal

- `GET /` e `GET /sessao` — interface e estado/token CSRF da sessão.
- `POST /registrar`, `POST /login`, `POST /logout` — autenticação.
- `POST /responder` — conversa.
- `POST /quiz/<categoria>` e `GET /exercicio/<categoria>` — conteúdo interativo.
- `GET /historico/<nome>` e `DELETE /limpar_historico/<nome>` — histórico próprio, somente autenticado.
- `GET /status` e `GET /conhecimento` — informações públicas.
- Rotas de estatísticas/diagnóstico têm acesso restrito, exceto quando habilitadas explicitamente para desenvolvimento.

Operações `POST` e `DELETE` exigem token CSRF; a interface obtém e envia o token automaticamente.

## Testes

Execute na raiz de `xbot_melhorado/`:

```bash
python -m unittest discover -v
```

Nesta atualização, **306 testes passaram** usando as dependências declaradas e um ambiente temporário isolado. A suíte cria bancos temporários e inclui uma verificação para detectar alteração do banco real.

## Diferença em relação ao Jarvis original

O [Jarvis](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/main) continua sendo o assistente browser-only em HTML/CSS/JavaScript, com voz e armazenamento local no navegador. O XBot acrescenta servidor, contas, base SQLite, regras/raciocínio local e controles de acesso. A comparação está no [README principal](README.md).

## README anterior preservado

O arquivo `xbot_melhorado/README.md` já existente foi mantido byte a byte, conforme solicitado anteriormente. O README do ZIP v0.3.0 foi incluído ao lado como `xbot_melhorado/README_V0.3.0.md` para distinguir a documentação nova sem apagar a anterior.
