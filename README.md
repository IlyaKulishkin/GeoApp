# GeoApp

Приложение для работы с географическими точками на карте. Предоставляет REST API для создания точек, обмена сообщениями и поиска контента в заданном радиусе от указанных координат.

---

## 🚀 Быстрый запуск

### Требования
- Docker (рекомендуется)
- Или Python 3.12+, GDAL, GEOS, PROJ, Postgres, Wagtail

### Запуск через Docker

```bash
# 1. Собрать образ
docker-compose build

# 2. Создать миграции
docker-compose run --rm web python manage.py makemigrations

# 3. Применить миграции
docker-compose run --rm web python manage.py migrate

# 4. Создать суперпользователя (опционально)
docker-compose run --rm web python manage.py createsuperuser

# 5. Запустить
docker-compose up
```

Приложение будет доступно по адресу:  
👉 **http://localhost:8000**


---

## 🧪 Тестирование

Запуск тестов внутри контейнера:

```bash
docker exec geoapp python manage.py test points
```

---

## 📚 Документация API

Интерактивная документация доступна по адресу:  
🔗 **http://localhost:8000/api/docs/**

Там вы можете:
- Просматривать все эндпоинты
- Авторизоваться через JWT
- Отправлять запросы прямо из браузера

> <img width="1897" height="957" alt="image" src="https://github.com/user-attachments/assets/e2ebf443-c33c-4a29-8ca6-fe36878a7bb2" />

---

## 🔐 Аутентификация

Все эндпоинты защищены JWT-токеном.

### Получение токена

```cmd
curl -X POST http://localhost:8000/api/auth/token/ -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin\"}"
```

Пример ответа:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.yyyyy",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx"
}
```

> 💡 **Swagger UI**: Откройте эндпоинт **POST /api/auth/token/** → нажмите **Try it out** → заполните поля → **Execute** и получите токен, потом нажмите кнопку **Authorize** → введите `<access_token>` → **Authorize**.  
> <img width="1892" height="951" alt="image" src="https://github.com/user-attachments/assets/c6719a70-d6b5-49cd-a4d7-f139addb0456" />
> <img width="1884" height="951" alt="image" src="https://github.com/user-attachments/assets/633abc4e-6ba0-4260-acf8-90a4338a1e6d" />

---

## 📍 Эндпоинты

### 1. Создание точки

```cmd
curl -X POST http://localhost:8000/api/points/ -H "Authorization: Bearer YOUR_ACCESS_TOKEN" -H "Content-Type: application/json" -d "{\"name\":\"Red Square\",\"latitude\":55.7539,\"longitude\":37.6208}"
```

**Параметры:**
- `name` — название точки (строка)
- `latitude` — широта (**-90 ≤ lat ≤ 90**)
- `longitude` — долгота (**-180 ≤ lon ≤ 180**)

> ❌ Попытка отправить `latitude=1000` вернёт ошибку:
> ```json
> {"latitude":["Latitude must be between -90 and 90."]}
> ```

> 💡 **Swagger UI**: откройте эндпоинт **POST /api/points/** → нажмите **Try it out** → заполните поля → **Execute**.  
> <img width="1889" height="952" alt="image" src="https://github.com/user-attachments/assets/e5e75971-3e04-4ff1-bc54-1368e7b7bd5d" />

---

### 2. Создание сообщения к точке

```cmd
curl -X POST http://localhost:8000/api/points/messages/ -H "Authorization: Bearer YOUR_ACCESS_TOKEN" -H "Content-Type: application/json" -d "{\"point_id\":1,\"text\":\"Hello from Moscow!\"}"
```

**Параметры:**
- `point_id` — ID существующей точки
- `text` — текст сообщения

> 💡 **Swagger UI**:
> <img width="1898" height="953" alt="image" src="https://github.com/user-attachments/assets/53c8099e-b535-4b43-86ee-683af7b0ffd4" />

---

### 3. Поиск точек в радиусе

```cmd
curl -X GET "http://localhost:8000/api/points/search/?latitude=55.75&longitude=37.62&radius=2" -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
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
    "created_at": "2025-01-15T12:00:00Z",
    "distance_km": 0.452
  }
]
```

> 💡 **Swagger UI**: используйте форму параметров под эндпоинтом **GET /api/points/search/**.  
> <img width="1899" height="954" alt="image" src="https://github.com/user-attachments/assets/f8ccb15c-9f03-404a-97b5-940627c10317" />

---

### 4. Поиск сообщений в радиусе

```cmd
curl -X GET "http://localhost:8000/api/messages/search/?latitude=55.75&longitude=37.62&radius=2" -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
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

> 💡 **Swagger UI**: аналогично, через форму параметров.  
> <img width="1898" height="957" alt="image" src="https://github.com/user-attachments/assets/ec947b45-61c1-4c6e-82d3-85a83393fe9c" />

---

## 🛠 Техническое описание

### Стек технологий
- **Python** 3.12
- **Django** 6.0
- **Django REST Framework** 3.16
- **GeoDjango** (с поддержкой Spatialite)
- **djangorestframework-simplejwt** — аутентификация
- **drf-spectacular** — генерация OpenAPI/Swagger
- **SQLite + Spatialite** — база данных

### Архитектура
- Модель `Point` содержит географическую точку (`PointField(srid=4326)`) и метаданные.
- Модель `Message` связана с точкой и автором.
- Все запросы требуют аутентификации.
- Поиск реализован через функции GeoDjango (`Distance`, `__distance_lte`).
- Координаты и радиус проходят строгую валидацию перед обработкой.
