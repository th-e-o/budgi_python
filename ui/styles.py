# ui/styles.py - Simplified and Modern UI styles
"""Clean, modern UI with focus on usability and performance"""

def get_main_styles() -> str:
    """Returns simplified, modern CSS styles"""
    return """
    <style>
        /* CSS Variables for Clean Theme */
        :root {
            --primary: #0055A4;
            --primary-dark: #003d7a;
            --primary-light: #4d8fd9;
            --secondary: #EF4135;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --background: #f8fafc;
            --surface: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border: #e2e8f0;
            --border-light: #f1f5f9;
            
            --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
            --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
            
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
            
            --transition: 200ms ease;
        }
        
        /* Reset and base styles */
        * {
            box-sizing: border-box;
        }
        
        /* Hide Streamlit defaults */
        #MainMenu, footer, header {
            visibility: hidden;
        }
        
        /* Remove all Streamlit default spacing */
        .main > div {
            padding: 0;
            max-width: 100%;
        }
        
        /* Fix the stApp container */
        .stApp {
            overflow-x: hidden;
        }
        
        /* Remove spacing from main containers */
        section.main > div {
            padding-top: 0 !important;
        }
        
        div[data-testid="stToolbar"] {
            display: none !important;
        }
        
        div[data-testid="stDecoration"] {
            display: none !important;
        }
        
        div[data-testid="stStatusWidget"] {
            display: none !important;
        }
        
        /* First element after navbar should have no margin */
        .main > div > div:first-child {
            margin-top: 0 !important;
        }
        
        /* Remove excessive padding/margin */
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            max-width: 100% !important;
        }
        
        /* Remove all default Streamlit spacing */
        .element-container {
            margin: 0 !important;
        }
        
        div[data-testid="stHorizontalBlock"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        div[data-testid="stHorizontalBlock"] > div {
            gap: 0.5rem !important;
            padding: 0 !important;
        }
        
        /* Remove spacing from the main app view */
        .appview-container {
            padding-top: 0 !important;
        }
        
        .main .block-container {
            padding-top: 0 !important;
        }
        
        /* Simplified Top Navigation */
        .stHorizontalBlock {
            margin-bottom: 0 !important;
        }
        
        /* Remove extra spacing from columns */
        .css-1n76uvr, .css-1n543e5, .css-12oz5g7 {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        /* Chat and Excel panels positioning */
        .chat-panel, .excel-panel {
            background: var(--surface);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            overflow: hidden;
            height: calc(100vh - 80px);
            display: flex;
            flex-direction: column;
            margin-top: 0.5rem;
        }
        
        .chat-panel-full, .excel-panel-full {
            background: var(--surface);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            overflow: hidden;
            height: calc(100vh - 80px);
            display: flex;
            flex-direction: column;
            max-width: 1200px;
            margin: 0.5rem auto 0;
        }
        
        /* Main content */
        .main {
            background: var(--background);
            min-height: 100vh;
            padding: 0 !important;
        }
        
        /* Clean panels */
        .chat-panel, .excel-panel {
            background: var(--surface);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            overflow: hidden;
            height: calc(100vh - 120px);
            display: flex;
            flex-direction: column;
            margin-top: 0.5rem;
        }
        
        .chat-panel-full, .excel-panel-full {
            background: var(--surface);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            overflow: hidden;
            height: calc(100vh - 120px);
            display: flex;
            flex-direction: column;
            max-width: 1200px;
            margin: 0.5rem auto 0;
        }
        
        /* Clean Chat Header */
        .modern-chat-header {
            background: var(--primary);
            color: white;
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .chat-header-content {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .chat-avatar-wrapper {
            position: relative;
        }
        
        .chat-avatar {
            width: 40px;
            height: 40px;
            border-radius: var(--radius-md);
            background: rgba(255, 255, 255, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }
        
        .online-indicator {
            position: absolute;
            bottom: 0;
            right: 0;
            width: 10px;
            height: 10px;
            background: var(--success);
            border: 2px solid var(--primary);
            border-radius: 50%;
        }
        
        .chat-header-info h3 {
            margin: 0;
            font-size: 1.125rem;
            font-weight: 500;
        }
        
        .chat-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            opacity: 0.9;
        }
        
        /* Excel Header */
        .excel-header {
            background: var(--surface);
            padding: 1.5rem;
            border-bottom: 1px solid var(--border);
        }
        
        .excel-header h3 {
            margin: 0 0 1rem 0;
            color: var(--text-primary);
            font-size: 1.25rem;
            font-weight: 600;
        }
        
        .excel-tabs {
            display: flex;
            gap: 0.5rem;
        }
        
        .excel-tab {
            padding: 0.5rem 1rem;
            background: transparent;
            border: none;
            border-radius: var(--radius-sm);
            cursor: pointer;
            color: var(--text-secondary);
            font-weight: 500;
            transition: all var(--transition);
        }
        
        .excel-tab:hover {
            color: var(--primary);
            background: var(--border-light);
        }
        
        .excel-tab.active {
            color: var(--primary);
            background: rgba(0, 85, 164, 0.1);
        }
        
        /* Clean Messages */
        .message-wrapper {
            display: flex;
            gap: 0.75rem;
            margin-bottom: 1rem;
            align-items: flex-start;
        }
        
        .message-wrapper.user {
            flex-direction: row-reverse;
        }
        
        .message-avatar {
            width: 36px;
            height: 36px;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.125rem;
            flex-shrink: 0;
        }
        
        .message-avatar.bot {
            background: var(--primary);
            color: white;
        }
        
        .message-avatar.user {
            background: var(--border);
            color: var(--text-secondary);
        }
        
        .message-content {
            max-width: 70%;
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        
        .message-bubble {
            padding: 0.75rem 1rem;
            border-radius: var(--radius-lg);
            position: relative;
        }
        
        .message-bubble.bot {
            background: var(--border-light);
            color: var(--text-primary);
        }
        
        .message-bubble.user {
            background: var(--primary);
            color: white;
        }
        
        .message-time {
            font-size: 0.75rem;
            color: var(--text-secondary);
            padding: 0 0.5rem;
        }
        
        /* Clean file message */
        .file-message {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.5rem;
            background: var(--border-light);
            border-radius: var(--radius-md);
        }
        
        .file-icon {
            font-size: 1.5rem;
        }
        
        .file-name {
            font-weight: 500;
            color: var(--text-primary);
        }
        
        .file-status {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        /* Typing indicator */
        .typing-indicator {
            padding: 0.75rem 1rem;
            background: var(--border-light);
            border-radius: var(--radius-lg);
            display: inline-flex;
            align-items: center;
            gap: 0.375rem;
        }
        
        .typing-dot {
            width: 6px;
            height: 6px;
            background: var(--text-secondary);
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        
        /* Welcome message */
        .welcome-container {
            text-align: center;
            padding: 3rem 2rem;
            max-width: 600px;
            margin: 0 auto;
        }
        
        .welcome-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .welcome-container h2 {
            color: var(--text-primary);
            margin: 0 0 0.5rem 0;
            font-size: 1.75rem;
        }
        
        .welcome-features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        
        .feature-card {
            background: var(--border-light);
            padding: 1.25rem;
            border-radius: var(--radius-lg);
            transition: all var(--transition);
        }
        
        .feature-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        .feature-icon {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
            display: block;
        }
        
        /* Simplified buttons */
        .stButton > button {
            background: var(--primary);
            color: white;
            border: none;
            border-radius: var(--radius-md);
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all var(--transition);
        }
        
        .stButton > button:hover {
            background: var(--primary-dark);
            transform: translateY(-1px);
        }
        
        .stButton > button[kind="secondary"] {
            background: var(--surface);
            color: var(--primary);
            border: 1px solid var(--primary);
        }
        
        .stButton > button[kind="secondary"]:hover {
            background: var(--primary);
            color: white;
        }
        
        /* Drag overlay */
        .drop-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 85, 164, 0.95);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }
        
        .drop-content {
            text-align: center;
            color: white;
        }
        
        /* File uploader */
        .stFileUploader > div {
            background: var(--border-light);
            border: 2px dashed var(--border);
            border-radius: var(--radius-lg);
            transition: all var(--transition);
        }
        
        .stFileUploader > div:hover {
            border-color: var(--primary);
            background: rgba(0, 85, 164, 0.02);
        }
        
        /* Data editor */
        div[data-testid="data-editor"] {
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            overflow: hidden;
        }
        
        /* Metrics */
        div[data-testid="metric-container"] {
            background: var(--surface);
            padding: 1rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border);
        }
        
        /* Forms */
        .stForm {
            background: var(--border-light);
            padding: 1.5rem;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border);
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--border-light);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-secondary);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .navbar-subtitle { display: none; }
            .message-bubble { max-width: 85%; }
            .welcome-features { grid-template-columns: 1fr; }
        }
        
        /* Hide Streamlit elements */
        .css-1kyxreq { display: none; }
        button[title="View fullscreen"] { display: none; }
    </style>
    """

