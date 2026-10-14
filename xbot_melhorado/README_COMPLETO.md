# 🤖 XBot v0.3.0 Beta — guia complementar

**Desenvolvido pela XByte Games Studios**

XBot é um chatbot inteligente com funcionalidades avançadas de educação, quiz interativo e base de conhecimento expandida sobre tecnologia, programação e arquitetura de computadores.

> **Atualizado para a v0.3.0 Beta.** Configuração (`XBOT_*`), segurança, produção e testes estão no
> [`README_V0.3.0.md`](README_V0.3.0.md). `python app.py` e `python app_improved.py` iniciam o mesmo aplicativo.

## ✨ Principais Funcionalidades

### 🧠 IA Conversacional Avançada
- Detecção inteligente de categorias usando regex
- Respostas contextuais personalizadas
- Sistema de busca avançado na base de conhecimento
- Suporte a múltiplas categorias de conversa

### 📚 Base de Conhecimento Expandida
- **HTML & CSS**: Desenvolvimento web, Visual Studio Code
- **Psicologia das Cores**: Teoria de cores, marketing, design
- **Python**: Programação, estruturas de controle, boas práticas
- **Arquitetura de Computadores**: Hardware Gigabyte, especificações técnicas
- **História da Computação**: Marcos históricos e evolução

### 🎯 Sistema de Quiz Interativo
- **Quiz de Arquitetura**: 10 questões sobre hardware
- **Quiz de Python**: Conceitos de programação
- **Quiz de Web**: HTML, CSS e desenvolvimento
- Sistema de pontuação e feedback educativo

### 💻 Exercícios Práticos
- Exemplos de código Python
- Projetos práticos com diferentes níveis
- Soluções comentadas e explicadas

### 🎨 Interface Moderna
- Design responsivo e intuitivo
- Tema escuro/claro
- Animações suaves
- Chat em tempo real

## 🚀 Como Usar

### Instalação

1. **Clone ou extraia o projeto**
```bash
cd xbot_melhorado
```

2. **Instale as dependências**
```bash
pip3 install -r requirements.txt
```

