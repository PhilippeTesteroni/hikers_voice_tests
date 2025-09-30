# Hiker's Voice E2E Tests

## Структура тестов

```
tests/
├── conftest.py              # Главная конфигурация pytest
├── pytest.ini               # Настройки pytest
├── requirements.txt         # Зависимости для тестов
├── run_tests.py            # Скрипт для запуска тестов
│
├── e2e/                    # E2E тесты
│   ├── conftest.py         # Конфигурация E2E тестов (Playwright)
│   ├── pages/              # Page Objects
│   │   ├── __init__.py
│   │   ├── base_page.py   # Базовый класс страниц
│   │   ├── home_page.py   # Главная страница
│   │   └── review_form_page.py  # Формы отзывов
│   ├── test_reviews.py    # TEST-001: Критический тест создания отзыва
│   └── test_diagnostic_home.py  # Диагностический тест
│
├── fixtures/               # Тестовые данные и утилиты
│   ├── __init__.py
│   ├── test_data.py       # Тестовые данные
│   └── api_client.py      # API клиенты для тестов
│
├── screenshots/            # Скриншоты при ошибках (создаётся автоматически)
├── reports/               # Отчёты о тестах (создаётся автоматически)
└── logs/                  # Логи тестов (создаётся автоматически)
```

## Установка

### 1. Установка зависимостей

```bash
cd /Users/philippkochnov/PycharmProjects/hikers
pip install -r tests/requirements.txt
```

### 2. Установка браузеров Playwright

```bash
playwright install chromium
```

Или используйте скрипт:

```bash
python tests/run_tests.py install
```

## Критические тесты

### TEST-001: Создание отзыва на существующую компанию

**Приоритет:** Критический

**Что тестируется:**
1. Клик на кнопку "Оставить отзыв" на главной
2. Выбор типа "Отзыв о компании" в модальном окне
3. Заполнение формы с автокомплитом компании
4. Отправка и проверка редиректа
5. Модерация через API
6. Проверка отображения на главной

```bash
# Быстрый запуск TEST-001
python run_test_001.py

# С конкретным рейтингом (1-5)
python run_test_001.py -r 5

# Через pytest
pytest tests/pages/test_reviews.py::test_create_company_review_with_autocomplete -v
```

## Запуск тестов

### Диагностика проблем

```bash
# Запуск диагностического теста
python run_diagnostic.py

# Или через pytest
pytest tests/pages/test_diagnostic_home.py -v -s
```

Это покажет:
- Все кнопки на странице
- Правильные селекторы
- HTML структуру элементов

### Быстрая проверка (Smoke тесты)

```bash
# Запуск критически важных тестов
python tests/run_tests.py smoke

# Или напрямую через pytest
pytest tests/pages -m smoke -v
```

### Запуск всех E2E тестов

```bash
# Через скрипт
python tests/run_tests.py all

# Или напрямую
pytest tests/pages -v
```

### Запуск с визуальным браузером

```bash
# Медленный режим для отладки
python tests/run_tests.py headed

# Режим отладки (останавливается на первой ошибке)
python tests/run_tests.py debug
```

### Запуск конкретного теста

```bash
# Конкретный файл
pytest tests/pages/test_review_creation.py -v

# Конкретный тест
pytest tests/pages/test_review_creation.py::TestReviewCreation::test_create_tour_review_success -v
```

### Параллельный запуск

```bash
# С 4 воркерами (по умолчанию)
python tests/run_tests.py parallel

# С указанием количества воркеров
python tests/run_tests.py parallel --workers=8
```

### Запуск с покрытием кода

```bash
python tests/run_tests.py coverage
```

### Генерация отчёта

```bash
python tests/run_tests.py report
# Отчёт будет в tests/reports/report.html
```

## Маркеры тестов

- `@pytest.mark.critical` - Критические тесты
- `@pytest.mark.smoke` - Smoke тесты
- `@pytest.mark.regression` - Регрессионные тесты
- `@pytest.mark.e2e` - E2E тесты
- `@pytest.mark.slow` - Медленные тесты
- `@pytest.mark.flaky` - Нестабильные тесты

### Запуск тестов по маркерам

```bash
# Только критические тесты
pytest tests/pages -m critical

# Smoke тесты, но не медленные
pytest tests/pages -m "smoke and not slow"

# Все тесты кроме flaky
pytest tests/pages -m "not flaky"
```

## Конфигурация

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
TEST_ENV=local
```

### Настройка браузера

В `tests/e2e/conftest.py` можно настроить:

- `headless`: запуск без GUI (по умолчанию False)
- `slow_mo`: замедление действий в мс (по умолчанию 100)
- `viewport`: размер окна (по умолчанию 1920x1080)

### Таймауты

В `tests/pytest.ini`:
- Глобальный таймаут: 60 секунд
- Таймаут страницы: 30 секунд (в base_page.py)

## Page Objects

### Использование в тестах

```python
from pages import HomePage, ReviewFormPage


async def test_example(page):
    # Создание Page Objects
    home_page = HomePage(page)
    review_form = ReviewFormPage(page)

    # Использование методов
    await home_page.open()
    await home_page.click_leave_review()
    await review_form.fill_tour_review(data)
    await review_form.submit_form()
```

### Добавление новых страниц

1. Создайте файл в `tests/e2e/pages/`
2. Наследуйте от `BasePage`
3. Определите локаторы как константы класса
4. Реализуйте методы взаимодействия
5. Импортируйте в `__init__.py`

## Тестовые данные

### Генераторы данных

```python
from fixtures import generate_unique_email, generate_unique_name

email = generate_unique_email()
name = generate_unique_name("TestReview")
```

### Использование тестовых данных

```python
from fixtures import get_review_test_data

review_data = get_review_test_data()
valid_tour = review_data["valid"]["tour_review"]
invalid_company = review_data["invalid"]["company_review"]
```

## API для модерации

### Использование в тестах

```python
from fixtures import TestModerationAPI

async def test_moderation(backend_url):
    api = TestModerationAPI(backend_url)
    await api.moderate_review(review_id, "approved")
    await api.close()
```

## Отладка

### Скриншоты при ошибках

Автоматически сохраняются в `tests/screenshots/` при падении тестов.

### Логирование

Логи сохраняются в `tests/logs/pytest.log`

Уровни логирования:
- Console: INFO
- File: DEBUG

### Запуск в режиме отладки

```bash
# Максимально подробный вывод
pytest tests/pages -vvv --capture=no --tb=long

# Или через скрипт
python tests/run_tests.py debug
```

## CI/CD интеграция

### GitHub Actions пример

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r tests/requirements.txt
          playwright install chromium
      
      - name: Run services
        run: |
          docker-compose up -d
          sleep 10
      
      - name: Run tests
        run: |
          pytest tests/e2e -m "critical" --headless
      
      - name: Upload reports
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: test-reports
          path: tests/reports/
```

## Проблемы и решения

### CAPTCHA в dev режиме

CAPTCHA автоматически проходится в dev режиме. Если нет, проверьте переменную окружения `TEST_MODE=true` на бэкенде.

### Медленные тесты

1. Используйте параллельный запуск
2. Разделите на smoke и regression
3. Оптимизируйте ожидания в Page Objects

### Нестабильные тесты

1. Используйте `assert_with_retry` фикстуру
2. Увеличьте таймауты
3. Пометьте как `@pytest.mark.flaky`

## Контакты

По вопросам обращайтесь к QA команде или создайте issue в репозитории.
