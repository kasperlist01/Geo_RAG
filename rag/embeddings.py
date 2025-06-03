import requests
from typing import List
from langchain.embeddings.base import Embeddings
from config import HUGGINGFACE_API_KEY, EMBEDDING_MODEL

class HuggingFaceEmbeddings(Embeddings):
    """Класс для создания эмбеддингов с использованием Hugging Face API"""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self.api_key = HUGGINGFACE_API_KEY
        self.api_url = f"https://router.huggingface.co/hf-inference/models/{model_name}/pipeline/feature-extraction"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Создание эмбеддингов для списка текстов"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {"inputs": texts}

        response = requests.post(
            self.api_url,
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            raise Exception(f"Ошибка в Hugging Face API: {response.text}")

        embeddings = response.json()
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Создание эмбеддинга для одного текста"""
        return self.embed_documents([text])[0]