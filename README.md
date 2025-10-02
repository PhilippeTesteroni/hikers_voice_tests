# Hiker's Voice - Система Автоматизированного Тестирования

## Философия проекта

Минимум усложнения, максимум ясности. Тесты должны быть простыми, поддерживаемыми и запускаться локально перед пушем в прод. Никаких лишних абстракций и переусложнений.

## Статус тестов ✅

| Тест | Описание | Статус | Файл |
|------|----------|--------|------|
| TEST-001 | Создание отзыва на компанию с автокомплитом | ✅ Работает | `test_reviews.py::test_create_company_review_with_autocomplete` |
| TEST-002 | Создание отзыва на гида с автокомплитом | ✅ Работает | `test_reviews.py::test_create_guide_review_with_autocomplete` |
| TEST-004 | Валидация формы отзыва (компания и гид) | ✅ Работает | `test_reviews.py::test_review_form_validation_errors` |
| TEST-005 | Загрузка фотографий в отзывы | ✅ Работает | `test_photo_upload.py::test_review_with_photos` |
| TEST-006 | Обнаружение дубликата компании | ✅ Работает | `test_companies.py::test_duplicate_company_detection_and_navigation` |
| TEST-007 | Обнаружение дубликата гида | ✅ Работает | `test_guides.py::test_duplicate_guide_detection_and_navigation` |
| TEST-008 | Создание гида без пересечения стран | ✅ Работает | `test_guides.py::test_create_guide_same_name_no_country_overlap` |
| TEST-009 | Lookup гидов с расширенной информацией | ✅ Работает | `test_lookup.py::test_guide_lookup_extended_info` |

## Структура проекта

```
hikers_voice_tests/
├── conftest.py              # Глобальная конфигурация pytest
├── pytest.ini               # Настройки pytest
├── requirements.txt         # Зависимости
│
├── pages/                   # Page Objects
│   ├── base_page.py        # Базовый класс с wait/click/fill методами
│   ├── home_page.py        # Главная страница
│   ├── company_page.py     # Компании (список, детали, создание, дубликаты)
│   ├── guide_page.py       # Гиды (список, детали, создание, дубликаты)
│   ├── review_form_page.py # Формы отзывов + автокомплиты + фото
│   └── reviews_page.py     # Список отзывов + lightbox
│
├── tests/                   # Тесты
│   ├── conftest.py         # E2E фикстуры (browser, clean_test_*)
│   ├── test_reviews.py     # TEST-001, 002, 004
│   ├── test_photo_upload.py # TEST-005
│   ├── test_companies.py   # TEST-006
│   ├── test_guides.py      # TEST-007, 008
│   └── test_lookup.py      # TEST-009
│
├── fixtures/                # Тестовые данные
│   ├── test_data.py        # Генераторы данных
│   ├── test_images_fixtures.py
│   └── test_images/        # Сгенерированные изображения
│
└── utils/                   # Утилиты
    ├── test_helper.py      # API хелперы (модерация, удаление)
    ├── rating_calculator.py
    └── image_generator.py
```

## Архитектура

### Page Object Pattern
- Все UI взаимодействия инкапсулированы в Page Objects
- `BasePage` - базовые методы wait/click/fill
- Селекторы как константы класса
- Методы возвращают данные, не делают assert

### Принципы тестов
1. **AAA паттерн** - Arrange, Act, Assert
2. **Линейность** - нет ветвлений кроме параметризации
3. **Cleanup через фикстуры** - `clean_test_review`, `clean_test_guide`
4. **Никаких time.sleep()** - только Playwright wait_for_*
5. **Понятные assert с сообщениями**

### Cleanup система
```python
# Автоматический cleanup через фикстуры
async def test_something(clean_test_guide: list):
    created_id = await create_guide()
    clean_test_guide.append(created_id)  # Удалится автоматически
    # Тест продолжается...
# В teardown фикстура удалит все гиды из списка
```

**Важно:** Cleanup происходит в фикстурах, НЕ в теле теста. Если cleanup падает - тест падает (предотвращает накопление мусора).

### Фикстуры

#### Browser фикстуры
- `page` - Playwright Page с viewport 1920x1080
- `browser_context` - Изолированный контекст для каждого теста
- Конфигурация: `--headless`, `--slow-mo=N`

#### Cleanup фикстуры
```python
@pytest_asyncio.fixture
async def clean_test_review(backend_url: str):
    """Отслеживает и удаляет отзывы после теста"""
    review_ids = []
    yield review_ids
    # Cleanup в teardown

@pytest_asyncio.fixture
async def clean_test_guide(backend_url: str):
    """Отслеживает и удаляет гидов после теста"""
    guide_ids = []
    yield guide_ids
    # Cleanup в teardown
```

#### Data фикстуры
- `review_test_data` - генератор тестовых данных
- `test_images` - список путей к 7 тестовым фото
- `api_client` - HTTP клиент для API вызовов

## Селекторы (приоритет)

1. `data-testid` ✅
2. `id` 
3. Уникальный `className`
4. `name` (формы)
5. `text` (последний вариант)

```python
# Правильные селекторы
SUBMIT = "[data-testid='submit-review']"
EMAIL = "input[name='email']"
BUTTON = "text=Оставить отзыв"
ALERT = ".alert-success"
```

