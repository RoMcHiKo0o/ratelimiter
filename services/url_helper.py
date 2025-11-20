"""
Утилиты для работы с URL:
- Разбор URL на подпути
- Поиск совпадений по подпутям
"""
from typing import List, Optional
from urllib.parse import urlparse, urljoin


class URLHelper:
    """Утилита для работы с URL и их подпутями."""

    @staticmethod
    def get_sub_urls(url: str) -> List[str]:
        """
        Возвращает список всех подпутей для данного URL.
        
        Например, для 'https://api.example.com/v1/users/123' вернёт:
        [
            'https://api.example.com/v1',
            'https://api.example.com/v1/users',
            'https://api.example.com/v1/users/123'
        ]
        
        Args:
            url: URL для разбора
            
        Returns:
            Список подпутей от базового пути до полного URL (в порядке от общего к частному)
        """
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        
        # Удаляем пустые элементы
        path_parts = [part for part in path_parts if part]
        
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        sub_urls = []
        
        for i in range(len(path_parts)):
            sub_path = '/'.join(path_parts[:i + 1])
            full_url = urljoin(base_url, f'/{sub_path}')
            sub_urls.append(full_url)
        
        return sub_urls

    def find_matching_sub_url(self, request_url: str, identifier_url: str) -> Optional[str]:
        """
        Находит наиболее специфичное совпадение между URL запроса и URL идентификатора.
        
        Проверяет все подпути запроса в обратном порядке (от самого специфичного к общему)
        и возвращает первое совпадение с идентификатором.
        
        Args:
            request_url: URL из запроса
            identifier_url: URL из идентификатора
            
        Returns:
            Совпавший URL или None если совпадений нет
        """
        sub_urls = self.get_sub_urls(request_url)
        
        # Проверяем в обратном порядке (от самого специфичного к общему)
        for sub_url in reversed(sub_urls):
            if sub_url == identifier_url:
                return sub_url
        
        return None

