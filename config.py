import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # API Keys
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    
    # Mistral API
    MISTRAL_API_URL: str = "https://api.mistral.ai/v1/chat/completions"
    MISTRAL_EMBEDDINGS_URL: str = "https://api.mistral.ai/v1/embeddings"
    MISTRAL_MODEL: str = "mistral-small-latest"
    MISTRAL_EMBED_MODEL: str = "mistral-embed"
    
    # Excel Parser
    PARSER_CHUNK_SIZE: int = 800
    PARSER_MAX_MEMORY_MB: int = 1024
    PARSER_WORKERS: int = min(6, os.cpu_count() - 1)
    PARSER_CACHE_ENABLED: bool = True
    PARSER_PROGRESS_ENABLED: bool = True
    
    # File handling
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_FILE_TYPES: list = None
    
    # UI
    CHAT_HISTORY_LIMIT: int = 100
    
    def __post_init__(self):
        if self.ALLOWED_FILE_TYPES is None:
            self.ALLOWED_FILE_TYPES = ['.xlsx', '.pdf', '.docx', '.txt', '.msg']

config = Config()