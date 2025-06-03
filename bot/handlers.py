import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from bot.states import UserStates
from bot.keyboards import get_main_keyboard, get_cancel_keyboard, get_confirm_clear_keyboard
from rag.document_processor import load_document, split_documents
from rag.retriever import  generate_response, extract_sources
from rag.utils import save_telegram_file, is_supported_file_type
from database.storage import VectorStorage

# Инициализация роутера
router = Router()

# Инициализация хранилища
storage = VectorStorage()


# Обработчик команды /start
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(UserStates.IDLE)
    await message.answer(
        "Привет! Я бот для работы с документами и ответов на вопросы.\n\n"
        "Я могу:\n"
        "📁 Загружать документы (PDF, FB2, TXT)\n"
        "❓ Отвечать на вопросы по загруженным документам\n"
        "🔄 Очищать базу данных\n\n"
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )


# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📚 <b>Справка по использованию бота:</b>\n\n"
        "1️⃣ <b>Загрузка документов</b>\n"
        "Нажмите '📁 Загрузить документ' и отправьте файл в формате PDF, FB2 или TXT.\n\n"
        "2️⃣ <b>Задать вопрос</b>\n"
        "Нажмите '❓ Задать вопрос' и введите ваш запрос по содержимому документов.\n\n"
        "3️⃣ <b>Очистка базы</b>\n"
        "Нажмите '🔄 Очистить базу' для удаления всех загруженных документов.\n\n"
        "ℹ️ Для возврата в главное меню используйте команду /start",
        parse_mode="HTML"
    )


# Обработчик кнопки "Загрузить документ"
@router.message(F.text == "📁 Загрузить документ")
async def upload_document_button(message: Message, state: FSMContext):
    await state.set_state(UserStates.WAITING_FOR_FILE)
    await message.answer(
        "Пожалуйста, отправьте документ в формате PDF, FB2 или TXT.",
        reply_markup=get_cancel_keyboard()
    )


# Обработчик кнопки "Задать вопрос"
@router.message(F.text == "❓ Задать вопрос")
async def ask_question_button(message: Message, state: FSMContext):
    await state.set_state(UserStates.WAITING_FOR_QUERY)
    await message.answer(
        "Пожалуйста, введите ваш вопрос по содержимому загруженных документов.",
        reply_markup=get_cancel_keyboard()
    )


# Обработчик кнопки "Очистить базу"
@router.message(F.text == "🔄 Очистить базу")
async def clear_database_button(message: Message):
    await message.answer(
        "Вы уверены, что хотите очистить базу данных? Все загруженные документы будут удалены.",
        reply_markup=get_confirm_clear_keyboard()
    )


# Обработчик кнопки "Отмена"
@router.message(F.text == "❌ Отмена")
async def cancel_operation(message: Message, state: FSMContext):
    await state.set_state(UserStates.IDLE)
    await message.answer(
        "Операция отменена. Возвращаемся в главное меню.",
        reply_markup=get_main_keyboard()
    )


# Обработчик подтверждения очистки базы
@router.callback_query(F.data == "confirm_clear")
async def confirm_clear_database(callback: CallbackQuery):
    try:
        storage.clear()
        await callback.message.answer(
            "✅ База данных успешно очищена. Все документы удалены.",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logging.error(f"Ошибка при очистке базы данных: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при очистке базы данных. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
    finally:
        await callback.answer()


# Обработчик отмены очистки базы
@router.callback_query(F.data == "cancel_clear")
async def cancel_clear_database(callback: CallbackQuery):
    await callback.message.answer(
        "Очистка базы данных отменена.",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


# Обработчик загрузки файла
@router.message(UserStates.WAITING_FOR_FILE, F.document)
async def process_document(message: Message, state: FSMContext):
    document = message.document
    file_name = document.file_name

    # Проверяем поддерживаемый формат
    if not is_supported_file_type(file_name):
        await message.answer(
            "❌ Неподдерживаемый формат файла. Пожалуйста, загрузите документ в формате PDF, FB2 или TXT.",
            reply_markup=get_cancel_keyboard()
        )
        return

    await message.answer("⏳ Загрузка и обработка документа...")

    try:
        # Загружаем файл
        file_content = await message.bot.download(document)

        # Сохраняем файл во временную директорию
        file_path = save_telegram_file(file_content, file_name)

        # Загружаем документ
        documents = load_document(file_path)

        if not documents:
            await message.answer(
                "❌ Не удалось извлечь текст из документа. Возможно, файл поврежден или защищен.",
                reply_markup=get_main_keyboard()
            )
            await state.set_state(UserStates.IDLE)
            return

        # Разбиваем на чанки
        chunks = split_documents(documents)

        # Добавляем в базу
        storage.add_documents(chunks)

        await message.answer(
            f"✅ Документ успешно загружен и обработан!\n\n"
            f"📊 Статистика:\n"
            f"- Название: {file_name}\n"
            f"- Извлечено фрагментов: {len(chunks)}\n\n"
            f"Теперь вы можете задать вопрос по содержимому документа.",
            reply_markup=get_main_keyboard()
        )

        await state.set_state(UserStates.IDLE)

    except Exception as e:
        logging.error(f"Ошибка при обработке документа: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке документа. Пожалуйста, попробуйте другой файл.",
            reply_markup=get_main_keyboard()
        )
        await state.set_state(UserStates.IDLE)


# Обработчик вопроса
@router.message(UserStates.WAITING_FOR_QUERY)
async def process_query(message: Message, state: FSMContext):
    query = message.text

    if not query:
        await message.answer(
            "❌ Пожалуйста, введите текст вопроса.",
            reply_markup=get_cancel_keyboard()
        )
        return

    await message.answer("🔍 Ищу ответ на ваш вопрос...")

    try:
        # Получаем ретривер и выполняем поиск
        found_documents = storage.search(query)

        if not found_documents:
            await message.answer(
                "❌ Не удалось найти информацию по вашему запросу. Попробуйте переформулировать вопрос или загрузить больше документов.",
                reply_markup=get_main_keyboard()
            )
            await state.set_state(UserStates.IDLE)
            return

        # Генерируем ответ
        response = generate_response(query, found_documents)

        # Извлекаем источники
        sources = extract_sources(found_documents)
        sources_text = "\n".join([f"- {source}" for source in sources])

        await message.answer(
            f"<b>Ответ на ваш вопрос:</b>\n\n{response}\n\n"
            f"<b>Источники:</b>\n{sources_text}",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )

        await state.set_state(UserStates.IDLE)

    except ValueError as e:
        await message.answer(
            f"❌ В базе нет загруженных документов. Пожалуйста, сначала загрузите документ.{e}",
            reply_markup=get_main_keyboard()
        )
        await state.set_state(UserStates.IDLE)
    except Exception as e:
        logging.error(f"Ошибка при обработке запроса: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        await state.set_state(UserStates.IDLE)