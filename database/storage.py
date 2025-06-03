import os
import json
import pickle
from typing import List, Optional, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from rag.embeddings import HuggingFaceEmbeddings
from config import CHROMA_DB_DIR, RETRIEVER_TOP_K


class VectorStorage:
    def __init__(self, persist_directory: str = CHROMA_DB_DIR):
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings()
        self.documents_path = os.path.join(persist_directory, "documents.pkl")

        # Создаем директорию, если она не существует
        os.makedirs(persist_directory, exist_ok=True)

        # Загружаем документы для BM25, если они существуют
        if os.path.exists(self.documents_path):
            try:
                with open(self.documents_path, 'rb') as f:
                    self.documents = pickle.load(f)
            except Exception as e:
                print(f"Ошибка при загрузке документов: {e}")
                self.documents = []
        else:
            self.documents = []

        # Инициализируем хранилище, если оно существует
        if os.path.exists(persist_directory) and os.listdir(persist_directory):
            self.db = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings
            )
        else:
            self.db = None

    def add_documents(self, documents: List[Document], collection_name: Optional[str] = None) -> None:
        """Добавляет документы в векторное хранилище"""
        # Сохраняем документы для BM25
        self.documents.extend(documents)

        # Сохраняем документы на диск
        try:
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.documents, f)
        except Exception as e:
            print(f"Ошибка при сохранении документов: {e}")

        if collection_name:
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
                collection_name=collection_name
            )
        else:
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )

        self.db = vectorstore

    def get_retriever(self, search_kwargs: Optional[Dict[str, Any]] = None):
        """Возвращает ансамблевый ретривер для поиска документов"""
        if not self.db:
            raise ValueError("Векторное хранилище не инициализировано")

        if not self.documents:
            raise ValueError("Нет документов для создания BM25 ретривера")

        if search_kwargs is None:
            search_kwargs = {"k": RETRIEVER_TOP_K}

        # Создаем BM25 ретривер
        bm25_retriever = BM25Retriever.from_documents(self.documents)
        bm25_retriever.k = search_kwargs["k"]

        # Создаем векторный ретривер
        vector_retriever = self.db.as_retriever(search_kwargs=search_kwargs)

        # Создаем ансамблевый ретривер
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever],
            weights=[0.5, 0.5]
        )

        return ensemble_retriever

    def search(self, query: str, k: int = RETRIEVER_TOP_K) -> List[Document]:
        """Поиск документов по запросу с использованием ансамблевого ретривера"""
        if not self.db:
            raise ValueError("Векторное хранилище не инициализировано")

        retriever = self.get_retriever({"k": k})
        return retriever.invoke(query)

    def clear(self) -> None:
        """Очищает векторное хранилище"""
        self.documents = []  # Очищаем документы для BM25

        # Удаляем файл с документами
        if os.path.exists(self.documents_path):
            os.remove(self.documents_path)

        if self.db:
            self.db = None

        if os.path.exists(self.persist_directory):
            for item in os.listdir(self.persist_directory):
                item_path = os.path.join(self.persist_directory, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    for subitem in os.listdir(item_path):
                        subitem_path = os.path.join(item_path, subitem)
                        if os.path.isfile(subitem_path):
                            os.remove(subitem_path)