from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
import models
from database import get_session
from dependencies import get_current_user

router = APIRouter(prefix="/ratings", tags=["Рейтинги"])


@router.post("/{content_id}")
def add_or_update_rating(
        content_id: int,
        rating_value: float = Query(..., ge=0.5, le=5.0, description="Оценка от 0.5 до 5"),
        review: Optional[str] = Query(None, max_length=1000),
        session: Session = Depends(get_session),
        current_user: models.User = Depends(get_current_user)
):
    """Добавить или обновить рейтинг контента"""
    # Проверяем существование контента
    content = session.get(models.Content, content_id)
    if not content:
        raise HTTPException(404, "Контент не найден")

    # Проверяем, не оценивал ли уже пользователь
    existing_rating = session.exec(
        select(models.Rating).where(
            models.Rating.user_id == current_user.id,
            models.Rating.content_id == content_id
        )
    ).first()

    if existing_rating:
        # Обновляем существующий рейтинг
        existing_rating.rating_value = rating_value
        existing_rating.review = review
        existing_rating.updated_at = datetime.utcnow()
        db_rating = existing_rating
    else:
        # Создаем новый рейтинг
        db_rating = models.Rating(
            user_id=current_user.id,
            content_id=content_id,
            rating_value=rating_value,
            review=review
        )
        session.add(db_rating)

    session.commit()
    session.refresh(db_rating)

    # Пересчитываем средний рейтинг контента
    avg_result = session.exec(
        select(func.avg(models.Rating.rating_value))
        .where(models.Rating.content_id == content_id)
    ).first()

    if avg_result:
        content.imdb_rating = round(avg_result * 2, 1)  # Приводим к шкале 0-10
        session.add(content)
        session.commit()

    return {
        "rating": db_rating,
        "average_rating": content.imdb_rating,
        "total_ratings": session.exec(
            select(func.count(models.Rating.id))
            .where(models.Rating.content_id == content_id)
        ).first()
    }


@router.get("/{content_id}")
def get_content_ratings(
        content_id: int,
        include_reviews: bool = False,
        limit: int = Query(20, le=100),
        offset: int = 0,
        session: Session = Depends(get_session)
):
    """Получить рейтинги для контента"""
    content = session.get(models.Content, content_id)
    if not content:
        raise HTTPException(404, "Контент не найден")

    # Получаем агрегированную статистику
    stats = session.exec(
        select(
            func.count(models.Rating.id).label("total_ratings"),
            func.avg(models.Rating.rating_value).label("average_rating"),
            func.min(models.Rating.rating_value).label("min_rating"),
            func.max(models.Rating.rating_value).label("max_rating")
        ).where(models.Rating.content_id == content_id)
    ).first()

    # Получаем сами рейтинги
    query = select(models.Rating).where(
        models.Rating.content_id == content_id
    ).order_by(models.Rating.created_at.desc())

    if not include_reviews:
        query = query.where(models.Rating.review.is_not(None))

    ratings = session.exec(
        query.offset(offset).limit(limit)
    ).all()

    return {
        "content_id": content_id,
        "content_title": content.title,
        "statistics": stats,
        "ratings": ratings
    }


@router.get("/user/{user_id}")
def get_user_ratings(
        user_id: int,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(get_current_user)
):
    """Получить все рейтинги пользователя"""
    if user_id != current_user.id:
        raise HTTPException(403, "Недостаточно прав")

    ratings = session.exec(
        select(models.Rating)
        .where(models.Rating.user_id == user_id)
        .order_by(models.Rating.updated_at.desc())
    ).all()

    return {
        "user_id": user_id,
        "total_ratings": len(ratings),
        "ratings": ratings
    }