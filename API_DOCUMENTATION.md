# API Документация

## Приложение Loyalty

### Генерация кода лояльности

**POST** `/api/loyalty/code/generate/`

**Заголовки:**
```
Authorization: Token <клиентский_токен>
```

**Ответ (успешно):**
```json
{
  "id": 1,
  "code": "123456",
  "created_at": "2023-08-01T12:00:00Z",
  "expires_at": "2023-08-01T12:15:00Z",
  "is_active": true
}
```

**Ответ (ошибка):**
```json
{
  "error": "Только клиенты могут генерировать коды лояльности"
}
```

### Генерация кода бесплатного кофе

**POST** `/api/loyalty/code/generate-free/`

**Заголовки:**
```
Authorization: Token <клиентский_токен>
```

**Ответ (успешно):**
```json
{
  "id": 2,
  "code": "789012",
  "created_at": "2023-08-01T12:00:00Z",
  "expires_at": "2023-08-01T12:15:00Z",
  "is_active": true
}
```

**Ответ (ошибка):**
```json
{
  "error": "Недостаточно кофе для получения бесплатного",
  "coffee_count": 5,
  "coffee_needed": 7
}
```

### Проверка кода лояльности

**POST** `/api/loyalty/code/verify/`

**Заголовки:**
```
Authorization: Token <токен_бариста>
```

**Параметры запроса:**
```json
{
  "code": "123456"
}
```

**Ответ (успешно):**
```json
{
  "success": true,
  "user": {
    "id": 3,
    "phone": "+79998887766",
    "first_name": "Анна",
    "last_name": "Петрова",
    "points": 150,
    "coffee_count": 12,
    "coffee_to_next_free": 2
  }
}
```

**Ответ (ошибка):**
```json
{
  "error": "Неверный код"
}
```

### Создание транзакции лояльности

**POST** `/api/loyalty/transaction/create/`

**Заголовки:**
```
Authorization: Token <токен_бариста>
```

**Параметры запроса:**
```json
{
  "code": "123456",
  "amount": 300,
  "transaction_type": "earning",
  "use_points": false,
  "coffee_quantity": 2
}
```

**Важно:** Поле `amount` теперь принимает значение в целых денежных единицах (сомах), а не в копейках. Например, 300 означает 300 сомов, что будет преобразовано в 30000 копеек при сохранении в базу данных.

**Параметры:**
- `code` — код лояльности клиента (получается через `/api/loyalty/code/verify/`)
- `amount` — сумма транзакции в целых денежных единицах (сомах)
- `transaction_type` — тип транзакции: "earning" (начисление) или "spending" (списание)
- `use_points` — использовать баллы для оплаты (только для "spending")
- `coffee_quantity` — количество кофе в заказе (по умолчанию 0, увеличивает счетчик только при покупке кофе)

**Ответ (успешно):**
```json
{
  "transaction": {
    "id": 1,
    "user": 3,
    "user_info": {
      "id": 3,
      "phone": "+79998887766",
      "role": "client",
      "first_name": "Анна",
      "last_name": "Петрова"
    },
    "barista": 2,
    "barista_info": {
      "id": 2,
      "phone": "+79991112233",
      "role": "barista",
      "first_name": "Иван",
      "last_name": "Иванов"
    },
    "coffee_shop": 1,
    "transaction_type": "earning",
    "amount": 30000,
    "amount_in_currency": 300,
    "points": 15,
    "created_at": "2023-08-01T12:30:00Z"
  },
  "user": {
    "id": 3,
    "points": 165,
    "coffee_count": 13,
    "coffee_to_next_free": 1
  }
}
```

**Ответ (ошибка):**
```json
{
  "error": "Только бариста может создавать транзакции"
}
```

### История транзакций

**GET** `/api/loyalty/transactions/`

**Заголовки:**
```
Authorization: Token <токен_пользователя>
```

**Ответ:**
```json
[
  {
    "id": 1,
    "user": 3,
    "user_info": {
      "id": 3,
      "phone": "+79998887766",
      "role": "client",
      "first_name": "Анна",
      "last_name": "Петрова"
    },
    "barista": 2,
    "barista_info": {
      "id": 2,
      "phone": "+79991112233",
      "role": "barista",
      "first_name": "Иван",
      "last_name": "Иванов"
    },
    "coffee_shop": 1,
    "transaction_type": "earning",
    "amount": 30000,
    "amount_in_currency": 300,
    "points": 15,
    "created_at": "2023-08-01T12:30:00Z"
  },
  // ... другие транзакции ...
]
```

**Примечания:**
- Клиенты видят только свои транзакции
- Бариста видят только транзакции своей кофейни
- Менеджеры видят все транзакции
- Поле `amount` хранится в копейках
- Поле `amount_in_currency` отображает сумму в целых денежных единицах (сомах) 