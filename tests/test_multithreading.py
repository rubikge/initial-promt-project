import pytest
import time
from unittest.mock import Mock, patch
from multithreading.multithreading import MultithreadedProcessor, DELAY_BETWEEN_TASKS, MAX_WORKERS, STRATEGY


def mock_process_task(task, *args, **kwargs):
    """Mock функция для обработки задачи"""
    time.sleep(0.01)  # Уменьшаем время для тестов
    return f"processed_{task}"


def mock_process_task_with_error(task, *args, **kwargs):
    """Mock функция, которая вызывает ошибку для определенных задач"""
    if task == "error_task":
        raise ValueError(f"Error processing {task}")
    time.sleep(0.01)  # Уменьшаем время для тестов
    return f"processed_{task}"


@pytest.fixture
def processor():
    """Создает экземпляр MultithreadedProcessor с mock функцией"""
    return MultithreadedProcessor(mock_process_task)


@pytest.fixture
def processor_with_error():
    """Создает экземпляр MultithreadedProcessor с функцией, которая может вызывать ошибки"""
    return MultithreadedProcessor(mock_process_task_with_error)


@pytest.fixture
def sample_tasks():
    """Возвращает список тестовых задач"""
    return ["task1", "task2", "task3", "task4"]


def test_processor_initialization():
    """Тест инициализации процессора с параметрами по умолчанию"""
    processor = MultithreadedProcessor(mock_process_task)
    
    assert processor._process_single_task == mock_process_task
    assert processor._max_workers == MAX_WORKERS
    assert processor._delay_between_tasks == DELAY_BETWEEN_TASKS
    assert processor._strategy == STRATEGY


def test_processor_initialization_with_custom_params():
    """Тест инициализации процессора с пользовательскими параметрами"""
    custom_max_workers = 2
    custom_delay = 50
    custom_strategy = "IMMEDIATE_ALL"
    
    processor = MultithreadedProcessor(
        mock_process_task,
        max_workers=custom_max_workers,
        delay_between_tasks=custom_delay,
        strategy=custom_strategy
    )
    
    assert processor._max_workers == custom_max_workers
    assert processor._delay_between_tasks == custom_delay
    assert processor._strategy == custom_strategy


def test_process_tasks_sequential_with_delay(processor, sample_tasks):
    """Тест обработки задач с стратегией SEQUENTIAL_WITH_DELAY"""
    processor._strategy = "SEQUENTIAL_WITH_DELAY"
    processor._delay_between_tasks = 0.01  # Уменьшаем задержку для тестов
    
    start_time = time.time()
    results, execution_time = processor.process_tasks(sample_tasks)
    end_time = time.time()
    
    # Проверяем результаты (независимо от порядка)
    assert len(results) == len(sample_tasks)
    expected_results = {f"processed_{task}" for task in sample_tasks}
    actual_results = set(results)
    assert actual_results == expected_results
    
    # Проверяем время выполнения
    actual_time = end_time - start_time
    assert actual_time >= execution_time
    assert execution_time > 0


def test_process_tasks_immediate_all(processor, sample_tasks):
    """Тест обработки задач с стратегией IMMEDIATE_ALL"""
    processor._strategy = "IMMEDIATE_ALL"
    
    results, execution_time = processor.process_tasks(sample_tasks)
    
    # Проверяем результаты (независимо от порядка)
    assert len(results) == len(sample_tasks)
    expected_results = {f"processed_{task}" for task in sample_tasks}
    actual_results = set(results)
    assert actual_results == expected_results
    assert execution_time > 0


def test_process_tasks_batched(processor, sample_tasks):
    """Тест обработки задач с стратегией BATCHED"""
    processor._strategy = "BATCHED"
    processor._delay_between_tasks = 0.01  # Уменьшаем задержку для тестов
    
    results, execution_time = processor.process_tasks(sample_tasks)
    
    # Проверяем результаты (независимо от порядка)
    assert len(results) == len(sample_tasks)
    expected_results = {f"processed_{task}" for task in sample_tasks}
    actual_results = set(results)
    assert actual_results == expected_results
    assert execution_time > 0


def test_process_tasks_with_unknown_strategy(processor, sample_tasks):
    """Тест обработки задач с неизвестной стратегией"""
    processor._strategy = "UNKNOWN_STRATEGY"
    
    with pytest.raises(ValueError, match="Неизвестная стратегия"):
        processor.process_tasks(sample_tasks)


def test_process_tasks_with_errors(processor_with_error):
    """Тест обработки задач с ошибками"""
    tasks = ["task1", "error_task", "task2"]
    processor_with_error._strategy = "IMMEDIATE_ALL"
    
    results, execution_time = processor_with_error.process_tasks(tasks)
    
    # Проверяем, что успешные задачи обработаны, а неудачные помечены как None
    assert len(results) == len(tasks)
    # Проверяем, что есть успешные результаты и есть None (ошибка)
    assert "processed_task1" in results
    assert "processed_task2" in results
    assert None in results
    assert execution_time > 0


