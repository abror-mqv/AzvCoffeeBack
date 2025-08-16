# Документация API (menue)

## Эндпоинты меню

### Для управляющего (требуется токен управляющего)

#### 1. Получить древовидное меню (категории с товарами)
**GET** `/api/menu-tree/`

**Заголовок:**
```
Authorization: Token <token>
```
**Ответ:**
```json
[
  {
    "id": 1,
    "name": "Кофе",
    "description": "Классические кофейные напитки",
    "image": null,
    "items": [
      {
        "id": 1,
        "category": {"id": 1, "name": "Кофе", ...},
        "name": "Эспрессо",
        "description": "Классический итальянский эспрессо",
        "ingredients": "Кофе арабика, вода",
        "image": null,
        "volume": "40 мл",  // Для обратной совместимости (объем варианта по умолчанию)
        "price": "120.00",  // Для обратной совместимости (цена варианта по умолчанию)
        "variants": [
          {
            "id": 1,
            "portion": {
              "id": 1,
              "name": "Стандартный",
              "volume": 40,
              "unit": "мл"
            },
            "price": "120.00",
            "is_default": true
          }
        ],
        "is_active": true,
        "created_at": "2024-06-07T12:00:00Z",
        "updated_at": "2024-06-07T12:00:00Z"
      },
      ...
    ]
  },
  ...
]
```
- Возвращаются все категории, у каждой — список товаров (items).
- Фильтрация по наличию/отсутствию производится на стороне клиента (is_active).
- Каждый товар содержит список вариантов (variants) с разными порциями и ценами.
- Для обратной совместимости сохранены поля volume и price (берутся из варианта по умолчанию).

#### 2. CRUD для позиций меню

##### Создать новую позицию
**POST** `/api/menu-items/`

**Заголовок:**
```
Authorization: Token <token>
Content-Type: application/json
```
**Тело запроса:**
```json
{
  "category_id": 1,
  "name": "Латте",
  "description": "Кофе с молоком",
  "ingredients": "Кофе, молоко",
  "is_active": true,
  "variants": [
    {
      "portion_id": 1,
      "price": "180.00",
      "is_default": true
    },
    {
      "portion_id": 2,
      "price": "220.00",
      "is_default": false
    }
  ]
}
```
**Пример успешного ответа:**
```json
{
  "id": 6,
  "category": {"id": 1, "name": "Кофе", ...},
  "name": "Латте",
  "description": "Кофе с молоком",
  "ingredients": "Кофе, молоко",
  "image": null,
  "volume": "250 мл",  // Из варианта по умолчанию
  "price": "180.00",   // Из варианта по умолчанию
  "variants": [
    {
      "id": 1,
      "portion": {
        "id": 1,
        "name": "Средний",
        "volume": 250,
        "unit": "мл"
      },
      "price": "180.00",
      "is_default": true
    },
    {
      "id": 2,
      "portion": {
        "id": 2,
        "name": "Большой",
        "volume": 350,
        "unit": "мл"
      },
      "price": "220.00",
      "is_default": false
    }
  ],
  "is_active": true,
  "created_at": "2024-06-07T12:00:00Z",
  "updated_at": "2024-06-07T12:00:00Z"
}
```

##### Обновить только фотографию
**PATCH** `/api/menu-items/<id>/image/`

**Заголовок:**
```
Authorization: Token <token>
Content-Type: multipart/form-data
```
**Тело запроса:**
- Поле `image` — файл изображения (jpeg, png и т.д.)

**Пример успешного ответа:**
```json
{
  "id": 6,
  "category": {"id": 1, "name": "Кофе", ...},
  "name": "Латте",
  "description": "Кофе с молоком",
  "ingredients": "Кофе, молоко",
  "image": "http://localhost:8000/media/menu_items/latte.jpg",
  "volume": "250 мл",
  "price": "180.00",
  "variants": [...],
  "is_active": true,
  "created_at": "2024-06-07T12:00:00Z",
  "updated_at": "2024-06-07T12:10:00Z"
}
```

##### Редактировать позицию
**PUT/PATCH** `/api/menu-items/<id>/`

