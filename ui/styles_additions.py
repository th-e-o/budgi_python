# ui/styles_additions.py - Additional styles for the modern UI

def get_additional_styles() -> str:
    """Returns additional CSS for enhanced components"""
    return """
    <style>
        /* Enhanced Message Styles */
        .message-wrapper {
            display: flex;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
            align-items: flex-start;
            animation: messageSlide 0.3s ease-out;
        }
        
        .message-wrapper.user {
            flex-direction: row-reverse;
        }
        
        .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            flex-shrink: 0;
            box-shadow: var(--shadow-sm);
            transition: all var(--transition-fast);
        }
        
        .message-avatar:hover {
            transform: scale(1.1);
        }
        
        .message-avatar.bot {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
        }
        
        .message-avatar.user {
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
            color: var(--gray-700);
        }
        
        .message-content {
            max-width: 70%;
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        
        .message-wrapper.user .message-content {
            align-items: flex-end;
        }
        
        .message-bubble {
            padding: 1rem 1.25rem;
            border-radius: 16px;
            box-shadow: var(--shadow-sm);
            position: relative;
            word-wrap: break-word;
            transition: all var(--transition-fast);
        }
        
        .message-bubble:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }
        
        .message-bubble.bot {
            background: white;
            color: var(--gray-800);
            border: 1px solid var(--gray-200);
            border-bottom-left-radius: 4px;
        }
        
        .message-bubble.bot.special {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-color: #3b82f6;
        }
        
        .message-bubble.user {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .message-time {
            font-size: 0.75rem;
            color: var(--gray-500);
            padding: 0 0.5rem;
        }
        
        .message-wrapper.user .message-time {
            text-align: right;
        }
        
        /* File Message Styling */
        .file-message {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.5rem;
            background: var(--gray-50);
            border-radius: 8px;
        }
        
        .file-icon {
            font-size: 2rem;
        }
        
        .file-info {
            flex: 1;
        }
        
        .file-name {
            font-weight: 600;
            color: var(--gray-800);
        }
        
        .file-status {
            font-size: 0.875rem;
            color: var(--gray-600);
        }
        
        /* Code Block Styling */
        .code-block {
            background: var(--gray-900);
            color: #e5e7eb;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 0.5rem 0;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.875rem;
            line-height: 1.5;
        }
        
        /* Message List Styling */
        .message-list {
            margin: 0.5rem 0;
            padding-left: 1.5rem;
        }
        
        .message-list li {
            margin: 0.25rem 0;
            line-height: 1.6;
        }
        
        /* Action Prompt */
        .message-actions {
            margin-top: 0.75rem;
            padding-top: 0.75rem;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
        }
        
        .action-prompt {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--primary);
            font-weight: 500;
        }
        
        .action-icon {
            font-size: 1.25rem;
        }
        
        /* Welcome Container */
        .welcome-container {
            text-align: center;
            padding: 3rem 2rem;
            max-width: 800px;
            margin: 0 auto;
            animation: fadeIn 0.5s ease-out;
        }
        
        .welcome-icon {
            font-size: 4rem;
            margin-bottom: 1.5rem;
            animation: bounce 1s ease-in-out;
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        
        .welcome-container h2 {
            color: var(--gray-800);
            margin: 0 0 0.5rem 0;
            font-size: 2rem;
            font-weight: 700;
        }
        
        .welcome-container > p {
            color: var(--gray-600);
            margin: 0 0 2rem 0;
            font-size: 1.125rem;
        }
        
        .welcome-features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        .feature-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--gray-200);
            transition: all var(--transition-base);
        }
        
        .feature-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
            border-color: var(--primary);
        }
        
        .feature-icon {
            font-size: 2rem;
            margin-bottom: 0.75rem;
            display: block;
        }
        
        .feature-card h4 {
            margin: 0 0 0.5rem 0;
            color: var(--gray-800);
            font-size: 1.125rem;
        }
        
        .feature-card p {
            margin: 0;
            color: var(--gray-600);
            font-size: 0.875rem;
        }
        
        .welcome-actions {
            margin-top: 2rem;
            padding: 1.5rem;
            background: var(--gray-50);
            border-radius: 12px;
            border: 1px dashed var(--gray-300);
        }
        
        .welcome-actions p {
            margin: 0;
            color: var(--gray-700);
            font-weight: 500;
        }
        
        /* File Preview Card */
        .file-preview-card {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            background: white;
            border: 1px solid var(--gray-200);
            border-left: 3px solid;
            border-radius: 8px;
            transition: all var(--transition-fast);
        }
        
        .file-preview-card:hover {
            box-shadow: var(--shadow-sm);
            transform: translateX(2px);
        }
        
        .file-preview-icon {
            width: 48px;
            height: 48px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }
        
        .file-preview-info {
            flex: 1;
        }
        
        .file-preview-name {
            font-weight: 600;
            color: var(--gray-800);
            margin-bottom: 0.25rem;
        }
        
        .file-preview-meta {
            font-size: 0.875rem;
            color: var(--gray-600);
            display: flex;
            gap: 0.5rem;
        }
        
        /* Chat Header Enhancements */
        .chat-avatar-wrapper {
            position: relative;
        }
        
        .online-indicator {
            position: absolute;
            bottom: 2px;
            right: 2px;
            width: 12px;
            height: 12px;
            background: #10b981;
            border: 2px solid white;
            border-radius: 50%;
            box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3);
            animation: pulse-status 2s infinite;
        }
        
        /* Enhanced Quick Reply Buttons */
        .stButton > button {
            border-radius: 20px !important;
            padding: 0.5rem 1rem !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(0, 85, 164, 0.2) !important;
        }
        
        /* Data Editor Enhancements */
        div[data-testid="data-editor"] {
            border: 1px solid var(--gray-200);
            border-radius: 8px;
            overflow: hidden;
        }
        
        div[data-testid="data-editor"] .cell {
            transition: all var(--transition-fast);
        }
        
        div[data-testid="data-editor"] .cell:hover {
            background: var(--gray-50);
        }
        
        /* Form Styling */
        .stForm {
            background: var(--gray-50);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--gray-200);
        }
        
        /* Select Box Styling */
        .stSelectbox > div > div {
            border-radius: 8px !important;
            border-color: var(--gray-300) !important;
        }
        
        .stSelectbox > div > div:hover {
            border-color: var(--primary) !important;
        }
        
        /* File Uploader Styling */
        .stFileUploader > div {
            background: var(--gray-50);
            border: 2px dashed var(--gray-300);
            border-radius: 12px;
            transition: all var(--transition-base);
        }
        
        .stFileUploader > div:hover {
            border-color: var(--primary);
            background: rgba(0, 85, 164, 0.02);
        }
        
        /* Metric Cards */
        div[data-testid="metric-container"] {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--gray-200);
            box-shadow: var(--shadow-sm);
            transition: all var(--transition-base);
        }
        
        div[data-testid="metric-container"]:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        /* Success/Error Messages */
        .stSuccess, .stError, .stWarning, .stInfo {
            border-radius: 8px !important;
            padding: 1rem !important;
            font-weight: 500 !important;
        }
        
        /* Tab Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background: var(--gray-100);
            padding: 0.25rem;
            border-radius: 10px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background: white;
            box-shadow: var(--shadow-sm);
        }
    </style>
    """