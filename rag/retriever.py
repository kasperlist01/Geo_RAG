import os
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate

from rag.embeddings import HuggingFaceEmbeddings
from rag.llm import OpenRouterLLM
from config import CHROMA_DB_DIR, MODEL_NAME


def create_vector_store(chunks: List[Document],
                        persist_directory: str = CHROMA_DB_DIR,
                        collection_name: Optional[str] = None) -> Chroma:
    """Создание векторного хранилища из фрагментов документов"""
    # Создаем директорию, если она не существует
    os.makedirs(persist_directory, exist_ok=True)

    # Создание векторного хранилища с использованием Hugging Face для эмбеддингов
    embeddings = HuggingFaceEmbeddings()

    # Используем collection_name если он предоставлен
    if collection_name:
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name=collection_name
        )
    else:
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_directory
        )

    return vectorstore


def search_documents(query: str, retriever) -> List[Document]:
    """Поиск документов с использованием ретривера"""
    return retriever.invoke(query)


def generate_response(query: str, documents: List[Document], model_name: str = MODEL_NAME) -> str:
    """Генерация ответа на основе найденных документов с использованием OpenRouter"""
    # Создание контекста из найденных документов
    context = "\n\n".join([doc.page_content for doc in documents])

    # Создание шаблона промпта
    prompt_template = """
    Ты - помощник, который отвечает на вопросы на основе предоставленной информации.

    Контекст:
    {context}

    Вопрос: {query}

    Инструкции:
    1. Отвечай только на основе предоставленного контекста.
    2. Если в контексте нет информации для ответа, так и скажи.
    3. Не выдумывай информацию.
    4. Предоставь структурированный и понятный ответ.

    Ответ:
    """

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "query"]
    )

    # Создание промпта с контекстом и вопросом
    formatted_prompt = prompt.format(context=context, query=query)

    # Генерация ответа с помощью OpenRouter LLM
    llm = OpenRouterLLM(model=model_name, temperature=0)
    response = llm.invoke(formatted_prompt)

    return response


def extract_sources(documents: List[Document]) -> List[str]:
    """Извлечение источников из документов"""
    sources = []
    for doc in documents:
        source_info = []

        if 'source' in doc.metadata:
            source_info.append(doc.metadata['source'])

        if 'page' in doc.metadata:
            source_info.append(f"страница {doc.metadata['page']}")
        elif 'section' in doc.metadata:
            source_info.append(f"раздел {doc.metadata['section']}")

        source = ", ".join(source_info)
        if source and source not in sources:
            sources.append(source)

    return sources