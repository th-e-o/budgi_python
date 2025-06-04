# ui/components/chat.py - Simplified chat components
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional
import re

class ChatComponents:
    """Simplified chat components focused on functionality"""
    
    @staticmethod
    def render_header():
        """Renders simplified chat header"""
        return """
        <div class="modern-chat-header">
            <div class="chat-header-content">
                <div class="chat-header-info">
                    <h4>BudgiBot</h4>
                </div>
            </div>
        </div>
        """
    
    @staticmethod
    def render_message(message: Dict, index: int = 0):
        """Renders a message with clean styling"""
        timestamp = message.get('timestamp', datetime.now().strftime("%H:%M"))
        role_class = 'user' if message['role'] == 'user' else 'bot'
        
        # Format message content
        content = message['content']
        
        # Escape HTML
        content = ChatComponents._escape_html(content)
        
        # Handle file messages
        if content.startswith("📎 Fichier envoyé :"):
            file_name = content.replace("📎 Fichier envoyé :", "").strip()
            file_size = message.get('file_size')
            content = ChatComponents._format_file_message(file_name, file_size)
        else:
            # Basic formatting
            content = content.replace('\n', '<br>')
            # Bold text
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            # Lists
            content = ChatComponents._format_simple_lists(content)
        
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
        """Escape HTML characters"""
        html_escape = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&apos;",
            ">": "&gt;",
            "<": "&lt;",
        }
        return "".join(html_escape.get(c, c) for c in text)
    
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
    def _format_simple_lists(content: str) -> str:
        """Format simple bullet lists"""
        lines = content.split('<br>')
        in_list = False
        formatted = []
        
        for line in lines:
            if line.strip().startswith('- ') or line.strip().startswith('• '):
                if not in_list:
                    formatted.append('<ul style="margin: 0.5rem 0; padding-left: 1.5rem;">')
                    in_list = True
                item = re.sub(r'^[\s\-•]+', '', line)
                formatted.append(f'<li>{item}</li>')
            else:
                if in_list and line.strip():
                    formatted.append('</ul>')
                    in_list = False
                formatted.append(line)
        
        if in_list:
            formatted.append('</ul>')
        
        return '<br>'.join(formatted)
    
    @staticmethod
    def render_typing_indicator():
        """Renders typing indicator"""
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