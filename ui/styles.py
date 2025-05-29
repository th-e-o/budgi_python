# ui/styles.py - Modern, impressive UI styles
"""Modern UI styles with glassmorphism, animations, and fluid design"""

def get_main_styles() -> str:
    """Returns modern, impressive CSS styles"""
    return """
    <style>
        /* CSS Variables for Modern Theme */
        :root {
            --primary: #0055A4;
            --primary-dark: #003d7a;
            --primary-light: #3d7fc7;
            --secondary: #EF4135;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --dark: #1e293b;
            --light: #f8fafc;
            --gray-100: #f1f5f9;
            --gray-200: #e2e8f0;
            --gray-300: #cbd5e1;
            --gray-400: #94a3b8;
            --gray-500: #64748b;
            --gray-600: #475569;
            --gray-700: #334155;
            --gray-800: #1e293b;
            --gray-900: #0f172a;
            
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
            --shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
            
            --blur-sm: 8px;
            --blur-md: 16px;
            --blur-lg: 24px;
            
            --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
            --transition-base: 300ms cubic-bezier(0.4, 0, 0.2, 1);
            --transition-slow: 500ms cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        /* Reset and base styles */
        * {
            box-sizing: border-box;
        }
        
        /* Hide Streamlit defaults */
        #MainMenu, footer, header {
            visibility: hidden;
        }
        
        .main > div {
            padding: 0;
        }
        
        /* Top Navigation Bar */
        .top-navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(var(--blur-lg));
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            z-index: 1000;
            transition: all var(--transition-base);
        }
        
        .navbar-content {
            height: 100%;
            padding: 0 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .navbar-brand {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .navbar-logo {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            box-shadow: var(--shadow-md);
        }
        
        .navbar-logo-placeholder {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            box-shadow: var(--shadow-md);
        }
        
        .chat-logo-placeholder {
            width: 45px;
            height: 45px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        
        /* Layout icon styling */
        .layout-icon {
            font-size: 1.25rem;
            line-height: 1;
        }
        
        .nav-icon {
            font-size: 1.25rem;
            line-height: 1;
        }
        
        .header-icon {
            font-size: 1rem;
            line-height: 1;
        }
        
        .fab-icon {
            font-size: 1.5rem;
            line-height: 1;
        }
        
        .voice-icon {
            font-size: 1.25rem;
            line-height: 1;
        }
        
        .navbar-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
            letter-spacing: -0.02em;
        }
        
        .navbar-subtitle {
            font-size: 0.875rem;
            color: var(--gray-500);
            margin-left: 0.5rem;
        }
        
        .navbar-controls {
            display: flex;
            align-items: center;
            gap: 2rem;
        }
        
        /* Layout Switcher */
        .layout-switcher {
            display: flex;
            gap: 0.5rem;
            background: var(--gray-100);
            padding: 0.25rem;
            border-radius: 12px;
        }
        
        .layout-btn {
            padding: 0.5rem;
            background: transparent;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            color: var(--gray-600);
            transition: all var(--transition-fast);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .layout-btn:hover {
            color: var(--primary);
            background: rgba(0, 85, 164, 0.1);
        }
        
        .layout-btn.active {
            background: white;
            color: var(--primary);
            box-shadow: var(--shadow-sm);
        }
        
        /* Navigation Actions */
        .nav-action-btn {
            position: relative;
            padding: 0.5rem;
            background: transparent;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            color: var(--gray-600);
            transition: all var(--transition-fast);
        }
        
        .nav-action-btn:hover {
            background: var(--gray-100);
            color: var(--primary);
        }
        
        .notification-badge {
            position: absolute;
            top: 0;
            right: 0;
            background: var(--secondary);
            color: white;
            font-size: 0.625rem;
            padding: 0.125rem 0.375rem;
            border-radius: 999px;
            font-weight: 600;
        }
        
        /* Main content area */
        .main {
            margin-top: 60px;
            padding: 1rem;
            background: var(--gray-50);
            min-height: calc(100vh - 60px);
        }
        
        /* Modern panels with glassmorphism */
        .chat-panel, .excel-panel {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(var(--blur-md));
            border-radius: 16px;
            box-shadow: var(--shadow-lg);
            border: 1px solid rgba(255, 255, 255, 0.5);
            overflow: hidden;
            height: calc(100vh - 100px);
            display: flex;
            flex-direction: column;
        }
        
        .chat-panel-full, .excel-panel-full {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(var(--blur-md));
            border-radius: 16px;
            box-shadow: var(--shadow-lg);
            border: 1px solid rgba(255, 255, 255, 0.5);
            overflow: hidden;
            height: calc(100vh - 100px);
            display: flex;
            flex-direction: column;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        /* Modern Chat Header */
        .modern-chat-header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 1.25rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-radius: 16px 16px 0 0;
        }
        
        .chat-header-content {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .chat-logo {
            width: 45px;
            height: 45px;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        
        .chat-header-info h3 {
            margin: 0;
            font-size: 1.25rem;
            font-weight: 600;
            letter-spacing: -0.02em;
        }
        
        .chat-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            opacity: 0.9;
        }
        
        .status-indicator {
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3);
            animation: pulse-status 2s infinite;
        }
        
        @keyframes pulse-status {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }
        
        .header-action-btn {
            padding: 0.5rem;
            background: rgba(255, 255, 255, 0.2);
            border: none;
            border-radius: 8px;
            cursor: pointer;
            color: white;
            transition: all var(--transition-fast);
        }
        
        .header-action-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
        }
        
        /* Excel Header with Tabs */
        .excel-header {
            background: white;
            padding: 1.5rem;
            border-bottom: 1px solid var(--gray-200);
        }
        
        .excel-header h3 {
            margin: 0 0 1rem 0;
            color: var(--gray-800);
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
            border-radius: 8px;
            cursor: pointer;
            color: var(--gray-600);
            font-weight: 500;
            transition: all var(--transition-fast);
            position: relative;
        }
        
        .excel-tab:hover {
            color: var(--primary);
            background: rgba(0, 85, 164, 0.05);
        }
        
        .excel-tab.active {
            color: var(--primary);
            background: rgba(0, 85, 164, 0.1);
        }
        
        .excel-tab.active::after {
            content: '';
            position: absolute;
            bottom: -1.5rem;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--primary);
        }
        
        /* Excel Upload Area */
        .excel-upload-area {
            margin: 2rem;
            padding: 3rem;
            border: 2px dashed var(--gray-300);
            border-radius: 12px;
            text-align: center;
            background: var(--gray-50);
            transition: all var(--transition-base);
            cursor: pointer;
        }
        
        .excel-upload-area:hover {
            border-color: var(--primary);
            background: rgba(0, 85, 164, 0.02);
        }
        
        .upload-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .excel-upload-area h4 {
            margin: 0 0 0.5rem 0;
            color: var(--gray-800);
        }
        
        .excel-upload-area p {
            margin: 0;
            color: var(--gray-500);
        }
        
        /* Excel Info Bar */
        .excel-info-bar {
            display: flex;
            justify-content: space-between;
            padding: 0.75rem 1rem;
            background: var(--gray-100);
            border-radius: 8px;
            margin-bottom: 1rem;
            font-size: 0.875rem;
            color: var(--gray-600);
        }
        
        /* Statistics Cards */
        .stats-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: var(--shadow-sm);
            text-align: center;
            border: 1px solid var(--gray-200);
            transition: all var(--transition-base);
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        .stat-card.success {
            border-color: var(--success);
            background: rgba(16, 185, 129, 0.05);
        }
        
        .stat-card.error {
            border-color: var(--error);
            background: rgba(239, 68, 68, 0.05);
        }
        
        .stat-card.info {
            border-color: var(--primary);
            background: rgba(0, 85, 164, 0.05);
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--gray-800);
            line-height: 1;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            font-size: 0.875rem;
            color: var(--gray-600);
        }
        
        /* Modern Messages */
        .message-wrapper {
            margin-bottom: 1rem;
            animation: messageSlide 0.3s ease-out;
        }
        
        @keyframes messageSlide {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message-bubble {
            max-width: 70%;
            padding: 1rem 1.25rem;
            border-radius: 16px;
            position: relative;
            box-shadow: var(--shadow-sm);
            transition: all var(--transition-fast);
        }
        
        .message-bubble:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }
        
        .message-bubble.user {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }
        
        .message-bubble.bot {
            background: white;
            color: var(--gray-800);
            border: 1px solid var(--gray-200);
            border-bottom-left-radius: 4px;
        }
        
        /* Modern Chat Input */
        .modern-chat-input {
            padding: 1rem;
            background: white;
            border-top: 1px solid var(--gray-200);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .voice-input-btn {
            padding: 0.75rem;
            background: var(--gray-100);
            border: none;
            border-radius: 50%;
            cursor: pointer;
            color: var(--gray-600);
            transition: all var(--transition-fast);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .voice-input-btn:hover {
            background: var(--primary);
            color: white;
            transform: scale(1.1);
        }
        
        /* Floating Action Buttons */
        .floating-actions {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            z-index: 100;
        }
        
        .fab {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: var(--shadow-lg);
            transition: all var(--transition-base);
            position: relative;
            overflow: hidden;
        }
        
        .fab::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .fab:hover::before {
            width: 100px;
            height: 100px;
        }
        
        .fab:hover {
            transform: scale(1.1);
            box-shadow: var(--shadow-xl);
        }
        
        .fab-primary {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
        }
        
        .fab-secondary {
            background: white;
            color: var(--primary);
            border: 1px solid var(--gray-200);
        }
        
        /* Drag and Drop Overlay */
        .drop-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 85, 164, 0.95);
            backdrop-filter: blur(var(--blur-lg));
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            animation: fadeIn 0.3s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .drop-content {
            text-align: center;
            color: white;
            animation: bounceIn 0.5s ease-out;
        }
        
        @keyframes bounceIn {
            0% {
                opacity: 0;
                transform: scale(0.3);
            }
            50% {
                transform: scale(1.05);
            }
            70% {
                transform: scale(0.9);
            }
            100% {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        .drop-icon {
            margin-bottom: 2rem;
            animation: float 3s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        
        .drop-content h2 {
            font-size: 2rem;
            margin: 0 0 0.5rem 0;
            font-weight: 600;
        }
        
        .drop-content p {
            font-size: 1.125rem;
            opacity: 0.9;
        }
        
        /* Enhanced Data Editor */
        div[data-testid="data-editor"] {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: var(--shadow-sm);
        }
        
        /* Streamlit specific overrides */
        .stButton > button {
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all var(--transition-fast);
            box-shadow: var(--shadow-sm);
        }
        
        .stButton > button:hover {
            background: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }
        
        .stButton > button[kind="secondary"] {
            background: white;
            color: var(--primary);
            border: 1px solid var(--primary);
        }
        
        .stButton > button[kind="secondary"]:hover {
            background: var(--primary);
            color: white;
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--gray-100);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--gray-400);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--gray-500);
        }
        
        /* Loading animations */
        .typing-indicator {
            padding: 1rem;
            background: white;
            border: 1px solid var(--gray-200);
            border-radius: 16px;
            border-bottom-left-radius: 4px;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: var(--shadow-sm);
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            background: var(--gray-400);
            border-radius: 50%;
            animation: typingDot 1.4s infinite;
        }
        
        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typingDot {
            0%, 60%, 100% {
                transform: translateY(0);
                background: var(--gray-400);
            }
            30% {
                transform: translateY(-10px);
                background: var(--primary);
            }
        }
        
        /* Responsive Design */
        @media (max-width: 1024px) {
            .navbar-subtitle {
                display: none;
            }
            
            .chat-panel, .excel-panel {
                height: calc(100vh - 80px);
            }
        }
        
        @media (max-width: 768px) {
            .layout-switcher {
                display: none;
            }
            
            .floating-actions {
                bottom: 1rem;
                right: 1rem;
            }
            
            .fab {
                width: 48px;
                height: 48px;
            }
            
            .message-bubble {
                max-width: 85%;
            }
        }
    </style>
    """

