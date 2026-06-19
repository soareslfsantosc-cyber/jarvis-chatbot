class JarvisEnhancements {
    constructor(jarvisInstance) {
        this.jarvis = jarvisInstance;
        this.init();
    }

    init() {
        this.enhanceKeyboardInteraction();
        this.enhanceMouseInteraction();
        this.addVisualImprovements();
        this.addFunctionalImprovements();
        this.addAdvancedCommands();
        this.setupErrorHandling();
        this.setupPerformanceMonitoring();
        this.setupAccessibilityFeatures();
        this.setupTabSystem();
    }

    enhanceKeyboardInteraction() {
        const textInput = this.jarvis.elements.textInput;
        const sendBtn = this.jarvis.elements.sendBtn;

        textInput.addEventListener('focus', () => {
            textInput.parentElement.style.boxShadow = '0 0 20px rgba(0, 188, 212, 0.5)';
            textInput.parentElement.style.borderColor = 'var(--accent)';
        });

        textInput.addEventListener('blur', () => {
            textInput.parentElement.style.boxShadow = '';
            textInput.parentElement.style.borderColor = '';
        });

        textInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendBtn.click();
            }
        });

        let messageHistory = [];
        let historyIndex = -1;

        const originalAddMessage = this.jarvis.addMessage.bind(this.jarvis);
        this.jarvis.addMessage = (text, sender, opts) => {
            if (sender === 'user') {
                messageHistory.unshift(text);
                if (messageHistory.length > 20) messageHistory.pop();
            }
            return originalAddMessage(text, sender, opts);
        };

        textInput.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowUp' && messageHistory.length > 0) {
                e.preventDefault();
                historyIndex = Math.min(historyIndex + 1, messageHistory.length - 1);
                textInput.value = messageHistory[historyIndex];
                setTimeout(() => textInput.selectionStart = textInput.selectionEnd = textInput.value.length, 0);
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                historyIndex = Math.max(historyIndex - 1, -1);
                textInput.value = historyIndex >= 0 ? messageHistory[historyIndex] : '';
            }
        });

        textInput.addEventListener('focus', () => {
            if (textInput.value === '') historyIndex = -1;
        });

        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
                e.preventDefault();
                this.jarvis.processCommand('limpar chat');
            }
        });

        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                textInput.focus();
            }
        });
    }

    enhanceMouseInteraction() {
        const buttons = document.querySelectorAll('button');
        buttons.forEach(btn => {
            btn.addEventListener('mouseenter', () => {
                btn.style.transform = 'scale(1.05)';
                btn.style.transition = 'transform 0.2s ease';
            });

            btn.addEventListener('mouseleave', () => {
                btn.style.transform = 'scale(1)';
            });

            btn.addEventListener('mousedown', () => {
                btn.style.transform = 'scale(0.95)';
            });

            btn.addEventListener('mouseup', () => {
                btn.style.transform = 'scale(1.05)';
            });
        });
    }

    addVisualImprovements() {
        const style = document.createElement('style');
        style.textContent = `
            .message {
                animation: slideIn 0.3s ease-out;
            }

            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        document.head.appendChild(style);
    }

    addFunctionalImprovements() {
        const footer = document.querySelector('.footer');
        if (footer) {
            const counter = document.createElement('div');
            counter.id = 'message-counter';
            counter.style.marginTop = '10px';
            counter.style.fontSize = '12px';
            counter.style.color = 'var(--muted)';
            counter.textContent = `Mensagens: 0`;
            footer.appendChild(counter);

            setInterval(() => {
                counter.textContent = `Mensagens: ${this.jarvis.history.length}`;
            }, 1000);
        }
    }

    addAdvancedCommands() {
        this.jarvis.registerCommand('limpar chat', () => {
            this.jarvis.elements.chatWindow.innerHTML = '';
            this.jarvis.history = [];
            this.jarvis.saveHistory();
            this.jarvis.addMessage("Chat limpo!", "jarvis", {typing: true});
        });

        this.jarvis.registerCommand('exportar conversa', () => {
            this.exportConversation();
        });

        this.jarvis.registerCommand('alto contraste', () => {
            this.toggleHighContrast();
        });

        this.jarvis.registerCommand('estatísticas', () => {
            this.showStats();
        });

        this.jarvis.registerCommand('ajuda', () => {
            this.showHelp();
        });
    }

    exportConversation() {
        try {
            const conversation = this.jarvis.history.map(msg =>
                `[${msg.ts || new Date().toLocaleString()}] ${msg.sender}: ${msg.text}`
            ).join('\n');

            const blob = new Blob([conversation], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `jarvis-conversa-${new Date().toISOString().split('T')[0]}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.jarvis.addMessage("Conversa exportada com sucesso!", "jarvis", {typing: true});
        } catch (error) {
            console.error('Erro ao exportar conversa:', error);
            this.jarvis.addMessage("Erro ao exportar conversa.", "jarvis", {typing: true});
        }
    }

    toggleHighContrast() {
        document.body.classList.toggle('high-contrast');
        const isHighContrast = document.body.classList.contains('high-contrast');
        this.jarvis.addMessage(
            `Modo alto contraste ${isHighContrast ? 'ativado' : 'desativado'}.`,
            "jarvis",
            {typing: true}
        );

        localStorage.setItem('jarvis-high-contrast', isHighContrast);
    }

    showStats() {
        const stats = {
            mensagens: this.jarvis.history.length,
            comandos: Object.keys(this.jarvis.commands).length,
            tema: this.jarvis.settings.theme,
            usuario: this.jarvis.user.name || 'Não definido'
        };

        const statsHtml = `
            <div class="stats-card">
                <h4>📊 Estatísticas do JARVIS</h4>
                <p><strong>Mensagens trocadas:</strong> ${stats.mensagens}</p>
                <p><strong>Comandos disponíveis:</strong> ${stats.comandos}</p>
                <p><strong>Tema atual:</strong> ${stats.tema}</p>
                <p><strong>Usuário:</strong> ${stats.usuario}</p>
            </div>
        `;

        this.jarvis.addMessage("Aqui estão suas estatísticas:", "jarvis", {
            typing: true,
            card: { html: statsHtml }
        });
    }

    showHelp() {
        const helpHtml = `
            <div class="help-card">
                <h4>🆘 Ajuda do JARVIS</h4>
                <h5>Comandos de Voz/Texto:</h5>
                <ul>
                    ${Object.keys(this.jarvis.commands).map(cmd => `<li><strong>"${cmd}"</strong></li>`).join('')}
                </ul>
            </div>
        `;

        this.jarvis.addMessage("Aqui está a lista de comandos:", "jarvis", {
            typing: true,
            card: { html: helpHtml }
        });
    }

    setupErrorHandling() {
        window.addEventListener('error', (event) => {
            console.error('Erro capturado:', event.error);
            this.logError(event.error);
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('Promise rejeitada:', event.reason);
            this.logError(event.reason);
        });
    }

    logError(error) {
        const errorLog = {
            timestamp: new Date().toISOString(),
            message: error.message || error,
            stack: error.stack || 'N/A',
            userAgent: navigator.userAgent
        };

        const errors = JSON.parse(localStorage.getItem('jarvis-errors') || '[]');
        errors.push(errorLog);

        if (errors.length > 10) {
            errors.shift();
        }

        localStorage.setItem('jarvis-errors', JSON.stringify(errors));
    }

    setupPerformanceMonitoring() {
        const originalAddMessage = this.jarvis.addMessage.bind(this.jarvis);
        this.jarvis.addMessage = (text, sender, opts) => {
            const startTime = performance.now();
            const result = originalAddMessage(text, sender, opts);
            const endTime = performance.now();

            if (sender === 'jarvis') {
                console.log(`Tempo de resposta: ${(endTime - startTime).toFixed(2)}ms`);
            }

            return result;
        };
    }

    setupAccessibilityFeatures() {
        if (localStorage.getItem('jarvis-high-contrast') === 'true') {
            document.body.classList.add('high-contrast');
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.modal.show');
                modals.forEach(modal => modal.classList.remove('show'));
            }
        });
    }

    setupTabSystem() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                
                // Remove active class from all buttons and contents
                tabButtons.forEach(b => b.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked button and corresponding content
                e.target.classList.add('active');
                const activeContent = document.getElementById(`${tabName}-tab`);
                if (activeContent) {
                    activeContent.classList.add('active');
                }
            });
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const checkJarvis = setInterval(() => {
        if (window.jarvisInstance) {
            new JarvisEnhancements(window.jarvisInstance);
            clearInterval(checkJarvis);
        }
    }, 100);
});




