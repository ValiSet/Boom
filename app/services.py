from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import defaultdict
from models import User, Transaction

import logging
import models, schemas

DAILY_LIMIT = 1000.0
WEEKLY_LIMIT = 5000.0


def check_limits(db: Session, user_id: int, date_from: datetime, date_to: datetime):
    """
        Проверяет, не превышает ли пользователь дневной или недельный лимит расходов
        в заданный период. Лимиты задаются через константы DAILY_LIMIT и WEEKLY_LIMIT.

        Параметры:
            db (Session): Сессия базы данных.
            user_id (int): ID пользователя.
            date_from (datetime): Начальная дата анализа.
            date_to (datetime): Конечная дата анализа.

        Вывод:
            Печатает и логирует предупреждение, если лимиты превышены.
    """
    txs = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.timestamp >= date_from,
        models.Transaction.timestamp <= date_to,
        models.Transaction.amount < 0
    ).all()

    daily_sums = defaultdict(float)
    for tx in txs:
        day = tx.timestamp.date()
        daily_sums[day] += abs(tx.amount)

    for day, amount in daily_sums.items():
        if amount > DAILY_LIMIT:
            logging.warning(f"User {user_id} exceeded daily limit on {day}: spent {amount} > {DAILY_LIMIT}")
            print(f"User {user_id} exceeded daily limit on {day}: spent {amount} > {DAILY_LIMIT}")

    week_start = date_to - timedelta(days=7)
    weekly_txs = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.timestamp >= week_start,
        models.Transaction.timestamp <= date_to,
        models.Transaction.amount < 0
    ).all()
    weekly_total = sum(abs(tx.amount) for tx in weekly_txs)

    if weekly_total > WEEKLY_LIMIT:
        logging.warning(f"User {user_id} exceeded weekly limit in period {week_start.date()} - {date_to.date()}: spent {weekly_total} > {WEEKLY_LIMIT}")
        print(f"User {user_id} exceeded weekly limit in period {week_start.date()} - {date_to.date()}: spent {weekly_total} > {WEEKLY_LIMIT}")


def import_transactions(db: Session, tx_list: list[schemas.TransactionIn]):
    """
        Импортирует список транзакций в базу данных. Если пользователь не существует,
        он автоматически создаётся.

        Параметры:
            db (Session): Сессия базы данных.
            tx_list (list[TransactionIn]): Список транзакций для импорта.

        Поведение:
            - Создаёт новых пользователей, если они не найдены.
            - Добавляет транзакции в базу.
            - Выполняет коммит по завершении.
    """
    seen_users = set()
    for tx in tx_list:
        if tx.user_id not in seen_users:
            user_exists = db.query(User).filter(User.id == tx.user_id).first()
            if not user_exists:
                db.add(User(id=tx.user_id, name=f"User {tx.user_id}"))
            seen_users.add(tx.user_id)

        transaction = Transaction(
            id=tx.id,
            user_id=tx.user_id,
            amount=tx.amount,
            currency=tx.currency,
            category=tx.category,
            timestamp=tx.timestamp,
        )
        db.add(transaction)
    db.commit()


def get_user_stats(db: Session, user_id: int, date_from: datetime, date_to: datetime, category: str = None):
    """
        Возвращает статистику расходов пользователя за указанный период,
        включая сумму расходов, разбивку по категориям и средний расход в день.

        Параметры:
            db (Session): Сессия базы данных.
            user_id (int): ID пользователя.
            date_from (datetime): Начальная дата анализа.
            date_to (datetime): Конечная дата анализа.
            category (str, optional): Категория транзакций для фильтрации (по умолчанию — все категории).

        Returns:
            dict: {
                "total_spent": float — общая сумма расходов,
                "by_category": dict — разбивка по категориям,
                "daily_average": float — средний расход в день
            }
    """
    query = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.timestamp >= date_from,
        models.Transaction.timestamp <= date_to,
        models.Transaction.amount < 0
    )
    if category:
        query = query.filter(models.Transaction.category == category)
    transactions = query.all()
    total_spent = sum(-tx.amount for tx in transactions if tx.amount < 0)
    category_totals = defaultdict(float)
    for tx in query:
        category_totals[tx.category or "Other"] += abs(tx.amount)

    days = max((date_to - date_from).days, 1)
    avg_per_day = total_spent / days

    return {
        "total_spent": round(total_spent, 2),
        "by_category": {k: round(v, 2) for k, v in category_totals.items()},
        "daily_average": round(avg_per_day, 2)
    }
