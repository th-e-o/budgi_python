# ui/styles.py - Version complètement corrigée et simplifiée
def get_main_styles() -> str:
    """Returns simplified CSS styles that work with Streamlit's structure"""
    return """
    <style>
        /* CSS Variables */
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
        
        /* Hide Streamlit defaults */
        #MainMenu, footer, header {
            visibility: hidden;
        }
        
        /* Remove Streamlit spacing */
        .main > div {
            padding-top: 0 !important;
        }
        
        .block-container {
            padding-top: 0 !important;
            max-width: 100% !important;
        }
        
        /* Background */
        .stApp {
            background: var(--background);
        }
        
        /* Chat Panel Styles */
        .chat-panel, .chat-panel_full {
            background: var(--surface);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            margin-bottom: 1rem;
            overflow: hidden;
        }
        
        /* Excel Panel Styles */
        .excel-panel, .excel-panel_full {
            background: #f5f7fa;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            overflow: hidden;
        }
        
        /* Headers */
        .modern-chat-header, .excel-header {
            background: var(--primary);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: var(--radius-lg) var(--radius-lg) 0 0;
        }
        
        .excel-header h3 {
            margin: 0;
            color: white;
            font-size: 1.25rem;
            font-weight: 600;
        }
        
        .excel-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
            font-size: 0.875rem;
        }
        
        /* Chat Components */
        .chat-header-content {
            display: flex;
            align-items: center;
            gap: 1rem;
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
        
        /* Messages */
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
        
        /* File message */
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
        
        /* Expander styling */
        .stExpander {
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-lg) !important;
            margin-bottom: 1rem !important;
            background: var(--surface) !important;
            box-shadow: var(--shadow-sm) !important;
        }
        
        .stExpander:hover {
            box-shadow: var(--shadow-md) !important;
        }
        
        .stExpander > div:first-child {
            background: var(--border-light) !important;
            padding: 1rem 1.5rem !important;
            font-weight: 600 !important;
        }
        
        /* Buttons */
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
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--border-light);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-secondary);
        }
        
        /* Container fixes */
        div[data-testid="stVerticalBlock"] > div[style*="height"] {
            overflow-y: auto !important;
        }
        
        /* Remove extra spacing */
        .element-container {
            margin: 0 !important;
        }
        
        div[data-testid="stToolbar"] {
            display: none !important;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .message-bubble { max-width: 85%; }
        }
    </style>
    """

def get_javascript() -> str:
    """Returns simplified JavaScript"""
    return """
    <script>
        // Drag and drop functionality
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
        })();
    </script>
    """