// XBot - Script JavaScript Melhorado v2.1
// Desenvolvido por XByte Games Studios

// Configurações e constantes
const CONFIG = {
    API_ENDPOINT: '/responder',
    STATUS_ENDPOINT: '/status',
    STORAGE_KEYS: {
        THEME: 'xbot_tema',
        USERNAME: 'xbot_nomeUsuario'
    },
    TYPING_DELAY: {
        MIN: 800,
        MAX: 2000
    },
    MAX_MESSAGE_LENGTH: 500
};

// Estado da aplicação
const AppState = {
    nomeUsuario: '',
    conversaAtiva: false,
    isTyping: false,
    messageCount: 0
};

// Utilitários
const Utils = {
    // Sanitizar HTML para prevenir XSS
    sanitizeHTML: (str) => {
        const temp = document.createElement('div');
        temp.textContent = str;
        return temp.innerHTML;
    },

    // Formatar timestamp
    formatTimestamp: () => {
        return new Date().toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Gerar delay aleatório
    getRandomDelay: () => {
        return CONFIG.TYPING_DELAY.MIN + Math.random() * (CONFIG.TYPING_DELAY.MAX - CONFIG.TYPING_DELAY.MIN);
    },

    // Debounce para otimizar eventos
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Gerenciamento de tema
const ThemeManager = {
    init: () => {
        const savedTheme = localStorage.getItem(CONFIG.STORAGE_KEYS.THEME);
        if (savedTheme === 'dark') {
            ThemeManager.setDarkMode();
        }
    },

    toggle: () => {
        const body = document.body;
        if (body.classList.contains('light-mode')) {
            ThemeManager.setDarkMode();
        } else {
            ThemeManager.setLightMode();
        }
    },

    setDarkMode: () => {
        const body = document.body;
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
        localStorage.setItem(CONFIG.STORAGE_KEYS.THEME, 'dark');
    },

    setLightMode: () => {
        const body = document.body;
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        localStorage.setItem(CONFIG.STORAGE_KEYS.THEME, 'light');
    }
};

// Gerenciamento de mensagens
const MessageManager = {
    add: (mensagem, tipo, isHTML = false) => {
        const chatBox = document.getElementById('chat-box');
        const divMensagem = document.createElement('div');
        divMensagem.className = tipo;
        
        const timestamp = Utils.formatTimestamp();
        const content = isHTML ? mensagem : Utils.sanitizeHTML(mensagem);
        
        if (tipo === 'user') {
            divMensagem.innerHTML = `<strong>Você</strong> <span class="timestamp">${timestamp}</span><br>${content}`;
        } else {
            divMensagem.innerHTML = `<strong>🤖 XBot</strong> <span class="timestamp">${timestamp}</span><br>${content}`;
        }
        
        chatBox.appendChild(divMensagem);
        MessageManager.scrollToBottom();
        AppState.messageCount++;
    },

    addHTML: (mensagem, tipo) => {
        MessageManager.add(mensagem, tipo, true);
    },

    scrollToBottom: () => {
        const chatBox = document.getElementById('chat-box');
        chatBox.scrollTop = chatBox.scrollHeight;
    },

    clear: () => {
        const chatBox = document.getElementById('chat-box');
        chatBox.innerHTML = '';
        AppState.messageCount = 0;
        MessageManager.add('Chat limpo! Como posso ajudá-lo?', 'bot');
    }
};

// Gerenciamento de indicador de digitação
const TypingIndicator = {
    show: () => {
        if (AppState.isTyping) return;
        
        const chatBox = document.getElementById('chat-box');
        const divDigitando = document.createElement('div');
        divDigitando.className = 'bot typing';
        divDigitando.id = 'typing-indicator';
        divDigitando.innerHTML = '<strong>🤖 XBot</strong> está digitando<span class="dots">...</span>';
        chatBox.appendChild(divDigitando);
        MessageManager.scrollToBottom();
        AppState.isTyping = true;
    },

    hide: () => {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
            AppState.isTyping = false;
        }
    }
};

// Gerenciamento de usuário
const UserManager = {
    init: () => {
        const savedName = localStorage.getItem(CONFIG.STORAGE_KEYS.USERNAME);
        if (savedName) {
            AppState.nomeUsuario = savedName;
        }
    },

    requestName: () => {
        const nome = prompt('Olá! Qual é o seu nome?');
        if (nome && nome.trim()) {
            AppState.nomeUsuario = nome.trim();
            localStorage.setItem(CONFIG.STORAGE_KEYS.USERNAME, AppState.nomeUsuario);
            MessageManager.add(`Olá, ${AppState.nomeUsuario}! Bem-vindo ao XBot. Como posso ajudá-lo hoje?`, 'bot');
            AppState.conversaAtiva = true;
        } else {
            AppState.nomeUsuario = 'Visitante';
            MessageManager.add('Olá! Bem-vindo ao XBot. Como posso ajudá-lo hoje?', 'bot');
            AppState.conversaAtiva = true;
        }
    },

    changeName: () => {
        const novoNome = prompt('Digite seu novo nome:', AppState.nomeUsuario);
        if (novoNome && novoNome.trim() && novoNome.trim() !== AppState.nomeUsuario) {
            const nomeAnterior = AppState.nomeUsuario;
            AppState.nomeUsuario = novoNome.trim();
            localStorage.setItem(CONFIG.STORAGE_KEYS.USERNAME, AppState.nomeUsuario);
            MessageManager.add(`Nome alterado de "${nomeAnterior}" para "${AppState.nomeUsuario}"!`, 'bot');
        }
    }
};

// Gerenciamento de API
const APIManager = {
    sendMessage: async (mensagem) => {
        try {
            const response = await fetch(CONFIG.API_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mensagem: mensagem,
                    nome_usuario: AppState.nomeUsuario
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Erro na API:', error);
            throw error;
        }
    },

    checkStatus: async () => {
        try {
            const response = await fetch(CONFIG.STATUS_ENDPOINT);
            const data = await response.json();
            console.log('Status do XBot:', data);
            return data;
        } catch (error) {
            console.warn('Não foi possível verificar o status do bot:', error);
            return null;
        }
    }
};

// Funcionalidades principais
const ChatBot = {
    sendMessage: async () => {
        const inputMensagem = document.getElementById('input-mensagem');
        const btnEnviar = document.getElementById('btn-enviar');
        const mensagem = inputMensagem.value.trim();
        
        if (!mensagem) return;
        
        if (mensagem.length > CONFIG.MAX_MESSAGE_LENGTH) {
            MessageManager.add(`Mensagem muito longa! Máximo de ${CONFIG.MAX_MESSAGE_LENGTH} caracteres.`, 'bot');
            return;
        }
        
        if (!AppState.conversaAtiva) {
            UserManager.requestName();
        }
        
        // Desabilitar input durante o envio
        inputMensagem.disabled = true;
        btnEnviar.disabled = true;
        
        // Adicionar mensagem do usuário
        MessageManager.add(mensagem, 'user');
        inputMensagem.value = '';
        
        // Mostrar indicador de digitação
        TypingIndicator.show();
        
        try {
            const data = await APIManager.sendMessage(mensagem);
            
            // Simular delay de digitação
            setTimeout(() => {
                TypingIndicator.hide();
                MessageManager.add(data.resposta, 'bot');
                
                // Reabilitar input
                inputMensagem.disabled = false;
                btnEnviar.disabled = false;
                inputMensagem.focus();
            }, Utils.getRandomDelay());
            
        } catch (error) {
            TypingIndicator.hide();
            MessageManager.add('Desculpe, ocorreu um erro. Tente novamente.', 'bot');
            console.error('Erro:', error);
            
            // Reabilitar input
            inputMensagem.disabled = false;
            btnEnviar.disabled = false;
            inputMensagem.focus();
        }
    },

    exportConversation: () => {
        const chatBox = document.getElementById('chat-box');
        const timestamp = new Date().toISOString().split('T')[0];
        
        const htmlContent = `
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conversa XBot - ${timestamp}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 10px; }
        .user { background: #e3f2fd; text-align: right; }
        .bot { background: #f3e5f5; text-align: left; }
        .timestamp { font-size: 0.8em; opacity: 0.7; }
    </style>
</head>
<body>
    <h1>Conversa com XBot</h1>
    <p>Exportado em: ${new Date().toLocaleString('pt-BR')}</p>
    <p>Total de mensagens: ${AppState.messageCount}</p>
    <hr>
    ${chatBox.innerHTML}
</body>
</html>`;
        
        const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversa_xbot_${timestamp}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        MessageManager.add('Conversa exportada com sucesso!', 'bot');
    }
};

// Funcionalidades de ajuda e informações
const HelpManager = {
    showHelp: () => {
        const helpMessage = `
            <strong>🆘 Como usar o XBot:</strong><br>
            • Digite qualquer mensagem para conversar<br>
            • Use 🌓 para alternar entre modo claro/escuro<br>
            • Use 🗑️ para limpar a conversa<br>
            • Use 💾 para exportar a conversa<br>
            • Use 👤 para alterar seu nome<br><br>
            <strong>Comandos úteis:</strong><br>
            • "oi" ou "olá" - Cumprimentar<br>
            • "tchau" - Despedir-se<br>
            • "obrigado" - Agradecer<br>
            • "problema" - Relatar problemas<br>
            • "xbyte" - Saber sobre a empresa<br>
            • "arquitetura" - Perguntas sobre computadores<br><br>
            <strong>Tópicos de conhecimento:</strong><br>
            • Hardware e Software<br>
            • Gerações de computadores<br>
            • Arquitetura Von Neumann<br>
            • Dispositivos de entrada e saída
        `;
        MessageManager.addHTML(helpMessage, 'bot');
    },

    showInfo: () => {
        const infoMessage = `
            <strong>🤖 Sobre o XBot:</strong><br>
            Versão: 2.1<br>
            Desenvolvedor: XByte Games Studios<br>
            Tecnologias: HTML5, CSS3, JavaScript ES6+, Python Flask<br>
            Recursos: IA conversacional, modo escuro, exportação, acessibilidade<br><br>
            <strong>🏢 XByte Games Studios:</strong><br>
            Somos uma empresa inovadora focada em desenvolvimento de jogos e tecnologia, 
            sempre buscando criar experiências digitais incríveis!<br><br>
            <strong>🧠 Base de Conhecimento:</strong><br>
            Especializado em Arquitetura de Computadores com conhecimento sobre 
            hardware, software, gerações de computadores e muito mais!
        `;
        MessageManager.addHTML(infoMessage, 'bot');
    }
};

// Event Listeners e inicialização
const EventManager = {
    init: () => {
        // Event listeners para botões
        document.getElementById('btn-tema').addEventListener('click', ThemeManager.toggle);
        document.getElementById('btn-limpar').addEventListener('click', MessageManager.clear);
        document.getElementById('btn-exportar').addEventListener('click', ChatBot.exportConversation);
        document.getElementById('btn-enviar').addEventListener('click', ChatBot.sendMessage);
        document.getElementById('btn-nome').addEventListener('click', UserManager.changeName);
        document.getElementById('btn-ajuda').addEventListener('click', HelpManager.showHelp);
        document.getElementById('btn-info').addEventListener('click', HelpManager.showInfo);

        // Event listener para Enter no input
        const inputMensagem = document.getElementById('input-mensagem');
        inputMensagem.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                ChatBot.sendMessage();
            }
        });

        // Event listener para input em tempo real (contador de caracteres)
        inputMensagem.addEventListener('input', Utils.debounce((e) => {
            const length = e.target.value.length;
            if (length > CONFIG.MAX_MESSAGE_LENGTH * 0.9) {
                e.target.style.borderColor = '#ff6b6b';
            } else {
                e.target.style.borderColor = '';
            }
        }, 300));

        // Verificar status do bot
        APIManager.checkStatus();
    }
};

// Inicialização da aplicação
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar componentes
    ThemeManager.init();
    UserManager.init();
    EventManager.init();
    
    // Mensagem de boas-vindas
    const welcomeMessage = `
        Olá! Eu sou o XBot, seu assistente virtual da XByte Games Studios. 
        Posso ajudá-lo com questões sobre arquitetura de computadores, 
        tecnologia e muito mais! Digite uma mensagem para começar!
    `;
    MessageManager.add(welcomeMessage, 'bot');
    
    // Focus no input
    document.getElementById('input-mensagem').focus();
    
    console.log('XBot v2.1 inicializado com sucesso!');
});

// Exportar para uso global (se necessário)
window.XBot = {
    ThemeManager,
    MessageManager,
    UserManager,
    ChatBot,
    HelpManager,
    AppState
};

