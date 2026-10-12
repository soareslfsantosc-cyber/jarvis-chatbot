# XBot v2.1 - Chatbot Inteligente

## Desenvolvido por XByte Games Studios

### Descrição
XBot é um chatbot inteligente especializado em Arquitetura de Computadores, desenvolvido com tecnologias modernas e foco na experiência do usuário.

### Características Principais

#### 🤖 Inteligência Artificial
- Base de conhecimento especializada em Arquitetura de Computadores
- Reconhecimento de padrões de conversação
- Respostas contextuais e personalizadas
- Suporte a múltiplas categorias de perguntas

#### 🎨 Interface Moderna
- Design responsivo para desktop e mobile
- Modo claro e escuro
- Animações suaves e feedback visual
- Acessibilidade aprimorada (ARIA labels, navegação por teclado)

#### 🔧 Funcionalidades Avançadas
- Exportação de conversas em HTML
- Histórico persistente de conversas
- Indicador de digitação em tempo real
- Contador de caracteres
- Verificação de status do bot

#### 📊 Monitoramento
- Estatísticas de uso em tempo real
- Logs detalhados
- Métricas de performance
- Histórico por usuário

### Tecnologias Utilizadas
- Frontend: HTML5, CSS3, JavaScript ES6+
- Backend: Python 3.11+, Flask 2.3.3, Flask-CORS
- Logging integrado e type hints

### Estrutura do Projeto
```
xbot_melhorado/
├── app.py
├── app_improved.py
├── knowledge_base.py
├── knowledge_base_extended.py
├── requirements.txt
├── README.md
├── README_COMPLETO.md
├── CHANGELOG.md
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```

### Instalação e execução
```bash
pip install -r requirements.txt
python app.py
``
Depois, acesse http://localhost:5000.

### Endpoints principais
- `GET /` - Interface do chatbot
- `POST /responder` - Processa mensagens
- `GET /status` - Status e estatísticas
- `GET /conhecimento` - Tópicos disponíveis

### Licença
© 2024 XByte Games Studios. Todos os direitos reservados.

**XBot v2.1** - Seu assistente virtual inteligente! 🤖
