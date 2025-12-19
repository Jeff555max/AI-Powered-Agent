"""
Обработчики команд и сообщений Telegram бота.
Разделение логики обработки от основного бота.
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)


class BotHandlers:
    """Обработчики команд и сообщений бота."""
    
    def __init__(
        self,
        session_manager,
        context_retriever,
        response_generator,
        user_db,
        vector_db
    ):
        """
        Инициализирует обработчики.
        
        Args:
            session_manager: Менеджер сессий
            context_retriever: Получатель контекста
            response_generator: Генератор ответов
            user_db: База данных пользователей
            vector_db: Векторная БД
        """
        self.session_manager = session_manager
        self.context_retriever = context_retriever
        self.response_generator = response_generator
        self.user_db = user_db
        self.vector_db = vector_db
        
        logger.info("BotHandlers инициализированы")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        
        # Создаем/обновляем пользователя в БД
        self.user_db.create_or_update_user(user_id, name=user_name)
        
        # Создаем сессию
        session = self.session_manager.get_or_create_session(user_id)
        
        welcome_message = """👋 Привет! Я AI ассистент с доступом к базе знаний.

Я могу ответить на ваши вопросы, используя информацию из внутренних документов.

📝 Просто отправьте мне свой вопрос, и я постараюсь помочь!

Команды:
/help - справка
/stats - статистика базы знаний
/clear - очистить историю диалога

Пример вопроса: "Какая корпоративная культура в компании?"
"""
        await update.message.reply_text(welcome_message)
        
        logger.info(f"Пользователь {user_id} ({user_name}) начал работу с ботом")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_message = """📖 Справка по использованию бота:

🔹 Как задать вопрос:
Просто напишите свой вопрос обычным текстом. Например:
- "Какие инструменты использует команда разработки?"
- "Расскажи про политику удаленной работы"
- "Что такое корпоративная культура компании?"

🔹 Доступные команды:
/start - приветствие
/help - эта справка
/stats - статистика базы знаний
/clear - очистить историю диалога

🔹 Как работает бот:
1. Я ищу релевантную информацию в базе знаний
2. Использую найденную информацию для формирования ответа
3. Отвечаю на основе реальных документов компании

❗ Важно: Я отвечаю только на основе информации из базы знаний. Если нужной информации нет, я честно об этом сообщу.
"""
        await update.message.reply_text(help_message)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stats"""
        try:
            # Статистика векторной БД
            vector_stats = self.vector_db.get_stats()
            
            # Статистика пользователей
            user_count = self.user_db.get_user_count()
            
            # Статистика сессий
            active_sessions = self.session_manager.get_active_session_count()
            
            stats_message = f"""📊 Статистика:

📚 База знаний:
  • Коллекция: {vector_stats['name']}
  • Документов: {vector_stats['document_count']}

👥 Пользователи:
  • Всего пользователей: {user_count}
  • Активных сессий: {active_sessions}

✅ Бот готов отвечать на ваши вопросы!
"""
            await update.message.reply_text(stats_message)
        
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            await update.message.reply_text(f"❌ Ошибка получения статистики: {str(e)}")
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /clear - очистка истории диалога"""
        user_id = update.effective_user.id
        
        session = self.session_manager.get_session(user_id)
        if session:
            session.clear_conversation_history()
            self.session_manager.save()
            await update.message.reply_text("✅ История диалога очищена!")
        else:
            await update.message.reply_text("ℹ️ История диалога пуста.")
        
        logger.info(f"Пользователь {user_id} очистил историю")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений (вопросов пользователя)"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        user_query = update.message.text
        
        logger.info(f"Получен вопрос от {user_name} (ID: {user_id}): {user_query}")
        
        # Отправляем индикатор "печатает..."
        await update.message.chat.send_action(action="typing")
        
        try:
            # Обновляем пользователя в БД
            self.user_db.create_or_update_user(user_id, name=user_name)
            self.user_db.increment_message_count(user_id)
            
            # Получаем или создаем сессию
            session = self.session_manager.get_or_create_session(user_id)
            
            # Добавляем запрос пользователя в историю
            session.add_message("user", user_query)
            
            # 1. Получаем релевантный контекст из векторной БД
            logger.info(f"Поиск контекста для запроса: {user_query}")
            documents = self.context_retriever.retrieve(user_query)
            
            logger.info(f"Найдено документов: {len(documents)}")
            
            # 2. Получаем историю диалога (без текущего вопроса)
            conversation_history = session.get_conversation_history(
                max_messages=10,
                include_timestamps=False
            )
            
            # Убираем последнее сообщение (текущий вопрос пользователя)
            history_for_ai = conversation_history[:-1] if len(conversation_history) > 1 else []
            
            logger.info(f"История диалога: {len(history_for_ai)} сообщений")
            
            # 3. Генерируем ответ
            answer = self.response_generator.generate(
                query=user_query,
                context_documents=documents,
                conversation_history=history_for_ai if history_for_ai else None
            )
            
            # 4. Добавляем ответ в историю
            session.add_message("assistant", answer)
            
            # Сохраняем сессии
            self.session_manager.save()
            
            # 5. Форматируем ответ с источниками
            sources = self.context_retriever.get_sources(documents)
            
            if sources:
                sources_text = "\n\n📚 Источники:\n" + "\n".join([
                    f"• {src}" for src in sources
                ])
                full_response = answer + sources_text
            else:
                full_response = answer
            
            # 6. Отправляем ответ
            await update.message.reply_text(full_response)
            
            logger.info(f"Ответ отправлен пользователю {user_id}")
        
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Извините, произошла ошибка при обработке вашего вопроса. Попробуйте еще раз."
            )

