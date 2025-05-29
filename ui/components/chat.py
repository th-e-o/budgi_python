# ui/components/chat.py - Version complète et corrigée
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional
import re

class ChatComponents:
    """Modern chat components with enhanced styling"""
    
    @staticmethod
    def render_header():
        """Renders modern chat header"""
        return """
        <div class="modern-chat-header">
            <div class="chat-header-content">
                <div class="chat-avatar-wrapper">
                    <div class="chat-avatar">
                        <span class="avatar-icon">🤖</span>
                    </div>
                    <span class="online-indicator"></span>
                </div>
                <div class="chat-header-info">
                    <h3>BudgiBot Assistant</h3>
                    <span class="chat-status">
                        <span class="status-indicator"></span>
                        En ligne • Prêt à vous aider
                    </span>
                </div>
            </div>
            <div class="chat-header-actions">
                <button class="header-action-btn" title="Historique">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                </button>
                <button class="header-action-btn" title="Options">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="3"/>
                        <path d="M12 1v6m0 6v6m9-9h-6m-6 0H3"/>
                    </svg>
                </button>
            </div>
        </div>
        """
    
    @staticmethod
    def render_message(message: Dict, index: int = 0):
        """Renders a message with modern styling"""
        timestamp = message.get('timestamp', datetime.now().strftime("%H:%M"))
        role_class = 'user' if message['role'] == 'user' else 'bot'
        
        # Format message content with proper styling
        content = message['content']
        
        # Escape HTML to prevent injection
        content = ChatComponents._escape_html(content)
        
        # Handle file messages
        if content.startswith("📎 Fichier envoyé :"):
            file_name = content.replace("📎 Fichier envoyé :", "").strip()
            file_size = message.get('file_size')
            content = ChatComponents._format_file_message(file_name, file_size)
        else:
            # Format code blocks
            content = ChatComponents._format_code_blocks(content)
            # Format lists
            content = ChatComponents._format_lists(content)
            # Format bold text
            content = ChatComponents._format_bold(content)
            # Format line breaks
            content = content.replace('\n', '<br>')
        
        # Handle special message types
        if message.get('type') == 'bpss_prompt':
            return ChatComponents._render_bpss_prompt(content, timestamp), True
        
        if message.get('error'):
            return ChatComponents._render_error_message(content, timestamp, role_class), False
        
        # Regular message
        avatar = "👤" if role_class == 'user' else "🤖"
        return f"""
        <div class="message-wrapper {role_class}">
            <div class="message-avatar {role_class}">
                <span>{avatar}</span>
            </div>
            <div class="message-content">
                <div class="message-bubble {role_class}">
                    <div class="message-text">{content}</div>
                </div>
                <span class="message-time">{timestamp}</span>
            </div>
        </div>
        """, False
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML characters to prevent injection"""
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&apos;",
            ">": "&gt;",
            "<": "&lt;",
        }
        return "".join(html_escape_table.get(c, c) for c in text)
    
    @staticmethod
    def _format_file_message(file_name: str, file_size: Optional[int] = None) -> str:
        """Format file upload message"""
        size_str = ""
        if file_size:
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
        
        return f"""
        <div class="file-message">
            <div class="file-icon">📎</div>
            <div class="file-info">
                <div class="file-name">{file_name}</div>
                <div class="file-status">Fichier envoyé {f'• {size_str}' if size_str else ''}</div>
            </div>
        </div>
        """
    
    @staticmethod
    def _format_code_blocks(content: str) -> str:
        """Format code blocks with syntax highlighting"""
        # Pattern for code blocks with optional language
        pattern = r'```(\w*)\n(.*?)```'
        
        def replace_code_block(match):
            lang = match.group(1) or 'text'
            code = match.group(2).strip()
            # Re-escape the code content
            code = ChatComponents._escape_html(code)
            return f'<pre class="code-block"><code class="language-{lang}">{code}</code></pre>'
        
        return re.sub(pattern, replace_code_block, content, flags=re.DOTALL)
    
    @staticmethod
    def _format_lists(content: str) -> str:
        """Format bullet lists"""
        lines = content.split('\n')
        formatted_lines = []
        in_list = False
        
        for line in lines:
            # Check if line starts with bullet point
            if re.match(r'^\s*[-•*]\s+', line):
                if not in_list:
                    formatted_lines.append('<ul class="message-list">')
                    in_list = True
                # Remove bullet and add as list item
                item = re.sub(r'^\s*[-•*]\s+', '', line)
                formatted_lines.append(f'<li>{item}</li>')
            else:
                if in_list and line.strip():  # End list if non-empty non-list line
                    formatted_lines.append('</ul>')
                    in_list = False
                formatted_lines.append(line)
        
        # Close list if still open
        if in_list:
            formatted_lines.append('</ul>')
        
        return '\n'.join(formatted_lines)
    
    @staticmethod
    def _format_bold(content: str) -> str:
        """Format bold text with **text** or __text__"""
        # Replace **text** with <strong>text</strong>
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        # Replace __text__ with <strong>text</strong>
        content = re.sub(r'__(.+?)__', r'<strong>\1</strong>', content)
        return content
    
    @staticmethod
    def _render_bpss_prompt(content: str, timestamp: str) -> str:
        """Render BPSS prompt message"""
        return f"""
        <div class="message-wrapper bot">
            <div class="message-avatar bot">
                <span>🤖</span>
            </div>
            <div class="message-content">
                <div class="message-bubble bot special">
                    <div class="message-text">{content}</div>
                    <div class="message-actions">
                        <div class="action-prompt">
                            <span class="action-icon">🛠️</span>
                            <span>Action suggérée disponible</span>
                        </div>
                    </div>
                </div>
                <span class="message-time">{timestamp}</span>
            </div>
        </div>
        """
    
    @staticmethod
    def _render_error_message(content: str, timestamp: str, role_class: str) -> str:
        """Render error message"""
        avatar = "👤" if role_class == 'user' else "🤖"
        return f"""
        <div class="message-wrapper {role_class}">
            <div class="message-avatar {role_class} error">
                <span>{avatar}</span>
            </div>
            <div class="message-content">
                <div class="message-bubble {role_class} error">
                    <div class="message-text">{content}</div>
                </div>
                <span class="message-time">{timestamp}</span>
            </div>
        </div>
        """
    
    @staticmethod
    def render_typing_indicator():
        """Renders modern typing indicator"""
        return """
        <div class="message-wrapper bot">
            <div class="message-avatar bot">
                <span>🤖</span>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
        </div>
        """
    
    @staticmethod
    def render_quick_replies_for_bot(message_index: int):
        """Renders quick reply buttons with modern styling"""
        # Create container with unique key
        container_key = f"quick_replies_{message_index}"
        
        with st.container():
            # Use columns for button layout
            cols = st.columns([1, 1, 1, 1.5])
            
            # Button configurations
            buttons = [
                ("💡 Détailler", "Peux-tu détailler ?", "secondary"),
                ("📝 Exemple", "Donne-moi un exemple", "secondary"),
                ("📊 Résumer", "Résume", "secondary"),
                ("💰 Extraire budget", "extract_budget", "primary")
            ]
            
            for col, (label, action, button_type) in zip(cols, buttons):
                with col:
                    # Use actual button type parameter correctly
                    button_kwargs = {
                        "label": label,
                        "key": f"{container_key}_{action}",
                        "use_container_width": True
                    }
                    
                    # Only add type if it's primary
                    if button_type == "primary":
                        button_kwargs["type"] = "primary"
                    
                    if st.button(**button_kwargs):
                        return action
        
        return None
    
    @staticmethod
    def render_file_preview(filename: str, file_size: Optional[int] = None):
        """Renders enhanced file preview"""
        extension = filename.split('.')[-1].lower()
        
        # File type configurations
        file_types = {
            'pdf': {'icon': '📄', 'color': '#dc2626', 'label': 'PDF'},
            'xlsx': {'icon': '📊', 'color': '#10b981', 'label': 'Excel'},
            'docx': {'icon': '📝', 'color': '#3b82f6', 'label': 'Word'},
            'txt': {'icon': '📃', 'color': '#6b7280', 'label': 'Texte'},
            'msg': {'icon': '📧', 'color': '#8b5cf6', 'label': 'Email'},
            'json': {'icon': '📋', 'color': '#f59e0b', 'label': 'JSON'}
        }
        
        file_info = file_types.get(extension, {
            'icon': '📎', 'color': '#6b7280', 'label': extension.upper()
        })
        
        size_str = ""
        if file_size:
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
        
        return f"""
        <div class="file-preview-card" style="border-left-color: {file_info['color']}">
            <div class="file-preview-icon" style="background: {file_info['color']}20; color: {file_info['color']}">
                {file_info['icon']}
            </div>
            <div class="file-preview-info">
                <div class="file-preview-name">{filename}</div>
                <div class="file-preview-meta">
                    <span class="file-type">{file_info['label']}</span>
                    {f'<span class="file-size">• {size_str}</span>' if size_str else ''}
                </div>
            </div>
        </div>
        """
    
    @staticmethod
    def render_welcome_message():
        """Renders welcome message for empty chat"""
        return """
        <div class="welcome-container">
            <div class="welcome-icon">🤖</div>
            <h2>Bienvenue sur BudgiBot</h2>
            <p>Votre assistant intelligent pour la gestion budgétaire</p>
            
            <div class="welcome-features">
                <div class="feature-card">
                    <span class="feature-icon">📊</span>
                    <h4>Analyse Excel</h4>
                    <p>Importez et analysez vos fichiers Excel</p>
                </div>
                <div class="feature-card">
                    <span class="feature-icon">💰</span>
                    <h4>Extraction budgétaire</h4>
                    <p>Extrayez automatiquement les données budgétaires</p>
                </div>
                <div class="feature-card">
                    <span class="feature-icon">🛠️</span>
                    <h4>Outils BPSS</h4>
                    <p>Utilisez nos outils spécialisés pour le budget</p>
                </div>
            </div>
            
            <div class="welcome-actions">
                <p>Comment puis-je vous aider aujourd'hui ?</p>
            </div>
        </div>
        """
    
    @staticmethod
    def render_quick_actions():
        """Renders quick action buttons"""
        quick_actions = [
            ("📂 Charger Excel", "load_excel"),
            ("💰 Extraire Budget", "extract_budget"),
            ("🛠️ Outil BPSS", "open_bpss"),
            ("📊 Analyser", "analyze")
        ]
        
        html = '<div class="quick-actions">'
        for label, action in quick_actions:
            html += f'<button class="quick-action-btn" data-action="{action}">{label}</button>'
        html += '</div>'
        
        return html