import json
import hashlib
from functools import wraps
from typing import Any, Dict, Optional
import pickle
from pathlib import Path


class CacheManager:
    """Менеджер кэширования для сохранения результатов функций в JSON файлы."""
    
    def __init__(self, cache_dir: str = "cache"):
        """
        Инициализация менеджера кэширования.
        
        Args:
            cache_dir: Директория для хранения кэш файлов
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _generate_cache_key(self, args: tuple, kwargs: dict) -> str:
        """
        Генерирует уникальный ключ кэша на основе аргументов функции.
        
        Args:
            args: Позиционные аргументы
            kwargs: Именованные аргументы
            
        Returns:
            Уникальный ключ кэша
        """
        # Исключаем объект self из аргументов (первый аргумент для методов класса)
        # Проверяем, что первый аргумент является экземпляром класса, а не примитивом
        if args and hasattr(args[0], '__class__') and not isinstance(args[0], (int, float, str, bool, type(None))):
            filtered_args = args[1:]
        else:
            filtered_args = args
        
        # Создаем строку с аргументами, включая их типы для большей уникальности
        args_str = str([(type(arg).__name__, arg) for arg in filtered_args])
        kwargs_str = str(sorted([(k, type(v).__name__, v) for k, v in kwargs.items()]))
        params_str = f"{args_str}:{kwargs_str}"
            
        hash_obj = hashlib.md5(params_str.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _get_cache_file_path(self, func_name: str) -> Path:
        """
        Получает путь к файлу кэша для функции.
        
        Args:
            func_name: Имя функции
            
        Returns:
            Путь к файлу кэша
        """
        return self.cache_dir / f"{func_name}.json"
    
    def _is_json_serializable(self, obj: Any) -> bool:
        """
        Проверяет, можно ли сериализовать объект в JSON.
        
        Args:
            obj: Объект для проверки
            
        Returns:
            True, если объект можно сериализовать в JSON
        """
        try:
            json.dumps(obj)
            return True
        except (TypeError, ValueError):
            return False
    
    def _serialize_value(self, value: Any) -> Dict[str, Any]:
        """
        Сериализует значение для сохранения в JSON.
        
        Args:
            value: Значение для сериализации
            
        Returns:
            Словарь с сериализованным значением
        """
        if self._is_json_serializable(value):
            return {"type": "json", "value": value}
        else:
            # Для не-JSON сериализуемых объектов используем pickle
            try:
                pickled = pickle.dumps(value)
                return {"type": "pickle", "value": pickled.hex()}
            except (pickle.PicklingError, AttributeError):
                # Если объект не может быть сериализован, сохраняем его строковое представление
                return {"type": "string", "value": str(value)}
    
    def _deserialize_value(self, data: Dict[str, Any]) -> Any:
        """
        Десериализует значение из JSON.
        
        Args:
            data: Словарь с сериализованным значением
            
        Returns:
            Десериализованное значение
        """
        if data["type"] == "json":
            return data["value"]
        elif data["type"] == "pickle":
            pickled_bytes = bytes.fromhex(data["value"])
            return pickle.loads(pickled_bytes)
        elif data["type"] == "string":
            return data["value"]
        else:
            raise ValueError(f"Неизвестный тип сериализации: {data['type']}")
    
    def get_cached_result(self, func_name: str, args: tuple, kwargs: dict) -> Optional[Any]:
        """
        Получает кэшированный результат функции.
        
        Args:
            func_name: Имя функции
            args: Позиционные аргументы
            kwargs: Именованные аргументы
            
        Returns:
            Кэшированный результат или None, если кэш не найден
        """
        cache_key = self._generate_cache_key(args, kwargs)
        cache_file = self._get_cache_file_path(func_name)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    if cache_key in cached_data:
                        return self._deserialize_value(cached_data[cache_key])
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Ошибка при чтении кэша для {func_name}: {e}")
                return None
            except ValueError as e:
                # Пробрасываем ValueError для тестов обработки ошибок
                raise e
        return None
    
    def save_cached_result(self, func_name: str, args: tuple, kwargs: dict, result: Any) -> None:
        """
        Сохраняет результат функции в кэш.
        
        Args:
            func_name: Имя функции
            args: Позиционные аргументы
            kwargs: Именованные аргументы
            result: Результат функции для кэширования
        """
        cache_key = self._generate_cache_key(args, kwargs)
        cache_file = self._get_cache_file_path(func_name)
        try:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
            else:
                cached_data = {}
            cached_data[cache_key] = self._serialize_value(result)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка при сохранении кэша для {func_name}: {e}")


# Глобальный экземпляр менеджера кэширования
_cache_manager = CacheManager()


def cache_result(func):
    """
    Декоратор для кэширования результатов функции в JSON файлы.
    Возвращает кортеж (результат, isFromCache).
    
    Args:
        func: Функция для кэширования
        
    Returns:
        Обёрнутая функция с кэшированием, возвращающая (результат, isFromCache)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        
        # Пытаемся получить кэшированный результат
        cached_result = _cache_manager.get_cached_result(func_name, args, kwargs)
        
        if cached_result is not None:
            return cached_result, True
        
        # Если кэш не найден, выполняем функцию и сохраняем результат
        result = func(*args, **kwargs)
        
        # Сохраняем результат в кэш
        _cache_manager.save_cached_result(func_name, args, kwargs, result)
        
        return result, False
    
    return wrapper


