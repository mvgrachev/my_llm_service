# Тестовый отчет

## Сценарии тестирования

| № | Сценарий | Описание | Результат |
|---|----------|----------|-----------|
| 1 | Вызов справки | Запуск с ключом `-h` для отображения справки | ✅ Успех |
| 2 | Недопустимый ключ | Запуск без обязательного ключа `-m` | ⚠️ Ошибка валидации |
| 3 | Успешный вызов (первый запуск) | Отправка запроса к LLM без кэша | ✅ Успех (cache miss) |
| 4 | Повторный вызов (кэш) | Повторная отправка того же запроса | ✅ Успех (cache hit) |
| 5 | Пустое сообщение | Отправка пустой строки в качестве сообщения | ⚠️ Ошибка валидации Pydantic |
| 6 | Недоступность модели (retry + fallback) | Неверный API ключ для LLM | ✅ Retry 3 раза + fallback |

---

## Детальное описание сценариев

### Сценарий 1: Вызов справки

**Команда:**
```bash
python3 main.py chat -h
```

**Описание:** Проверка доступности справочной информации о команде `chat`.

**Результат:**
```
usage: main.py chat [-h] -m MESSAGE [-j]

options:
  -h, --help            show this help message and exit
  -m MESSAGE, --message MESSAGE
                        Message to send to the LLM
  -j, --json            Output result in JSON format
```

---

### Сценарий 2: Недопустимый ключ

**Команда:**
```bash
python3 main.py chat -b
```

**Описание:** Попытка запуска без обязательного параметра `-m/--message`.

**Результат:**
```
usage: main.py chat [-h] -m MESSAGE [-j]
main.py chat: error: the following arguments are required: -m/--message
```

---

### Сценарий 3: Успешный вызов (первый запуск)

**Команда:**
```bash
python3 main.py chat -m "Mitsubishi Pajero, 185 лс" -j
```

**Описание:** Первичный запрос к LLM с отключенным кэшем. Проверка логирования, генерации запроса к LLM и записи в Redis.

**Логи:**
```
2026-07-26 21:04:01,351 - llm_service.chat - INFO - [REQUEST] Time: 2026-07-26 21:04:01, Message: Mitsubishi Pajero, 185 лс...
2026-07-26 21:04:01,355 - llm_service.cache - INFO - [CACHE Redis] Miss for key: chat:f4051e12ae2866ead520c035ce6876dc...
2026-07-26 21:04:01,355 - llm_service.chat - INFO - [CACHE MISS] Key: chat:f4051e12ae2866ead520c035ce6876dc
2026-07-26 21:04:01,356 - llm_service.chat - INFO - [PROMPT] Temperature: 0.3, Max tokens: 1500
2026-07-26 21:04:01,356 - llm_service.deepseek - INFO - [DEEPSEEK] Generating response for input: Mitsubishi Pajero, 185 лс...
2026-07-26 21:04:01,357 - llm_service.deepseek - INFO - [DEEPSEEK] Prompt: Рассчитай стоимость КАСКО в зависимости от марки автомобиля и количества лошидиных сил. Укажи базовую стоимость и учет коэффициентов. 

Формат ответа: JSON. Обязательные поля: model (марка автомобиля)...
2026-07-26 21:04:09,836 - llm_service.deepseek - INFO - [DEEPSEEK] Response received: {"model": "Mitsubishi Pajero", "price": 120000}...
2026-07-26 21:04:09,839 - llm_service.chat - INFO - [LLM RESPONSE] Raw response: {"model": "Mitsubishi Pajero", "price": 120000}...
2026-07-26 21:04:09,842 - llm_service.chat - INFO - [RESPONSE] Model: Mitsubishi Pajero, Price: 120000.0, Time: 2026-07-26 21:04:09
```

**Ответ:**
```json
{
  "model": "Mitsubishi Pajero",
  "price": 120000.0
}
```

---

### Сценарий 4: Повторный вызов (кэш)

**Команда:**
```bash
python3 main.py chat -m "Mitsubishi Pajero, 185 лс" -j
```

**Описание:** Повторная отправка того же запроса. Проверка чтения из кэша Redis.

**Логи:**
```
2026-07-26 21:05:58,533 - llm_service.chat - INFO - [REQUEST] Time: 2026-07-26 21:05:58, Message: Mitsubishi Pajero, 185 лс...
2026-07-26 21:05:58,536 - llm_service.cache - INFO - [CACHE Redis] Hit for key: chat:f4051e12ae2866ead520c035ce6876dc...
2026-07-26 21:05:58,536 - llm_service.chat - INFO - [CACHE HIT] Key: chat:f4051e12ae2866ead520c035ce6876dc, Response: {"model": "Mitsubishi Pajero", "price": 120000.0}
```

