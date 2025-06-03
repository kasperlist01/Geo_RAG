import os
import tempfile
from typing import Optional


def save_telegram_file(file_obj, file_name: str) -> str:
    """Сохраняет файл, полученный от Telegram, во временную директорию"""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, file_name)

    with open(file_path, 'wb') as f:
        f.write(file_obj.getvalue())

    return file_path


def get_file_extension(file_name: str) -> Optional[str]:
    """Возвращает расширение файла в нижнем регистре"""
    _, ext = os.path.splitext(file_name)
    return ext.lower() if ext else None


def is_supported_file_type(file_name: str) -> bool:
    """Проверяет, поддерживается ли тип файла"""
    supported_extensions = ['.pdf', '.fb2', '.txt']
    ext = get_file_extension(file_name)
    return ext in supported_extensions