def get_javascript() -> str:
    """Returns enhanced JavaScript for modern interactions"""
    return """
    <script>
        // Enhanced drag and drop with visual feedback
        (function() {
            let dragCounter = 0;
            const dropOverlay = document.getElementById('drop-overlay');
            
            // Prevent default drag behaviors
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                document.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            // Drag enter
            document.addEventListener('dragenter', function(e) {
                dragCounter++;
                if (dragCounter === 1 && dropOverlay) {
                    dropOverlay.style.display = 'flex';
                }
            });
            
            // Drag leave
            document.addEventListener('dragleave', function(e) {
                dragCounter--;
                if (dragCounter === 0 && dropOverlay) {
                    setTimeout(() => {
                        dropOverlay.style.display = 'none';
                    }, 100);
                }
            });
            
            // Drop
            document.addEventListener('drop', function(e) {
                dragCounter = 0;
                if (dropOverlay) {
                    dropOverlay.style.display = 'none';
                }
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    // Find file input and trigger change
                    const fileInput = document.querySelector('input[type="file"]');
                    if (fileInput) {
                        const dataTransfer = new DataTransfer();
                        dataTransfer.items.add(files[0]);
                        fileInput.files = dataTransfer.files;
                        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
            });
            
            // Smooth scroll for messages
            function smoothScrollToBottom() {
                const containers = document.querySelectorAll('[data-testid="stVerticalBlock"] > div');
                containers.forEach(container => {
                    if (container.style.height && container.style.height.includes('px')) {
                        container.scrollTo({
                            top: container.scrollHeight,
                            behavior: 'smooth'
                        });
                    }
                });
            }
            
            // Auto-scroll on new messages
            const observer = new MutationObserver((mutations) => {
                let hasNewMessage = false;
                mutations.forEach(mutation => {
                    if (mutation.addedNodes.length > 0) {
                        mutation.addedNodes.forEach(node => {
                            if (node.nodeType === 1 && node.querySelector?.('.message-wrapper')) {
                                hasNewMessage = true;
                            }
                        });
                    }
                });
                
                if (hasNewMessage) {
                    setTimeout(smoothScrollToBottom, 100);
                }
            });
            
            // Start observing
            setTimeout(() => {
                const containers = document.querySelectorAll('[data-testid="stVerticalBlock"] > div');
                containers.forEach(container => {
                    if (container.style.height && container.style.height.includes('px')) {
                        observer.observe(container, {
                            childList: true,
                            subtree: true
                        });
                    }
                });
            }, 1000);
            
            // Keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                // Ctrl/Cmd + K for quick search
                if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                    e.preventDefault();
                    // Focus chat input
                    const chatInput = document.querySelector('textarea[placeholder*="message"]');
                    if (chatInput) chatInput.focus();
                }
                
                // Ctrl/Cmd + E for Excel focus
                if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                    e.preventDefault();
                    // Switch to Excel view
                    const excelBtn = document.querySelector('.layout-btn[data-layout="excel"]');
                    if (excelBtn) excelBtn.click();
                }
            });
            
            // Add ripple effect to buttons
            document.addEventListener('click', function(e) {
                if (e.target.matches('button, .fab')) {
                    const button = e.target;
                    const ripple = document.createElement('span');
                    const rect = button.getBoundingClientRect();
                    const size = Math.max(rect.width, rect.height);
                    const x = e.clientX - rect.left - size / 2;
                    const y = e.clientY - rect.top - size / 2;
                    
                    ripple.style.width = ripple.style.height = size + 'px';
                    ripple.style.left = x + 'px';
                    ripple.style.top = y + 'px';
                    ripple.classList.add('ripple');
                    
                    button.appendChild(ripple);
                    
                    setTimeout(() => ripple.remove(), 600);
                }
            });
        })();
    </script>
    
    <style>
        /* Ripple effect */
        .ripple {
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            transform: scale(0);
            animation: ripple-animation 0.6s ease-out;
            pointer-events: none;
        }
        
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        button, .fab {
            position: relative;
            overflow: hidden;
        }
    </style>
    """