class JarvisAssistant {
    constructor() {
        // state
        this.isListening = false;
        this.recognition = null;
        this.synth = window.speechSynthesis;
        this.settings = this.loadSettings();
        this.history = this.loadHistory();
        this.customCommands = this.loadCustomCommands();
        this.commands = {};

        this.registerCommand = (keyword, action) => {
            this.commands[keyword.toLowerCase()] = action;
        };

        this.user = this.loadProfile();

        // elements
        this.elements = {
            loadingScreen: document.getElementById("loading-screen"),
            talkBtn: document.getElementById("talk-btn"),
            micIcon: document.getElementById("mic-icon"),
            chatWindow: document.getElementById("chat-window"),
            textInput: document.getElementById("text-input"),
            sendBtn: document.getElementById("send-btn"),
            statusDot: document.querySelector(".status-dot"),
            statusText: document.querySelector(".status-text"),
            settingsBtn: document.getElementById("settings-btn"),
            settingsModal: document.getElementById("settings-modal"),
            closeSettings: document.getElementById("close-settings"),
            profileBtn: document.getElementById("profile-btn"),
            profileModal: document.getElementById("profile-modal"),
            profileInput: document.getElementById("profile-input"),
            avatarInput: document.getElementById("avatar-input"),
            saveProfile: document.getElementById("save-profile"),
            profileNameLabel: document.getElementById("profile-name"),
            profileAvatar: document.getElementById("profile-avatar"),
            rateInput: document.getElementById("voice-rate"),
            pitchInput: document.getElementById("voice-pitch"),
            volumeInput: document.getElementById("voice-volume"),
            rateVal: document.getElementById("rate-value"),
            pitchVal: document.getElementById("pitch-value"),
            volumeVal: document.getElementById("volume-value"),
            autoListen: document.getElementById("auto-listen"),
            persistChat: document.getElementById("persist-chat"),
            themeSelect: document.getElementById("theme-select"),
            customList: document.getElementById("custom-list"),
            addCustomBtn: document.getElementById("add-custom-btn"),
            quickCmds: document.querySelectorAll(".quick-cmd"),
            shortcutsBtn: document.getElementById("shortcut-btn"),
            shortcutsModal: document.getElementById("shortcuts-modal"),
            closeShortcuts: document.getElementById("close-shortcuts"),
            searchHistoryBtn: document.getElementById("search-history-btn"),
            searchHistoryModal: document.getElementById("search-history-modal"),
            closeSearchHistory: document.getElementById("close-search-history"),
            searchInput: document.getElementById("search-input"),
            searchResults: document.getElementById("search-results"),
            addCommandBtn: document.getElementById("add-command-btn"),
            addCommandModal: document.getElementById("add-command-modal"),
            closeAddCommand: document.getElementById("close-add-command"),
            commandKeyword: document.getElementById("command-keyword"),
            commandResponse: document.getElementById("command-response"),
            saveCommandBtn: document.getElementById("save-command-btn"),
            commandsList: document.getElementById("commands-list")
        };

        this.init();
    }

    init() {
        this.showLoading();
        
        // Timeout de segurança para evitar loading infinito
        const safetyTimeout = setTimeout(() => {
            console.warn("Loading timeout - forçando inicialização");
            this.hideLoading();
            this.addMessage("Sistema inicializado com limitações. Algumas funcionalidades podem não estar disponíveis.", "jarvis");
            this.updateStatus("online");
        }, 5000);

        try {
            setTimeout(async () => {
                try {
                    this.setupSpeech();
                    this.bindUI();
                    this.applyTheme();
                    this.renderProfile();
                    this.renderCustomCommands();

                    if (this.settings.persist && this.history.length) this.restoreHistory();
                    
                    clearTimeout(safetyTimeout);
                    this.hideLoading();
                    await this.delay(300);
                    this.greetUser();
                    this.updateStatus("online");
                } catch (error) {
                    console.error("Erro durante inicialização:", error);
                    clearTimeout(safetyTimeout);
                    this.hideLoading();
                    this.addMessage("Erro durante inicialização. Algumas funcionalidades podem estar limitadas.", "jarvis");
                    this.updateStatus("online");
                }
            }, 900);
        } catch (error) {
            console.error("Erro crítico na inicialização:", error);
            clearTimeout(safetyTimeout);
            this.hideLoading();
            this.updateStatus("online");
        }
    }

