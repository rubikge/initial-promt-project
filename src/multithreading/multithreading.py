from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import List, Tuple, Any, Callable

# Константы для настройки
DELAY_BETWEEN_TASKS = 100  # секунд между запусками задач
MAX_WORKERS = 4  # максимальное количество потоков

# Альтернативные стратегии запуска:
# 1. SEQUENTIAL_WITH_DELAY - текущая: запуск с задержкой между задачами
# 2. IMMEDIATE_ALL - запуск всех задач сразу (для тестирования без кэширования)
# 3. BATCHED - запуск группами с задержкой между группами
STRATEGY = "SEQUENTIAL_WITH_DELAY"

class MultithreadedProcessor:
    """Класс для многопоточной обработки задач"""
    
    def __init__(self, process_single_task: Callable, max_workers: int = None, delay_between_tasks: int = None, strategy: str = None):
        """
        Инициализация процессора
        
        Args:
            process_single_task: функция для обработки одной задачи
            max_workers: максимальное количество потоков (по умолчанию MAX_WORKERS)
            delay_between_tasks: задержка между задачами в секундах (по умолчанию DELAY_BETWEEN_TASKS)
            strategy: стратегия запуска (по умолчанию STRATEGY)
        """
        self._process_single_task = process_single_task
        self._max_workers = max_workers or MAX_WORKERS
        self._delay_between_tasks = delay_between_tasks or DELAY_BETWEEN_TASKS
        self._strategy = strategy or STRATEGY
    
    def process_tasks(self, tasks: List[Any], *args, **kwargs) -> Tuple[List[Any], float]:
        """
        Обработка списка задач в многопоточном режиме
        
        Args:
            tasks: список задач для обработки
            *args, **kwargs: дополнительные аргументы для process_single_task
            
        Returns:
            Tuple[List[Any], float]: обработанные результаты и время выполнения
        """
        print(f"Начинаем обработку {len(tasks)} задач в многопоточном режиме...")
        print(f"Стратегия: {self._strategy}")
        print(f"Задержка между задачами: {self._delay_between_tasks} секунд")
        print(f"Максимальное количество потоков: {self._max_workers}")
        
        start_time = time.time()
        
        # Если список задач пустой, возвращаем пустой результат
        if not tasks:
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Обработка завершена за {execution_time:.2f} секунд")
            return [], execution_time
        
        # Ограничиваем количество потоков
        max_workers = min(self._max_workers, len(tasks))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {}
            
            if self._strategy == "SEQUENTIAL_WITH_DELAY":
                future_to_task = self._run_sequential_with_delay(executor, tasks, *args, **kwargs)
            elif self._strategy == "IMMEDIATE_ALL":
                future_to_task = self._run_immediate_all(executor, tasks, *args, **kwargs)
            elif self._strategy == "BATCHED":
                future_to_task = self._run_batched(executor, tasks, *args, **kwargs)
            else:
                raise ValueError(f"Неизвестная стратегия: {self._strategy}")
            
            # Обрабатываем завершенные задачи и собираем результаты
            print("\nОжидаем завершения всех задач...")
            results = []
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    processed_task = future.result()
                    results.append(processed_task)
                    print(f"✓ Обработана задача: {task}")
                    print("-" * 50)
                except Exception as exc:
                    print(f"✗ Ошибка при обработке задачи {task}: {exc}")
                    # Добавляем None для неудачных задач, чтобы сохранить порядок
                    results.append(None)
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Обработка завершена за {execution_time:.2f} секунд")
        
        return results, execution_time
    
    def _run_sequential_with_delay(self, executor: ThreadPoolExecutor, tasks: List[Any], *args, **kwargs) -> dict:
        """Запуск с задержкой между задачами для эффективного кэширования"""
        future_to_task = {}
        
        for i, task in enumerate(tasks):
            # Запускаем первую задачу сразу, остальные с задержкой
            if i > 0:
                print(f"Ожидание {self._delay_between_tasks} секунд перед запуском задачи: {task}")
                time.sleep(self._delay_between_tasks)
            
            future = executor.submit(self._process_single_task, task, *args, **kwargs)
            future_to_task[future] = task
            print(f"Задача: {task} отправлена в пул потоков")
        
        return future_to_task
    
    def _run_immediate_all(self, executor: ThreadPoolExecutor, tasks: List[Any], *args, **kwargs) -> dict:
        """Запуск всех задач сразу"""
        future_to_task = {}
        
        for task in tasks:
            future = executor.submit(self._process_single_task, task, *args, **kwargs)
            future_to_task[future] = task
            print(f"Задача: {task} отправлена в пул потоков")
        
        return future_to_task
    
    def _run_batched(self, executor: ThreadPoolExecutor, tasks: List[Any], *args, **kwargs) -> dict:
        """Запуск группами с задержкой между группами"""
        future_to_task = {}
        batch_size = 2
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            if i > 0:
                print(f"Ожидание {self._delay_between_tasks} секунд перед запуском новой группы")
                time.sleep(self._delay_between_tasks)
            
            for task in batch:
                future = executor.submit(self._process_single_task, task, *args, **kwargs)
                future_to_task[future] = task
                print(f"Задача: {task} отправлена в пул потоков")
        
        return future_to_task