**Заголовок:**
```
Authorization: Token <token>
Content-Type: application/json
```
**Тело запроса:** (любые поля MenuItem, например)
```json
{
  "name": "Латте с корицей",
  "description": "Латте с добавлением корицы",
  "ingredients": "Кофе, молоко, корица",
  "variants": [
    {
      "id": 1,  // ID существующего варианта для обновления
      "price": "190.00"
    },
    {
      "portion_id": 3,  // Новый вариант (без ID)
      "price": "260.00",
      "is_default": false
    }
  ]
}
```
**Пример успешного ответа:**
```json
{
  "id": 6,
  "category": {"id": 1, "name": "Кофе", ...},
  "name": "Латте с корицей",
  "description": "Латте с добавлением корицы",
  "ingredients": "Кофе, молоко, корица",
  "image": "http://localhost:8000/media/menu_items/latte.jpg",
  "volume": "250 мл",
  "price": "190.00",
  "variants": [
    {
      "id": 1,
      "portion": {
        "id": 1,
        "name": "Средний",
        "volume": 250,
        "unit": "мл"
      },
      "price": "190.00",
      "is_default": true
    },
    {
      "id": 2,
      "portion": {
        "id": 2,
        "name": "Большой",
        "volume": 350,
        "unit": "мл"
      },
      "price": "220.00",
      "is_default": false
    },
    {
      "id": 3,
      "portion": {
        "id": 3,
        "name": "Гигант",
        "volume": 450,
        "unit": "мл"
      },
      "price": "260.00",
      "is_default": false
    }
  ],
  "is_active": true,
  "created_at": "2024-06-07T12:00:00Z",
  "updated_at": "2024-06-07T12:10:00Z"
}
```

##### Удалить позицию
**DELETE** `/api/menu-items/<id>/`

**Заголовок:**
```
Authorization: Token <token>
```
**Ответ (успех):**
```
204 No Content
```

##### Остальные операции
- **GET /api/menu-items/** — получить все позиции (плоский список)
- **GET /api/menu-items/<id>/** — получить одну позицию

#### 3. Управление порциями

##### Получить список порций
**GET** `/api/portions/`

**Заголовок:**
```
Authorization: Token <token>
```
**Пример успешного ответа:**
```json
[
  {
    "id": 1,
    "name": "Стандартный",
    "volume": 40,
    "unit": "мл"
  },
  {
    "id": 2,
    "name": "Средний",
    "volume": 250,
    "unit": "мл"
  },
  {
    "id": 3,
    "name": "Большой",
    "volume": 350,
    "unit": "мл"
  }
]
```

##### Создать новую порцию
**POST** `/api/portions/`

**Заголовок:**
```
Authorization: Token <token>
Content-Type: application/json
```
**Тело запроса:**
```json
{
  "name": "Гигант",
  "volume": 450,
  "unit": "мл"
}
```
**Пример успешного ответа:**
```json
{
  "id": 4,
  "name": "Гигант",
  "volume": 450,
  "unit": "мл"
}
```

##### Редактировать порцию
**PUT/PATCH** `/api/portions/<id>/`

##### Удалить порцию
**DELETE** `/api/portions/<id>/`

#### 4. Управление вариантами товаров

##### Получить варианты товара
**GET** `/api/menu-items/<menu_item_id>/variants/`

**Заголовок:**
```
Authorization: Token <token>
```
**Пример успешного ответа:**
```json
[
  {
    "id": 1,
    "portion": {
      "id": 1,
      "name": "Средний",
      "volume": 250,
      "unit": "мл"
    },
    "price": "180.00",
    "is_default": true
  },
  {
    "id": 2,
    "portion": {
      "id": 2,
      "name": "Большой",
      "volume": 350,
      "unit": "мл"
    },
    "price": "220.00",
    "is_default": false
  }
]
```

##### Добавить вариант товара
**POST** `/api/menu-items/<menu_item_id>/variants/`

**Заголовок:**
```
Authorization: Token <token>
Content-Type: application/json
```
**Тело запроса:**
```json
{
  "portion_id": 3,
  "price": "260.00",
  "is_default": false
}
```
**Пример успешного ответа:**
```json
{
  "id": 3,
  "portion": {
    "id": 3,
    "name": "Гигант",
    "volume": 450,
    "unit": "мл"
  },
  "price": "260.00",
  "is_default": false
}
```

##### Редактировать вариант товара
**PUT/PATCH** `/api/variants/<id>/`

##### Удалить вариант товара
**DELETE** `/api/variants/<id>/`

---

## Примечания
- Все ответы в формате JSON.
- Для всех эндпоинтов требуется токен управляющего (см. документацию core).
- Для загрузки/отображения изображений используется поле `image` (может быть null).
- Категория возвращается как объект (id, name, ...).
- Каждый товар может иметь несколько вариантов с разными порциями и ценами.
- Один из вариантов должен быть отмечен как вариант по умолчанию (is_default=true).
- Для обратной совместимости сохранены поля volume и price (берутся из варианта по умолчанию). 