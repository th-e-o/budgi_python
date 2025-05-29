# ui/styles.py
"""Gestion centralisée des styles CSS de l'application"""

def get_main_styles() -> str:
    """Retourne les styles CSS principaux de l'application"""
    return """
    <style>
        /* Ajustements pour la sidebar */
        section[data-testid="stSidebar"] {
            background-color: #f8f9fa;
            padding-top: 0;
        }
        
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
        }
        /* Container principal adapté */
        .main > div {
            padding-top: 0;
            padding-bottom: 0;
        }
        /* Variables CSS */
        :root {
            --primary-color: #0055A4;
            --secondary-color: #EF4135;
            --user-msg-bg: #007AFF;
            --bot-msg-bg: #E9ECEF;
            --chat-bg: #F8F9FA;
            --text-dark: #212529;
            --text-light: #6C757D;
            --border-radius: 12px;
            --transition-speed: 0.2s;
        }
        
        /* Container principal du chat */
        .main-chat-container {
            height: calc(100vh - 200px);
            display: flex;
            flex-direction: column;
            background: white;
            border-radius: var(--border-radius);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        /* Header du chat */
        /* Chat header fixe */
        .chat-header {
            position: sticky;
            top: 0;
            z-index: 100;
            background: linear-gradient(135deg, var(--primary-color) 0%, #003d7a 100%);
            color: white;
            padding: 1.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: -1rem -1rem 1rem -1rem;
            border-radius: 0;
        }
        /* Container des messages avec hauteur fixe */
        div[data-testid="stVerticalBlock"] > div:has(.chat-messages) {
            height: 500px;
            overflow-y: auto;
            background: var(--chat-bg);
            border-radius: 8px;
            padding: 1rem;
        }
        
        /* Zone d'input fixe en bas */
        .chat-input-container {
            position: sticky;
            bottom: 0;
            background: white;
            padding: 1rem;
            border-top: 1px solid #E0E0E0;
            margin: 0 -1rem -1rem -1rem;
        }
        
        /* Ajuster les marges du chat pour la sidebar */
        @media (min-width: 768px) {
            .main .block-container {
                max-width: none;
                padding-left: 2rem;
                padding-right: 2rem;
            }
        }
        .bot-avatar {
            width: 50px;
            height: 50px;
            background: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .bot-info h2 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        .bot-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background: #4CAF50;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* Zone des messages */
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 1.5rem;
            background: var(--chat-bg);
            scroll-behavior: smooth;
        }
        
        /* Messages */
        .message-wrapper {
            display: flex;
            margin-bottom: 1rem;
            animation: fadeInUp 0.3s ease-out;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message-wrapper.user {
            justify-content: flex-end;
        }
        
        .message-wrapper.bot {
            justify-content: flex-start;
        }
        
        .message-bubble {
            max-width: 70%;
            padding: 0.75rem 1.25rem;
            border-radius: 18px;
            word-wrap: break-word;
            position: relative;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        .message-bubble.user {
            background: var(--user-msg-bg);
            color: white;
            border-bottom-right-radius: 4px;
            margin-left: 3rem;
        }
        
        .message-bubble.bot {
            background: var(--bot-msg-bg);
            color: var(--text-dark);
            border-bottom-left-radius: 4px;
            margin-right: 3rem;
        }
        
        .message-time {
            font-size: 0.75rem;
            color: var(--text-light);
            margin-top: 0.25rem;
            display: block;
        }
        
        .message-bubble.user .message-time {
            color: rgba(255,255,255,0.7);
            text-align: right;
        }
        
        /* Indicateur de frappe */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem 1.5rem;
            background: var(--bot-msg-bg);
            border-radius: 18px;
            border-bottom-left-radius: 4px;
            max-width: 80px;
            margin-bottom: 1rem;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            background: var(--text-light);
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        
        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
                opacity: 0.7;
            }
            30% {
                transform: translateY(-10px);
                opacity: 1;
            }
        }
        
        /* Zone de saisie */
        .chat-input-container {
            padding: 1rem;
            background: white;
            border-top: 1px solid #E0E0E0;
            display: flex;
            gap: 0.5rem;
            align-items: flex-end;
        }
        
        .chat-button {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: none;
            background: var(--primary-color);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--transition-speed);
            font-size: 1.2rem;
        }
        
        .chat-button:hover {
            transform: scale(1.1);
            box-shadow: 0 2px 8px rgba(0,85,164,0.3);
        }
        
        /* Quick actions */
        .quick-actions {
            display: flex;
            gap: 0.5rem;
            margin-top: 0.5rem;
            flex-wrap: wrap;
        }
        
        .quick-action-btn {
            padding: 0.5rem 1rem;
            background: white;
            border: 1px solid #E0E0E0;
            border-radius: 20px;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all var(--transition-speed);
            color: var(--text-dark);
        }
        
        .quick-action-btn:hover {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }

        /* Quick replies sous les messages bot */
        .quick-replies {
            margin-top: 0.5rem;
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .quick-replies button {
            padding: 0.4rem 0.8rem;
            font-size: 0.85rem;
            border-radius: 16px;
            border: 1px solid var(--primary-color);
            background: white;
            color: var(--primary-color);
            cursor: pointer;
            transition: all 0.2s;
        }

        .quick-replies button:hover {
            background: var(--primary-color);
            color: white;
            transform: translateY(-1px);
        }

        /* Style Streamlit pour les boutons quick reply */
        .stButton > button[kind="secondary"] {
            background-color: white;
            color: var(--primary-color);
            border: 1px solid var(--primary-color);
            padding: 0.4rem 0.8rem;
            font-size: 0.85rem;
            border-radius: 16px;
        }

        .stButton > button[kind="secondary"]:hover {
            background-color: var(--primary-color);
            color: white;
        }
        
        /* Tool cards */
        .tool-card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: all var(--transition-speed);
        }
        
        .tool-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .message-bubble {
                max-width: 85%;
            }
            
            .main-chat-container {
                height: calc(100vh - 150px);
            }
        }
        
        /* Hide Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """

def get_javascript() -> str:
    """Retourne le JavaScript nécessaire pour l'application"""
    return """
    <script>
        // Auto-scroll to bottom
        function scrollToBottom() {
            // Chercher tous les containers possibles
            const messagesContainers = document.querySelectorAll('.chat-messages, [data-testid="stVerticalBlock"] > div:has(.message-wrapper)');
            messagesContainers.forEach(container => {
                if (container.scrollHeight > container.clientHeight) {
                    container.scrollTop = container.scrollHeight;
                }
            });
            
            // Chercher spécifiquement les containers avec hauteur fixe
            const fixedHeightContainers = document.querySelectorAll('div[style*="height: 500px"], div[style*="overflow-y: auto"]');
            fixedHeightContainers.forEach(container => {
                if (container.querySelector('.message-wrapper, .chat-messages')) {
                    container.scrollTop = container.scrollHeight;
                }
            });
        }
        
        // Fonction pour effacer le champ de saisie
        function clearMessageInput() {
            const textarea = document.querySelector('textarea[aria-label="Message"]');
            if (textarea) {
                textarea.value = '';
                // Déclencher l'événement pour que Streamlit mette à jour
                const event = new Event('input', { bubbles: true });
                textarea.dispatchEvent(event);
            }
        }
        
        // Gérer la touche Enter
        function setupEnterKeyHandler() {
            const textarea = document.querySelector('textarea[aria-label="Message"]');
            if (textarea && !textarea.hasAttribute('data-enter-handler')) {
                textarea.setAttribute('data-enter-handler', 'true');
                
                textarea.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        
                        // Trouver et cliquer sur le bouton d'envoi
                        const sendButton = document.querySelector('button[kind="primary"]');
                        if (!sendButton) {
                            // Chercher par d'autres moyens
                            const buttons = document.querySelectorAll('button');
                            for (let btn of buttons) {
                                if (btn.textContent.includes('➤') || btn.getAttribute('aria-label')?.includes('send')) {
                                    btn.click();
                                    break;
                                }
                            }
                        } else {
                            sendButton.click();
                        }
                    }
                });
            }
        }
        
        // Observer pour nouveaux messages et réinitialiser les handlers
        function setupObserver() {
            const observer = new MutationObserver((mutations) => {
                // Scroll automatique si nouveau message
                let shouldScroll = false;
                mutations.forEach(mutation => {
                    if (mutation.addedNodes.length > 0) {
                        mutation.addedNodes.forEach(node => {
                            if (node.classList && (node.classList.contains('message-wrapper') || 
                                node.querySelector && node.querySelector('.message-wrapper'))) {
                                shouldScroll = true;
                            }
                        });
                    }
                });
                
                if (shouldScroll) {
                    setTimeout(scrollToBottom, 100);
                }
                
                // Réinitialiser le handler Enter au cas où le textarea est recréé
                setupEnterKeyHandler();
            });
            
            // Observer le body entier pour capturer tous les changements
            observer.observe(document.body, { 
                childList: true, 
                subtree: true,
                attributes: false,
                characterData: false
            });
        }
        
        // Quick action handlers
        function setQuickAction(text) {
            const textarea = document.querySelector('textarea[aria-label="Message"]');
            if (textarea) {
                textarea.value = text;
                const event = new Event('input', { bubbles: true });
                textarea.dispatchEvent(event);
                textarea.focus();
            }
        }
        
        // Initialisation
        document.addEventListener('DOMContentLoaded', function() {
            setupEnterKeyHandler();
            setupObserver();
            scrollToBottom();
        });
        
        // Réinitialiser périodiquement (pour gérer les updates Streamlit)
        setInterval(function() {
            setupEnterKeyHandler();
        }, 1000);
        
        // Scroll initial après un court délai
        setTimeout(scrollToBottom, 500);
    </script>
    """