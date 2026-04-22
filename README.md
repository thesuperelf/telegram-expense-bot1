# Telegram Expense Bot

Telegram-бот на `aiogram 3` для учета личных расходов.

## Что умеет

- Добавление расхода по шагам: сумма -> категория -> комментарий
- Навигация в FSM через кнопки `Назад` и `Отмена`
- Просмотр последних расходов
- Статистика по периодам
- Сравнение периодов
- Управление пользовательскими категориями
- Удаление расхода по ID

## Стек

- Python 3.12+
- aiogram 3
- SQLAlchemy 2
- SQLite / aiosqlite
- python-dotenv

## Настройка

Создайте файл `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=sqlite+aiosqlite:///expenses.db
```

Установите зависимости:

```bash
pip install -r requirements.txt
```

Запуск:

```bash
python bot.py
```

## Структура

```text
bot.py
config.py
database/
handlers/
keyboards/
middlewares/
services/
states/
utils/
```

## Примечания

- `expenses.db` создается автоматически при первом запуске.
- `.env`, `expenses.db` и `__pycache__` исключены через `.gitignore`.
