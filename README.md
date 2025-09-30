# Hiker's Voice - Система Автоматизированного Тестирования

## Философия проекта

Минимум усложнения, максимум ясности. Тесты должны быть простыми, поддерживаемыми и запускаться локально перед пушем в прод. Никаких лишних абстракций и переусложнений.

## Статус тестов ✅

| Тест | Описание | Статус | Файл |
|------|----------|--------|------|
| TEST-001 | Создание отзыва на компанию с автокомплитом | ✅ Работает | `test_reviews.py::test_create_company_review_with_autocomplete` |
| TEST-002 | Создание отзыва на гида с автокомплитом | ✅ Работает | `test_reviews.py::test_create_guide_review_with_autocomplete` |

## Реализованные тесты

### TEST-001: Создание отзыва на компанию с автокомплитом
- ✅ Проверка создания отзыва на компанию
- ✅ Использование автокомплита для выбора компании "Svaneti"
- ✅ Модерация через тестовый API
- ✅ Проверка отображения на главной странице
- ✅ Проверка полного текста на странице отзыва
- ✅ Параметризованный тест с разными рейтингами (1-5)

### TEST-002: Создание отзыва на существующего гида
- ✅ Создание анонимного отзыва на гида "Георгий Челидзе"
- ✅ Использование автокомплита для выбора гида
- ✅ Правильная привязка отзыва к гиду через EntityLinker
- ✅ Математическая проверка пересчёта рейтинга с толерантностью 0.05
- ✅ Проверка отображения на трёх страницах: гида, главной и /reviews
- ✅ Проверка корректного подсчёта звёзд в отзывах

## Решенные проблемы 🔧

### 1. Проблема привязки отзывов к гидам

**Проблема:** Тестовый эндпоинт модерации не устанавливал связи между отзывом и гидом/компанией.

**Решение:** Тестовый эндпоинт `/api/v1/test/moderate/{review_id}` теперь использует `ReviewService.approve_review()` который:
- Вызывает EntityLinker для установки связей
- Создает/находит гида или компанию
- Обновляет рейтинги
- Создает записи в таблице review_guide (many-to-many)

**Файл с тестовыми эндпоинтами:** `/backend/app/api/test_moderation.py`

### 2. Подсчёт звёзд в отзывах

**Проблема:** Компонент Rating всегда рендерит 5 SVG элементов, нужно считать только заполненные.

**Решение:** 
```python
filled_stars = await review_element.locator("svg.text-yellow-400").count()
```

### 3. Округление рейтингов

**Проблема:** Backend округляет до 1 десятичного знака, тесты ожидали точное значение.

**Решение:** Добавлена толерантность 0.05 в проверках рейтинга.

## Структура проекта

```
hikers_voice_tests/
├── conftest.py              # Главная конфигурация pytest
├── pytest.ini               # Настройки pytest
├── requirements.txt         # Зависимости проекта
├── README.MD               # Этот файл
│
├── pages/                   # Page Objects паттерн
│   ├── __init__.py         
│   ├── base_page.py        # Базовый класс с общими методами
│   ├── home_page.py        # Главная страница
│   ├── review_form_page.py # Формы создания отзывов
│   ├── guide_page.py       # Страница гида
│   └── reviews_page.py     # Страница всех отзывов
│
├── tests/                   # Тесты
│   ├── conftest.py         # E2E конфигурация и фикстуры
│   └── test_reviews.py     # Тесты отзывов TEST-001 и TEST-002
│
├── fixtures/                # Тестовые данные
│   ├── __init__.py
│   └── test_data.py        # Генераторы тестовых данных
│
└── utils/                   # Утилиты
    ├── __init__.py
    ├── test_helper.py      # API хелперы для модерации
    └── rating_calculator.py # Математика расчёта рейтингов
```

## Тестовые эндпоинты Backend

Все тестовые эндпоинты находятся в файле `/backend/app/api/test_moderation.py` и доступны только в dev окружении.

### Основные эндпоинты модерации
- `GET /api/v1/test/reviews/all` - все отзывы с полной информацией о связях
- `POST /api/v1/test/moderate/{review_id}` - модерация с полным EntityLinker
- `GET /api/v1/test/reviews/{review_id}/diagnostic` - диагностика связей отзыва

### Дополнительные эндпоинты
- `POST /api/v1/test/moderate/{review_id}/edit` - редактирование и одобрение
- `POST /api/v1/test/moderate/{review_id}/ban-ip` - бан IP
- `POST /api/v1/test/moderate/{review_id}/mute-ip` - временный мьют IP
- `POST /api/v1/test/moderate/{review_id}/allow-ip` - разрешение IP и одобрение

### Эндпоинты для очистки
- `DELETE /api/v1/test/reviews/{review_id}` - удаление отзыва
- `DELETE /api/v1/test/companies/{company_id}` - удаление компании

## Запуск тестов

### Быстрый старт
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск конкретного теста
pytest tests/test_reviews.py::test_create_guide_review_with_autocomplete -v

