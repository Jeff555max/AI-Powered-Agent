"""
Менеджер сессий пользователей.
Управляет состоянием диалогов и контекстом пользователей.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
import json
import os

from .user_context import UserContext

logger = logging.getLogger(__name__)


class SessionManager:
    """Менеджер сессий пользователей."""
    
    def __init__(self, session_timeout: int = 3600, persist_file: str = "sessions.json"):
        """
        Инициализирует менеджер сессий.
        
        Args:
            session_timeout: Таймаут сессии в секундах (по умолчанию 1 час)
            persist_file: Файл для сохранения сессий
        """
        self.sessions: Dict[str, UserContext] = {}
        self.session_timeout = session_timeout
        self.persist_file = persist_file
        
        # Загружаем сохраненные сессии
        self._load_sessions()
        
        logger.info(f"SessionManager инициализирован (timeout={session_timeout}s)")
    
    def get_or_create_session(self, user_id: str) -> UserContext:
        """
        Получает существующую сессию или создает новую.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Контекст пользователя
        """
        user_id = str(user_id)
        
        # Проверяем существующую сессию
        if user_id in self.sessions:
            session = self.sessions[user_id]
            
            # Проверяем, не истекла ли сессия
            if not session.is_expired(self.session_timeout):
                session.update_last_activity()
                return session
            else:
                logger.info(f"Сессия пользователя {user_id} истекла, создаем новую")
                # Сессия истекла, создаем новую
                del self.sessions[user_id]
        
        # Создаем новую сессию
        session = UserContext(user_id)
        self.sessions[user_id] = session
        
        logger.info(f"Создана новая сессия для пользователя {user_id}")
        
        return session
    
    def get_session(self, user_id: str) -> Optional[UserContext]:
        """
        Получает существующую сессию без создания новой.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Контекст пользователя или None
        """
        user_id = str(user_id)
        return self.sessions.get(user_id)
    
    def delete_session(self, user_id: str):
        """
        Удаляет сессию пользователя.
        
        Args:
            user_id: ID пользователя
        """
        user_id = str(user_id)
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"Сессия пользователя {user_id} удалена")
    
    def cleanup_expired_sessions(self):
        """Удаляет истекшие сессии."""
        expired = []
        
        for user_id, session in self.sessions.items():
            if session.is_expired(self.session_timeout):
                expired.append(user_id)
        
        for user_id in expired:
            del self.sessions[user_id]
            logger.info(f"Удалена истекшая сессия: {user_id}")
        
        if expired:
            logger.info(f"Очищено {len(expired)} истекших сессий")
    
    def get_active_session_count(self) -> int:
        """
        Получает количество активных сессий.
        
        Returns:
            Количество активных сессий
        """
        # Сначала очищаем истекшие
        self.cleanup_expired_sessions()
        return len(self.sessions)
    
    def get_all_user_ids(self) -> list:
        """
        Получает список всех активных пользователей.
        
        Returns:
            Список ID пользователей
        """
        self.cleanup_expired_sessions()
        return list(self.sessions.keys())
    
    def _load_sessions(self):
        """Загружает сессии из файла."""
        if not os.path.exists(self.persist_file):
            return
        
        try:
            with open(self.persist_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for user_id, session_data in data.items():
                context = UserContext(user_id)
                context.conversation_history = session_data.get('conversation_history', [])
                context.last_activity = datetime.fromisoformat(session_data.get('last_activity'))
                self.sessions[user_id] = context
            
            logger.info(f"Загружено {len(self.sessions)} сессий из {self.persist_file}")
        except Exception as e:
            logger.error(f"Ошибка загрузки сессий: {e}")
    
    def _save_sessions(self):
        """Сохраняет сессии в файл."""
        try:
            data = {}
            for user_id, session in self.sessions.items():
                data[user_id] = {
                    'conversation_history': session.conversation_history,
                    'last_activity': session.last_activity.isoformat()
                }
            
            with open(self.persist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Сохранено {len(self.sessions)} сессий в {self.persist_file}")
        except Exception as e:
            logger.error(f"Ошибка сохранения сессий: {e}")
    
    def save(self):
        """Публичный метод для сохранения сессий."""
        self._save_sessions()