/* ========== MELHORIAS ADICIONAIS ========== */

// Extensão da classe para adicionar mais funcionalidades
class JarvisAdvancedFeatures {
    constructor(jarvisInstance) {
        this.jarvis = jarvisInstance;
        this.init();
    }

    init() {
        this.setupAdvancedCommands();
        this.setupNotifications();
        this.setupAutoSave();
        this.setupCommandSuggestions();
    }

    setupAdvancedCommands() {
        // Comando: Limpar chat
        this.jarvis.registerCommand('limpar chat', () => {
            if (confirm('Tem certeza que deseja limpar o chat?')) {
                this.jarvis.elements.chatWindow.innerHTML = '';
                this.jarvis.history = [];
                this.jarvis.saveHistory();
                this.jarvis.addMessage("Chat limpo com sucesso!", "jarvis", {typing: true});
            }
        });

        // Comando: Exportar conversa
        this.jarvis.registerCommand('exportar conversa', () => {
            this.exportConversation();
        });

        // Comando: Estatísticas
        this.jarvis.registerCommand('estatísticas', () => {
            this.showStatistics();
        });

        // Comando: Ajuda
        this.jarvis.registerCommand('ajuda', () => {
            this.showHelp();
        });

        // Comando: Resetar configurações
        this.jarvis.registerCommand('resetar configurações', () => {
            if (confirm('Isso resetará todas as configurações. Continuar?')) {
                localStorage.removeItem('jarvis-settings');
                localStorage.removeItem('jarvis-profile');
                localStorage.removeItem('jarvis-custom-commands');
                location.reload();
            }
        });

        // Comando: Status do sistema
        this.jarvis.registerCommand('status do sistema', () => {
            this.showSystemStatus();
        });
    }

