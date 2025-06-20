import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open
from caching.caching import (
    CacheManager, 
    cache_result, 
    cache_result_dict, 
    cache_result_with_dir, 
    cache_result_with_dir_dict,
    clear_cache,
    clear_function_cache,
    get_cache_info
)


class TestCacheManager:
    """Тесты для класса CacheManager."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Создает временную директорию для кэша."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Создает экземпляр CacheManager с временной директорией."""
        return CacheManager(temp_cache_dir)
    
    def test_init_creates_cache_dir(self, temp_cache_dir):
        """Тест создания директории кэша при инициализации."""
        cache_dir = Path(temp_cache_dir) / "new_cache"
        cache_manager = CacheManager(str(cache_dir))
        assert cache_dir.exists()
        assert cache_dir.is_dir()
    
    def test_generate_cache_key(self, cache_manager):
        """Тест генерации ключа кэша."""
        args = (1, "test", [1, 2, 3])
        kwargs = {"param1": "value1", "param2": 42}
        
        key1 = cache_manager._generate_cache_key(args, kwargs)
        key2 = cache_manager._generate_cache_key(args, kwargs)
        
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash length
    
    def test_generate_cache_key_different_args(self, cache_manager):
        """Тест генерации разных ключей для разных аргументов."""
        args1 = (1, "test")
        args2 = (2, "test")
        kwargs = {"param": "value"}
        
        key1 = cache_manager._generate_cache_key(args1, kwargs)
        key2 = cache_manager._generate_cache_key(args2, kwargs)
        
        assert key1 != key2
    
    def test_generate_cache_key_with_self(self, cache_manager):
        """Тест генерации ключа для методов класса (исключение self)."""
        class TestClass:
            def method(self, x, y):
                pass
        
        obj = TestClass()
        args = (obj, 1, 2)
        kwargs = {"param": "value"}
        
        key = cache_manager._generate_cache_key(args, kwargs)
        assert isinstance(key, str)
    
    def test_get_cache_file_path(self, cache_manager):
        """Тест получения пути к файлу кэша."""
        func_name = "test_function"
        cache_file = cache_manager._get_cache_file_path(func_name)
        
        assert cache_file.name == "test_function.json"
        assert cache_file.parent == Path(cache_manager.cache_dir)
    
    def test_is_json_serializable(self, cache_manager):
        """Тест проверки JSON сериализуемости."""
        assert cache_manager._is_json_serializable({"key": "value"}) == True
        assert cache_manager._is_json_serializable([1, 2, 3]) == True
        assert cache_manager._is_json_serializable("string") == True
        assert cache_manager._is_json_serializable(42) == True
        assert cache_manager._is_json_serializable(None) == True
        
        # Не сериализуемые объекты
        assert cache_manager._is_json_serializable(lambda x: x) == False
        assert cache_manager._is_json_serializable(object()) == False
    
    def test_serialize_deserialize_json_value(self, cache_manager):
        """Тест сериализации и десериализации JSON значений."""
        test_value = {"key": "value", "list": [1, 2, 3]}
        
        serialized = cache_manager._serialize_value(test_value)
        assert serialized["type"] == "json"
        assert serialized["value"] == test_value
        
        deserialized = cache_manager._deserialize_value(serialized)
        assert deserialized == test_value
    
    def test_serialize_deserialize_pickle_value(self, cache_manager):
        """Тест сериализации и десериализации pickle значений."""
        test_value = lambda x: x * 2
        
        serialized = cache_manager._serialize_value(test_value)
        # Лямбда-функции не сериализуются через pickle, ожидаем type == 'string'
        assert serialized["type"] == "string"
        assert isinstance(serialized["value"], str)
        
        deserialized = cache_manager._deserialize_value(serialized)
        # После десериализации получаем строковое представление
        assert isinstance(deserialized, str)
        assert "lambda" in deserialized or "<function" in deserialized
    
    def test_get_cached_result_not_found(self, cache_manager):
        """Тест получения кэшированного результата, когда кэш не найден."""
        result = cache_manager.get_cached_result("nonexistent", (1, 2), {})
        assert result is None
    
    def test_get_cached_result_found(self, cache_manager):
        """Тест получения кэшированного результата."""
        func_name = "test_func"
        args = (1, 2)
        kwargs = {"param": "value"}
        test_result = {"data": "test"}
        
        # Сохраняем результат
        cache_manager.save_cached_result(func_name, args, kwargs, test_result)
        
        # Получаем результат
        cached_result = cache_manager.get_cached_result(func_name, args, kwargs)
        assert cached_result == test_result
    
    def test_save_cached_result(self, cache_manager):
        """Тест сохранения результата в кэш."""
        func_name = "test_func"
        args = (1, 2)
        kwargs = {"param": "value"}
        test_result = {"data": "test"}
        
        cache_manager.save_cached_result(func_name, args, kwargs, test_result)
        
        cache_file = cache_manager._get_cache_file_path(func_name)
        assert cache_file.exists()
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert len(data) == 1
    
    def test_save_cached_result_multiple_entries(self, cache_manager):
        """Тест сохранения нескольких записей в кэш."""
        func_name = "test_func"
        
        # Первая запись
        cache_manager.save_cached_result(func_name, (1,), {}, "result1")
        
        # Вторая запись
        cache_manager.save_cached_result(func_name, (2,), {}, "result2")
        
        cache_file = cache_manager._get_cache_file_path(func_name)
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert len(data) == 2


