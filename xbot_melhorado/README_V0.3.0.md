# XBot v0.3.0 Beta — Chatbot de Arquitetura de Computadores

**XByte Games Studios** · Python 3.11+ · Flask · SQLite (apenas `sqlite3` da biblioteca padrão)

XBot é um chatbot educacional sobre Arquitetura de Computadores, programação e web design, com
base de conhecimento em SQLite, motor de raciocínio de 20 parâmetros, quizzes, exercícios,
contas de usuário e um **teste gratuito de 10 minutos para visitantes**.

---

## Início rápido

```bash
pip install -r requirements.txt
```

**1. Gere uma chave secreta** (ela assina os cookies de login; o XBot não inicia sem ela):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**2. Informe a chave** — de um destes jeitos:

```powershell
# Windows (PowerShell) — vale só para esta janela
$env:XBOT_SECRET_KEY = "cole-a-chave-aqui"
```
```bash
# Linux / macOS
export XBOT_SECRET_KEY="cole-a-chave-aqui"
```
```text
# ou, para não repetir: copie .env.example para .env e preencha XBOT_SECRET_KEY=
# (o .env fica ao lado do app.py e nunca deve ir para o Git — já está no .gitignore)
```

**3. Rode** e abra <http://127.0.0.1:5000>:

```bash
python app.py
```

`python app.py` e `python app_improved.py` iniciam **exatamente a mesma aplicação** — a versão
completa, compatível com a interface (`/sessao`, `/login`, `/registrar`, `/logout`, `/responder`,
quizzes, exercícios, histórico). O `app_improved.py` ficou só como atalho para quem já usava
esse comando.

Sem `XBOT_SECRET_KEY` o XBot recusa iniciar e explica o que fazer — não existe chave padrão.

### Só para desenvolver no seu computador

```powershell
$env:XBOT_ENV = "development"      # Linux/macOS: export XBOT_ENV=development
python app.py
```

Em `development` o XBot usa uma chave temporária se você não definir `XBOT_SECRET_KEY` (os
logins deixam de valer ao reiniciar), liga o modo debug com recarregamento automático (somente em
`127.0.0.1`) e deixa abertas as rotas de diagnóstico. **Nunca use este modo em um servidor.**

---

## Configuração (variáveis `XBOT_*`)

Variáveis de ambiente têm prioridade sobre o arquivo `.env`. Todas são opcionais, **exceto
`XBOT_SECRET_KEY` em produção**. Um valor inválido interrompe o início com uma mensagem clara.

| Variável | Padrão | Para que serve |
|---|---|---|
| `XBOT_SECRET_KEY` | — (obrigatória em produção) | Chave de sessão, mínimo 32 caracteres, não pode parecer exemplo |
| `XBOT_ENV` | `production` | `production`, `development` ou `testing` |
| `XBOT_HOST` / `XBOT_PORT` | `127.0.0.1` / `5000` | Onde o servidor escuta (padrão: só este computador) |
| `XBOT_DEBUG` | ligado só em `development` | Debug do Flask; recusado fora de `development` e fora de `127.0.0.1` |
| `XBOT_ALLOWED_ORIGINS` | vazio | Origens CORS permitidas, separadas por vírgula. `*` é recusado |
| `XBOT_COOKIE_SAMESITE` | `Lax` | `Lax`, `Strict` ou `None` (`None` exige HTTPS) |
| `XBOT_COOKIE_SECURE` | `auto` | `auto` marca o cookie `Secure` quando a conexão é HTTPS |
| `XBOT_TRUSTED_PROXIES` | `0` | Quantos proxies reversos confiar (para enxergar o IP real) |
| `XBOT_DB_PATH` | `xbot.db` ao lado do `app.py` | Caminho do banco SQLite |
| `XBOT_GUEST_SECONDS` | `600` | Duração do teste do visitante (10 minutos) |
| `XBOT_GUEST_COOLDOWN_SECONDS` | `86400` | Por quanto tempo um teste esgotado continua esgotado |
| `XBOT_GUEST_MAX_SESSIONS` | `1` | Janelas de teste por IP + navegador (aumente em demonstrações de sala) |
| `XBOT_LOGIN_MAX_FAILURES_EMAIL` / `_IP` | `5` / `20` | Falhas de login toleradas na janela, por e-mail e por IP |
| `XBOT_LOGIN_WINDOW_SECONDS` | `900` | Janela (15 min) das falhas de login |
| `XBOT_REGISTER_MAX_PER_HOUR` | `10` | Cadastros por IP por hora |
| `XBOT_DIAGNOSTICS` | só em `development` | `1` abre `/estatisticas`, `/db_status` e `/raciocinio_debug` a todos |
| `XBOT_MAX_BODY_BYTES` | `16384` | Tamanho máximo do corpo das requisições |