    exportConversation() {
        try {
            const conversation = this.jarvis.history.map(msg => {
                const timestamp = new Date(msg.ts).toLocaleString('pt-BR');
                return `[${timestamp}] ${msg.sender.toUpperCase()}: ${msg.text}`;
            }).join('\n\n');

            const blob = new Blob([conversation], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `jarvis-conversa-${new Date().toISOString().split('T')[0]}.txt`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);

            this.jarvis.addMessage("Conversa exportada com sucesso!", "jarvis", {typing: true});
        } catch (error) {
            console.error('Erro ao exportar:', error);
            this.jarvis.addMessage("Erro ao exportar conversa.", "jarvis", {typing: true});
        }
    }

    showStatistics() {
        const customCmdsCount = Object.keys(this.jarvis.customCommands).length;
        const userMessages = this.jarvis.history.filter(m => m.sender === 'user').length;
        const jarvisMessages = this.jarvis.history.filter(m => m.sender === 'jarvis').length;

        const statsHtml = `
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <span>📊 Total de mensagens:</span>
                    <strong>${this.jarvis.history.length}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <span>👤 Suas mensagens:</span>
                    <strong>${userMessages}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <span>🤖 Respostas JARVIS:</span>
                    <strong>${jarvisMessages}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <span>⚙️ Comandos personalizados:</span>
                    <strong>${customCmdsCount}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <span>🎨 Tema atual:</span>
                    <strong>${this.jarvis.settings.theme}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <span>👤 Usuário:</span>
                    <strong>${this.jarvis.user.name || 'Não definido'}</strong>
                </div>
            </div>
        `;

        this.jarvis.addMessage("Aqui estão suas estatísticas:", "jarvis", {
            typing: true,
            card: { html: statsHtml }
        });
    }

