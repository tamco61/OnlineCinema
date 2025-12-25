from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, and_
from typing import List
import models
from database import get_session
from dependencies import get_current_user

router = APIRouter(prefix="/watchlist", tags=["Закладки"])


@router.get("/", response_model=List[models.ContentResponse])
def get_watchlist(
        priority_min: Optional[int] = Query(None, ge=0, le=10),
        priority_max: Optional[int] = Query(None, ge=0, le=10),
        session: Session = Depends(get_session),
        current_user: models.User = Depends(get_current_user)
):
    """Получить список закладок пользователя"""
    query = select(models.Content).join(models.Watchlist).where(
        models.Watchlist.user_id == current_user.id
    )

    if priority_min is not None:
        query = query.where(models.Watchlist.priority >= priority_min)

    if priority_max is not None:
        query = query.where(models.Watchlist.priority <= priority_max)

    query = query.order_by(models.Watchlist.priority.desc())

    results = session.exec(query).all()
    return results


@router.post("/{content_id}")
def add_to_watchlist(
        content_id: int,
        priority: int = Query(0, ge=0, le=10),
        session: Session = Depends(get_session),
        current_user: models.User = Depends(get_current_user)
):
    """Добавить контент в закладки"""
    # Проверяем существование контента
    content = session.get(models.Content, content_id)
    if not content:
        raise HTTPException(404, "Контент не найден")

    # Проверяем, не добавлен ли уже
    existing = session.exec(
        select(models.Watchlist).where(
            and_(
                models.Watchlist.user_id == current_user.id,
                models.Watchlist.content_id == content_id
            )
        )
    ).first()

    if existing:
        raise HTTPException(400, "Контент уже в закладках")

    # Добавляем в закладки
    watchlist_item = models.Watchlist(
        user_id=current_user.id,
        content_id=content_id,
        priority=priority
    )

    session.add(watchlist_item)
    session.commit()
    session.refresh(watchlist_item)

    return {
        "message": "Добавлено в закладки",
        "watchlist_item": watchlist_item
    }


@router.put("/{content_id}")
def update_watchlist_priority(
        content_id: int,
        priority: int = Query(..., ge=0, le=10),
        session: Session = Depends(get_session),
        current_user: models.User = Depends(get_current_user)
):
    """Обновить приоритет в закладках"""
    watchlist_item = session.exec(
        select(models.Watchlist).where(
            and_(
                models.Watchlist.user_id == current_user.id,
                models.Watchlist.content_id == content_id
            )
        )
    ).first()

    if not watchlist_item:
        raise HTTPException(404, "Контент не найден в закладках")

    watchlist_item.priority = priority
    session.add(watchlist_item)
    session.commit()

    return {"message": "Приоритет обновлен", "priority": priority}


@router.delete("/{content_id}")
def remove_from_watchlist(
        content_id: int,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(get_current_user)
):
    """Удалить контент из закладок"""
    watchlist_item = session.exec(
        select(models.Watchlist).where(
            and_(
                models.Watchlist.user_id == current_user.id,
                models.Watchlist.content_id == content_id
            )
        )
    ).first()

    if not watchlist_item:
        raise HTTPException(404, "Контент не найден в закладках")

    session.delete(watchlist_item)
    session.commit()

    return {"message": "Удалено из закладок"}