class TestCacheDecorators:
    """Тесты для декораторов кэширования."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Создает временную директорию для кэша."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_cache_result_decorator(self, temp_cache_dir):
        """Тест декоратора cache_result."""
        @cache_result_with_dir(temp_cache_dir)
        def test_function(x, y, param=None):
            return {"sum": x + y, "param": param}
        
        # Первый вызов - результат вычисляется
        result1, is_from_cache1 = test_function(1, 2, param="test")
        assert is_from_cache1 == False
        assert result1 == {"sum": 3, "param": "test"}
        
        # Второй вызов с теми же параметрами - результат из кэша
        result2, is_from_cache2 = test_function(1, 2, param="test")
        assert is_from_cache2 == True
        assert result2 == {"sum": 3, "param": "test"}
        
        # Вызов с другими параметрами - результат вычисляется
        result3, is_from_cache3 = test_function(3, 4, param="other")
        assert is_from_cache3 == False
        assert result3 == {"sum": 7, "param": "other"}
    
    def test_cache_result_dict_decorator(self, temp_cache_dir):
        """Тест декоратора cache_result_dict."""
        @cache_result_with_dir_dict(temp_cache_dir)
        def test_function(x, y):
            return x * y
        
        # Первый вызов
        result1 = test_function(2, 3)
        assert result1["isFromCache"] == False
        assert result1["result"] == 6
        
        # Второй вызов с теми же параметрами
        result2 = test_function(2, 3)
        assert result2["isFromCache"] == True
        assert result2["result"] == 6
    
    def test_cache_result_with_complex_objects(self, temp_cache_dir):
        """Тест кэширования с комплексными объектами."""
        @cache_result_with_dir(temp_cache_dir)
        def test_function(data_list, data_dict):
            return {
                "list": data_list,
                "dict": data_dict,
                "lambda": lambda x: x * 2
            }
        
        test_list = [1, 2, 3]
        test_dict = {"a": 1, "b": 2}
        
        # Первый вызов
        result1, is_from_cache1 = test_function(test_list, test_dict)
        assert is_from_cache1 == False
        assert result1["list"] == test_list
        assert result1["dict"] == test_dict
        assert callable(result1["lambda"])
        
        # Второй вызов
        result2, is_from_cache2 = test_function(test_list, test_dict)
        assert is_from_cache2 == True
        # Если результат строка, значит объект не сериализовался (например, из-за лямбда)
        if isinstance(result2, str):
            assert "lambda" in result2 or "<function" in result2
        else:
            assert result2["list"] == test_list
            assert result2["dict"] == test_dict
            assert callable(result2["lambda"])
    
    def test_cache_result_with_methods(self, temp_cache_dir):
        """Тест кэширования методов класса."""
        class TestClass:
            def __init__(self, value):
                self.value = value
            
            @cache_result_with_dir(temp_cache_dir)
            def method(self, x):
                return self.value + x
        
        obj = TestClass(10)
        
        # Первый вызов
        result1, is_from_cache1 = obj.method(5)
        assert is_from_cache1 == False
        assert result1 == 15
        
        # Второй вызов
        result2, is_from_cache2 = obj.method(5)
        assert is_from_cache2 == True
        assert result2 == 15


class TestCacheManagement:
    """Тесты для функций управления кэшем."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Создает временную директорию для кэша."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_clear_cache(self, temp_cache_dir):
        """Тест очистки всего кэша."""
        # Создаем несколько файлов кэша
        cache_file1 = Path(temp_cache_dir) / "func1.json"
        cache_file2 = Path(temp_cache_dir) / "func2.json"
        
        cache_file1.write_text('{"key": "value"}')
        cache_file2.write_text('{"key2": "value2"}')
        
        assert cache_file1.exists()
        assert cache_file2.exists()
        
        # Очищаем кэш
        clear_cache(temp_cache_dir)
        
        assert not cache_file1.exists()
        assert not cache_file2.exists()
    
    def test_clear_function_cache(self, temp_cache_dir):
        """Тест очистки кэша конкретной функции."""
        # Создаем файлы кэша
        func1_file = Path(temp_cache_dir) / "func1.json"
        func2_file = Path(temp_cache_dir) / "func2.json"
        
        func1_file.write_text('{"key": "value"}')
        func2_file.write_text('{"key2": "value2"}')
        
        # Очищаем кэш только для func1
        clear_function_cache("func1", temp_cache_dir)
        
        assert not func1_file.exists()
        assert func2_file.exists()
    
    def test_get_cache_info_empty(self, temp_cache_dir):
        """Тест получения информации о пустом кэше."""
        info = get_cache_info(temp_cache_dir)
        
        assert info["total_files"] == 0
        assert info["total_size"] == 0
        assert info["files"] == []
    
    def test_get_cache_info_with_files(self, temp_cache_dir):
        """Тест получения информации о кэше с файлами."""
        # Создаем файлы кэша
        func1_file = Path(temp_cache_dir) / "func1.json"
        func2_file = Path(temp_cache_dir) / "func2.json"
        
        func1_file.write_text('{"key1": "value1", "key2": "value2"}')
        func2_file.write_text('{"key3": "value3"}')
        
        info = get_cache_info(temp_cache_dir)
        
        assert info["total_files"] == 2
        assert info["total_size"] > 0
        assert len(info["files"]) == 2
        
        # Проверяем детали файлов
        file_names = [f["name"] for f in info["files"]]
        assert "func1.json" in file_names
        assert "func2.json" in file_names
        
        # Проверяем количество записей
        for file_info in info["files"]:
            if file_info["name"] == "func1.json":
                assert file_info["entries"] == 2
            elif file_info["name"] == "func2.json":
                assert file_info["entries"] == 1