def get_javascript() -> str:
    """Returns simplified JavaScript"""
    return """
    <script>
        // Simplified drag and drop
        (function() {
            let dragCounter = 0;
            const dropOverlay = document.getElementById('drop-overlay');
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                document.addEventListener(eventName, e => {
                    e.preventDefault();
                    e.stopPropagation();
                });
            });
            
            document.addEventListener('dragenter', () => {
                dragCounter++;
                if (dragCounter === 1 && dropOverlay) {
                    dropOverlay.style.display = 'flex';
                }
            });
            
            document.addEventListener('dragleave', () => {
                dragCounter--;
                if (dragCounter === 0 && dropOverlay) {
                    setTimeout(() => dropOverlay.style.display = 'none', 100);
                }
            });
            
            document.addEventListener('drop', e => {
                dragCounter = 0;
                if (dropOverlay) dropOverlay.style.display = 'none';
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    const fileInput = document.querySelector('input[type="file"]');
                    if (fileInput) {
                        const dataTransfer = new DataTransfer();
                        dataTransfer.items.add(files[0]);
                        fileInput.files = dataTransfer.files;
                        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
            });
            
            // Auto-scroll for new messages
            const observer = new MutationObserver(() => {
                const containers = document.querySelectorAll('[data-testid="stVerticalBlock"] > div');
                containers.forEach(container => {
                    if (container.style.height && container.style.height.includes('px')) {
                        container.scrollTo({
                            top: container.scrollHeight,
                            behavior: 'smooth'
                        });
                    }
                });
            });
            
            setTimeout(() => {
                const containers = document.querySelectorAll('[data-testid="stVerticalBlock"] > div');
                containers.forEach(container => {
                    if (container.style.height && container.style.height.includes('px')) {
                        observer.observe(container, { childList: true, subtree: true });
                    }
                });
            }, 1000);
        })();
    </script>
    """