import os
from dotenv import load_dotenv

load_dotenv()

# API ключи
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Настройки базы данных
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "")

# Настройки для обработки документов
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVER_TOP_K = 3

# Настройки для модели
MODEL_NAME = "qwen/qwen3-235b-a22b:free"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"