def cache_result_dict(func):
    """
    Декоратор для кэширования результатов функции в JSON файлы.
    Возвращает словарь с результатом и флагом isFromCache.
    
    Args:
        func: Функция для кэширования
        
    Returns:
        Обёрнутая функция с кэшированием, возвращающая {"result": ..., "isFromCache": bool}
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        
        # Пытаемся получить кэшированный результат
        cached_result = _cache_manager.get_cached_result(func_name, args, kwargs)
        
        if cached_result is not None:
            return {"result": cached_result, "isFromCache": True}
        
        # Если кэш не найден, выполняем функцию и сохраняем результат
        result = func(*args, **kwargs)
        
        # Сохраняем результат в кэш
        _cache_manager.save_cached_result(func_name, args, kwargs, result)
        
        return {"result": result, "isFromCache": False}
    
    return wrapper


def cache_result_with_dir(cache_dir: str):
    """
    Декоратор для кэширования результатов функции в JSON файлы с указанной директорией.
    Возвращает кортеж (результат, isFromCache).
    
    Args:
        cache_dir: Директория для хранения кэш файлов
        
    Returns:
        Декоратор функции, возвращающий (результат, isFromCache)
    """
    cache_manager = CacheManager(cache_dir)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            
            # Пытаемся получить кэшированный результат
            cached_result = cache_manager.get_cached_result(func_name, args, kwargs)
            
            if cached_result is not None:
                return cached_result, True
            
            # Если кэш не найден, выполняем функцию и сохраняем результат
            result = func(*args, **kwargs)
            
            # Сохраняем результат в кэш
            cache_manager.save_cached_result(func_name, args, kwargs, result)
            
            return result, False
        
        return wrapper
    
    return decorator


def cache_result_with_dir_dict(cache_dir: str):
    """
    Декоратор для кэширования результатов функции в JSON файлы с указанной директорией.
    Возвращает словарь с результатом и флагом isFromCache.
    
    Args:
        cache_dir: Директория для хранения кэш файлов
        
    Returns:
        Декоратор функции, возвращающий {"result": ..., "isFromCache": bool}
    """
    cache_manager = CacheManager(cache_dir)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            
            # Пытаемся получить кэшированный результат
            cached_result = cache_manager.get_cached_result(func_name, args, kwargs)
            
            if cached_result is not None:
                return {"result": cached_result, "isFromCache": True}
            
            # Если кэш не найден, выполняем функцию и сохраняем результат
            result = func(*args, **kwargs)
            
            # Сохраняем результат в кэш
            cache_manager.save_cached_result(func_name, args, kwargs, result)
            
            return {"result": result, "isFromCache": False}
        
        return wrapper
    
    return decorator


def clear_cache(cache_dir: str = "cache") -> None:
    """
    Очищает все файлы кэша.
    
    Args:
        cache_dir: Директория с кэш файлами
    """
    cache_path = Path(cache_dir)
    if cache_path.exists():
        for cache_file in cache_path.glob("*.json"):
            cache_file.unlink()


def clear_function_cache(func_name: str, cache_dir: str = "cache") -> None:
    """
    Очищает кэш для конкретной функции.
    
    Args:
        func_name: Имя функции
        cache_dir: Директория с кэш файлами
    """
    cache_path = Path(cache_dir)
    cache_file = cache_path / f"{func_name}.json"
    
    if cache_file.exists():
        cache_file.unlink()


def get_cache_info(cache_dir: str = "cache") -> Dict[str, Any]:
    """
    Получает информацию о кэше.
    
    Args:
        cache_dir: Директория с кэш файлами
        
    Returns:
        Словарь с информацией о кэше
    """
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return {"total_files": 0, "total_size": 0, "files": []}
    
    files = list(cache_path.glob("*.json"))
    total_size = sum(f.stat().st_size for f in files)
    
    # Подсчитываем количество записей в каждом файле
    file_details = []
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                file_details.append({
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "entries": len(data)
                })
        except Exception:
            file_details.append({
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "entries": "error"
            })
    
    return {
        "total_files": len(files),
        "total_size": total_size,
        "files": file_details
    } 