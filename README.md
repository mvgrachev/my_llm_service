# LLM Service

API сервис для работы с LLM (Large Language Models).

## Требования

- Python 3.11+
- pip
- Docker (для запуска Redis)

## Установка Redis

```bash
# Запуск Redis через Docker
docker run -d --name redis-test -p 6379:6379 redis:7-alpine
```

Redis будет доступен по адресу `localhost:6379`.

Проверка работы Redis:

```bash
docker exec redis-test redis-cli ping
```

## Установка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
python3 main.py
```

## Структура проекта

```
my_llm_service/
├── api/          # API endpoints
├── services/     # Business logic
├── llm/          # LLM integration
├── cache/        # Cache management
├── config/       # Configuration
├── tests/        # Tests
├── main.py       # Entry point
├── cli.py        # CLI interface
├── requirements.txt
└── README.md
```

## Использование

После запуска сервер будет доступен по адресу `http://localhost:8000`

## Примеры API-запросов через curl

Отправка запроса к роуту `/chat`:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Mitsubishi Pajero, 181 лс"}'
```

Ожидаемый ответ:

```json
{
  "model": "Mitsubishi Pajero",
  "price": "1 200 000 ₽"
}
```

Повторный запрос с тем же сообщением будет обработан из кеша Redis без повторного вызова LLM.

## Примеры вызова сервиса из командной строки

### С использованием CLI-скрипта

```bash
# Простой вызов с сообщением
python3 main.py chat "Mitsubishi Pajero, 181 лс"

# Вызов с явным указанием сообщения
python3 main.py chat -m "Mitsubishi Pajero, 181 лс"

# Получить результат в формате JSON
python3 main.py chat -m "Mitsubishi Pajero, 181 лс" -j
```
