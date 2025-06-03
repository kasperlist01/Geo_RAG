import os
import fitz
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Optional
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP


def load_pdf(file_path: str) -> List[Document]:
    """Загрузка PDF файла и извлечение текста"""
    documents = []

    try:
        pdf = fitz.open(file_path)
        for i, page in enumerate(pdf):
            text = page.get_text()
            if text.strip():
                doc = Document(
                    page_content=text,
                    metadata={
                        "source": os.path.basename(file_path),
                        "page": i + 1,
                        "file_path": file_path,
                        "file_type": "pdf"
                    }
                )
                documents.append(doc)
        pdf.close()
    except Exception as e:
        print(f"Ошибка при загрузке PDF: {e}")

    return documents


def load_fb2(file_path: str) -> List[Document]:
    """Загрузка FB2 файла и извлечение текста"""
    documents = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Простой парсинг FB2 (может потребоваться более сложная логика)
        soup = BeautifulSoup(content, 'lxml')

        # Извлекаем текст из разделов body
        for i, section in enumerate(soup.find_all('section')):
            text = section.get_text()
            if text.strip():
                doc = Document(
                    page_content=text,
                    metadata={
                        "source": os.path.basename(file_path),
                        "section": i + 1,
                        "file_path": file_path,
                        "file_type": "fb2"
                    }
                )
                documents.append(doc)
    except Exception as e:
        print(f"Ошибка при загрузке FB2: {e}")

    return documents


def load_text(file_path: str) -> List[Document]:
    """Загрузка текстового файла"""
    documents = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        if text.strip():
            doc = Document(
                page_content=text,
                metadata={
                    "source": os.path.basename(file_path),
                    "file_path": file_path,
                    "file_type": "text"
                }
            )
            documents.append(doc)
    except Exception as e:
        print(f"Ошибка при загрузке текстового файла: {e}")

    return documents


def load_document(file_path: str) -> List[Document]:
    """Загрузка документа в зависимости от его формата"""
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.pdf':
        return load_pdf(file_path)
    elif file_extension == '.fb2':
        return load_fb2(file_path)
    elif file_extension == '.txt':
        return load_text(file_path)
    else:
        raise ValueError(f"Неподдерживаемый формат файла: {file_extension}")


def split_documents(documents: List[Document],
                    chunk_size: int = CHUNK_SIZE,
                    chunk_overlap: int = CHUNK_OVERLAP) -> List[Document]:
    """Разделение документов на более мелкие фрагменты"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    return chunks