3. **Gere e informe a chave secreta** (obrigatória — o XBot não inicia sem ela)
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
export XBOT_SECRET_KEY="<cole a chave>"      # PowerShell: $env:XBOT_SECRET_KEY = "<cole a chave>"
```
   Ou copie `.env.example` para `.env` e preencha `XBOT_SECRET_KEY=`. Para apenas testar no seu
   computador, use `XBOT_ENV=development` (chave temporária).

4. **Execute a aplicação** (`app.py` e `app_improved.py` iniciam o mesmo app)
```bash
python3 app.py
```

5. **Acesse no navegador**
```
http://127.0.0.1:5000
```

### Comandos Especiais

#### Quiz
- `quiz arquitetura` - Quiz sobre hardware
- `quiz python` - Quiz sobre programação  
- `quiz web` - Quiz sobre desenvolvimento web

#### Exercícios
- `exercício python` - Exercícios práticos de Python

#### Informações
- Digite qualquer tópico para obter informações
- Exemplos: "html", "cores", "gigabyte", "python"

## 📊 APIs Disponíveis

### Endpoints Principais
- `POST /responder` - Processar mensagens do chat
- `GET /status` - Status do sistema
- `GET /conhecimento` - Tópicos disponíveis
- `GET /estatisticas` - Métricas de uso

### Endpoints de Quiz
- `POST /quiz/<categoria>` - Iniciar quiz específico
- `GET /exercicio/<categoria>` - Obter exercícios

### Endpoints de Dados
- `GET /historico/<usuario>` - Histórico de conversas (só do próprio usuário logado)
- `DELETE /limpar_historico/<usuario>` - Apaga uma conversa (só do próprio usuário logado)
- `GET /estatisticas` - Estatísticas detalhadas (exige login)

### Endpoints de Sessão
- `GET /sessao` - Estado da sessão (autenticado, tempo restante do visitante) e token CSRF
- `POST /registrar`, `POST /login`, `POST /logout` - Conta e sessão

Requisições `POST`/`DELETE` precisam do cabeçalho `X-CSRF-Token` (a interface já envia). Detalhes no `README_V0.3.0.md`.

## 🏗️ Estrutura do Projeto

```
xbot_melhorado/
├── app.py                       # Aplicação Flask principal (única)
├── app_improved.py              # Atalho: inicia o mesmo app do app.py
├── wsgi.py                      # Entrada para waitress / gunicorn
├── config.py, seguranca.py      # Configuração por ambiente e segurança
├── database/                    # SQLite: conhecimento, usuários, visitantes
├── tests/                       # Testes automatizados (python -m unittest discover)
├── knowledge_base.py            # Base de conhecimento original
├── knowledge_base_extended.py   # Base expandida com novos tópicos
├── templates/
│   └── index.html              # Interface web principal
├── static/
│   ├── style.css              # Estilos CSS modernos
│   └── script.js              # JavaScript interativo
├── requirements.txt            # Dependências Python
├── README.md                  # README v2.1 preservado
├── README_V0.3.0.md           # Guia atual de configuração/segurança
├── README_COMPLETO.md         # Guia complementar
└── CHANGELOG.md               # Log de mudanças
```

## 🔧 Tecnologias Utilizadas

### Backend
- **Flask 2.3.3** - Framework web Python
- **Flask-CORS** - CORS restrito às origens configuradas
- **SQLite** (`sqlite3` da biblioteca padrão) - Conhecimento, contas e limites
- **Python 3.11+** - Linguagem principal

### Frontend
- **HTML5** - Estrutura da página
- **CSS3** - Estilos modernos e responsivos
- **JavaScript ES6** - Interatividade

### Dados
- **Python Dictionaries** - Base de conhecimento estruturada
- **JSON** - Comunicação API
- **Regex** - Detecção de padrões

## 🎯 Casos de Uso

### Para Estudantes
- ✅ Aprender arquitetura de computadores
- ✅ Praticar programação Python
- ✅ Estudar desenvolvimento web
- ✅ Fazer quizzes educativos

### Para Desenvolvedores
- ✅ Consultar referências técnicas
- ✅ Obter exemplos de código
- ✅ Testar conhecimentos
- ✅ Explorar conceitos avançados

### Para Educadores
- ✅ Ferramenta de ensino interativa
- ✅ Sistema de avaliação automática
- ✅ Conteúdo educacional estruturado
- ✅ Métricas de engajamento

## 📈 Estatísticas de Melhoria

### Comparação com Versão Anterior
- **Linhas de código**: +300% (200 → 800+ linhas)
- **Funcionalidades**: +500% (5 → 25+ features)
- **Base de conhecimento**: +400% (10 → 40+ tópicos)
- **Categorias de resposta**: 12 tipos diferentes
- **Padrões de detecção**: 15 regex patterns

## 🔒 Segurança e Performance

### Validações
- ✅ Sanitização de entrada de dados
- ✅ Limitação de tamanho de mensagens
- ✅ Tratamento de erros HTTP
- ✅ Validação de JSON (tipos incorretos retornam `400`, nunca `500`)
- ✅ Proteção CSRF, CORS restrito e cookies `HttpOnly`/`SameSite`
- ✅ Limite de tentativas de login e política de senha forte
- ✅ Teste de 10 minutos do visitante controlado no servidor
- ✅ Históricos privados: só o dono (logado) lê ou apaga

### Performance
- ⚡ Tempo de resposta: <100ms
- 🔄 Suporte a múltiplos usuários
- 💾 Uso de memória otimizado
- 🌐 CORS só para as origens de `XBOT_ALLOWED_ORIGINS`

## 🚀 Próximos Passos

### Funcionalidades Futuras
- [x] Sistema de usuários com login
- [ ] Histórico persistente em banco
- [ ] Mais categorias de quiz
- [ ] Sistema de conquistas
- [ ] API para integração externa
- [ ] Suporte a múltiplos idiomas

### Melhorias Técnicas
- [ ] Migração para banco de dados
- [ ] Cache Redis
- [ ] Containerização Docker
- [x] Testes automatizados
- [ ] CI/CD pipeline

## 📞 Suporte

### Contato
- **Empresa**: XByte Games Studios
- **Versão atual**: 0.3.0 Beta (base histórica: 2.1)
- **Tipo**: Assistente Virtual Inteligente

### Problemas Conhecidos
- Nenhum problema crítico identificado
- Todos os bugs da versão anterior foram corrigidos

### Contribuição
Para contribuir com o projeto:
1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Abra um Pull Request

---

**Desenvolvido com ❤️ pela XByte Games Studios**

*XBot v0.3.0 Beta — Transformando educação através da tecnologia*