    showHelp() {
        const helpHtml = `
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <h4 style="margin: 0; color: var(--accent);">🆘 Comandos Disponíveis</h4>
                <div style="font-size: 12px; line-height: 1.6;">
                    <p><strong>"que horas são"</strong> - Mostra a hora atual</p>
                    <p><strong>"que dia é hoje"</strong> - Mostra a data atual</p>
                    <p><strong>"calcule [expressão]"</strong> - Realiza cálculos matemáticos</p>
                    <p><strong>"previsão do tempo"</strong> - Mostra previsão do tempo</p>
                    <p><strong>"notícias"</strong> - Mostra notícias recentes</p>
                    <p><strong>"limpar chat"</strong> - Limpa o histórico de mensagens</p>
                    <p><strong>"exportar conversa"</strong> - Baixa a conversa em arquivo</p>
                    <p><strong>"estatísticas"</strong> - Mostra estatísticas de uso</p>
                    <p><strong>"status do sistema"</strong> - Informações do sistema</p>
                </div>
            </div>
        `;

        this.jarvis.addMessage("Aqui estão os comandos disponíveis:", "jarvis", {
            typing: true,
            card: { html: helpHtml }
        });
    }

    showSystemStatus() {
        const memoryInfo = performance.memory ? `${Math.round(performance.memory.usedJSHeapSize / 1048576)}MB` : 'N/A';
        const userAgent = navigator.userAgent.split(' ').slice(-2).join(' ');

        const statusHtml = `
            <div style="display: flex; flex-direction: column; gap: 8px; font-size: 12px;">
                <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <span>🌐 Navegador:</span>
                    <strong>${userAgent}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <span>💾 Memória usada:</span>
                    <strong>${memoryInfo}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <span>🔊 Suporte a voz:</span>
                    <strong>${this.jarvis.recognition ? 'Sim' : 'Não'}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <span>🔔 Notificações:</span>
                    <strong>${'Notification' in window ? 'Disponível' : 'Não disponível'}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <span>📱 Tipo de dispositivo:</span>
                    <strong>${this.getDeviceType()}</strong>
                </div>
            </div>
        `;

        this.jarvis.addMessage("Status do sistema:", "jarvis", {
            typing: true,
            card: { html: statusHtml }
        });
    }

    getDeviceType() {
        const ua = navigator.userAgent;
        if (/mobile/i.test(ua)) return 'Mobile';
        if (/tablet/i.test(ua)) return 'Tablet';
        return 'Desktop';
    }

    setupNotifications() {
        // Solicitar permissão de notificações (se suportado)
        if ('Notification' in window && Notification.permission === 'default') {
            // Não solicitar automaticamente, apenas deixar disponível
        }
    }

    setupAutoSave() {
        // Auto-save a cada 30 segundos
        setInterval(() => {
            this.jarvis.saveHistory();
            this.jarvis.saveSettings();
            this.jarvis.saveProfile();
            this.jarvis.saveCustomCommands();
        }, 30000);
    }

    setupCommandSuggestions() {
        const textInput = this.jarvis.elements.textInput;
        
        // Sugestões de comandos baseadas no que o usuário está digitando
        textInput.addEventListener('input', (e) => {
            const value = e.target.value.toLowerCase();
            if (value.length > 0) {
                // Aqui você pode adicionar lógica de sugestão
                // Por enquanto, apenas registramos
            }
        });
    }
}