def test_process_tasks_with_empty_list(processor):
    """Тест обработки пустого списка задач"""
    processor._strategy = "IMMEDIATE_ALL"
    
    results, execution_time = processor.process_tasks([])
    
    assert len(results) == 0
    assert execution_time >= 0


def test_process_tasks_with_single_task(processor):
    """Тест обработки одной задачи"""
    processor._strategy = "IMMEDIATE_ALL"
    
    results, execution_time = processor.process_tasks(["single_task"])
    
    assert len(results) == 1
    assert results[0] == "processed_single_task"
    assert execution_time > 0


def test_max_workers_limitation():
    """Тест ограничения максимального количества потоков"""
    processor = MultithreadedProcessor(mock_process_task, max_workers=2)
    processor._strategy = "IMMEDIATE_ALL"
    
    # Создаем больше задач, чем max_workers
    tasks = ["task1", "task2", "task3", "task4", "task5"]
    
    results, execution_time = processor.process_tasks(tasks)
    
    assert len(results) == len(tasks)
    expected_results = {f"processed_{task}" for task in tasks}
    actual_results = set(results)
    assert actual_results == expected_results
    assert execution_time > 0


def test_process_tasks_with_additional_args(processor):
    """Тест обработки задач с дополнительными аргументами"""
    processor._strategy = "IMMEDIATE_ALL"
    
    def mock_task_with_args(task, arg1, arg2, kwarg1=None):
        time.sleep(0.01)  # Уменьшаем время для тестов
        return f"processed_{task}_{arg1}_{arg2}_{kwarg1}"
    
    processor._process_single_task = mock_task_with_args
    
    results, execution_time = processor.process_tasks(
        ["task1", "task2"], 
        "arg1_value", 
        "arg2_value", 
        kwarg1="kwarg_value"
    )
    
    expected_result = "processed_task1_arg1_value_arg2_value_kwarg_value"
    assert len(results) == 2
    # Проверяем, что оба результата содержат ожидаемые значения
    assert any(expected_result in result for result in results)
    assert any("processed_task2_arg1_value_arg2_value_kwarg_value" in result for result in results)


@patch('multithreading.multithreading.ThreadPoolExecutor')
def test_thread_pool_executor_usage(mock_executor, processor, sample_tasks):
    """Тест использования ThreadPoolExecutor"""
    processor._strategy = "IMMEDIATE_ALL"
    
    # Настраиваем mock более детально
    mock_executor_instance = Mock()
    mock_future = Mock()
    mock_future.result.return_value = "processed_task"
    
    # Настраиваем submit метод
    mock_executor_instance.submit.return_value = mock_future
    
    # Настраиваем as_completed
    with patch('multithreading.multithreading.as_completed') as mock_as_completed:
        mock_as_completed.return_value = [mock_future]
        
        # Настраиваем контекстный менеджер
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor.return_value.__exit__.return_value = None
        
        processor.process_tasks(sample_tasks)
        
        # Проверяем, что ThreadPoolExecutor был создан с правильными параметрами
        mock_executor.assert_called_once_with(max_workers=min(MAX_WORKERS, len(sample_tasks)))


def test_delay_between_tasks_sequential(processor, sample_tasks):
    """Тест задержки между задачами в последовательной стратегии"""
    processor._strategy = "SEQUENTIAL_WITH_DELAY"
    processor._delay_between_tasks = 0.01  # Уменьшаем задержку для тестов
    
    start_time = time.time()
    processor.process_tasks(sample_tasks)
    end_time = time.time()
    
    # Проверяем, что общее время больше минимального ожидаемого
    # (количество задержек * время задержки + время обработки)
    min_expected_time = (len(sample_tasks) - 1) * processor._delay_between_tasks
    assert (end_time - start_time) >= min_expected_time


def test_batch_strategy_batch_size():
    """Тест размера группы в стратегии BATCHED"""
    processor = MultithreadedProcessor(mock_process_task, strategy="BATCHED")
    processor._delay_between_tasks = 0.01  # Уменьшаем задержку для тестов
    
    # Создаем 5 задач, размер группы по умолчанию = 2
    tasks = ["task1", "task2", "task3", "task4", "task5"]
    
    start_time = time.time()
    processor.process_tasks(tasks)
    end_time = time.time()
    
    # Проверяем, что время больше минимального ожидаемого
    # 3 группы (0-1, 2-3, 4), 2 задержки между группами
    min_expected_time = 2 * processor._delay_between_tasks
    assert (end_time - start_time) >= min_expected_time 