Veja `.env.example` para um modelo comentado.

---

## Colocando no ar (produção)

O servidor embutido do Flask (`python app.py`) **não é feito para ficar exposto**. Por isso, em
produção ele só aceita `XBOT_HOST=127.0.0.1`; com outro endereço o XBot recusa iniciar e aponta
para o `wsgi.py`. Para atender a rede/Internet:

```bash
pip install waitress
waitress-serve --listen=127.0.0.1:8000 wsgi:app              # Windows, Linux, macOS

# alternativa (Linux/macOS): pip install gunicorn
gunicorn --preload -w 1 --threads 4 -b 127.0.0.1:8000 wsgi:app
```

* Coloque um **proxy com HTTPS** na frente (nginx, Caddy, o proxy da hospedagem) e defina
  `XBOT_TRUSTED_PROXIES=1`. Em HTTPS o cookie de sessão sai com `Secure` e o servidor envia HSTS.
* Use **um processo** (várias threads, como acima). Históricos de conversa e andamento de quiz
  ficam na memória do processo; o relógio do visitante, as contas e as tentativas de login ficam
  no SQLite e valem para qualquer quantidade de processos.
* `--preload` (gunicorn) faz a criação das tabelas e o seed inicial rodarem uma única vez.
* Interface em **outro domínio**? Liste-o em `XBOT_ALLOWED_ORIGINS` e use
  `XBOT_COOKIE_SAMESITE=None` (com HTTPS). Sem isso, só o próprio site do XBot pode chamar a API.

---

## Como a segurança funciona

| Assunto | O que o XBot faz |
|---|---|
| **Chave secreta** | Vem só de `XBOT_SECRET_KEY`; sem ela, o início falha com instruções. Nada fixo no código |
| **Debug / rede** | Debug só em `development` e só em `127.0.0.1`; em produção o servidor embutido só escuta em `127.0.0.1` |
| **Teste do visitante** | Os 10 minutos são contados **no servidor**, presos a IP + navegador (HMAC, sem guardar o IP). Apagar o cookie não devolve tempo; depois de esgotado, só volta após 24 h |
| **Login e cadastro** | 5 falhas por e-mail e 20 por IP em 15 min bloqueiam o login (resposta `429` + `Retry-After`); no máximo 10 cadastros por IP/hora; resposta igual para "e-mail inexistente" e "senha errada" |
| **Senha** | 10 a 128 caracteres, com letra e algo que não seja letra; recusa senhas comuns, sequências (`abc123…`), repetições e senhas que contêm seu nome/e-mail. Contas antigas continuam entrando |
| **CSRF** | Toda requisição que altera algo (`POST`/`DELETE`) precisa do cabeçalho `X-CSRF-Token` (entregue por `/sessao`, `/login`, `/registrar`, `/logout`) e de `Origin`/`Referer` do próprio site. A interface já faz isso sozinha |
| **CORS** | Só as origens de `XBOT_ALLOWED_ORIGINS`; nunca `*` |
| **Históricos** | Exigem login e pertencem a quem está logado. O nome na URL só escolhe *qual* conversa **sua**; ler ou apagar a conversa de outra pessoa não funciona |
| **Entradas** | Corpo precisa ser um objeto JSON; campo de tipo errado, texto com caractere nulo ou inválido (como `\ud800` solto) ou grande demais devolve `400` controlado, nunca `500` |
| **Cookies** | `HttpOnly`, `SameSite=Lax` e `Secure` automático em HTTPS |
| **Cabeçalhos** | CSP restritiva, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy`, JSON sem cache |
| **Início do servidor** | Tabelas e seeds rodam **uma vez** (o recarregador do modo debug não executa tudo duas vezes) e nunca sobrescrevem conhecimento existente |

---

## API

| Rota | Método | Quem acessa |
|---|---|---|
| `/` | GET | todos — página do chat |
| `/sessao` | GET | todos — estado da sessão (`autenticado`, `tempo_restante`, `bloqueado`) e `csrf_token` |
| `/registrar`, `/login`, `/logout` | POST | todos (com limites de tentativas) |
| `/responder` | POST | visitante dentro dos 10 min (resposta resumida) ou usuário logado |
| `/quiz/<categoria>` | POST | idem |
| `/exercicio/<categoria>` | GET | idem |
| `/historico/<nome>` | GET | **somente logado, somente o próprio** |
| `/limpar_historico/<nome>` | DELETE | **somente logado, somente o próprio** |
| `/status`, `/conhecimento` | GET | todos |
| `/estatisticas`, `/db_status`, `/raciocinio_debug` | GET, GET, POST | usuário logado (abertos em `development` ou com `XBOT_DIAGNOSTICS=1`) |

Usando a API fora do navegador (por exemplo, `curl`) é preciso levar o cookie e o token CSRF:

```bash
# 1) abre a sessão: guarda o cookie e mostra o token
curl -s -c cookies.txt http://127.0.0.1:5000/sessao
# {"autenticado":false,"bloqueado":false,"csrf_token":"<TOKEN>","tempo_restante":599,"usuario":null}