// Inicializar as funcionalidades avançadas
document.addEventListener('DOMContentLoaded', () => {
    const checkJarvis = setInterval(() => {
        if (window.jarvisInstance) {
            new JarvisAdvancedFeatures(window.jarvisInstance);
            clearInterval(checkJarvis);
        }
    }, 100);
});




/* ========== MELHORIAS AVANÇADAS - VERSÃO 3.5 ========== */

class JarvisAdvancedEnhancements {
    constructor(jarvisInstance) {
        this.jarvis = jarvisInstance;
        this.init();
    }

    init() {
        this.setupDarkModeToggle();
        this.setupSmartSuggestions();
        this.setupMessageAnalytics();
        this.setupQuickActions();
        this.setupVoiceCommandPreview();
        this.setupChatExport();
        this.setupNotifications();
        this.setupKeyboardShortcuts();
    }

    // ===== MODO ESCURO AUTOMÁTICO =====
    setupDarkModeToggle() {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const savedTheme = localStorage.getItem('jarvis-theme') || (prefersDark ? 'dark' : 'light');
        
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        // Detectar mudança de preferência do sistema
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            const newTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('jarvis-theme', newTheme);
        });
    }

    // ===== SUGESTÕES INTELIGENTES =====
    setupSmartSuggestions() {
        const textInput = this.jarvis.elements.textInput;
        
        textInput.addEventListener('input', (e) => {
            const value = e.target.value.toLowerCase().trim();
            
            if (value.length > 2) {
                const suggestions = this.generateSuggestions(value);
                if (suggestions.length > 0) {
                    this.showSuggestions(suggestions, textInput);
                }
            }
        });

        // Fechar sugestões ao clicar fora
        document.addEventListener('click', (e) => {
            if (e.target !== textInput) {
                this.hideSuggestions();
            }
        });
    }

    generateSuggestions(input) {
        const allCommands = [
            ...Object.keys(this.jarvis.customCommands),
            'que horas são', 'que dia é hoje', 'calcule', 'previsão do tempo',
            'notícias', 'limpar chat', 'exportar conversa', 'estatísticas',
            'ajuda', 'status do sistema', 'resetar configurações'
        ];

        return allCommands.filter(cmd => 
            cmd.toLowerCase().includes(input) && cmd.toLowerCase() !== input
        ).slice(0, 5);
    }

    showSuggestions(suggestions, inputElement) {
        let suggestionsBox = document.getElementById('suggestions-box');
        
        if (!suggestionsBox) {
            suggestionsBox = document.createElement('div');
            suggestionsBox.id = 'suggestions-box';
            suggestionsBox.style.cssText = `
                position: absolute;
                bottom: 60px;
                left: 10px;
                right: 10px;
                background: rgba(0, 188, 212, 0.1);
                border: 1px solid var(--accent);
                border-radius: 6px;
                max-height: 200px;
                overflow-y: auto;
                z-index: 100;
            `;
            inputElement.parentElement.appendChild(suggestionsBox);
        }

        suggestionsBox.innerHTML = suggestions.map(s => `
            <div class="suggestion-item" style="padding: 8px 12px; cursor: pointer; border-bottom: 1px solid rgba(0,188,212,0.2); transition: background 0.2s;">
                ${s}
            </div>
        `).join('');

        suggestionsBox.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                inputElement.value = item.textContent;
                this.hideSuggestions();
                inputElement.focus();
            });
            item.addEventListener('mouseenter', () => {
                item.style.background = 'rgba(0, 188, 212, 0.2)';
            });
            item.addEventListener('mouseleave', () => {
                item.style.background = 'transparent';
            });
        });

        suggestionsBox.style.display = 'block';
    }

    hideSuggestions() {
        const suggestionsBox = document.getElementById('suggestions-box');
        if (suggestionsBox) suggestionsBox.style.display = 'none';
    }

    // ===== ANÁLISE DE MENSAGENS =====
    setupMessageAnalytics() {
        // Registrar estatísticas de uso
        setInterval(() => {
            const stats = {
                totalMessages: this.jarvis.history.length,
                userMessages: this.jarvis.history.filter(m => m.sender === 'user').length,
                jarvisMessages: this.jarvis.history.filter(m => m.sender === 'jarvis').length,
                customCommandsUsed: Object.keys(this.jarvis.customCommands).length,
                lastActivity: new Date().toISOString()
            };
            localStorage.setItem('jarvis-analytics', JSON.stringify(stats));
        }, 60000); // A cada minuto
    }

    // ===== AÇÕES RÁPIDAS =====
    setupQuickActions() {
        const quickActionsHTML = `
            <div id="quick-actions" style="
                display: flex;
                gap: 8px;
                margin-top: 10px;
                flex-wrap: wrap;
            ">
                <button class="quick-action" data-action="time" style="padding: 6px 12px; background: rgba(0,188,212,0.2); border: 1px solid var(--accent); border-radius: 4px; color: var(--text-color); cursor: pointer; font-size: 12px;">⏰ Horário</button>
                <button class="quick-action" data-action="date" style="padding: 6px 12px; background: rgba(0,188,212,0.2); border: 1px solid var(--accent); border-radius: 4px; color: var(--text-color); cursor: pointer; font-size: 12px;">📅 Data</button>
                <button class="quick-action" data-action="weather" style="padding: 6px 12px; background: rgba(0,188,212,0.2); border: 1px solid var(--accent); border-radius: 4px; color: var(--text-color); cursor: pointer; font-size: 12px;">🌤️ Clima</button>
                <button class="quick-action" data-action="help" style="padding: 6px 12px; background: rgba(0,188,212,0.2); border: 1px solid var(--accent); border-radius: 4px; color: var(--text-color); cursor: pointer; font-size: 12px;">❓ Ajuda</button>
            </div>
        `;

        const chatWindow = this.jarvis.elements.chatWindow;
        if (chatWindow && !document.getElementById('quick-actions')) {
            const container = document.createElement('div');
            container.innerHTML = quickActionsHTML;
            chatWindow.appendChild(container);

            document.querySelectorAll('.quick-action').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const action = e.target.dataset.action;
                    this.executeQuickAction(action);
                });
            });
        }
    }

    executeQuickAction(action) {
        switch(action) {
            case 'time':
                this.jarvis.addMessage('que horas são', 'user');
                this.jarvis.processCommand('que horas são');
                break;
            case 'date':
                this.jarvis.addMessage('que dia é hoje', 'user');
                this.jarvis.processCommand('que dia é hoje');
                break;
            case 'weather':
                this.jarvis.addMessage('previsão do tempo', 'user');
                this.jarvis.processCommand('previsão do tempo');
                break;
            case 'help':
                this.jarvis.addMessage('ajuda', 'user');
                this.jarvis.processCommand('ajuda');
                break;
        }
    }

    // ===== PREVIEW DE COMANDOS DE VOZ =====
    setupVoiceCommandPreview() {
        const micBtn = this.jarvis.elements.micBtn;
        
        if (micBtn) {
            micBtn.addEventListener('mouseenter', () => {
                this.showVoicePreview();
            });
            
            micBtn.addEventListener('mouseleave', () => {
                this.hideVoicePreview();
            });
        }
    }

    showVoicePreview() {
        let preview = document.getElementById('voice-preview');
        
        if (!preview) {
            preview = document.createElement('div');
            preview.id = 'voice-preview';
            preview.style.cssText = `
                position: absolute;
                bottom: 70px;
                right: 20px;
                background: rgba(0, 188, 212, 0.15);
                border: 1px solid var(--accent);
                border-radius: 6px;
                padding: 12px;
                max-width: 250px;
                font-size: 12px;
                z-index: 100;
            `;
            document.body.appendChild(preview);
        }

        preview.innerHTML = `
            <strong>🎤 Comandos de Voz Disponíveis:</strong><br>
            • "que horas são"<br>
            • "que dia é hoje"<br>
            • "calcule [expressão]"<br>
            • "previsão do tempo"<br>
            • "notícias"<br>
            ${Object.keys(this.jarvis.customCommands).slice(0, 3).map(cmd => `• "${cmd}"`).join('<br>')}
        `;
        preview.style.display = 'block';
    }

    hideVoicePreview() {
        const preview = document.getElementById('voice-preview');
        if (preview) preview.style.display = 'none';
    }

    // ===== EXPORTAR CHAT COM FORMATAÇÃO =====
    setupChatExport() {
        const exportBtn = document.createElement('button');
        exportBtn.id = 'export-chat-btn';
        exportBtn.title = 'Exportar conversa';
        exportBtn.style.cssText = `
            padding: 8px 12px;
            background: rgba(0, 188, 212, 0.2);
            border: 1px solid var(--accent);
            border-radius: 4px;
            color: var(--text-color);
            cursor: pointer;
            margin-top: 10px;
        `;
        exportBtn.innerHTML = '💾 Exportar';

        exportBtn.addEventListener('click', () => {
            this.exportChatAsJSON();
        });

        const settingsModal = document.getElementById('settings-modal');
        if (settingsModal) {
            settingsModal.appendChild(exportBtn);
        }
    }

    exportChatAsJSON() {
        const chatData = {
            exportDate: new Date().toLocaleString('pt-BR'),
            userProfile: this.jarvis.user,
            settings: this.jarvis.settings,
            messages: this.jarvis.history,
            customCommands: this.jarvis.customCommands,
            statistics: {
                totalMessages: this.jarvis.history.length,
                userMessages: this.jarvis.history.filter(m => m.sender === 'user').length,
                jarvisMessages: this.jarvis.history.filter(m => m.sender === 'jarvis').length
            }
        };

        const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `jarvis-chat-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        this.jarvis.addMessage('Conversa exportada em formato JSON!', 'jarvis', {typing: true});
    }

    // ===== NOTIFICAÇÕES DO NAVEGADOR =====
    setupNotifications() {
        if ('Notification' in window && Notification.permission === 'default') {
            // Não solicitar automaticamente
        }
    }

    // ===== ATALHOS DE TECLADO AVANÇADOS =====
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Shift+E: Exportar chat
            if (e.ctrlKey && e.shiftKey && e.key === 'E') {
                e.preventDefault();
                this.exportChatAsJSON();
            }

            // Ctrl+Shift+C: Limpar chat com confirmação
            if (e.ctrlKey && e.shiftKey && e.key === 'C') {
                e.preventDefault();
                if (confirm('Tem certeza que deseja limpar o chat?')) {
                    this.jarvis.elements.chatWindow.innerHTML = '';
                    this.jarvis.history = [];
                    this.jarvis.saveHistory();
                    this.jarvis.addMessage('Chat limpo!', 'jarvis', {typing: true});
                }
            }

            // Ctrl+Shift+S: Mostrar estatísticas
            if (e.ctrlKey && e.shiftKey && e.key === 'S') {
                e.preventDefault();
                this.jarvis.processCommand('estatísticas');
            }

            // Ctrl+Shift+R: Resetar configurações
            if (e.ctrlKey && e.shiftKey && e.key === 'R') {
                e.preventDefault();
                if (confirm('Isso resetará todas as configurações. Continuar?')) {
                    localStorage.clear();
                    location.reload();
                }
            }
        });
    }
}

// Inicializar as funcionalidades avançadas
document.addEventListener('DOMContentLoaded', () => {
    const checkJarvis = setInterval(() => {
        if (window.jarvisInstance) {
            new JarvisAdvancedEnhancements(window.jarvisInstance);
            clearInterval(checkJarvis);
        }
    }, 100);
});

