// XBot - Script JavaScript v0.3.0 Beta
// Desenvolvido por XByte Games Studios

// Configurações e constantes
const CONFIG = {
    API_ENDPOINT: '/responder',
    STATUS_ENDPOINT: '/status',
    SESSAO_ENDPOINT: '/sessao',
    LOGIN_ENDPOINT: '/login',
    REGISTRAR_ENDPOINT: '/registrar',
    LOGOUT_ENDPOINT: '/logout',
    CSRF_HEADER: 'X-CSRF-Token',
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
    messageCount: 0,
    csrfToken: null,   // token anti-CSRF entregue pelo servidor (/sessao, /login, /registrar, /logout)
    sessao: { autenticado: false, usuario: null, tempoRestante: null, bloqueado: false }
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

// Camada HTTP (v0.3.0 Beta): todo POST/DELETE leva o token CSRF do servidor no cabeçalho
// X-CSRF-Token. O servidor também confere a origem da requisição.
const Http = {
    _sessaoEmAndamento: null,

    // Consulta /sessao. Chamadas simultâneas compartilham a mesma requisição.
    buscarSessao: () => {
        if (!Http._sessaoEmAndamento) {
            Http._sessaoEmAndamento = fetch(CONFIG.SESSAO_ENDPOINT, { credentials: 'same-origin' })
                .then((response) => response.json())
                .then((data) => {
                    Http.atualizarToken(data);
                    return data;
                })
                .finally(() => {
                    Http._sessaoEmAndamento = null;
                });
        }
        return Http._sessaoEmAndamento;
    },

    // Guarda o token que vier em qualquer resposta (o servidor troca o token no login/logout).
    atualizarToken: (data) => {
        if (data && typeof data.csrf_token === 'string' && data.csrf_token) {
            AppState.csrfToken = data.csrf_token;
        }
    },

    garantirToken: async () => {
        if (!AppState.csrfToken) {
            await Http.buscarSessao();
        }
        return AppState.csrfToken;
    },

    // Requisição que altera estado (POST/DELETE). Devolve { ok, status, data, retryAfter } também
    // nos erros 4xx/5xx, porque o servidor responde erros em JSON. Se o token tiver expirado
    // (403 'csrf'), busca um novo e repete UMA vez.
    requisitar: async (url, { method = 'POST', corpo, repetir = true } = {}) => {
        const headers = { [CONFIG.CSRF_HEADER]: await Http.garantirToken() };
        if (corpo !== undefined) {
            headers['Content-Type'] = 'application/json';
        }
        const response = await fetch(url, {
            method,
            headers,
            credentials: 'same-origin',
            body: corpo === undefined ? undefined : JSON.stringify(corpo)
        });

        let data = null;
        try {
            data = await response.json();
        } catch (e) {
            data = null;   // corpo vazio ou que não é JSON (ex.: erro de um proxy)
        }
        Http.atualizarToken(data);

        if (response.status === 403 && data && data.codigo === 'csrf' && repetir) {
            AppState.csrfToken = null;
            return Http.requisitar(url, { method, corpo, repetir: false });
        }
        return {
            ok: response.ok,
            status: response.status,
            data: data || {},
            retryAfter: response.headers.get('Retry-After')
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

// Gerenciamento de autenticação (v0.3.0 Beta)
const AuthManager = {
    init: () => {
        AuthManager.verificarSessao();
        AuthManager.iniciarContagem();

        document.getElementById('btn-auth').addEventListener('click', () => {
            if (AppState.sessao.autenticado) {
                AuthManager.fazerLogout();
            } else {
                AuthManager.abrirModal('login');
            }
        });

        document.getElementById('auth-modal-fechar').addEventListener('click', AuthManager.fecharModal);
        document.getElementById('auth-modal').addEventListener('click', (e) => {
            if (e.target.id === 'auth-modal') AuthManager.fecharModal();
        });

        document.getElementById('auth-tab-login').addEventListener('click', () => AuthManager.trocarTab('login'));
        document.getElementById('auth-tab-registrar').addEventListener('click', () => AuthManager.trocarTab('registrar'));

        document.getElementById('form-login').addEventListener('submit', async (e) => {
            e.preventDefault();
            await AuthManager.fazerLogin(
                document.getElementById('login-email').value,
                document.getElementById('login-senha').value
            );
        });

        document.getElementById('form-registrar').addEventListener('submit', async (e) => {
            e.preventDefault();
            await AuthManager.fazerCadastro(
                document.getElementById('registrar-nome').value,
                document.getElementById('registrar-email').value,
                document.getElementById('registrar-senha').value
            );
        });
    },

    abrirModal: (aba = 'login') => {
        document.getElementById('auth-modal').hidden = false;
        AuthManager.trocarTab(aba);
    },

    fecharModal: () => {
        document.getElementById('auth-modal').hidden = true;
        ['login-erro', 'registrar-erro'].forEach(id => {
            const el = document.getElementById(id);
            el.hidden = true;
            el.textContent = '';
        });
    },

    trocarTab: (aba) => {
        const ehLogin = aba === 'login';
        document.getElementById('auth-tab-login').classList.toggle('active', ehLogin);
        document.getElementById('auth-tab-registrar').classList.toggle('active', !ehLogin);
        document.getElementById('form-login').hidden = !ehLogin;
        document.getElementById('form-registrar').hidden = ehLogin;
    },

    // Converte o JSON do servidor (tempo_restante) para o formato usado na tela (tempoRestante).
    aplicarSessao: (data) => {
        AppState.sessao = {
            autenticado: Boolean(data.autenticado),
            usuario: data.usuario || null,
            tempoRestante: typeof data.tempo_restante === 'number' ? data.tempo_restante : null,
            bloqueado: Boolean(data.bloqueado)
        };
    },

    verificarSessao: async () => {
        try {
            const data = await Http.buscarSessao();
            AuthManager.aplicarSessao(data);
            AuthManager.atualizarUI();
        } catch (error) {
            console.warn('Não foi possível verificar a sessão:', error);
        }
    },

    // Mensagem para o usuário a partir da resposta de erro do servidor (que já vem em português).
    mensagemDeErro: (resposta, padrao) => {
        const { status, data, retryAfter } = resposta;
        if (data.erro) {
            return data.erro;
        }
        if (status === 429) {
            const segundos = parseInt(retryAfter, 10);
            const espera = Number.isFinite(segundos) && segundos > 0
                ? ` Tente novamente em ${Math.ceil(segundos / 60)} min.`
                : ' Aguarde alguns minutos.';
            return `Muitas tentativas.${espera}`;
        }
        return padrao;
    },

    fazerLogin: async (email, senha) => {
        const erroEl = document.getElementById('login-erro');
        erroEl.hidden = true;
        try {
            const resposta = await Http.requisitar(CONFIG.LOGIN_ENDPOINT, { corpo: { email, senha } });
            const data = resposta.data;

            if (data.sucesso) {
                AppState.sessao = { autenticado: true, usuario: data.usuario, tempoRestante: null, bloqueado: false };
                AuthManager.atualizarUI();
                AuthManager.fecharModal();
                MessageManager.add(`Bem-vindo de volta, ${data.usuario.nome}! Agora você tem acesso completo, sem limites. 🎉`, 'bot');
            } else {
                erroEl.textContent = AuthManager.mensagemDeErro(resposta, 'Não foi possível entrar.');
                erroEl.hidden = false;
            }
        } catch (error) {
            erroEl.textContent = 'Erro de conexão. Tente novamente.';
            erroEl.hidden = false;
        }
    },

    fazerCadastro: async (nome, email, senha) => {
        const erroEl = document.getElementById('registrar-erro');
        erroEl.hidden = true;
        try {
            const resposta = await Http.requisitar(CONFIG.REGISTRAR_ENDPOINT, { corpo: { nome, email, senha } });
            const data = resposta.data;

            if (data.sucesso) {
                AppState.sessao = { autenticado: true, usuario: data.usuario, tempoRestante: null, bloqueado: false };
                AuthManager.atualizarUI();
                AuthManager.fecharModal();
                MessageManager.add(`Cadastro concluído, ${data.usuario.nome}! Você agora tem acesso completo ao XBot, sem limites. 🎉`, 'bot');
            } else {
                erroEl.textContent = AuthManager.mensagemDeErro(resposta, 'Não foi possível cadastrar.');
                erroEl.hidden = false;
            }
        } catch (error) {
            erroEl.textContent = 'Erro de conexão. Tente novamente.';
            erroEl.hidden = false;
        }
    },

    fazerLogout: async () => {
        try {
            await Http.requisitar(CONFIG.LOGOUT_ENDPOINT);
        } catch (error) {
            console.warn('Falha ao encerrar a sessão:', error);
        } finally {
            await AuthManager.verificarSessao();
            MessageManager.add('Você saiu da sua conta. Continuando como visitante.', 'bot');
        }
    },

    // Relógio da tela: só desconta os segundos entre uma resposta do servidor e a próxima.
    // Quem decide se o visitante está bloqueado é SEMPRE o servidor (cada resposta reajusta o valor).
    iniciarContagem: () => {
        setInterval(() => {
            const sessao = AppState.sessao;
            if (sessao.autenticado || sessao.bloqueado || typeof sessao.tempoRestante !== 'number') {
                return;
            }
            sessao.tempoRestante = Math.max(0, sessao.tempoRestante - 1);
            sessao.bloqueado = sessao.tempoRestante === 0;
            AuthManager.atualizarUI();
        }, 1000);
    },

    atualizarUI: () => {
        const btnAuth = document.getElementById('btn-auth');
        const badge = document.getElementById('sessao-badge');
        const { autenticado, usuario, tempoRestante, bloqueado } = AppState.sessao;

        if (autenticado) {
            btnAuth.textContent = `🚪 Sair (${usuario.nome})`;
            badge.hidden = true;
        } else {
            btnAuth.textContent = '👤 Entrar';
            if (typeof tempoRestante === 'number') {
                const min = Math.floor(tempoRestante / 60);
                const seg = tempoRestante % 60;
                badge.textContent = bloqueado
                    ? '⏰ Tempo esgotado'
                    : `⏱️ ${min}:${seg.toString().padStart(2, '0')} restantes`;
                badge.classList.toggle('tempo-baixo', tempoRestante <= 120);
                badge.hidden = false;
            } else {
                badge.hidden = true;
            }
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
            const { ok, status, data } = await Http.requisitar(CONFIG.API_ENDPOINT, {
                corpo: { mensagem: mensagem, nome_usuario: AppState.nomeUsuario }
            });

            // 403 com bloqueado=true: o servidor encerrou o teste gratuito do visitante.
            // O corpo traz o aviso e é tratado em ChatBot.sendMessage (abre o cadastro).
            if (data.bloqueado) {
                return data;
            }

            if (!ok) {
                const erro = new Error(`HTTP error! status: ${status}`);
                // Erros 4xx trazem uma explicação útil ("mensagem deve ser um texto"...); 5xx ficam genéricos.
                erro.mensagemServidor = status < 500 ? data.erro : null;
                throw erro;
            }

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

            // v0.3.0 Beta: visitante com tempo esgotado — bloquear e abrir modal
            if (data.bloqueado) {
                TypingIndicator.hide();
                MessageManager.add(data.resposta, 'bot');
                inputMensagem.disabled = false;
                btnEnviar.disabled = false;
                AppState.sessao.bloqueado = true;
                AppState.sessao.tempoRestante = 0;
                AuthManager.atualizarUI();
                AuthManager.abrirModal('registrar');
                return;
            }

            // Atualizar status de sessão (tempo restante do visitante, se aplicável)
            AppState.sessao.autenticado = data.autenticado;
            AppState.sessao.tempoRestante = data.tempo_restante;
            AuthManager.atualizarUI();

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
            MessageManager.add(error.mensagemServidor || 'Desculpe, ocorreu um erro. Tente novamente.', 'bot');
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
    AuthManager.init();
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

