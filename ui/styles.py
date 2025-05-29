# ui/styles.py
"""Gestion centralisée des styles CSS de l'application"""

def get_main_styles() -> str:
    """Retourne les styles CSS principaux de l'application"""
    return """
    <style>
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
        .chat-header {
            background: linear-gradient(135deg, var(--primary-color) 0%, #003d7a 100%);
            color: white;
            padding: 1.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
            const messages = document.querySelector('.chat-messages');
            if (messages) {
                messages.scrollTop = messages.scrollHeight;
            }
        }
        
        // Call on load and after updates
        window.addEventListener('load', scrollToBottom);
        
        // Watch for new messages
        const observer = new MutationObserver(scrollToBottom);
        const messagesContainer = document.querySelector('.chat-messages');
        if (messagesContainer) {
            observer.observe(messagesContainer, { childList: true, subtree: true });
        }
        
        // Quick action handlers
        function setQuickAction(text) {
            const input = document.querySelector('textarea[aria-label="Message"]');
            if (input) {
                input.value = text;
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    </script>
    """