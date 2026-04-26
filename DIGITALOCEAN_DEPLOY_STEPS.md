# DigitalOcean Deploy: пошагово

Цель: получить рабочий сайт на поддомене, например:

```text
https://recipes.yourdomain.com
```

Там пользователи смогут смотреть рецепты, регистрироваться, логиниться, добавлять свои рецепты и восстанавливать пароль через email.

## 1. Подготовить поддомен

В DNS панели домена создай запись:

```text
Type: A
Name: recipes
Value: IP_ТВОЕГО_DROPLET
```

Пример:

```text
Type: A
Name: recipes
Value: 123.123.123.123
```

Подожди 5-30 минут. Иногда DNS обновляется дольше.

## 2. Зайти на droplet

На своём компьютере:

```bash
ssh root@IP_ТВОЕГО_DROPLET
```

Пример:

```bash
ssh root@123.123.123.123
```

## 3. Установить Docker, Git, Nginx и Certbot

На droplet:

```bash
apt update
apt install -y docker.io docker-compose git nginx certbot python3-certbot-nginx
systemctl enable docker
systemctl start docker
```

## 4. Скачать проект

На droplet:

```bash
cd /opt
git clone https://github.com/msrig/Recipe-Book.git
cd Recipe-Book
```

## 5. Создать production env

```bash
cp .env.production.example .env.production
nano .env.production
```

Минимально заполни:

```env
OPENAI_API_KEY=твой_openai_key
OPENAI_MODEL=gpt-5.2

ADMIN_USERNAME=mama
ADMIN_PASSWORD=придумай_сложный_пароль
JWT_SECRET_KEY=очень_длинная_случайная_строка

PUBLIC_BASE_URL=https://recipes.yourdomain.com
```

Сохранить в nano:

```text
Ctrl + O
Enter
Ctrl + X
```

## 6. Запустить приложение

```bash
docker-compose up -d --build
```

Проверить:

```bash
docker-compose ps
curl http://127.0.0.1:8000/health
```

Должно вернуться:

```json
{"status":"healthy"}
```

## 7. Настроить Nginx

Создай конфиг:

```bash
nano /etc/nginx/sites-available/recipe-book
```

Вставь, заменив домен:

```nginx
server {
    server_name recipes.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Включи сайт:

```bash
ln -s /etc/nginx/sites-available/recipe-book /etc/nginx/sites-enabled/recipe-book
nginx -t
systemctl reload nginx
```

## 8. Включить HTTPS

```bash
certbot --nginx -d recipes.yourdomain.com
```

Certbot спросит email и согласие. Отвечай по инструкции.

После этого сайт должен открываться:

```text
https://recipes.yourdomain.com
```

## 9. Перенести users.json

Важно: `backend/data/users.json` не лежит в Git, потому что там пользователи и хеши паролей.

На своём компьютере из папки проекта:

```bash
scp backend/data/users.json root@IP_ТВОЕГО_DROPLET:/tmp/users.json
```

На droplet:

```bash
docker ps
```

Найди имя контейнера. Потом:

```bash
docker cp /tmp/users.json ИМЯ_КОНТЕЙНЕРА:/var/data/backend/data/users.json
docker-compose restart
```

Пример имени контейнера может быть:

```text
recipe-book-recipe-book-1
```

Тогда команда будет:

```bash
docker cp /tmp/users.json recipe-book-recipe-book-1:/var/data/backend/data/users.json
docker-compose restart
```

## 10. Настроить email для сброса пароля

Чтобы реально приходили письма, нужен SMTP: Gmail, SendGrid, Mailgun, Resend или другой провайдер.

В `.env.production` заполни:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=твой_smtp_login
SMTP_PASSWORD=твой_smtp_password
SMTP_FROM_EMAIL=recipes@yourdomain.com
SMTP_USE_TLS=true
PASSWORD_RESET_EXPIRE_MINUTES=60
```

После изменения:

```bash
docker-compose restart
```

## 11. Проверить сайт

Открой:

```text
https://recipes.yourdomain.com
```

Потом:

```text
https://recipes.yourdomain.com/admin/login.html
```

Проверь:

- вход;
- регистрацию;
- добавление рецепта;
- профиль;
- сброс пароля;
- фильтр по пользователю.

## Как обновлять сайт потом

Когда новые изменения запушены на GitHub, на droplet:

```bash
cd /opt/Recipe-Book
git pull
docker-compose up -d --build
```

## Что нельзя пушить в Git

Не пушить:

```text
backend/.env
.env.production
backend/data/users.json
```

Они должны жить только локально или на сервере.