    /* ---------- storage ---------- */
    loadSettings(){
        const def = {voiceRate:1,voicePitch:1,voiceVolume:1,autoListen:false,theme:"dark",persist:true};
        try {
            const raw = localStorage.getItem("jarvis-settings");
            return raw? {...def, ...JSON.parse(raw)}:def;
        } catch { return def; }
    }
    saveSettings(){ localStorage.setItem("jarvis-settings", JSON.stringify(this.settings)); }

    loadHistory(){ try { return JSON.parse(localStorage.getItem("jarvis-history")||"[]"); } catch { return []; } }
    saveHistory(){ if(this.settings.persist) localStorage.setItem("jarvis-history", JSON.stringify(this.history)); }

    loadCustomCommands(){ try { return JSON.parse(localStorage.getItem("jarvis-custom-commands")||"{}"); } catch { return {}; } }
    saveCustomCommands(){ localStorage.setItem("jarvis-custom-commands", JSON.stringify(this.customCommands)); }

    loadProfile(){ try { return JSON.parse(localStorage.getItem("jarvis-profile")||"{}"); } catch { return {}; } }
    saveProfile(){ localStorage.setItem("jarvis-profile", JSON.stringify(this.user)); }

    /* ---------- UI ---------- */
    showLoading(){ this.elements.loadingScreen.classList.remove("hidden"); }
    hideLoading(){ this.elements.loadingScreen.classList.add("hidden"); setTimeout(()=>this.elements.loadingScreen.style.display="none",500) }

    applyTheme(){ document.body.setAttribute("data-theme", this.settings.theme || "dark"); this.elements.themeSelect.value = this.settings.theme; }

    updateStatus(status){
        this.elements.statusDot.className = `status-dot ${status}`;
        this.elements.statusText.textContent = status === "online" ? "Online" : (status === "listening" ? "Escutando" : "Offline");
    }

    renderProfile(){
        const name = this.user.name || "Amigo";
        this.elements.profileNameLabel.textContent = name;
        this.elements.profileAvatar.src = this.user.avatar || "assets/avatar.png";
        this.elements.profileInput.value = this.user.name || "";
        this.elements.avatarInput.value = this.user.avatar || "assets/avatar.png";
    }

