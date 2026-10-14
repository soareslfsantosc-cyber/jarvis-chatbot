# Jarvis original — frontend de assistente virtual

**Branch:** [`main`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/main)

**Página inicial:** `index.html`

A versão original do Jarvis é um assistente executado no navegador. A interface e a lógica principal usam HTML, CSS e JavaScript, sem um servidor Python.

## Recursos

- Entrada de mensagens por texto e reconhecimento de voz do navegador.
- Respostas faladas com a Web Speech API, quando suportada pelo navegador.
- Histórico de conversa, configurações, perfil e comandos personalizados armazenados no `localStorage`.
- Temas visuais, controles de velocidade/tom/volume da fala e opção de escuta automática.
- Pesquisa do histórico, atalhos de teclado e comandos rápidos para ações como consultar hora e data.

O suporte a voz depende do navegador e de permissão para usar o microfone. Os dados guardados no `localStorage` ficam no navegador/dispositivo atual.

## Arquivos principais

- `index.html` — estrutura da interface de conversa, perfil, configurações e modais.
- `app.js` — lógica do assistente, voz, comandos, perfil e histórico.
- `main.css` — folha de estilo apontada pela página inicial.
- `style.css`, `improvements.css`, `jarvis-4.0-styles.css` e `script.js` — arquivos adicionais/alternativos presentes nesta branch.

## Executar localmente

Na raiz do repositório, com a branch `main` selecionada, inicie um servidor estático:

```bash
python3 -m http.server 8000
```

Abra <http://localhost:8000>. Não há instalação de dependências Python para esta versão. A página usa Font Awesome via CDN para ícones.

## Diferença em relação ao XBot

O Jarvis original trabalha principalmente no cliente, com APIs de voz do navegador e armazenamento local. O XBot v2.1, na branch [`xbot-atual`](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/tree/xbot-atual), acrescenta backend Python/Flask, uma base de conhecimento temática, quizzes e exercícios. Veja o [guia do XBot](https://github.com/soareslfsantosc-cyber/jarvis-chatbot/blob/xbot-atual/README_XBOT_V2.md).

## Observação sobre os arquivos existentes

A página `index.html` referencia `jarvis_enhancements.js`, mas a árvore atual contém `jarvis_enhancement.js` (sem o “s” final). Essa documentação não altera o código; o caminho pode precisar ser alinhado caso o script complementar não carregue.
