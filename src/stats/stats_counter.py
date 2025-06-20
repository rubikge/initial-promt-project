from threading import Lock
from typing import Dict, Any, Optional

class StatsCounter:
    """Универсальный потокобезопасный счетчик статистики"""
    
    def __init__(self):
        self._stats = {}  # {category: {metric: value}}
        self._lock = Lock()
    
    def add_stats(self, category: str, metrics: Dict[str, Any]) -> None:
        """
        Добавить статистику по категории потокобезопасно
        
        Args:
            category: категория статистики (например, 'prompt_name')
            metrics: словарь с метриками {metric_name: value}
        """
        with self._lock:
            if category not in self._stats:
                self._stats[category] = {}
            
            for metric_name, value in metrics.items():
                if metric_name not in self._stats[category]:
                    # Инициализируем значение в зависимости от типа
                    if isinstance(value, (int, float)):
                        self._stats[category][metric_name] = 0
                    elif isinstance(value, str):
                        self._stats[category][metric_name] = ""
                    elif isinstance(value, list):
                        self._stats[category][metric_name] = []
                    elif isinstance(value, dict):
                        self._stats[category][metric_name] = {}
                    else:
                        self._stats[category][metric_name] = value
                
                # Обновляем значение
                current_value = self._stats[category][metric_name]
                if isinstance(value, (int, float)) and isinstance(current_value, (int, float)):
                    self._stats[category][metric_name] += value
                elif isinstance(value, str) and isinstance(current_value, str):
                    self._stats[category][metric_name] = value  # Заменяем строку
                elif isinstance(value, list) and isinstance(current_value, list):
                    self._stats[category][metric_name].extend(value)
                elif isinstance(value, dict) and isinstance(current_value, dict):
                    current_value.update(value)
                else:
                    self._stats[category][metric_name] = value
    
    def get_stats(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Получить статистику потокобезопасно
        
        Args:
            category: категория статистики (если None, возвращает всю статистику)
            
        Returns:
            Словарь со статистикой
        """
        with self._lock:
            if category is None:
                return self._stats.copy()
            else:
                return self._stats.get(category, {}).copy()
    
    def get_category_stats(self, category: str) -> Dict[str, Any]:
        """
        Получить статистику по конкретной категории
        
        Args:
            category: категория статистики
            
        Returns:
            Словарь со статистикой категории
        """
        return self.get_stats(category)
    
    def clear_stats(self, category: Optional[str] = None) -> None:
        """
        Очистить статистику
        
        Args:
            category: категория для очистки (если None, очищает всю статистику)
        """
        with self._lock:
            if category is None:
                self._stats.clear()
            else:
                if category in self._stats:
                    del self._stats[category]
    
    def has_category(self, category: str) -> bool:
        """
        Проверить наличие категории в статистике
        
        Args:
            category: категория для проверки
            
        Returns:
            True если категория существует
        """
        with self._lock:
            return category in self._stats
    
    def get_total_count(self, category: str, metric: str) -> int:
        """
        Получить общее количество для числовой метрики
        
        Args:
            category: категория статистики
            metric: название метрики
            
        Returns:
            Общее количество
        """
        stats = self.get_category_stats(category)
        return stats.get(metric, 0)
    
    def print_summary(self, title: str = "СТАТИСТИКА") -> None:
        """
        Вывести сводку статистики
        
        Args:
            title: заголовок для вывода
        """
        stats = self.get_stats()
        
        if not stats:
            print(f"\n{title}: Нет данных")
            return
        
        print(f"\n=== {title} ===")
        
        for category, metrics in stats.items():
            print(f"\n{category.upper()}:")
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)):
                    if isinstance(value, float):
                        print(f"  {metric_name}: {value:,.4f}")
                    else:
                        print(f"  {metric_name}: {value:,}")
                else:
                    print(f"  {metric_name}: {value}")
        
        print("=" * 50)