## Работа с автокомплитами

Все автокомплиты используют debounce 300ms:

```python
async def type_and_wait_dropdown(self, text: str):
    await input.click()  # Триггер onFocus
    await self.page.wait_for_timeout(300)
    await input.type(text, delay=100)
    await self.page.wait_for_timeout(500)  # Debounce + API
    await self.page.wait_for_selector(DROPDOWN, state="visible")
```

**Важно:** 
- Клик перед вводом (триггерит `onFocus`)
- Ожидание debounce + время на API
- `state="visible"` обязательно

## Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# По категориям
pytest tests/test_reviews.py -v      # Отзывы
pytest tests/test_guides.py -v       # Гиды
pytest tests/test_lookup.py -v       # Lookup

# Параметризованный - один сценарий
pytest tests/test_lookup.py -k "guide_review" -v

# Критичные
pytest -m critical

# С визуализацией
pytest tests/ --slow-mo=500

# Headless (CI)
pytest tests/ --headless
```

## Предусловия

1. **Backend:** http://localhost:8000 (APP_ENV=dev)
2. **Frontend:** http://localhost:3000  
3. **Seed данные:**
   - Гид "Георгий Челидзе" (id=1) + контакты + страны GE/AM
   - Компании с "Svaneti"
   - Минимум 1 компания в каталоге
4. `pip install -r requirements.txt`
5. `python utils/image_generator.py`

## Реализованные тесты

### TEST-001, 002: Создание отзывов
- Отзывы на компании/гидов с автокомплитом
- Модерация через API
- Проверка отображения на всех страницах
- Математическая проверка рейтингов (TEST-002)
- **Cleanup:** `clean_test_review` фикстура

### TEST-004: Валидация формы
**Параметризация:** company/guide

**Проверки:**
- Блокировка кнопки при пустой форме
- Длина текста 10-4000 символов
- Обязательность всех полей
- Чекбокс правил

### TEST-005: Загрузка фото
**Параметризация:** 4 комбинации (company/guide × 1/5 фото)

**Проверки:**
- Превью в форме
- Фотогалерея на странице отзыва
- Lightbox (открытие, навигация, закрытие)
- **Cleanup:** `clean_test_review` фикстура

### TEST-006: Дубликат компании
**Проверки:**
- Warning при дубликате (HTTP 409)
- Кнопки: "Перейти" / "Попробовать снова"
- Навигация к существующей компании

### TEST-007: Дубликат гида
**Параметризация:** go_to_existing/create_new

**Проверки:**
- Warning при пересечении стран
- Карточка с полной информацией
- Навигация (сценарий A)
- Force create + cleanup (сценарий B)
- **Cleanup:** `clean_test_guide` фикстура

### TEST-008: Гид без пересечения стран
**Проверки:**
- Warning НЕ появляется (разные страны)
- Успешное создание нового гида
- **Cleanup:** `clean_test_guide` фикстура

### TEST-009: Lookup с расширенной информацией
**Параметризация:** guide_review/company_review

**Проверки:**
- Создание дубля гида (TR)
- Dropdown показывает 2+ гидов
- Формат: Имя + 🌍 Страны [• контакт/рейтинг]
- Уникальность информации
- **Cleanup:** `clean_test_guide` фикстура

## Решённые проблемы

### 1. Lightbox - двойные кнопки
Mobile кнопки (hidden) находились первыми

**Решение:** `.sm\\:block` для desktop версии

### 2. wait_for_review_form() не поддерживал гидов
Всегда ждал COMPANY_NAME_INPUT

**Решение:** Параметр `review_type`

### 3. Dropdown не появлялся
Неправильный селектор + нет debounce + нет клика

**Решение:**
- Селектор: `div.absolute.z-10[class*='bg-']`
- Клик перед вводом
- Ожидание 500ms (debounce + API)
- `state="visible"`

### 4. Разные input для lookup
`GuideAutocomplete` vs `GuidesSelector` - разные placeholder

**Решение:** Параметр `form_type` в методе

### 5. Cleanup в теле теста
Cleanup был в try/finally блоках

**Решение:** Фикстуры `clean_test_review` / `clean_test_guide`

## Чеклист создания теста

- [ ] Селекторы из актуального фронтенда?
- [ ] Селекторы как константы в Page Object?
- [ ] Используются методы из BasePage?
- [ ] Маркеры `@pytest.mark.e2e`, `@pytest.mark.critical`?
- [ ] Используются фикстуры cleanup?
- [ ] Понятные assert сообщения?
- [ ] Тест линейный (нет fallback)?
- [ ] Нет `time.sleep()`?

## Отладка

| Ошибка | Решение |
|--------|---------|
| Dropdown не появляется | `await input.click()` перед вводом |
| Timeout на селектор | Проверить в DevTools |
| Cleanup падает | APP_ENV=dev в backend |
| ModuleNotFoundError PIL | `pip install Pillow` |

```bash
# Debug команды
pytest tests/test_guides.py --slow-mo=1000 -v
pytest tests/test_lookup.py -k "company" -v
PLAYWRIGHT_DEBUG=1 pytest tests/test_guides.py -v
```

---

**Версия:** 2.0.0  
**Дата:** 02.10.2025  
**Изменения:** Реорганизация файлов + cleanup через фикстуры
