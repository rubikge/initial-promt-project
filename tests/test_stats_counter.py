import unittest
import threading
import time
from src.stats.stats_counter import StatsCounter


class TestStatsCounter(unittest.TestCase):
    """Тесты для класса StatsCounter"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.stats = StatsCounter()
    
    def test_add_stats_numeric(self):
        """Тест добавления числовых метрик"""
        # Добавляем числовые метрики
        self.stats.add_stats("test_category", {"count": 5, "total_time": 10.5})
        self.stats.add_stats("test_category", {"count": 3, "total_time": 5.2})
        
        # Проверяем результат
        result = self.stats.get_stats("test_category")
        expected = {"count": 8, "total_time": 15.7}
        self.assertEqual(result, expected)
    
    def test_add_stats_string(self):
        """Тест добавления строковых метрик"""
        # Добавляем строковые метрики
        self.stats.add_stats("test_category", {"name": "test1"})
        self.stats.add_stats("test_category", {"name": "test2"})  # Должна замениться
        
        result = self.stats.get_stats("test_category")
        self.assertEqual(result["name"], "test2")
    
    def test_add_stats_list(self):
        """Тест добавления списков"""
        # Добавляем списки
        self.stats.add_stats("test_category", {"items": ["a", "b"]})
        self.stats.add_stats("test_category", {"items": ["c", "d"]})
        
        result = self.stats.get_stats("test_category")
        self.assertEqual(result["items"], ["a", "b", "c", "d"])
    
    def test_add_stats_dict(self):
        """Тест добавления словарей"""
        # Добавляем словари
        self.stats.add_stats("test_category", {"config": {"key1": "value1"}})
        self.stats.add_stats("test_category", {"config": {"key2": "value2"}})
        
        result = self.stats.get_stats("test_category")
        expected_config = {"key1": "value1", "key2": "value2"}
        self.assertEqual(result["config"], expected_config)
    
    def test_multiple_categories(self):
        """Тест работы с несколькими категориями"""
        self.stats.add_stats("category1", {"count": 10})
        self.stats.add_stats("category2", {"count": 20})
        
        all_stats = self.stats.get_stats()
        self.assertEqual(all_stats["category1"]["count"], 10)
        self.assertEqual(all_stats["category2"]["count"], 20)
    
    def test_get_category_stats(self):
        """Тест получения статистики по категории"""
        self.stats.add_stats("test_category", {"count": 5})
        
        result = self.stats.get_category_stats("test_category")
        self.assertEqual(result["count"], 5)
        
        # Тест несуществующей категории
        result = self.stats.get_category_stats("nonexistent")
        self.assertEqual(result, {})
    
    def test_clear_stats(self):
        """Тест очистки статистики"""
        self.stats.add_stats("category1", {"count": 10})
        self.stats.add_stats("category2", {"count": 20})
        
        # Очищаем одну категорию
        self.stats.clear_stats("category1")
        all_stats = self.stats.get_stats()
        self.assertNotIn("category1", all_stats)
        self.assertIn("category2", all_stats)
        
        # Очищаем все
        self.stats.clear_stats()
        all_stats = self.stats.get_stats()
        self.assertEqual(all_stats, {})
    
    def test_has_category(self):
        """Тест проверки наличия категории"""
        self.assertFalse(self.stats.has_category("test"))
        
        self.stats.add_stats("test", {"count": 1})
        self.assertTrue(self.stats.has_category("test"))
    
    def test_get_total_count(self):
        """Тест получения общего количества"""
        self.stats.add_stats("test_category", {"count": 5})
        self.stats.add_stats("test_category", {"count": 3})
        
        total = self.stats.get_total_count("test_category", "count")
        self.assertEqual(total, 8)
        
        # Тест несуществующей метрики
        total = self.stats.get_total_count("test_category", "nonexistent")
        self.assertEqual(total, 0)
    
    def test_thread_safety(self):
        """Тест потокобезопасности"""
        def add_stats_thread(category, count):
            for i in range(count):
                self.stats.add_stats(category, {"count": 1})
                time.sleep(0.001)  # Небольшая задержка для создания конкуренции
        
        # Создаем несколько потоков
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_stats_thread, args=(f"category_{i}", 100))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем, что все данные корректны
        all_stats = self.stats.get_stats()
        for i in range(5):
            category = f"category_{i}"
            self.assertIn(category, all_stats)
            self.assertEqual(all_stats[category]["count"], 100)
    
    def test_mixed_data_types(self):
        """Тест смешанных типов данных"""
        self.stats.add_stats("mixed", {
            "count": 10,
            "name": "test",
            "items": ["a", "b"],
            "config": {"key": "value"}
        })
        
        result = self.stats.get_stats("mixed")
        self.assertEqual(result["count"], 10)
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["items"], ["a", "b"])
        self.assertEqual(result["config"], {"key": "value"})
    
    def test_empty_metrics(self):
        """Тест с пустыми метриками"""
        self.stats.add_stats("empty", {})
        result = self.stats.get_stats("empty")
        self.assertEqual(result, {})
    
    def test_none_category(self):
        """Тест с None категорией"""
        # get_stats с None должна вернуть всю статистику
        self.stats.add_stats("test", {"count": 1})
        all_stats = self.stats.get_stats(None)
        self.assertIn("test", all_stats)
    
    def test_print_summary(self):
        """Тест вывода сводки (проверяем, что не вызывает ошибок)"""
        self.stats.add_stats("test1", {"count": 10, "time": 5.5})
        self.stats.add_stats("test2", {"name": "test", "items": ["a", "b"]})
        
        # Проверяем, что метод выполняется без ошибок
        try:
            self.stats.print_summary("TEST SUMMARY")
        except Exception as e:
            self.fail(f"print_summary вызвал исключение: {e}")
    
    def test_print_summary_empty(self):
        """Тест вывода пустой сводки"""
        try:
            self.stats.print_summary("EMPTY SUMMARY")
        except Exception as e:
            self.fail(f"print_summary с пустыми данными вызвал исключение: {e}")


if __name__ == "__main__":
    unittest.main() 