**Ответ:**
```json
{
  "model": "Mitsubishi Pajero",
  "price": 120000.0
}
```

---

### Сценарий 5: Пустое сообщение

**Команда:**
```bash
python3 main.py chat -m "" -j
```

**Описание:** Проверка валидации пустого сообщения.

**Ответ:**
```json
{
  "success": false,
  "error": "1 validation error for ChatRequest\nmessage\n  String should have at least 1 character [type=string_too_short, input_value='', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.13/v/string_too_short",
  "message": "Failed to process request"
}
```

---

### Сценарий 6: Недоступность модели (retry + fallback)

**Команда:**
```bash
python3 main.py chat -m "Mitsubishi Pajero, 121 лс" -j
```

**Описание:** Проверка механизма повторных попыток (retry) и fallback при недоступности LLM из-за неверного API ключа.

**Логи (фрагменты):**
```
2026-07-27 00:30:57,161 - llm_service.chat - INFO - [REQUEST] Time: 2026-07-27 00:30:57, Message: Mitsubishi Pajero, 121 лс...
2026-07-27 00:30:57,166 - llm_service.cache - INFO - [CACHE Redis] Miss for key: chat:f1c73fa04d34cea338e33531afcb1a30...
2026-07-27 00:30:57,167 - llm_service.chat - INFO - [CACHE MISS] Key: chat:f1c73fa04d34cea338e33531afcb1a30
2026-07-27 00:30:57,168 - llm_service.chat - INFO - [PROMPT] Temperature: 0.3, Max tokens: 1500
2026-07-27 00:30:57,171 - llm_service.deepseek - INFO - [DEEPSEEK] Generating response for input: Mitsubishi Pajero, 121 лс...
2026-07-27 00:30:57,174 - llm_service.deepseek - INFO - [DEEPSEEK] Prompt: Рассчитай стоимость КАСКО в зависимости от марки автомобиля и количества лошидиных сил. Укажи базовую стоимость и учет коэффициентов. 

Формат ответа: JSON. Обязательные поля: model (марка автомобиля)...
2026-07-27 00:30:57,322 - llm_service.deepseek - ERROR - [DEEPSEEK] Error during generation: rpc error: code = Unauthenticated desc = Unknown api key 'AQVN****98iI (CE9D1A49)'
2026-07-27 00:30:57,322 - llm_service.chat - ERROR - [ERROR] Attempt 1/3: llm generation error: rpc error: code = unauthenticated desc = unknown api key 'aqvn****98ii (ce9d1a49)'
2026-07-27 00:30:57,323 - llm_service.chat - WARNING - [RETRY] Waiting 1 seconds before retry...

... (повторные попытки с увеличением задержки: 1с → 3с → 5с) ...

2026-07-27 00:31:07,543 - llm_service.chat - INFO - [PROMPT] Temperature: 0.3, Max tokens: 1500
2026-07-27 00:31:07,543 - llm_service.deepseek - INFO - [DEEPSEEK] Generating response for input: Mitsubishi Pajero, 121 лс...
2026-07-27 00:31:07,653 - llm_service.deepseek - ERROR - [DEEPSEEK] Error during generation: rpc error: code = Unauthenticated desc = Unknown api key 'AQVN****98iI (CE9D1A49)'
2026-07-27 00:31:07,653 - llm_service.chat - ERROR - [ERROR] Attempt 4/3: llm generation error: rpc error: code = unauthenticated desc = unknown api key 'aqvn****98ii (ce9d1a49)'
2026-07-27 00:31:07,654 - llm_service.chat - WARNING - [FAILED] LLM processing error after 3 attempts: LLM generation error: rpc error: code = Unauthenticated desc = Unknown api key 'AQVN****98iI (CE9D1A49)'
```

**Ответ (fallback):**
```json
{
  "model": "Ошибка",
  "price": 0.0
}
```

---

## Резюме

Все сценарии выполнены успешно:
- ✅ Справка работает корректно
- ⚠️ Валидация обязательных параметров работает
- ✅ LLM генерирует ответы и записывает в кэш
- ✅ Кэш Redis работает: повторные запросы возвращаются из кэша
- ⚠️ Валидация пустых сообщений корректно отклоняет запросы
- ✅ Механизм retry (3 попытки) и fallback работает при недоступности LLM
