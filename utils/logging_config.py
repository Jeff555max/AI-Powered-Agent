"""
Конфигурация логирования.
"""

import logging
import sys


def setup_logging(level: str = "INFO"):
    """
    Настраивает систему логирования.
    
    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
    """
    # Получаем уровень
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Формат логов
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Настраиваем root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Отключаем избыточное логирование от внешних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    
    logging.info(f"Логирование настроено: уровень={level}")