    renderCustomCommands(){
        this.elements.customList.innerHTML = "";
        Object.keys(this.customCommands).forEach(keyword => {
            const cmd = this.customCommands[keyword];
            const item = document.createElement("div");
            item.className = "custom-command-item";
            item.innerHTML = `
                <div class="command-info">
                    <div class="command-keyword">"${keyword}"</div>
                    <small>${cmd.response.substring(0, 30)}...</small>
                </div>
                <button class="delete-cmd-btn" data-keyword="${keyword}" title="Deletar">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            this.elements.customList.appendChild(item);
        });

        // Bind delete buttons
        document.querySelectorAll(".delete-cmd-btn").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const keyword = e.currentTarget.dataset.keyword;
                delete this.customCommands[keyword];
                this.saveCustomCommands();
                this.renderCustomCommands();
            });
        });
    }

    renderCommandsList(){
        this.elements.commandsList.innerHTML = "";
        Object.keys(this.customCommands).forEach(keyword => {
            const cmd = this.customCommands[keyword];
            const item = document.createElement("div");
            item.className = "command-item-settings";
            item.innerHTML = `
                <div class="command-details">
                    <div class="command-keyword-settings">"${keyword}"</div>
                    <div class="command-response-preview">${cmd.response}</div>
                </div>
                <div class="command-actions">
                    <button class="edit-cmd-btn" data-keyword="${keyword}" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="delete-cmd-settings-btn" data-keyword="${keyword}" title="Deletar">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            this.elements.commandsList.appendChild(item);
        });

        // Bind delete and edit buttons
        document.querySelectorAll(".delete-cmd-settings-btn").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const keyword = e.currentTarget.dataset.keyword;
                delete this.customCommands[keyword];
                this.saveCustomCommands();
                this.renderCommandsList();
            });
        });

        document.querySelectorAll(".edit-cmd-btn").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const keyword = e.currentTarget.dataset.keyword;
                const cmd = this.customCommands[keyword];
                this.elements.commandKeyword.value = keyword;
                this.elements.commandResponse.value = cmd.response;
                delete this.customCommands[keyword];
                this.saveCustomCommands();
                this.renderCommandsList();
            });
        });
    }

    /* ---------- messages ---------- */
    addMessage(text, sender="jarvis", opts={typing:false,card:null}) {
        const chat = this.elements.chatWindow;
        const msg = document.createElement("div");
        msg.className = `message ${sender}`;

        const avatar = document.createElement("img");
        avatar.className = "avatar";
        avatar.src = sender === "user" ? (this.user.avatar || "assets/avatar.png") : "assets/avatar.png";
        avatar.alt = sender;

        const bubble = document.createElement("div");
        bubble.className = "bubble";

        if (opts.typing) {
            bubble.innerHTML = `<span class=\"typing\"><span class=\"dot\"></span><span class=\"dot\"></span><span class=\"dot\"></span></span>`;
            msg.appendChild(avatar);
            msg.appendChild(bubble);
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;

            setTimeout(()=> {
                bubble.textContent = text;
                if (sender === "jarvis") this.speak(text);
                this.history.unshift({sender, text, ts: new Date().toISOString()});
                if(this.history.length>50) this.history = this.history.slice(0,50);
                this.saveHistory();
                if (opts.card) this.addCard(opts.card);
            }, 900 + Math.random()*700);
        } else {
            bubble.textContent = text;
            msg.appendChild(avatar);
            msg.appendChild(bubble);
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
            if (sender === "jarvis") this.speak(text);
            this.history.unshift({sender, text, ts: new Date().toISOString()});
            if(this.history.length>50) this.history = this.history.slice(0,50);
            this.saveHistory();
            if (opts.card) this.addCard(opts.card);
        }
    }

    addCard(card){
        // basic card UI appended to chat
        const chat = this.elements.chatWindow;
        const wrapper = document.createElement("div");
        wrapper.className = "message jarvis";
        wrapper.style.alignItems = "stretch";
        wrapper.innerHTML = `<div class=\"avatar\" style=\"width:46px;height:46px;background:transparent\"></div>\n            <div class=\"bubble\" style=\"padding:12px;max-width:460px;border-radius:12px\">\n                ${card.html || ""}\n            </div>`;
        chat.appendChild(wrapper);
        chat.scrollTop = chat.scrollHeight;
    }

    restoreHistory(){
        // render last 20 messages (reverse to older->new)
        const msgs = this.history.slice(0,20).reverse();
        msgs.forEach(m => this.addMessage(m.text, m.sender, {typing:false}));
    }

    /* ---------- search history ---------- */
    searchHistory(query){
        if(!query.trim()) {
            this.elements.searchResults.innerHTML = "<p class='no-results'>Digite para pesquisar...</p>";
            return;
        }

        const lowerQuery = query.toLowerCase();
        const results = this.history.filter(msg => 
            msg.text.toLowerCase().includes(lowerQuery)
        );

        if(results.length === 0) {
            this.elements.searchResults.innerHTML = "<p class='no-results'>Nenhum resultado encontrado.</p>";
            return;
        }

        this.elements.searchResults.innerHTML = results.map((msg, idx) => `
            <div class="search-result-item">
                <div class="result-sender ${msg.sender}">${msg.sender === 'user' ? 'Você' : 'JARVIS'}</div>
                <div class="result-text">${msg.text}</div>
                <div class="result-time">${new Date(msg.ts).toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'})}</div>
            </div>
        `).join("");
    }

    /* ---------- speech ---------- */
    setupSpeech(){
        // recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            this.recognition = new SpeechRecognition();
            this.recognition.lang = "pt-BR";
            this.recognition.interimResults = false;
            this.recognition.onstart = ()=>{ this.isListening=true; this.elements.talkBtn.classList.add("listening"); this.updateStatus("listening"); this.playSound("start_listen.mp3") }
            this.recognition.onresult = (e)=> {
                const txt = Array.from(e.results).map(r=>r[0].transcript).join("");
                this.elements.textInput.value = txt;
                this.addMessage(txt, "user");
                this.processCommand(txt);
            }
            this.recognition.onend = ()=>{ this.isListening=false; this.elements.talkBtn.classList.remove("listening"); this.updateStatus("online"); if(this.settings.autoListen) setTimeout(()=>this.startListening(),800); this.playSound("stop_listen.mp3") }
            this.recognition.onerror = (ev)=>{ console.error(ev); this.addMessage("Erro no reconhecimento: "+ev.error,"jarvis"); }
        } else {
            console.warn("Reconhecimento de voz não suportado");
        }

        // synthesis defaults
        this.voiceSettings = {rate:this.settings.voiceRate,pitch:this.settings.voicePitch,volume:this.settings.voiceVolume};
    }

    speak(text){
        if(!text) return;
        if(!this.synth) return;
        this.synth.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang="pt-BR"; u.rate=this.settings.voiceRate; u.pitch=this.settings.voicePitch; u.volume=this.settings.voiceVolume;
        this.synth.speak(u);
    }

    startListening(){
        if(!this.recognition || this.isListening) return;
        try { this.recognition.start(); } catch(e){ console.error(e); }
    }
    stopListening(){ if(this.recognition && this.isListening) this.recognition.stop(); }

    /* ---------- commands & processing ---------- */
    async processCommand(raw){
        if(!raw) return;
        const cmd = raw.toLowerCase().trim();

        // Check custom commands first
        for (const [keyword, cmdObj] of Object.entries(this.customCommands)) {
            if (cmd.includes(keyword.toLowerCase())) {
                this.addMessage(cmdObj.response, "jarvis", {typing:true});
                return;
            }
        }

        // Save custom "meu nome é ..." flow
        if (cmd.startsWith("meu nome é") || cmd.startsWith("meu nome e")) {
            const name = cmd.replace(/meu nome é|meu nome e/i,"").trim();
            if (name) { this.user.name = this.capitalize(name); this.saveProfile(); this.renderProfile(); this.addMessage(`Prazer em te conhecer, ${this.user.name}! Como posso ajudar?`, "jarvis", {typing:true}); return; }
        }
        // small talk
        if (/(oi|olá|bom dia|boa tarde|boa noite|eae)/i.test(cmd)) { this.addMessage(this._random(["E aí, beleza?","Tô aqui — manda o que precisa","Diz aí!"]), "jarvis", {typing:true}); return; }

        // time / date
        if (cmd.includes("hora")) {
            const t = new Date().toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"});
            this.addMessage(`${this.user.name ? this.user.name + ', ' : ''}agora são ${t}`, "jarvis", {typing:true}); return;
        }
        if (cmd.includes("dia") || cmd.includes("data")) {
            const d = new Date().toLocaleDateString("pt-BR",{weekday:"long",day:"2-digit",month:"long",year:"numeric"});
            this.addMessage(`${this.user.name ? this.user.name + ', ' : ''}hoje é ${d}`, "jarvis", {typing:true}); return;
        }

        // calculator simple: "calcule 2+2" or "quanto é 12 * 3"
        const calcMatch = cmd.match(/(?:calcule|quanto é|quanto e|quanto) (.+)/i);
        if (calcMatch) {
            try {
                const result = this.safeCalculate(calcMatch[1]);
                if (result !== null) {
                    this.addMessage(`${this.user.name ? this.user.name + ', ' : ''}o resultado é: ${result}`, "jarvis", {typing:true, card:{html:`<strong>Calculadora</strong><p>${calcMatch[1]} = <strong>${result}</strong></p>`}});
                } else {
                    this.addMessage(`${this.user.name ? this.user.name + ', ' : ''}não consegui calcular isso. Use apenas números, operadores básicos (+, -, *, /, %).`, "jarvis", {typing:true});;
                }
            } catch (e) {
                this.addMessage(`${this.user.name ? this.user.name + ', ' : ''}erro no cálculo. Verifique a expressão e tente novamente.`, "jarvis", {typing:true});
            }
            return;
        }

        // fake weather: "previsão do tempo em SP" or "previsão do tempo"
        if (cmd.includes("previsão") || cmd.includes("tempo") || cmd.includes("clima")) {
            const cityMatch = cmd.match(/em (.+)/);
            const city = cityMatch ? this.capitalize(cityMatch[1]) : "sua cidade";
            // simulated card
            const tmp = (20 + Math.floor(Math.random()*12));
            const cond = this._random(["Ensolarado","Nublado com pancadas","Chuvoso","Parcialmente nublado","Tempestade isolada"]);
            const card = {
                html: `<div style=\"display:flex;gap:12px;align-items:center\">\n                        <div style=\"font-size:34px\">${tmp}ºC</div>\n                        <div>\n                            <div style=\"font-weight:700\">${city}</div>\n                            <div style=\"font-size:13px;color:var(--muted)\">${cond}</div>\n                        </div>\n                    </div>`
            };
            this.addMessage(`${this.user.name ? this.user.name + ', ' : ''}a previsão em ${city} é de ${tmp}ºC — ${cond}`, "jarvis", {typing:true, card});
            return;
        }

        // perguntas basicas sobre tecnologia
        if (cmd === "o que é html") {
            this.addMessage("HTML (HyperText Markup Language) é a linguagem de marcação padrão para criar páginas web. Ele descreve a estrutura de uma página da web semanticamente e originalmente incluiu sugestões para a aparência dos documentos.", "jarvis", {typing: true});
            return;
        }
        if (cmd === "o que é css") {
            this.addMessage("CSS (Cascading Style Sheets) é uma linguagem de folha de estilo usada para descrever a apresentação de um documento escrito em HTML ou XML (incluindo dialetos XML como SVG, MathML ou XHTML). O CSS descreve como os elementos devem ser renderizados na tela, no papel, na fala ou em outras mídias.", "jarvis", {typing: true});
            return;
        }
        if (cmd === "o que é javascript") {
            this.addMessage("JavaScript é uma linguagem de programação interpretada de alto nível, caracterizada como dinâmica, fracamente tipada, baseada em protótipos e multi-paradigma. É mais conhecida como a linguagem de script para páginas Web, mas é usada em muitos ambientes fora do navegador, como Node.js, aplicativos móveis e desenvolvimento de jogos.", "jarvis", {typing: true});
            return;
        }

        // perguntas basicas sobre tecnologia
        if (cmd === "o que é html") {
            this.addMessage("HTML (HyperText Markup Language) é a linguagem de marcação padrão para criar páginas web. Ele descreve a estrutura de uma página da web semanticamente e originalmente incluiu sugestões para a aparência dos documentos.", "jarvis", {typing: true});
            return;
        }
        if (cmd === "o que é css") {
            this.addMessage("CSS (Cascading Style Sheets) é uma linguagem de folha de estilo usada para descrever a apresentação de um documento escrito em HTML ou XML (incluindo dialetos XML como SVG, MathML ou XHTML). O CSS descreve como os elementos devem ser renderizados na tela, no papel, na fala ou em outras mídias.", "jarvis", {typing: true});
            return;
        }
        if (cmd === "o que é javascript") {
            this.addMessage("JavaScript é uma linguagem de programação interpretada de alto nível, caracterizada como dinâmica, fracamente tipada, baseada em protótipos e multi-paradigma. É mais conhecida como a linguagem de script para páginas Web, mas é usada em muitos ambientes fora do navegador, como Node.js, aplicativos móveis e desenvolvimento de jogos.", "jarvis", {typing: true});
            return;
        }

        // noticias simulated
        if (cmd.includes("notícia") || cmd.includes("noticias") || cmd.includes("notícias")) {
            const items = [
                {title:"Nova biblioteca JS faz devs felizes",url:"#"},
                {title:"Hackathon local reúne comunidade",url:"#"},
                {title:"Framework X lança versão 2.0",url:"#"}
            ];
            const html = `<strong>Últimas notícias</strong><ul style=\"margin:8px 0 0;padding-left:16px\">${items.map(i=>`<li><a href=\"${i.url}\" target=\"_blank\">${i.title}</a></li>`).join("")}</ul>`;
            this.addMessage(`${this.user.name ? this.user.name + ', ' : ''}encontrei algumas notícias:`, "jarvis", {typing:true, card:{html}});
            return;
        }

        // open/search
        if (cmd.startsWith("abrir ") || cmd.startsWith("abrir")) {
            if (cmd.includes("google")) { window.open("https://google.com","_blank"); this.addMessage(`${this.user.name ? this.user.name + ', ' : ''}abrindo Google...`, "jarvis", {typing:true}); return; }
            if (cmd.includes("youtube")) { window.open("https://youtube.com","_blank"); this.addMessage(`${this.user.name ? this.user.name + ', ' : ''}abrindo YouTube...`, "jarvis", {typing:true}); return; }
        }

        // custom commands
        const registeredCommand = this.commands[cmd];
        if (registeredCommand) {
            registeredCommand();
            return;
        }

        // fallback: search suggestion
        this.addMessage(`${this.user.name ? this.user.name + ', ' : ''}não sei isso com certeza. Pesquisar na web por "${cmd}"?`, "jarvis", {typing:true});
    }

    /* ---------- UI bindings ---------- */
    bindUI(){
        // send text
        this.elements.sendBtn.addEventListener("click", ()=>{
            const text = this.elements.textInput.value;
            if(text) { this.addMessage(text, "user"); this.processCommand(text); this.elements.textInput.value = ""; }
        });
        this.elements.textInput.addEventListener("keypress", e=>{
            if(e.key === "Enter") this.elements.sendBtn.click();
        });

        // talk button
        this.elements.talkBtn.addEventListener("click", ()=>{
            if(this.isListening) this.stopListening();
            else this.startListening();
        });

        // settings modal
        this.elements.settingsBtn.addEventListener("click", ()=>{
            this.elements.settingsModal.classList.add("show");
            this.elements.rateInput.value = this.settings.voiceRate;
            this.elements.pitchInput.value = this.settings.voicePitch;
            this.elements.volumeInput.value = this.settings.voiceVolume;
            this.elements.rateVal.textContent = this.settings.voiceRate;
            this.elements.pitchVal.textContent = this.settings.voicePitch;
            this.elements.volumeVal.textContent = this.settings.voiceVolume;
            this.elements.autoListen.checked = this.settings.autoListen;
            this.elements.persistChat.checked = this.settings.persist;
            this.renderCommandsList();
        });
        this.elements.closeSettings.addEventListener("click", ()=>this.elements.settingsModal.classList.remove("show"));

        this.elements.rateInput.addEventListener("input", e=>{ this.settings.voiceRate = +e.target.value; this.elements.rateVal.textContent = e.target.value; this.saveSettings(); });
        this.elements.pitchInput.addEventListener("input", e=>{ this.settings.voicePitch = +e.target.value; this.elements.pitchVal.textContent = e.target.value; this.saveSettings(); });
        this.elements.volumeInput.addEventListener("input", e=>{ this.settings.voiceVolume = +e.target.value; this.elements.volumeVal.textContent = e.target.value; this.saveSettings(); });
        this.elements.autoListen.addEventListener("change", e=>{ this.settings.autoListen = e.target.checked; this.saveSettings(); });
        this.elements.persistChat.addEventListener("change", e=>{ this.settings.persist = e.target.checked; this.saveSettings(); });

        // profile modal
        this.elements.profileBtn.addEventListener("click", ()=>this.elements.profileModal.classList.add("show"));
        document.getElementById("close-profile").addEventListener("click", ()=>this.elements.profileModal.classList.remove("show"));
        this.elements.saveProfile.addEventListener("click", ()=>{
            this.user.name = this.elements.profileInput.value;
            this.user.avatar = this.elements.avatarInput.value;
            this.saveProfile();
            this.renderProfile();
            this.elements.profileModal.classList.remove("show");
        });

        // theme select
        this.elements.themeSelect.addEventListener("change", e=>{
            this.settings.theme = e.target.value;
            this.saveSettings();
            this.applyTheme();
        });

        // quick commands
        this.elements.quickCmds.forEach(btn=>{
            btn.addEventListener("click", e=>{
                const cmd = e.target.dataset.command;
                this.elements.textInput.value = cmd;
                this.elements.sendBtn.click();
            });
        });

        // shortcuts modal
        this.elements.shortcutsBtn.addEventListener("click", ()=>this.elements.shortcutsModal.classList.add("show"));
        this.elements.closeShortcuts.addEventListener("click", ()=>this.elements.shortcutsModal.classList.remove("show"));

        // search history modal
        this.elements.searchHistoryBtn.addEventListener("click", ()=>{
            this.elements.searchHistoryModal.classList.add("show");
            this.elements.searchInput.value = "";
            this.elements.searchResults.innerHTML = "<p class='no-results'>Digite para pesquisar...</p>";
            this.elements.searchInput.focus();
        });
        this.elements.closeSearchHistory.addEventListener("click", ()=>this.elements.searchHistoryModal.classList.remove("show"));

        this.elements.searchInput.addEventListener("input", (e)=>{
            this.searchHistory(e.target.value);
        });

        // add command modal
        this.elements.addCommandBtn.addEventListener("click", ()=>{
            this.elements.addCommandModal.classList.add("show");
            this.elements.commandKeyword.value = "";
            this.elements.commandResponse.value = "";
            this.elements.commandKeyword.focus();
        });

        this.elements.closeAddCommand.addEventListener("click", ()=>this.elements.addCommandModal.classList.remove("show"));

        this.elements.saveCommandBtn.addEventListener("click", ()=>{
            const keyword = this.elements.commandKeyword.value.trim().toLowerCase();
            const response = this.elements.commandResponse.value.trim();

            if(!keyword || !response) {
                alert("Por favor, preencha todos os campos.");
                return;
            }

            this.customCommands[keyword] = {response, createdAt: new Date().toISOString()};
            this.saveCustomCommands();
            this.renderCustomCommands();
            this.renderCommandsList();
            this.elements.addCommandModal.classList.remove("show");
            this.addMessage(`Comando "${keyword}" adicionado com sucesso!`, "jarvis", {typing:true});
        });

        // keyboard shortcuts
        document.addEventListener("keydown", e=>{
            if(e.key === "Enter" && document.activeElement === this.elements.textInput) { this.elements.sendBtn.click(); }
            if((e.ctrlKey || e.metaKey) && e.key === "h") { e.preventDefault(); this.elements.searchHistoryBtn.click(); }
        });
    }

    /* ---------- helpers ---------- */
    capitalize(str){ return str.charAt(0).toUpperCase() + str.slice(1); }
    _random(arr){ return arr[Math.floor(Math.random()*arr.length)]; }
    delay(ms){ return new Promise(res=>setTimeout(res,ms)); }

    playSound(file){
        const audio = new Audio(`assets/${file}`);
        audio.volume = this.settings.voiceVolume;
        audio.play();
    }

    greetUser(){
        const hour = new Date().getHours();
        let greeting;
        if(hour < 12) greeting = "Bom dia";
        else if (hour < 18) greeting = "Boa tarde";
        else greeting = "Boa noite";

        if (!this.user.name) {
            this.addMessage(`${greeting}, para começarmos, qual é o seu nome?`, "jarvis", {typing:true});
        } else {
            this.addMessage(`${greeting}, ${this.user.name}! Como posso ajudar hoje?`, "jarvis", {typing:true});
        }
    }

    // Função de calculadora segura para substituir eval()
    safeCalculate(expression) {
        try {
            // Sanitizar entrada: permitir apenas números, operadores básicos, parênteses e espaços
            const sanitized = expression.replace(/[^0-9+\-*/().,% ]/g, '').replace(/,/g, '.');
            
            if (!sanitized || sanitized.trim() === '') {
                return null;
            }

            // Verificar se há caracteres válidos
            if (!/[0-9]/.test(sanitized)) {
                return null;
            }

            // Substituir % por /100
            const processed = sanitized.replace(/(\d+(?:\.\d+)?)\s*%/g, '($1/100)');

            // Parser simples e seguro para expressões matemáticas
            return this.parseExpression(processed);
        } catch (error) {
            console.error('Erro na calculadora:', error);
            return null;
        }
    }

    // Parser de expressões matemáticas seguro
    parseExpression(expr) {
        // Remove espaços
        expr = expr.replace(/\s/g, '');
        
        // Verifica se a expressão é válida
        if (!/^[0-9+\-*/().]+$/.test(expr)) {
            return null;
        }

        // Verifica parênteses balanceados
        let parenthesesCount = 0;
        for (let char of expr) {
            if (char === '(') parenthesesCount++;
            if (char === ')') parenthesesCount--;
            if (parenthesesCount < 0) return null;
        }
        if (parenthesesCount !== 0) return null;

        try {
            // Usar Function constructor como alternativa mais segura ao eval
            const result = new Function('return ' + expr)();
            
            // Verificar se o resultado é um número válido
            if (typeof result !== 'number' || !isFinite(result)) {
                return null;
            }

            // Arredondar para 10 casas decimais para evitar problemas de precisão
            return Math.round(result * 10000000000) / 10000000000;
        } catch (error) {
            return null;
        }
    }
}

// Tornar a instância disponível globalmente para as melhorias
window.jarvisInstance = new JarvisAssistant();

