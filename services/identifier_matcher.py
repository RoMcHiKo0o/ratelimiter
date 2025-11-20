"""
Сервис для работы с идентификаторами API:
- Поиск подходящих идентификаторов по URL и методу
- Проверка конфликтов между идентификаторами
- Валидация идентификаторов
"""
import json
from typing import Optional, List

from logger import setup_logger
from services.url_helper import URLHelper

logger = setup_logger(__name__)


class IdentifierMatcher:
    """Сервис для сопоставления и проверки идентификаторов API."""

    def __init__(self, api_manager):
        """
        Инициализация сервиса.
        
        Args:
            api_manager: Экземпляр APIManager для доступа к списку API
        """
        self._api_manager = api_manager
        self._url_helper = URLHelper()

    def find_identifier(
        self,
        url: str,
        method: str,
        extra: str,
        first_match_only: bool = True
    ) -> Optional[dict | List[dict]]:
        """
        Находит идентификатор(ы), соответствующие переданным параметрам.
        
        Args:
            url: URL для поиска
            method: HTTP метод
            extra: Дополнительный параметр идентификатора
            first_match_only: Если True, возвращает только первый найденный идентификатор,
                            иначе возвращает список всех подходящих
            
        Returns:
            dict - если first_match_only=True и найден идентификатор
            List[dict] - если first_match_only=False
            None - если идентификатор не найден
        """
        matching_identifiers = []
        
        for identifier_key in self._api_manager.get_all_apis().keys():
            identifier_dict = json.loads(identifier_key)
            
            if not self._matches_extra(identifier_dict, extra):
                continue
            
            if not self._matches_method(identifier_dict, method, first_match_only):
                continue
            
            # Проверяем все подпути URL
            url_match = self._url_helper.find_matching_sub_url(
                url, 
                identifier_dict.get("url")
            )
            
            if url_match:
                matched_identifier = {
                    "url": url_match,
                    "method": identifier_dict.get("method"),
                    "extra": extra
                }
                
                if first_match_only:
                    return matched_identifier
                    
                matching_identifiers.append(matched_identifier)
        
        return None if first_match_only else matching_identifiers

    def check_conflict(self, identifier_str: str) -> List[dict]:
        """
        Проверяет наличие конфликтующих идентификаторов.
        
        Args:
            identifier_str: JSON-строка идентификатора для проверки
            
        Returns:
            Список конфликтующих идентификаторов, или пустой список если конфликтов нет
        """
        try:
            identifier_dict = json.loads(identifier_str)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Ошибка парсинга идентификатора: {e}")
            return []
        
        url = identifier_dict.get("url", "")
        method = identifier_dict.get("method", "")
        extra = identifier_dict.get("extra", "")
        
        conflicting = self.find_identifier(
            url=url,
            method=method,
            extra=extra,
            first_match_only=False
        )
        
        if conflicting:
            logger.error(
                f"Найдены конфликтующие идентификаторы. "
                f"Идентификатор: {identifier_dict}. Конфликты: {conflicting}"
            )
        
        return conflicting or []

    def has_conflict(self, identifier_str: str) -> bool:
        """
        Проверяет наличие конфликтов (булева версия).
        
        Args:
            identifier_str: JSON-строка идентификатора для проверки
            
        Returns:
            True если есть конфликты, False иначе
        """
        return len(self.check_conflict(identifier_str)) > 0

    @staticmethod
    def _matches_extra(identifier_dict: dict, extra: str) -> bool:
        """Проверяет соответствие extra параметра."""
        return identifier_dict.get("extra", "") == extra

    @staticmethod
    def _matches_method(identifier_dict: dict, method: str, first_match_only: bool) -> bool:
        """
        Проверяет соответствие HTTP метода.
        
        Args:
            identifier_dict: Словарь идентификатора
            method: HTTP метод для проверки
            first_match_only: Флаг, влияющий на логику проверки метода
            
        Returns:
            True если метод соответствует, False иначе
        """
        identifier_method = identifier_dict.get("method", "")
        
        # Если методы точно совпадают
        if method == identifier_method:
            return True
        
        # Если идентификатор поддерживает любой метод
        if identifier_method == "ANY":
            return True
        
        # Если ищем любой метод, но это не первый поиск
        if method == "ANY" and not first_match_only:
            return True
        
        return False

