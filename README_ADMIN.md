# Recipe Book Admin Panel

## Установка и запуск

### Требования
- Python 3.8+
- pip

### 1. Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

### 2. Конфигурация

Отредактируйте файл `backend/.env`:

```
CLAUDE_API_KEY=sk-ant-... (ваш ключ Claude API)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
JWT_SECRET_KEY=ваш-секретный-ключ
```

### 3. Запуск сервера

```bash
cd backend
python main.py
```

Или с помощью uvicorn:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Сервер будет доступен по адресу: `http://localhost:8000`

### 4. Доступ к админ-панели

- **URL**: http://localhost:8000/admin/
- **Логин**: admin (по умолчанию, можно изменить в .env)
- **Пароль**: admin123 (по умолчанию, можно изменить в .env)
- **API Документация**: http://localhost:8000/docs

## API Endpoints

### Authentication
- `POST /api/auth/login` - Вход в систему
- `GET /api/auth/verify` - Проверка токена

### Recipes
- `GET /api/recipes/` - Получить все рецепты (с фильтрацией)
- `GET /api/recipes/{recipe_id}` - Получить рецепт
- `POST /api/recipes/` - Создать рецепт
- `PUT /api/recipes/{recipe_id}` - Обновить рецепт
- `DELETE /api/recipes/{recipe_id}` - Удалить рецепт
- `POST /api/recipes/{recipe_id}/image` - Загрузить изображение

### Categories & Countries
- `GET /api/recipes/categories/list` - Получить все категории
- `POST /api/recipes/categories/` - Добавить категорию
- `GET /api/recipes/countries/list` - Получить все страны

## Структура проекта

```
backend/
├── main.py              # FastAPI приложение
├── config.py            # Конфигурация
├── requirements.txt     # Python зависимости
├── .env                 # Переменные окружения
├── models/
│   └── recipe.py       # Моделиданных
├── routes/
│   ├── auth.py         # Аутентификация
│   └── recipes.py      # Рецепты CRUD
└── agents/
    └── recipe_agent.py # Claude AI агент

admin/
├── login.html          # Страница входа
├── index.html          # Админ-панель
├── create-recipe.html  # Форма создания
├── css/
│   └── style.css       # Стили админки
└── js/
    ├── api-client.js   # API клиент
    └── auth.js         # Аутентификация
```

## Примечания

- Рецепты хранятся в JSON файле: `backend/data/recipes.json`
- Изображения сохраняются в папке: `images/`
- По умолчанию приложение использует In-Memory хранилище, которое сбрасывается при перезагрузке
- Для production используйте обычную базу данных (PostgreSQL, MongoDB и т.д.)
