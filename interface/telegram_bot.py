"""
Telegram бот.
Основной интерфейс взаимодействия с пользователями.
"""

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import logging

from .handlers import BotHandlers

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram бот с RAG функциональностью."""
    
    def __init__(
        self,
        token: str,
        session_manager,
        context_retriever,
        response_generator,
        user_db,
        vector_db
    ):
        """
        Инициализирует Telegram бота.
        
        Args:
            token: Токен Telegram бота
            session_manager: Менеджер сессий
            context_retriever: Получатель контекста
            response_generator: Генератор ответов
            user_db: База данных пользователей
            vector_db: Векторная БД
        """
        self.token = token
        
        # Инициализируем обработчики
        self.handlers = BotHandlers(
            session_manager=session_manager,
            context_retriever=context_retriever,
            response_generator=response_generator,
            user_db=user_db,
            vector_db=vector_db
        )
        
        # Создаем приложение
        self.application = Application.builder().token(self.token).build()
        
        # Регистрируем обработчики команд
        self._register_handlers()
        
        logger.info("Telegram бот инициализирован")
    
    def _register_handlers(self):
        """Регистрирует обработчики команд и сообщений."""
        # Команды
        self.application.add_handler(
            CommandHandler("start", self.handlers.start_command)
        )
        self.application.add_handler(
            CommandHandler("help", self.handlers.help_command)
        )
        self.application.add_handler(
            CommandHandler("stats", self.handlers.stats_command)
        )
        self.application.add_handler(
            CommandHandler("clear", self.handlers.clear_command)
        )
        
        # Текстовые сообщения
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handlers.handle_message
            )
        )
        
        logger.info("Обработчики зарегистрированы")
    
    def run(self):
        """Запускает бота."""
        logger.info("Запуск Telegram бота...")
        logger.info("Бот готов к работе! Нажмите Ctrl+C для остановки.")
        
        # Запускаем бота
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