# Запуск всех тестов отзывов
pytest tests/test_reviews.py -v

# С визуальным браузером (медленно)
pytest tests/test_reviews.py --slow-mo=500

# В headless режиме (быстро)
pytest tests/test_reviews.py --headless

# С подробным выводом
pytest tests/test_reviews.py -v -s

# Только smoke тесты
pytest -m smoke

# Только критичные тесты
pytest -m critical
```

## Предусловия

### Обязательные требования
1. **Backend** запущен на `http://localhost:8000`
2. **Frontend** запущен на `http://localhost:3000`
3. **База данных** содержит seed данные:
   - Гид: Георгий Челидзе (id=1)
   - Компании с "Svaneti" в названии
4. **Тестовые эндпоинты** включены (APP_ENV=dev)

### Проверка готовности
```bash
# Проверка Backend
curl http://localhost:8000/healthz

# Проверка Frontend
curl http://localhost:3000

# Проверка тестовых эндпоинтов
curl http://localhost:8000/api/v1/test/reviews/all
```

## Важные фикстуры

### clean_test_review
Автоматически удаляет созданные отзывы после теста:
```python
@pytest.fixture
async def clean_test_review(backend_url):
    review_ids = []
    yield review_ids  # Тест добавляет ID созданных отзывов
    # Автоматическая очистка после теста
```

### review_test_data
Генерирует тестовые данные для отзывов:
```python
{
    "valid": {
        "tour_review": {...},
        "guide_review": {...}
    }
}
```

## Паттерны написания тестов

### Структура теста (AAA)
```python
async def test_feature(page: Page, review_test_data: dict):
    # Arrange - подготовка данных
    test_data = review_test_data["valid"]["tour_review"]
    home_page = HomePage(page)
    
    # Act - выполнение действий
    await home_page.open()
    await home_page.click_leave_review()
    # ... заполнение формы
    
    # Assert - проверка результатов
    assert await home_page.check_review_exists(), "Review not found"
    logger.info(f"TEST-XXX completed: review_id={review_id}")
```

### Правила кода
- ✅ **Используйте** существующие Page Objects
- ✅ **Следуйте** паттерну AAA (Arrange-Act-Assert)
- ✅ **Добавляйте** понятные assert сообщения
- ✅ **Логируйте** только финальный успех теста
- ❌ **НЕ создавайте** новые конфиги
- ❌ **НЕ используйте** time.sleep() - только wait_for_*
- ❌ **НЕ хардкодьте** данные - используйте фикстуры

## Отладка

### Диагностика отзыва
```bash
# Проверить связи отзыва
curl http://localhost:8000/api/v1/test/reviews/{review_id}/diagnostic

# Пример ответа для правильно связанного отзыва:
{
  "entity_links": {
    "guide_id (legacy)": 1,
    "guide_name (legacy)": "Георгий Челидзе"
  },
  "linked_guides": [{
    "id": 1,
    "name": "Георгий Челидзе", 
    "is_primary": true
  }],
  "issues": []  # Пустой массив = всё хорошо
}
```

### Частые проблемы и решения

| Проблема | Причина | Решение |
|----------|---------|---------|
| Отзыв не привязан к гиду | Старый тестовый эндпоинт | Обновите backend, используйте новый эндпоинт |
| Селектор не найден | Изменился фронтенд | Проверьте актуальность в `/frontend/src/components/` |
| Рейтинг не совпадает | Округление | Используйте толерантность 0.05 |
| Cleanup падает | Нет прав или объект не найден | Проверьте, что объект существует |
| Автокомплит не работает | Слишком быстрый ввод | Добавьте `wait_for_timeout(500)` после ввода |
| Модерация не работает | EntityLinker не вызывается | Убедитесь, что используется ReviewService |

### Запуск с отладкой
```bash
# Визуальный режим с паузами
pytest tests/test_reviews.py --slow-mo=1000 --headed

# С выводом всех логов
pytest tests/test_reviews.py -v -s --log-cli-level=INFO

# Конкретный тест с отладкой
pytest tests/test_reviews.py::test_create_guide_review_with_autocomplete -vvv
```

## Будущие улучшения

### Планируется
- [ ] TEST-003: Создание новой компании
- [ ] TEST-004: Редактирование отзыва
- [ ] TEST-005: Фильтрация отзывов по стране
- [ ] Тесты для many-to-many связей (несколько гидов в отзыве)
- [ ] Тесты модерации IP (бан/мьют)
- [ ] API тесты без UI

### Технический долг
- [ ] Вынести URL в environment переменные
- [ ] Добавить retry механизм для нестабильных тестов
- [ ] Параллельный запуск тестов
- [ ] Генерация HTML отчётов

---

**Принцип проекта:** Простые, надёжные тесты, которые работают из коробки и легко поддерживаются.

**Последнее обновление:** Декабрь 2024
**Версия:** 1.2.0