# 2) manda o token no cabeçalho X-CSRF-Token
curl -s -b cookies.txt -c cookies.txt -H "Content-Type: application/json" \
     -H "X-CSRF-Token: <TOKEN>" \
     -d '{"mensagem":"o que é uma CPU?","nome_usuario":"Ana"}' \
     http://127.0.0.1:5000/responder
```

O token muda quando você entra, sai ou se cadastra: use sempre o último `csrf_token` recebido.

---

## Testes

```bash
python -m unittest discover -v
```

São cerca de 300 testes (cadastro, login e bloqueio, sessão, expiração/bloqueio do visitante,
históricos, CSRF/CORS, entradas inválidas, inicialização única, quiz, rotas e o servidor iniciado de
verdade em outro processo). Eles **nunca usam o seu `xbot.db`**: trabalham em bancos temporários, com
o relógio simulado (os 10 minutos e as 24 h são testados sem esperar) e não criam contas reais. O último
teste (`test_zz_banco_real`) confere que o seu banco real não mudou. Levam cerca de um minuto.

---

## Banco de dados (SQLite)

* O arquivo `xbot.db` é criado na primeira execução. Ele guarda conhecimento, usuários, o relógio
  dos visitantes (`visitantes`) e as tentativas de login (`auth_tentativas`) — as duas últimas só
  guardam HMACs e horários. **Não envie o `xbot.db` nem o `.env` para o Git.**
* Atualizar uma versão antiga é seguro: tabelas novas são criadas sem mexer nas existentes, e
  usuários e senhas atuais continuam valendo.
* Os seeds (`database/seed.py`, `database/apostilas_seed.py`) só rodam sozinhos em banco **vazio**.
  Antes eles rodavam a cada início e sobrescreviam palavras-chave refinadas. Para reaplicar de
  propósito: `python database/seed.py --forcar` (faz um backup `.bak` antes).
* Seu banco rodou versões antigas? `python database/reparar_refinamento.py` **só mostra** o que
  seria corrigido; `--aplicar` faz backup e restaura as palavras-chave refinadas.

---

## Limites conhecidos

* **Limite do visitante.** O visitante é reconhecido por **IP + navegador (User-Agent)**. Apagar
  cookies ou abrir janela anônima **não** dá novo teste, mas quem troca de rede **ou** de navegador
  (ou muda o User-Agent) ganha um novo teste de 10 minutos. Ao contrário, várias pessoas atrás do
  mesmo IP *e* do mesmo navegador dividem o relógio (ajuste `XBOT_GUEST_MAX_SESSIONS` em
  demonstrações de sala). Só uma conta (cadastro) dá acesso sem limite de tempo; um teto por IP é
  uma melhoria possível, ainda não implementada.
* **Contas.** Não há confirmação de e-mail: contas descartáveis são possíveis e o cadastro avisa
  quando um e-mail já existe. O bloqueio de login por e-mail (5 falhas em 15 min) pode ser usado
  para atrapalhar a conta de outra pessoa por até 15 minutos.
* **Sair não invalida um cookie já copiado.** A sessão fica num cookie assinado (sem tabela de
  sessões no servidor): o logout limpa e troca o token, mas um cookie copiado antes continua válido
  até expirar (cerca de 31 dias). Por isso o HTTPS é obrigatório fora do seu computador.
* **Sem limite por minuto** de mensagens para usuários logados (só o tamanho de cada mensagem).
* **Memória.** Históricos de conversa e quizzes em andamento ficam **na memória** e somem ao
  reiniciar o servidor — use um único processo.
* **Sem papel de administrador.** Qualquer conta logada acessa `/estatisticas`, `/db_status` e
  `/raciocinio_debug` quando elas estão abertas (por padrão ficam fechadas fora de `development`).
* **Servidor.** O servidor embutido do Flask não é para produção: use `waitress`/`gunicorn` atrás
  de um proxy com HTTPS (veja acima) e mantenha o app em `127.0.0.1`.

---

## Estrutura do projeto

```
xbot_melhorado/
├── app.py                  # Aplicação Flask única (rotas, XBotIA, quiz, exercícios)
├── app_improved.py         # Atalho: inicia o mesmo app do app.py
├── wsgi.py                 # Entrada para waitress / gunicorn
├── config.py               # Configuração lida de XBOT_* (e do .env)
├── seguranca.py            # CSRF, validação de JSON, cabeçalhos, IP do cliente
├── historico.py            # Históricos em memória, por dono
├── relogio.py              # Relógio (simulável nos testes)
├── knowledge_base*.py      # Conhecimento em Python (+ quiz e exercícios)
├── database/               # SQLite: db, auth, visitantes, throttle, seeds, reasoning...
├── templates/index.html    # Interface
├── static/                 # style.css e script.js
├── tests/                  # Suíte de testes (unittest)
├── .env.example            # Modelo de configuração
└── requirements.txt        # Flask, Flask-CORS, Werkzeug
```

---

## Solução de problemas

* **"XBOT_SECRET_KEY não está definida"** — faça os passos 1 e 2 do início rápido (ou use
  `XBOT_ENV=development` para testar localmente).
* **"Sessão de segurança inválida" (403 `csrf`)** — recarregue a página; se usa `curl`, envie o
  `X-CSRF-Token` mais recente (veja acima).
* **403 `origem_invalida` atrás de um proxy/hospedagem** — o XBot confere o cabeçalho `Origin`
  (ou `Referer`) das requisições que alteram algo. Se o proxy troca o `Host` ou o esquema
  (`http`/`https`), o endereço público do site não bate com o que o app enxerga: acrescente-o em
  `XBOT_ALLOWED_ORIGINS` (por exemplo `https://meu-xbot.exemplo.com`) e confirme
  `XBOT_TRUSTED_PROXIES`.
* **"Muitas tentativas" (429)** — espere o tempo indicado em `Retry-After`.
* **"Seu tempo de teste gratuito acabou" mesmo depois de limpar os cookies** — é de propósito: o
  relógio fica no servidor. Crie uma conta ou ajuste `XBOT_GUEST_COOLDOWN_SECONDS` / `XBOT_GUEST_SECONDS`.
* **"XBOT_HOST=… em modo produção"** — o servidor embutido só escuta em `127.0.0.1`; use o `wsgi.py`.

---

© XByte Games Studios. Todos os direitos reservados.
