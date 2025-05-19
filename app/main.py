from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from fastapi import Query, HTTPException
from middleware import catch_exceptions_middleware
from datetime import datetime
from schemas import UserResponse

import database
import models
import services
import import_data
import schemas

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
app.middleware("http")(catch_exceptions_middleware)


def get_db():
    """
        Создает и предоставляет сессию базы данных для запроса.

        Yields:
            Session: Сессия SQLAlchemy для взаимодействия с базой данных.
    """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def load_data():
    """
        Загружает данные транзакций при запуске приложения,
        если база данных пуста. Использует функцию импорта данных из JSON.
        Также автоматически создает пользователей, если их нет.
    """
    db = next(get_db())
    if db.query(models.Transaction).count() == 0:
        tx_list = import_data.load_transactions()
        services.import_transactions(db, tx_list)


@app.get("/users/{user_id}/stats", response_model=schemas.StatsResponse)
def user_stats(
    user_id: int,
    from_date: str = Query(..., alias="from"),
    to_date: str = Query(..., alias="to"),
    category: str = Query(None),
    db: Session = Depends(get_db)
):
    """
        Получает статистику по транзакциям пользователя за указанный период.

        Параметры:
            user_id (int): ID пользователя.
            from_date (str): Начальная дата периода в ISO-формате (alias: 'from').
            to_date (str): Конечная дата периода в ISO-формате (alias: 'to').
            category (str, optional): Фильтр по категории транзакций.
            db (Session): Сессия базы данных, передается через Depends.

        Returns:
            StatsResponse: Объект с суммой расходов, разбивкой по категориям и дневным средним.

        Raises:
            HTTPException: 400 — если дата некорректна или 'from' позже 'to'.
            HTTPException: 404 — если пользователь не найден.
        """
    try:
        date_from = datetime.fromisoformat(from_date)
        date_to = datetime.fromisoformat(to_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный формат даты, ожидался ISO формат")
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="Дата 'from' не может быть позже даты 'to'")

    # Получаем пользователя
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Делаем логику
    services.check_limits(db, user.id, date_from, date_to)
    return services.get_user_stats(db, user.id, date_from, date_to, category=category)

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
        Возвращает информацию о пользователе по его ID.

        Параметры:
            user_id (int): ID пользователя.
            db (Session): Сессия базы данных, передается через Depends.

        Returns:
            UserResponse: Информация о пользователе (id и name).

        Raises:
            HTTPException: 404 — если пользователь не найден.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user