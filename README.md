# Hiker's Voice — Автоматизированное Тестирование

> **Минимум усложнения, максимум ясности.** Тесты должны быть простыми, поддерживаемыми и запускаться локально перед деплоем в прод.

---

## 📋 Содержание

- [Статус тестов](#статус-тестов-)
- [Архитектура](#архитектура-)
  - [Page Object Pattern](#page-object-pattern)
  - [Ключевые паттерны](#ключевые-паттерны)
  - [Система cleanup](#система-cleanup)
  - [Работа с автокомплитами](#работа-с-автокомплитами)
  - [Модерация](#модерация)
- [Структура проекта](#структура-проекта-)
- [Запуск тестов](#запуск-тестов-)
- [Тесты в деталях](#тесты-в-деталях-)
- [Отладка](#отладка-)
- [Чеклист создания теста](#чеклист-создания-теста-)

---

## Статус тестов ✅

| ID | Тест | Описание | Статус | Файл |
|----|------|----------|--------|------|
| **TEST-001** | Создание отзыва на компанию | Отзыв через автокомплит, модерация, проверка на главной и странице компании | ✅ | `test_reviews.py::test_create_company_review_with_autocomplete_refactored` |
| **TEST-002** | Создание отзыва на гида | Анонимный отзыв, проверка рейтинга, математическая точность | ✅ | `test_reviews.py::test_create_guide_review_with_autocomplete_refactored` |
| **TEST-003** | Создание компании | Полная форма + минимальная форма + валидация | ✅ | `test_companies.py::test_create_new_company` |
| **TEST-004** | Валидация формы отзыва | Проверка лимитов текста, обязательных полей, правил | ✅ | `test_reviews.py::test_review_form_validation_errors` |
| **TEST-005** | Загрузка фотографий | 1-5 фото, превью, галерея, lightbox навигация | ✅ | `test_photo_upload.py::test_review_with_photos_refactored` |
| **TEST-006** | Дубликат компании | Обнаружение, предупреждение, навигация | ✅ | `test_companies.py::test_duplicate_company_detection_and_navigation` |
| **TEST-007** | Дубликат гида (пересечение стран) | Две опции: перейти / создать новый | ✅ | `test_guides.py::test_duplicate_guide_detection_and_navigation` |
| **TEST-008** | Гид без пересечения стран | Одно имя, разные страны → успешное создание | ✅ | `test_guides.py::test_create_guide_same_name_no_country_overlap` |
| **TEST-009** | Lookup с расширенной информацией | Автокомплит показывает страны + контакты для дублей | ✅ | `test_lookup.py::test_guide_lookup_extended_info` |
| **TEST-010** | Галерея фотографий сущности | 3 отзыва × 5 фото = 15, lightbox, счётчик, навигация | ✅ | `test_entity_photo_gallery.py::test_entity_photo_gallery` |
| **TEST-011** | Редактирование с валидным ключом | Компания/гид: получение мастер-ключа, редактирование, проверка тоста и данных | ✅ | `test_entity_edit.py::test_edit_entity_with_valid_key` |
| **TEST-012** | Редактирование с невалидным ключом | Попытка редактирования с неверным UUID → красный тост с ошибкой | ✅ | `test_entity_edit.py::test_edit_entity_with_invalid_key` |
| **TEST-013** | Попытка редактирования без ключа | Пустое поле, случайная строка, невалидный UUID → кнопка disabled или ошибка | ✅ | `test_entity_edit.py::test_edit_attempt_with_invalid_format` |

**Всего:** 13 тестов, все работают.

---

## Архитектура 🏗

### Page Object Pattern

Все взаимодействия с UI инкапсулированы в Page Objects. Селекторы — константы класса, методы возвращают данные (не делают assert).

```python
# pages/home_page.py
class HomePage(BasePage):
    # Селекторы
    LEAVE_REVIEW_BTN = "button:has-text('Оставить отзыв')"
    REVIEW_CARD = "[data-testid='review-card']"
    
    # Методы
    async def click_leave_review(self):
        await self.page.click(self.LEAVE_REVIEW_BTN)
    
    async def find_review_by_author(self, name: str):
        # Возвращает данные, а не делает assert
        cards = await self.page.locator(self.REVIEW_CARD).all()
        for card in cards:
            author = await card.locator(".author-name").text_content()
            if name in author:
                return card
        return None
```

**BasePage** (`pages/base_page.py`) предоставляет:
- `wait_for_load()` — ждёт `networkidle` + React hydration + шрифты
- `click_and_wait()` — клик + ожидание навигации/селектора
- `fill_and_validate()` — заполнение + проверка значения
- `wait_for_condition()` — универсальное ожидание условия с polling

**Наследование:**
```
BasePage
├── HomePage (главная, список отзывов)
├── CompanyPage (компании: список, детали, создание)
├── GuidePage (гиды: список, детали, создание)
├── ReviewFormPage (формы отзывов + автокомплиты + фото)
└── ReviewsPage (детали отзыва + фотогалерея + lightbox)
```

---

### Ключевые паттерны

#### 1. **AAA (Arrange-Act-Assert)**

```python
async def test_example(page, clean_test_company):
    # Arrange
    company = await frontend_api_client.create_company(...)
    clean_test_company.append(company["id"])
    
    # Act
    await home_page.open()
    await home_page.click_leave_review()
    # ...
    
    # Assert
    assert "success=review_created" in page.url
    assert rating == expected_rating
```

#### 2. **Линейность — никаких ветвлений**

```python
# ❌ НЕ ТАК
if await element.is_visible():
    # do something
else:
    # fallback

# ✅ ТАК
await element.wait_for(state="visible", timeout=10000)
# continue
```

Единственное исключение — **параметризация** через `@pytest.mark.parametrize`.

#### 3. **Никаких time.sleep()**

```python
# ❌ НЕ ТАК
await page.wait_for_timeout(2000)

# ✅ ТАК
await page.wait_for_selector(DROPDOWN, state="visible")
await page.wait_for_load_state("networkidle")
```

Исключение: короткие задержки для debounce (300-500ms).

#### 4. **Фикстуры вместо конструкторов**

```python
# ✅ Используем фикстуры
async def test_example(page: Page, review_test_data: dict):
    data = review_test_data["valid"]["tour_review"]
    # ...

# ❌ НЕ создаём подключения в тесте
async def test_bad():
    page = await browser.new_page()  # WRONG!
```

#### 5. **Ожидание данных с retry**

```python
# ✅ Простое ожидание без reload
success = await base_page.wait_for_condition(
    check_fn=lambda: company_page.get_reviews_count() > 0,
    timeout=10000,
    error_message="Reviews did not appear"
)
assert success

# ✅ С reload для ISR кеша (более стабильно)
success = await base_page.wait_for_condition(
    check_fn=lambda: company_page.get_reviews_count() > 0,
    timeout=30000,
    interval=5000,
    retry_with_reload=True,  # Перезагружает страницу между проверками
    error_message="Reviews did not appear after retries"
)
assert success
```

**Когда использовать `retry_with_reload=True`:**
- После модерации отзыва (ISR кеш может не обновиться сразу)
- После создания компании/гида
- После загрузки фото
- В любой ситуации, когда данные могут кешироваться

---

### Система cleanup

**Правило:** Cleanup происходит **в фикстурах**, а не в теле теста. Если cleanup падает — тест падает (предотвращает накопление мусора в БД).

#### Фикстуры cleanup

##### `clean_test_review` — отзывы

```python
@pytest_asyncio.fixture
async def clean_test_review(backend_url: str):
    review_ids = []
    yield review_ids
    # Teardown: удаление через admin API
    for review_id in review_ids:
        response = await client.post(f"/admin/review/{review_id}/delete", headers=auth_headers)
        if response.status_code not in [303, 404]:
            pytest.fail(f"CLEANUP FAILED: review {review_id}")
```

**Креды админа:**
```python
ADMIN_USERNAME = "Philippe_testeroni"  # ← ЗАГЛАВНАЯ P!
ADMIN_PASSWORD = "KeklikG0nnaKek!"
```

##### `clean_test_company` — компании

```python
@pytest_asyncio.fixture
async def clean_test_company(backend_url: str):
    company_ids = []
    yield company_ids
    # Teardown: DELETE /api/v1/test/companies/{id}
    for company_id in company_ids:
        deleted = await test_helper.delete_company(company_id)
        if not deleted:
            pytest.fail(f"CLEANUP FAILED: company {company_id}")
```

##### `clean_test_guide` — гиды

```python
@pytest_asyncio.fixture
async def clean_test_guide(backend_url: str):
    guide_ids = []
    yield guide_ids
    # Teardown: DELETE /api/v1/test/guides/{id}
    for guide_id in guide_ids:
        deleted = await test_helper.delete_guide(guide_id)
        if not deleted:
            pytest.fail(f"CLEANUP FAILED: guide {guide_id}")
```

#### Использование в тестах

```python
async def test_example(clean_test_review: list, clean_test_company: list):
    # Создаём компанию
    company = await frontend_api_client.create_company(...)
    clean_test_company.append(company["id"])  # ← отслеживаем для cleanup
    
    # Создаём отзыв
    review_id = await create_review(...)
    clean_test_review.append(review_id)  # ← отслеживаем для cleanup
    
    # Тест продолжается...
    # В teardown фикстуры автоматически удалят всё
```

**Важно:** Если cleanup падает — тест падает. Никаких fallback'ов.

---

### Работа с автокомплитами

Все автокомплиты имеют **debounce 300ms**. Правильная последовательность:

```python
async def type_and_wait_dropdown(self, text: str):
    # 1. Клик по input (триггерит onFocus)
    await input.click()
    await self.page.wait_for_timeout(300)
    
    # 2. Ввод текста с задержкой между символами
    await input.type(text, delay=100)
    
    # 3. Ожидание debounce + API
    await self.page.wait_for_timeout(500)
    
    # 4. Проверка появления dropdown
    await self.page.wait_for_selector(DROPDOWN, state="visible")
```

**Важно:**
- Клик **перед** вводом
- Ожидание `state="visible"` (не `attached`)
- Дополнительное время на API запрос

#### Селектор dropdown

```python
# Правильный селектор (работает с обеими темами)
DROPDOWN = "div.absolute.z-10[class*='bg-']"

# ❌ НЕ работает
DROPDOWN = ".dropdown"  # нет такого класса
DROPDOWN = "ul"         # слишком общий
```

---

### Модерация

#### Модерация отзывов

Отзывы создаются со статусом `pending_rate_limited` **без** привязки к сущности (`company_id`/`guide_id` = NULL). Привязка происходит **только** при модерации.

```python
# ❌ НЕПРАВИЛЬНО — поиск по company_id до модерации
review_id = await find_review(company_id=company_id)

# ✅ ПРАВИЛЬНО — поиск только по author_name
review_id = await test_helper.find_and_moderate_review(
    author_name="Test User *20250104_153045*",  # уникальное имя с timestamp
    action="approve",
    company_id=company_id  # используется только для верификации ПОСЛЕ модерации
)
```

**Endpoint:** `POST /api/v1/test/moderate/{review_id}?action=approve`

**Эффекты модерации:**
- Статус → `approved`
- Привязка к компании/гиду (`company_id`/`guide_id`)
- Пересчёт рейтинга
- ISR кэш инвалидируется автоматически (~1 секунда)

#### Удаление сущностей

**Отзывы:**
```python
# Через admin панель с Basic Auth
POST /admin/review/{review_id}/delete
Authorization: Basic <base64(Philippe_testeroni:KeklikG0nnaKek!)>

# Ожидаемый ответ: 303 See Other (редирект после удаления)
```

**Компании и гиды:**
```python
# Через test API (без авторизации)
DELETE /api/v1/test/companies/{company_id}
DELETE /api/v1/test/guides/{guide_id}

# Ожидаемый ответ: 200 OK или 204 No Content
```

**Важно:**
- Удаление компании/гида → каскадное удаление отзывов
- Удаление фото происходит автоматически
- В тестах cleanup идёт в порядке: reviews → companies/guides

---

## Структура проекта 📁

```
hikers_voice_tests/
├── conftest.py              # Глобальная конфигурация pytest
├── pytest.ini               # Настройки pytest (маркеры, логи)
├── requirements.txt         # Зависимости
├── README.md                # Эта документация
│
├── pages/                   # Page Objects
│   ├── __init__.py
│   ├── base_page.py        # BasePage с wait/click/fill методами
│   ├── home_page.py        # Главная страница + список отзывов
│   ├── company_page.py     # Компании: список, детали, создание, дубликаты
│   ├── guide_page.py       # Гиды: список, детали, создание, дубликаты
│   ├── review_form_page.py # Формы отзывов + автокомплиты + загрузка фото
│   └── reviews_page.py     # Детали отзыва + фотогалерея + lightbox
│
├── tests/                   # Тесты
│   ├── conftest.py         # E2E фикстуры (browser, clean_test_*)
│   ├── test_reviews.py     # TEST-001, 002, 004 (создание отзывов, валидация)
│   ├── test_companies.py   # TEST-003, 006 (создание компании, дубликаты)
│   ├── test_guides.py      # TEST-007, 008 (дубликаты гидов)
│   ├── test_lookup.py      # TEST-009 (автокомплит с расширенной информацией)
│   ├── test_photo_upload.py        # TEST-005 (загрузка фото)
│   ├── test_entity_photo_gallery.py # TEST-010 (галерея на странице сущности)
│   └── test_entity_edit.py # TEST-011, 012, 013 (редактирование компаний/гидов)
│
├── fixtures/                # Тестовые данные
│   ├── test_data.py        # Генераторы данных (generate_company_data, etc.)
│   ├── test_images_fixtures.py  # Фикстура test_images
│   └── test_images/        # Папка со сгенерированными изображениями
│
└── utils/                   # Утилиты
    ├── test_helper.py      # TestHelper (модерация, удаление через API)
    ├── frontend_api_client.py  # Создание сущностей через фронтенд API
    ├── image_generator.py  # Генератор тестовых изображений
    └── rating_calculator.py # Расчёт средних рейтингов
```

---

## Запуск тестов 🚀

### Предусловия

1. **Backend:** `http://localhost:8000` (APP_ENV=dev)
2. **Frontend:** `http://localhost:3000`
3. **Зависимости:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Тестовые изображения:**
   ```bash
   python utils/image_generator.py
   ```

### Команды запуска

```bash
# Все тесты
pytest tests/ -v

# По категориям
pytest tests/test_reviews.py -v      # Отзывы
pytest tests/test_companies.py -v    # Компании
pytest tests/test_guides.py -v       # Гиды
pytest tests/test_lookup.py -v       # Lookup
pytest tests/test_photo_upload.py -v # Загрузка фото
pytest tests/test_entity_photo_gallery.py -v # Галерея
pytest tests/test_entity_edit.py -v  # Редактирование

# Параметризованный — один сценарий
pytest tests/test_lookup.py -k "guide_review" -v
pytest tests/test_guides.py -k "go_to_existing" -v

# Критичные тесты
pytest -m critical

# С визуализацией
pytest tests/ --slow-mo=500

# Headless (CI)
pytest tests/ --headless

# Один тест
pytest tests/test_reviews.py::test_create_company_review_with_autocomplete_refactored -v
```

### Опции командной строки

```bash
--headless          # Headless режим (default: True)
--slow-mo=N         # Замедление действий (default: 100ms)
--env=ENV           # Окружение: local, staging, prod (default: local)
```

---

## Тесты в деталях 🔍

### TEST-001, 002: Создание отзывов с автокомплитом

**Файл:** `test_reviews.py`

**Параметризация:** `rating=[1, 5]` (boundary values)

**Сценарий (компания):**
1. Создать уникальную компанию через API
2. Открыть форму отзыва
3. Заполнить через автокомплит (поиск по первым 10 символам, выбор точного совпадения)
4. Отправить форму
5. Модерировать через API
6. Проверить отображение на главной странице
7. Проверить рейтинг на странице компании (новая компания → rating = 1 или 5, reviews = 1)

**Сценарий (гид):**
- Анонимный автор (пустое имя → "Аноним")
- Математическая проверка рейтинга (точное соответствие)
- Создание уникального гида через API

**Cleanup:** `clean_test_review`, `clean_test_company`, `clean_test_guide`

**Важные детали:**
- Автор с timestamp (`*20250104_153045*`) для уникальности
- Автокомплит: поиск по 10 символам, выбор полного имени
- ISR кэш инвалидируется автоматически

---

### TEST-003: Создание компании

**Файл:** `test_companies.py`

**Варианты:**
1. `test_create_new_company` — полная форма (все поля)
2. `test_create_company_minimal_data` — только обязательные поля
3. `test_company_validation_errors` — проверка валидации

**Сценарий (полная форма):**
1. Открыть `/companies`
2. Клик "Добавить компанию"
3. Заполнить все поля (имя, страна, описание, email, телефон, сайт, Instagram, Telegram)
4. Отправить
5. Получить `company_id` из success сообщения
6. Перейти на страницу компании через кнопку
7. Проверить все данные

**Cleanup:** `clean_test_company`

**Особенности:**
- Компании создаются сразу со статусом `approved` (модерация не нужна)
- Instagram/Telegram: автоматическое удаление `@` в отображении

---

### TEST-004: Валидация формы отзыва

**Файл:** `test_reviews.py`

**Параметризация:** `review_type=["company", "guide"]`

**Проверки:**
1. Кнопка "Отправить" заблокирована при пустой форме
2. Минимум текста: 10 символов (показывает ошибку)
3. Максимум текста: 4000 символов (показывает ошибку)
4. Кнопка активируется только когда все поля заполнены + правила приняты
5. Снятие галочки "Правила" → кнопка снова блокируется

**Cleanup:** Не требуется (форма не отправляется)

---

### TEST-005: Загрузка фотографий в отзывы

**Файл:** `test_photo_upload.py`

**Параметризация:**
- `review_type=["company", "guide"]`
- `photo_count=[1, 5]` (boundary values)

**Сценарий:**
1. Создать уникальную сущность через API
2. Заполнить форму отзыва
3. Загрузить N фотографий
4. Проверить превью в форме (N миниатюр)
5. Отправить форму (timeout увеличен для 5 фото)
6. Модерировать отзыв
7. Перейти на страницу отзыва
8. Проверить галерею фотографий (N фото)
9. Открыть lightbox
10. Проверить счётчик "1 / N"
11. Навигация вперёд/назад
12. Закрыть lightbox

**Cleanup:** `clean_test_review`, `clean_test_company`, `clean_test_guide`

**Важные детали:**
- Timeout для submit: 30s если 5 фото, 15s если 1 фото
- Ожидание сохранения фото на диск: `photo_count * 2000ms`

---

### TEST-006: Обнаружение дубликата компании

**Файл:** `test_companies.py`

**Сценарий:**
1. Создать компанию через API
2. Попытаться создать компанию с таким же именем через UI
3. Проверить появление предупреждения (HTTP 409)
4. Проверить наличие двух кнопок:
   - "Перейти к компании"
   - "Попробовать снова"
5. Клик "Перейти к компании"
6. Проверить навигацию на страницу существующей компании
7. Проверить, что имя совпадает

**Cleanup:** `clean_test_company`

---

### TEST-007: Обнаружение дубликата гида (пересечение стран)

**Файл:** `test_guides.py`

**Параметризация:** `action=["go_to_existing", "create_new"]`

**Сценарий (общее начало):**
1. Создать гида через API (страны: GE, AM)
2. Попытаться создать гида с таким же именем и пересекающейся страной (GE)
3. Проверить появление предупреждения с карточкой гида
4. Карточка показывает:
   - Имя гида
   - Страны (значки)
   - Рейтинг
   - Количество отзывов
   - Контакты

**Сценарий A (go_to_existing):**
5. Клик "Да, перейти к профилю"
6. Проверить навигацию `/guides/{guide_id}`
7. Проверить имя гида

**Сценарий B (create_new):**
5. Клик "Нет, создать новый"
6. Проверить success сообщение с новым `guide_id`
7. Перейти на `/guides` и проверить, что оба гида существуют

**Cleanup:** `clean_test_guide`

---

### TEST-008: Создание гида без пересечения стран

**Файл:** `test_guides.py`

**Сценарий:**
1. Создать гида через API (страны: GE, AM)
2. Создать гида с таким же именем, но **другой страной** (TR)
3. Проверить, что предупреждение **НЕ** появляется
4. Проверить success сообщение
5. Получить `guide_id`

**Cleanup:** `clean_test_guide`

**Важная деталь:** Дубликаты детектируются **только** при пересечении стран.

---

### TEST-009: Lookup с расширенной информацией

**Файл:** `test_lookup.py`

**Параметризация:** `form_type=["guide_review", "company_review"]`

**Сценарий:**
1. Создать два гида с одинаковым именем, но разными странами (GE и TR)
2. Открыть форму отзыва (на гида или компанию)
3. Ввести часть имени гида в автокомплит
4. Дождаться появления dropdown
5. Проверить, что dropdown показывает минимум 2 гида
6. Проверить формат каждого элемента:
   ```
   Имя гида
   🌍 Страна1, Страна2 [• Контакт | Рейтинг]
   ```
7. Проверить, что `line2` (расширенная информация) у гидов **различается**
8. Проверить наличие "Грузия" и "Турция" в расширенных данных

**Cleanup:** `clean_test_guide`

**Важные детали:**
- Разные формы используют разные компоненты (`GuideAutocomplete` vs `GuidesSelector`)
- Параметр `form_type` определяет правильный placeholder

---

### TEST-010: Галерея фотографий на странице сущности

**Файл:** `test_entity_photo_gallery.py`

**Параметризация:** `entity_type=["guide", "company"]`

**Сценарий:**
1. Создать уникальную сущность через API
2. Создать **3 отзыва** с **5 фотографиями** каждый (итого 15 фото)
3. Перейти на страницу сущности
4. Проверить заголовок галереи: "Фотографии из отзывов (15)"
5. Проверить отображение **6 миниатюр**
6. Проверить оверлей на 6-й миниатюре: "+9"
7. Клик на первую фотографию → открыть lightbox
8. Проверить счётчик: "1 / 15"
9. Навигация вперёд: 2, 3, 4, 5
10. Навигация назад: 4
11. Закрыть lightbox

**Cleanup:** `clean_test_review`, `clean_test_company`, `clean_test_guide`

**Важные детали:**
- Галерея показывает максимум 6 миниатюр
- Остальные фото скрыты за оверлеем (total - 6 = remaining)
- Lightbox: кнопки `[aria-label='Следующее фото']` и `[aria-label='Предыдущее фото']`

---

### TEST-011, 012, 013: Редактирование сущностей

**Файл:** `test_entity_edit.py`

Подробности в секции [Тесты в деталях](#тесты-в-деталях-) оригинального README (слишком объёмно для краткого изложения).

---

## Отладка 🔧

### Типичные ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| Dropdown не появляется | Нет клика перед вводом | `await input.click()` перед `input.type()` |
| Timeout на селектор | Селектор неверный | Проверить в DevTools (F12) |
| Cleanup падает | APP_ENV != dev | `export APP_ENV=dev` в backend |
| ModuleNotFoundError PIL | Pillow не установлен | `pip install Pillow` |
| Автокомплит выбирает не ту сущность | Нет `select_exact` | Передай полное имя в параметре |
| Review не найден при модерации | Поиск по `company_id` до модерации | Ищи только по `author_name` |
| 401 при удалении отзыва | Неверные креды админа | `Philippe_testeroni` (заглавная P!) |

### Debug команды

```bash
# Замедлить выполнение до 1 секунды
pytest tests/test_guides.py --slow-mo=1000 -v

# Запустить один параметр
pytest tests/test_lookup.py -k "company" -v

# Playwright debug mode
PLAYWRIGHT_DEBUG=1 pytest tests/test_guides.py -v

# Логи в консоль
pytest tests/ -v -s

# Остановиться на первом падении
pytest tests/ -x
```

### Проверка cleanup

```bash
# Проверить, что ничего не осталось в БД
curl http://localhost:8000/api/v1/test/reviews/all | jq '.reviews | length'
curl http://localhost:8000/api/v1/test/companies/all | jq '.companies | length'
curl http://localhost:8000/api/v1/test/guides/all | jq '.guides | length'
```

---

## Чеклист создания теста ✅

Перед коммитом проверь:

- [ ] Селекторы взяты из актуального кода фронтенда?
- [ ] Селекторы добавлены как константы класса в Page Object?
- [ ] Используются методы из `BasePage` (`wait_for_load`, `click_and_wait`, `fill_and_validate`)?
- [ ] Маркеры `@pytest.mark.e2e`, `@pytest.mark.critical`?
- [ ] Используются фикстуры cleanup (`clean_test_review`, etc.)?
- [ ] Понятные assert сообщения при падении?
- [ ] Тест линейный (нет `if/else` кроме параметризации)?
- [ ] Нет `time.sleep()` (используются `wait_for_*`)?
- [ ] Создание сущностей через `frontend_api_client` для изоляции?
- [ ] Cleanup в фикстурах, а не в теле теста?
- [ ] Используется `wait_for_condition` для ожидания (не hard reload)?

---

## Приоритет селекторов

1. ✅ `data-testid` (лучший вариант)
2. ✅ `id`
3. ✅ Уникальный `className`
4. ✅ `name` (для форм)
5. ⚠️ `text` (последний вариант, хрупкий)

```python
# Примеры правильных селекторов
SUBMIT_BTN = "[data-testid='submit-review']"          # data-testid
EMAIL_INPUT = "input[name='email']"                    # name
DROPDOWN = "div.absolute.z-10[class*='bg-']"          # уникальный className
LEAVE_REVIEW_BTN = "button:has-text('Оставить отзыв')" # text (если нет альтернативы)
SUCCESS_ALERT = ".bg-green-100"                        # className
```

**Избегай:**
- Абсолютные XPath (`/html/body/div[2]/div[1]...`)
- Слишком длинные цепочки классов
- Селекторы, зависящие от структуры DOM

---

## Полезные ссылки

- **Playwright Docs:** https://playwright.dev/python/
- **pytest-playwright:** https://github.com/microsoft/playwright-pytest
- **Frontend Repo:** `/Users/philippkochnov/PycharmProjects/hikers/frontend`
- **Backend Repo:** `/Users/philippkochnov/PycharmProjects/hikers/backend`

---

**Версия:** 3.2.0  
**Дата:** 05.10.2025  
**Автор:** Philippe Kochnov  
**Изменения:** Рефакторинг wait_for_data_update → wait_for_condition. Удалён CDP hard reload, добавлен опциональный обычный reload для стабильности. Параметр retry_with_reload=True для ISR кеша. Тесты обновлены для использования retry с reload.