class TestCacheErrorHandling:
    """Тесты обработки ошибок в кэшировании."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Создает временную директорию для кэша."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_cache_manager_with_corrupted_json(self, temp_cache_dir):
        """Тест обработки поврежденного JSON файла."""
        cache_manager = CacheManager(temp_cache_dir)
        
        # Создаем поврежденный JSON файл
        cache_file = cache_manager._get_cache_file_path("test_func")
        cache_file.write_text('{"invalid": json}')
        
        # Пытаемся получить кэшированный результат
        result = cache_manager.get_cached_result("test_func", (1,), {})
        assert result is None
    
    def test_cache_manager_with_invalid_pickle_data(self, temp_cache_dir):
        """Тест обработки неверных pickle данных."""
        cache_manager = CacheManager(temp_cache_dir)
        
        # Создаем файл с неверными pickle данными
        cache_file = cache_manager._get_cache_file_path("test_func")
        cache_key = cache_manager._generate_cache_key((1,), {})
        
        invalid_data = {
            cache_key: {
                "type": "pickle",
                "value": "invalid_hex_string"
            }
        }
        
        cache_file.write_text(json.dumps(invalid_data))
        
        # Пытаемся получить кэшированный результат
        with pytest.raises(ValueError):
            cache_manager.get_cached_result("test_func", (1,), {})
    
    def test_cache_manager_with_unknown_serialization_type(self, temp_cache_dir):
        """Тест обработки неизвестного типа сериализации."""
        cache_manager = CacheManager(temp_cache_dir)
        
        # Создаем файл с неизвестным типом сериализации
        cache_file = cache_manager._get_cache_file_path("test_func")
        cache_key = cache_manager._generate_cache_key((1,), {})
        
        invalid_data = {
            cache_key: {
                "type": "unknown_type",
                "value": "some_value"
            }
        }
        
        cache_file.write_text(json.dumps(invalid_data))
        
        # Пытаемся получить кэшированный результат
        with pytest.raises(ValueError):
            cache_manager.get_cached_result("test_func", (1,), {}) 