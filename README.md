# Jarvis Chatbot, XBot 2.1 e XBot v0.3.0 Beta

O repositório contém **três versões/projetos relacionados**, preservados em branches distintas: o Jarvis original, o XBot 2.1 e sua evolução XBot v0.3.0 Beta.

## Projetos e branches

| Projeto | Branch | Localização | Documentação |
|---|---|---|---|
| Jarvis original | [`main`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/main) | arquivos web na raiz | [Guia do Jarvis](README_JARVIS_ORIGINAL.md) |
| XBot 2.1 | [`xbot-atual`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/xbot-atual) | `xbot_melhorado/` | [Guia do XBot 2.1](README_XBOT_V2.md) |
| XBot v0.3.0 Beta | [`xbot-v0.3.0`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/xbot-v0.3.0) | `xbot_melhorado/` | [Guia do XBot v0.3.0](README_XBOT_V0.3.0.md) |

## Comparativo dos três

| Aspecto | Jarvis original (`main`) | XBot 2.1 (`xbot-atual`) | XBot v0.3.0 Beta (`xbot-v0.3.0`) |
|---|---|---|---|
| Execução | HTML, CSS e JavaScript no navegador | Python/Flask com frontend web | Python/Flask com frontend web e configuração por ambiente |
| Respostas | Lógica local, comandos e APIs de voz do navegador | Regras/regex e bases de conhecimento locais | Motor de raciocínio e busca de conhecimento local em SQLite; sem API externa de IA generativa |
| Foco | Assistente geral, voz, perfil e comandos | Conteúdo educacional, arquitetura, programação e web; quizzes e exercícios | Mantém os recursos educacionais e acrescenta contas, teste de visitante e controles de segurança |
| Dados e usuários | Preferências e histórico no `localStorage` do navegador | Histórico e estatísticas mantidos em memória; sem contas persistentes | SQLite para contas, conhecimento e limites; históricos e quizzes ativos permanecem em memória |
| Segurança e execução | Depende do navegador/dispositivo | Servidor de desenvolvimento; use apenas localmente até configurar implantação apropriada | Hash de senhas, limites de login/cadastro, CSRF, CORS configurável, cookies protegidos e chave secreta obrigatória em produção |

## O que mudou do XBot 2.1 para o v0.3.0

A v0.3.0 é uma **versão separada**, não uma substituição do XBot 2.1. Ela acrescenta autenticação, prévia de 10 minutos para visitantes, persistência SQLite, controles de sessão, proteção CSRF, CORS por allowlist, limites contra tentativas repetidas e uma configuração de produção com chave secreta e entrada WSGI. O branch `xbot-atual` continua guardando o XBot 2.1; a versão v0.3.0 está em `xbot-v0.3.0`.

Os dois XBots usam conhecimento e raciocínio locais; nenhum dos dois integra uma API externa de IA generativa. No XBot v0.3.0, o histórico do chat e o progresso de quizzes continuam em memória e são reiniciados quando o servidor reinicia.

## Executar localmente

### Jarvis original

Na branch `main`, na raiz do repositório:

```bash
python3 -m http.server 8000
```

Abra <http://localhost:8000>. O uso de voz depende do navegador e da permissão do microfone.

### XBot 2.1

Na branch `xbot-atual`:

```bash
cd xbot_melhorado
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
pip install -r requirements.txt
python app_improved.py
```

Abra <http://localhost:5000>. O modo debug é destinado ao desenvolvimento local; não exponha o servidor embutido diretamente à internet.

### XBot v0.3.0 Beta

Na branch `xbot-v0.3.0`:

```bash
cd xbot_melhorado
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
pip install -r requirements.txt
XBOT_ENV=development python app.py
```

Abra <http://127.0.0.1:5000>. Para produção, configure `XBOT_SECRET_KEY`, use Waitress ou Gunicorn por WSGI e coloque HTTPS/proxy à frente. Consulte o [guia v0.3.0](README_XBOT_V0.3.0.md).

## Documentação complementar

- [Jarvis original](README_JARVIS_ORIGINAL.md)
- [XBot 2.1](README_XBOT_V2.md)
- [XBot v0.3.0 Beta](README_XBOT_V0.3.0.md)
- `xbot_melhorado/README.md` na branch `xbot-atual` continua sendo o README original do XBot 2.1.
- Na branch `xbot-v0.3.0`, o README anterior também foi preservado; o guia recebido com essa versão está em `xbot_melhorado/README_V0.3.0.md`.

## Licença

O material original do repositório está sob a [licença personalizada para estudo, pesquisa, ensino e referência não comercial](LICENSE). Ela permite copiar, adaptar e compartilhar apenas para esses fins, com os avisos de autoria mantidos; **uso comercial, venda, monetização e implantação operacional/comercial não são permitidos sem autorização escrita**. Esta não é uma licença MIT. Componentes de terceiros permanecem sujeitos às respectivas licenças.

É uma licença personalizada, não uma licença open source aprovada pela OSI; a aplicação e a interpretação dos termos dependem da legislação aplicável. Para uma proteção jurídica específica, considere revisão por um profissional do direito.
