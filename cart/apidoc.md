# Cart API (Orders)

Базовый префикс: /api/
Аутентификация: Token (Authorization: Token <token>)

Роли и доступ:
- Клиент (client/anon_client): создаёт заказ, видит свои.
- Бариста/Старший бариста: видят заказы своего заведения, принимают заказ.
- Менеджер: видит заказы своего заведения.

Суммы в копейках; дублируем суммы в сомах для удобства.

## Справочник значений
- delivery_type: pickup | delivery
- payment_method: cash | card | online (заглушка)
- payment_status: pending | paid | failed
- status: new | accepted | in_progress | ready | completed | cancelled

---

## Создать заказ
POST /api/cart/orders/
(Только клиент)

Body
```
{
  "coffee_shop_id": 1,
  "delivery_type": "pickup",
  "payment_method": "cash",
  "customer_comment": "Меньше льда, пожалуйста",
  "delivery_address": "г. Бишкек ...",
  "use_points": true,
  "items": [
    { "variant_id": 10, "quantity": 2, "is_coffee": true },
    { "variant_id": 15, "quantity": 1, "is_coffee": false }
  ]
}
```
Примечания:
- Если `delivery_type = delivery`, поле `delivery_address` обязательно.
- `use_points` — флаг «списать бонусы». При true от суммы заказа будет вычтено максимально доступное количество баллов клиента (1 балл = 1 сом). Списание и начисление фактически происходят только после подтверждения заказа бариста/старшим бариста (anti‑fraud).

Успех 201 (пример):
```
{
  "id": 123,
  "user": 45,
  "coffee_shop": 1,
  "delivery_type": "pickup",
  "payment_method": "cash",
  "payment_status": "pending",
  "status": "new",
  "items_total_amount": 45000,
  "discount_amount": 0,
  "final_amount": 45000,
  "items_total_amount_som": 450.0,
  "final_amount_som": 450.0,
  "customer_comment": "Меньше льда, пожалуйста",
  "delivery_address": null,
  "items": [
    { "id": 1, "item_variant": 10, "name_snapshot": "Капучино", "portion_snapshot": "Стандарт (300 мл)", "quantity": 2, "unit_price": 15000, "total_price": 30000, "is_coffee": true },
    { "id": 2, "item_variant": 15, "name_snapshot": "Чизкейк",  "portion_snapshot": "Порция",              "quantity": 1, "unit_price": 15000, "total_price": 15000, "is_coffee": false }
  ],
  "created_at": "2025-08-11T01:23:45Z"
}
```
Ошибки 400 (примеры):
```
{ "delivery_address": "Адрес обязателен для доставки" }
{ "coffee_shop_id": "Заведение не найдено" }
{ "items": "Список позиций не может быть пустым" }
```

---

## Список заказов
GET /api/cart/orders/list/

- Клиент: только свои заказы.
- Бариста/Старший бариста: заказы своего `coffee_shop`.
- Менеджер: заказы своего `coffee_shop`.

Ответ 200: список заказов (см. формат выше), отсортирован по created_at DESC.

---

## Принять заказ
PATCH /api/cart/orders/{id}/accept/
(Только barista/senior_barista того же заведения)

Действие: меняет статус new → accepted и применяет бонусную логику:
- Если при создании заказа был флаг `use_points=true`, списывает запланированное количество баллов у клиента.
- Начисляет баллы по текущему рангу клиента (кэшбек % от суммы), вычисленные при создании заказа.
- Увеличивает `coffee_count` на количество кофейных позиций заказа.
- Увеличивает `total_spent` клиента на `final_amount` заказа (в копейках).

Ответ 200: объект заказа со статусом accepted.
Ошибки: 403 (чужое заведение/нет прав), 400 (статус не new).

## Примечания
- Оплата online пока заглушка, payment_status остаётся pending.
- Поле `is_coffee` у позиции используется для бонусной логики (увеличение `coffee_count`).
