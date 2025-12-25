"""
Роутер справочников
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional

from database import get_session
import dependencies
import models
import schemas

router = APIRouter()


@router.get("/all", response_model=schemas.ReferenceData)
async def get_all_references(
        session: Session = Depends(get_session)
):
    """
    Получить все справочники одним запросом
    """
    # Типы контента
    content_types = session.exec(
        select(models.ContentType)
        .where(models.ContentType.is_active == True)
        .order_by(models.ContentType.sort_order)
    ).all()

    # Возрастные рейтинги
    age_ratings = session.exec(
        select(models.AgeRating)
        .where(models.AgeRating.is_active == True)
        .order_by(models.AgeRating.min_age)
    ).all()

    # Тарифы подписки
    subscription_tiers = session.exec(
        select(models.SubscriptionTier)
        .where(models.SubscriptionTier.is_active == True)
        .order_by(models.SubscriptionTier.sort_order)
    ).all()

    # Качество видео
    video_qualities = session.exec(
        select(models.VideoQuality)
        .order_by(models.VideoQuality.sort_order)
    ).all()

    # Жанры
    genres = session.exec(
        select(models.Genre)
        .where(models.Genre.is_active == True)
        .order_by(models.Genre.name)
    ).all()

    # Страны
    countries = session.exec(
        select(models.Country)
        .order_by(models.Country.name)
    ).all()

    return schemas.ReferenceData(
        content_types=content_types,
        age_ratings=age_ratings,
        subscription_tiers=subscription_tiers,
        video_qualities=video_qualities,
        genres=genres,
        countries=countries
    )


# Типы контента
@router.get("/content-types", response_model=List[schemas.ContentTypeResponse])
async def get_content_types(
        active_only: bool = Query(default=True, description="Только активные"),
        session: Session = Depends(get_session)
):
    query = select(models.ContentType)
    if active_only:
        query = query.where(models.ContentType.is_active == True)
    query = query.order_by(models.ContentType.sort_order)
    return session.exec(query).all()


@router.post("/content-types", response_model=schemas.ContentTypeResponse)
async def create_content_type(
        data: schemas.ContentTypeCreate,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    existing = session.exec(
        select(models.ContentType).where(models.ContentType.code == data.code)
    ).first()

    if existing:
        raise HTTPException(400, "Тип контента с таким кодом уже существует")

    db_type = models.ContentType(**data.dict())
    session.add(db_type)
    session.commit()
    session.refresh(db_type)
    return db_type


# Возрастные рейтинги
@router.get("/age-ratings", response_model=List[schemas.AgeRatingResponse])
async def get_age_ratings(
        active_only: bool = Query(default=True),
        session: Session = Depends(get_session)
):
    query = select(models.AgeRating)
    if active_only:
        query = query.where(models.AgeRating.is_active == True)
    query = query.order_by(models.AgeRating.min_age)
    return session.exec(query).all()


# Тарифы подписки
@router.get("/subscription-tiers", response_model=List[schemas.SubscriptionTierResponse])
async def get_subscription_tiers(
        active_only: bool = Query(default=True),
        session: Session = Depends(get_session)
):
    query = select(models.SubscriptionTier)
    if active_only:
        query = query.where(models.SubscriptionTier.is_active == True)
    query = query.order_by(models.SubscriptionTier.sort_order)
    return session.exec(query).all()


# Жанры
@router.get("/genres", response_model=List[schemas.GenreResponse])
async def get_genres(
        active_only: bool = Query(default=True),
        session: Session = Depends(get_session)
):
    query = select(models.Genre)
    if active_only:
        query = query.where(models.Genre.is_active == True)
    query = query.order_by(models.Genre.name)
    return session.exec(query).all()


# Страны
@router.get("/countries", response_model=List[schemas.CountryResponse])
async def get_countries(session: Session = Depends(get_session)):
    return session.exec(
        select(models.Country).order_by(models.Country.name)
    ).all()