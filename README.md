# GeoApp

Приложение для работы с географическими точками на карте. Предоставляет REST API для создания точек, обмена сообщениями и поиска контента в заданном радиусе от указанных координат.

> ✨ **Особенность**: при создании точки автоматически определяется её реальный адрес (через [DaData](https://dadata.ru)) и сохраняется в фоне с помощью Celery.

---

## 🚀 Быстрый запуск

### Требования
- Docker и Docker Compose

### Запуск через Docker

```bash
# 1. Собрать образ
docker-compose build

# 2. Запустить всё (веб, Celery, Redis, PostGIS)
docker-compose up
```

Приложение будет доступно по адресу:  
👉 **http://localhost:8000**

👉 API: http://localhost:8000/api/docs/  
👉 Wagtail CMS: http://localhost:8000/cms/  

> 🔑 **Суперпользователь создаётся автоматически** при первом запуске (логин/пароль из `.env.local`).

---

## 🧪 Тестирование

Запуск тестов внутри контейнера:

```bash
docker-compose exec web python manage.py test points
```

---

## 📚 Документация API

Интерактивная документация доступна по адресу:  
🔗 **http://localhost:8000/api/docs/**

Там вы можете:
- Просматривать все эндпоинты
- Авторизоваться через JWT
- Отправлять запросы прямо из браузера

> <img width="1897" height="957" alt="Swagger UI" src="https://github.com/user-attachments/assets/e2ebf443-c33c-4a29-8ca6-fe36878a7bb2" />

---

## 🔐 Аутентификация

Все эндпоинты защищены JWT-токеном.

### Получение токена

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pass123"}'
```

Пример ответа:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.yyyyy",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx"
}
```

> 💡 **Swagger UI**:  
> 1. Откройте **POST /api/auth/token/** → **Try it out** → заполните поля → **Execute**  
> 2. Нажмите **Authorize** → введите `Bearer <access_token>` → **Authorize**

---

## 📍 Эндпоинты

### 1. Создание точки

```bash
curl -X POST http://localhost:8000/api/points/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Red Square","latitude":55.7539,"longitude":37.6208}'
```

**Параметры:**
- `name` — название точки (строка)
- `latitude` — широта (**-90 ≤ lat ≤ 90**)
- `longitude` — долгота (**-180 ≤ lon ≤ 180**)

> ⏳ Адрес (`address`) подтягивается **асинхронно** через Celery и DaData.  
> Через несколько секунд он появится в ответе `/api/points/search/`.

> ❌ Ошибки валидации:
> ```json
> {"latitude":["Latitude must be between -90 and 90."]}
> ```

> 💡 **Swagger UI**:  
> Откройте **POST /api/points/** → **Try it out** → заполните поля → **Execute**  
> <img width="1889" height="952" alt="Create Point" src="https://github.com/user-attachments/assets/e5e75971-3e04-4ff1-bc54-1368e7b7bd5d" />

---

### 2. Создание сообщения к точке

```bash
curl -X POST http://localhost:8000/api/points/messages/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"point_id":1,"text":"Hello from Moscow!"}'
```

**Параметры:**
- `point_id` — ID существующей точки
- `text` — текст сообщения

> 💡 **Swagger UI**:  
> <img width="1898" height="953" alt="Create Message" src="https://github.com/user-attachments/assets/53c8099e-b535-4b43-86ee-683af7b0ffd4" />

---

### 3. Поиск точек в радиусе

```bash
curl -X GET "http://localhost:8000/api/points/search/?latitude=55.75&longitude=37.62&radius=2" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Параметры:**
- `latitude` — широта центра поиска (**-90 ≤ lat ≤ 90**)
- `longitude` — долгота центра поиска (**-180 ≤ lon ≤ 180**)
- `radius` — радиус поиска в километрах (**radius > 0**)

**Ответ:**
```json
[
  {
    "id": 1,
    "name": "Red Square",
    "address": "г Москва, Красная площадь",  // ← Автоматически из DaData!
    "created_at": "2025-01-15T12:00:00Z",
    "distance_km": 0.452
  }
]
```

> 💡 **Swagger UI**: используйте форму параметров под эндпоинтом **GET /api/points/search/**.  
> <img width="1899" height="954" alt="Search Points" src="https://github.com/user-attachments/assets/f8ccb15c-9f03-404a-97b5-940627c10317" />

---

### 4. Поиск сообщений в радиусе

```bash
curl -X GET "http://localhost:8000/api/messages/search/?latitude=55.75&longitude=37.62&radius=2" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Ответ:**
```json
[
  {
    "id": 1,
    "text": "Hello from Moscow!",
    "created_at": "2025-01-15T12:05:00Z",
    "point_name": "Red Square",
    "point_latitude": 55.7539,
    "point_longitude": 37.6208,
    "author_username": "admin"
  }
]
```

> 💡 **Swagger UI**:  
> <img width="1898" height="957" alt="Search Messages" src="https://github.com/user-attachments/assets/ec947b45-61c1-4c6e-82d3-85a83393fe9c" />

---

## 🖥️ Wagtail CMS

### Управление данными
- **Points** и **Messages** доступны напрямую в админке:  
- При создании точки через CMS **адрес также подтягивается автоматически**.
- Все поля редактируются.

### Создание страниц
Вы можете создавать **GeoPage** — страницы с:
- HTML-описанием
- Привязкой к одной или нескольким точкам

> 🧹 Меню очищено: нет вложенности, только нужные пункты.

---

## Как работает обратное геокодирование

1. Пользователь создаёт точку через API или Wagtail.
2. Точка сохраняется в БД.
3. Вызывается fetch_address_for_point.delay(point.id).
4. Celery сериализует задачу в JSON и кладёт в Redis.
5. Celery-воркер забирает задачу, делает запрос к DaData.
6. Получает адрес → обновляет point.address.

> DaData ищет адреса в радиусе 100м от созданной точки, присваивается ближайщий

---

## 🛠 Техническое описание

### Стек технологий
- **Python** 3.12
- **Django** 6.0
- **Django REST Framework** 3.16
- **GeoDjango + PostGIS** — гео-запросы
- **Wagtail 7+** — CMS
- **Celery + Redis** — фоновые задачи
- **dadata-py** — обратное геокодирование
- **djangorestframework-simplejwt** — аутентификация
- **drf-spectacular** — OpenAPI/Swagger
- **PostgreSQL + PostGIS** — база данных

### Архитектура
- **Модель `Point`** содержит:
  - Геометрию (`PointField(srid=4326)`)
  - Реальный адрес (`address = TextField(null=True, blank=True)`)
- **Модель `Message`** связана с точкой и автором.
- **Celery worker** выполняет фоновую задачу `fetch_address_for_point` после создания точки.
- **Redis** используется как брокер сообщений.
- **Поиск** реализован через GeoDjango (`Distance`, `__distance_lte`).
- **Координаты и радиус** проходят строгую валидацию.

### Docker-инфраструктура
- `web` — Django-сервер
- `celery` — фоновый воркер
- `redis` — очередь задач
- `db` — PostGIS-база
