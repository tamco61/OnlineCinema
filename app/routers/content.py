"""
Роутер контента
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlmodel import Session, select, func, and_, or_, join
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from database import get_session
import dependencies
import models
import schemas

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=schemas.PaginatedResponse)
async def get_content_list(
        filters: schemas.ContentFilters = Depends(),
        pagination: schemas.PaginationParams = Depends(),
        session: Session = Depends(get_session),
        current_user: Optional[models.User] = Depends(dependencies.get_current_user)
):
    """
    Получение списка контента с фильтрами
    """
    # Базовый запрос
    query = select(models.Content)

    # Применяем фильтры
    if filters.query:
        search_term = f"%{filters.query}%"
        query = query.where(
            or_(
                models.Content.title.ilike(search_term),
                models.Content.description.ilike(search_term),
                models.Content.director.ilike(search_term),
                models.Content.writer.ilike(search_term)
            )
        )

    if filters.content_type_id:
        query = query.where(models.Content.content_type_id == filters.content_type_id)

    if filters.genre_ids:
        for genre_id in filters.genre_ids[:5]:  # Ограничиваем количество жанров
            query = query.join(models.ContentGenre).where(
                models.ContentGenre.genre_id == genre_id
            )

    if filters.country_ids:
        for country_id in filters.country_ids[:5]:
            query = query.join(models.ContentCountry).where(
                models.ContentCountry.country_id == country_id
            )

    if filters.age_rating_ids:
        query = query.where(models.Content.age_rating_id.in_(filters.age_rating_ids))

    if filters.min_year:
        query = query.where(models.Content.release_year >= filters.min_year)

    if filters.max_year:
        query = query.where(models.Content.release_year <= filters.max_year)

    if filters.min_rating:
        query = query.where(
            or_(
                models.Content.imdb_rating >= filters.min_rating,
                models.Content.kinopoisk_rating >= filters.min_rating,
                models.Content.our_rating >= filters.min_rating
            )
        )

    if filters.max_duration:
        query = query.where(models.Content.duration_minutes <= filters.max_duration)

    if filters.featured_only:
        query = query.where(models.Content.is_featured == True)

    if filters.popular_only:
        query = query.where(models.Content.is_popular == True)

    if filters.new_only:
        week_ago = datetime.utcnow() - timedelta(days=7)
        query = query.where(
            and_(
                models.Content.is_new == True,
                models.Content.created_at >= week_ago
            )
        )

    if filters.available_only:
        now = datetime.utcnow()
        query = query.where(
            and_(
                models.Content.is_available == True,
                models.Content.available_from <= now,
                or_(
                    models.Content.available_to.is_(None),
                    models.Content.available_to >= now
                )
            )
        )

    if filters.subscription_only is not None:
        query = query.where(models.Content.requires_subscription == filters.subscription_only)

    # Сортировка
    sort_field = getattr(models.Content, filters.sort_by, models.Content.created_at)
    if filters.sort_order == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())

    # Получаем общее количество
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).first()

    # Пагинация
    offset = (pagination.page - 1) * pagination.size
    query = query.offset(offset).limit(pagination.size)

    # Выполняем запрос
    content_list = session.exec(query).all()

    # Добавляем информацию о пользователе
    enhanced_content = []
    for item in content_list:
        enhanced_item = schemas.ContentResponse.from_orm(item)

        # Проверяем, находится ли в закладках
        if current_user:
            in_watchlist = session.exec(
                select(models.Watchlist).where(
                    and_(
                        models.Watchlist.user_id == current_user.id,
                        models.Watchlist.content_id == item.id
                    )
                )
            ).first()
            enhanced_item.in_watchlist = in_watchlist is not None

            # Получаем прогресс просмотра
            watch_history = session.exec(
                select(models.WatchHistory).where(
                    and_(
                        models.WatchHistory.user_id == current_user.id,
                        models.WatchHistory.content_id == item.id
                    )
                ).order_by(models.WatchHistory.watched_at.desc()).limit(1)
            ).first()

            if watch_history:
                enhanced_item.watch_progress = watch_history.progress_percentage

        enhanced_content.append(enhanced_item)

    return schemas.PaginatedResponse(
        items=enhanced_content,
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=(total + pagination.size - 1) // pagination.size,
        has_next=offset + len(enhanced_content) < total,
        has_prev=pagination.page > 1
    )


@router.get("/{content_id}", response_model=schemas.ContentDetailResponse)
async def get_content_detail(
        content_id: int = Path(..., title="ID контента", ge=1),
        session: Session = Depends(get_session),
        current_user: Optional[models.User] = Depends(dependencies.get_current_user)
):
    """
    Получение детальной информации о контенте
    """
    content = session.get(models.Content, content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Контент не найден"
        )

    # Проверяем доступ
    try:
        dependencies.check_content_access(content, current_user)
    except HTTPException as e:
        if current_user and current_user.is_staff:
            # Staff может видеть недоступный контент
            pass
        else:
            raise e

    # Увеличиваем счетчик просмотров
    content.views_count += 1
    session.add(content)
    session.commit()
    session.refresh(content)

    # Получаем связанные данные
    response = schemas.ContentDetailResponse.from_orm(content)

    # Получаем жанры
    genres = session.exec(
        select(models.Genre)
        .join(models.ContentGenre)
        .where(models.ContentGenre.content_id == content_id)
    ).all()
    response.genres = genres

    # Получаем страны
    countries = session.exec(
        select(models.Country)
        .join(models.ContentCountry)
        .where(models.ContentCountry.content_id == content_id)
    ).all()
    response.countries = countries

    # Получаем актеров
    actors = session.exec(
        select(models.Actor)
        .join(models.ContentActor)
        .where(models.ContentActor.content_id == content_id)
        .order_by(models.ContentActor.is_main.desc())
        .limit(20)
    ).all()
    response.actors = actors

    # Получаем сезоны (для сериалов)
    if content.content_type_rel.code == "series":
        seasons = session.exec(
            select(models.Season)
            .where(models.Season.content_id == content_id)
            .order_by(models.Season.season_number)
        ).all()
        response.seasons = seasons

    # Получаем сводку по рейтингам
    ratings_summary = session.exec(
        select(
            func.count(models.Rating.id).label("total_ratings"),
            func.avg(models.Rating.rating_value).label("average_rating"),
            func.count(models.Rating.review.is_not(None)).label("review_count")
        ).where(models.Rating.content_id == content_id)
    ).first()

    if ratings_summary:
        # Распределение оценок
        rating_dist = session.exec(
            select(
                models.Rating.rating_value,
                func.count(models.Rating.id).label("count")
            )
            .where(models.Rating.content_id == content_id)
            .group_by(models.Rating.rating_value)
            .order_by(models.Rating.rating_value)
        ).all()

        distribution = {str(rating): count for rating, count in rating_dist}

        response.ratings_summary = schemas.RatingsSummary(
            total_ratings=ratings_summary[0] or 0,
            average_rating=float(ratings_summary[1]) if ratings_summary[1] else 0,
            rating_distribution=distribution,
            review_count=ratings_summary[2] or 0,
            last_rating_date=None  # Можно добавить
        )

    # Получаем рейтинг пользователя (если авторизован)
    if current_user:
        user_rating = session.exec(
            select(models.Rating).where(
                and_(
                    models.Rating.user_id == current_user.id,
                    models.Rating.content_id == content_id
                )
            )
        ).first()

        if user_rating:
            response.user_rating = schemas.RatingResponse.from_orm(user_rating)

        # Проверяем закладки
        in_watchlist = session.exec(
            select(models.Watchlist).where(
                and_(
                    models.Watchlist.user_id == current_user.id,
                    models.Watchlist.content_id == content_id
                )
            )
        ).first()
        response.in_watchlist = in_watchlist is not None

        # Получаем прогресс просмотра
        watch_history = session.exec(
            select(models.WatchHistory).where(
                and_(
                    models.WatchHistory.user_id == current_user.id,
                    models.WatchHistory.content_id == content_id
                )
            ).order_by(models.WatchHistory.watched_at.desc()).limit(1)
        ).first()

        if watch_history:
            response.watch_progress = watch_history.progress_percentage

    return response


@router.get("/{content_id}/similar", response_model=List[schemas.ContentResponse])
async def get_similar_content(
        content_id: int = Path(..., title="ID контента", ge=1),
        limit: int = Query(default=10, le=50),
        session: Session = Depends(get_session),
        current_user: Optional[models.User] = Depends(dependencies.get_current_user)
):
    """
    Получение похожего контента
    """
    content = session.get(models.Content, content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Контент не найден"
        )

    # Ищем контент с теми же жанрами
    genre_subquery = select(models.ContentGenre.genre_id).where(
        models.ContentGenre.content_id == content_id
    )

    similar_query = select(models.Content).distinct().join(models.ContentGenre).where(
        and_(
            models.Content.id != content_id,
            models.Content.is_available == True,
            models.Content.content_type_id == content.content_type_id,
            models.ContentGenre.genre_id.in_(genre_subquery)
        )
    ).order_by(
        models.Content.our_rating.desc().nullslast(),
        models.Content.imdb_rating.desc().nullslast()
    ).limit(limit)

    similar = session.exec(similar_query).all()
    return similar


@router.get("/{content_id}/episodes", response_model=List[schemas.EpisodeResponse])
async def get_content_episodes(
        content_id: int = Path(..., title="ID контента", ge=1),
        season_number: Optional[int] = Query(None, ge=1),
        session: Session = Depends(get_session),
        current_user: Optional[models.User] = Depends(dependencies.get_current_user)
):
    """
    Получение эпизодов контента (для сериалов)
    """
    content = session.get(models.Content, content_id)
    if not content or content.content_type_rel.code != "series":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сериал не найден"
        )

    # Проверяем доступ
    try:
        dependencies.check_content_access(content, current_user)
    except HTTPException as e:
        if current_user and current_user.is_staff:
            pass
        else:
            raise e

    query = select(models.Episode).where(
        models.Episode.content_id == content_id
    )

    if season_number:
        query = query.join(models.Season).where(
            models.Season.season_number == season_number
        )

    query = query.order_by(
        models.Season.season_number,
        models.Episode.episode_number
    )

    episodes = session.exec(query).all()

    # Добавляем прогресс просмотра
    enhanced_episodes = []
    for episode in episodes:
        enhanced_episode = schemas.EpisodeResponse.from_orm(episode)

        if current_user:
            watch_history = session.exec(
                select(models.WatchHistory).where(
                    and_(
                        models.WatchHistory.user_id == current_user.id,
                        models.WatchHistory.episode_id == episode.id
                    )
                ).order_by(models.WatchHistory.watched_at.desc()).limit(1)
            ).first()

            if watch_history:
                enhanced_episode.watch_progress = watch_history.progress_percentage

        enhanced_episodes.append(enhanced_episode)

    return enhanced_episodes


@router.post("/", response_model=schemas.ContentResponse)
async def create_content(
        content_data: schemas.ContentCreate,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    """
    Создание нового контента (только для staff)
    """
    # Проверяем существование типа контента
    content_type = session.get(models.ContentType, content_data.content_type_id)
    if not content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Тип контента не найден"
        )

    # Проверяем возрастной рейтинг
    age_rating = session.get(models.AgeRating, content_data.age_rating_id)
    if not age_rating:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Возрастной рейтинг не найден"
        )

    # Создаем контент
    db_content = models.Content(
        **content_data.dict(exclude={"genre_ids", "country_ids", "actor_ids"})
    )

    session.add(db_content)
    session.flush()  # Получаем ID

    # Добавляем жанры
    for genre_id in content_data.genre_ids[:10]:  # Ограничиваем количество
        genre = session.get(models.Genre, genre_id)
        if genre:
            session.add(models.ContentGenre(
                content_id=db_content.id,
                genre_id=genre_id
            ))

    # Добавляем страны
    for country_id in content_data.country_ids[:5]:
        country = session.get(models.Country, country_id)
        if country:
            session.add(models.ContentCountry(
                content_id=db_content.id,
                country_id=country_id
            ))

    # Добавляем актеров
    for actor_id in content_data.actor_ids[:20]:
        actor = session.get(models.Actor, actor_id)
        if actor:
            session.add(models.ContentActor(
                content_id=db_content.id,
                actor_id=actor_id
            ))

    session.commit()
    session.refresh(db_content)

    logger.info(f"Создан новый контент: {db_content.title} (ID: {db_content.id})")
    return db_content


@router.put("/{content_id}", response_model=schemas.ContentResponse)
async def update_content(
        content_id: int,
        content_update: schemas.ContentUpdate,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    """
    Обновление контента (только для staff)
    """
    content = session.get(models.Content, content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Контент не найден"
        )

    update_data = content_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(content, key, value)

    content.updated_at = datetime.utcnow()
    session.add(content)
    session.commit()
    session.refresh(content)

    logger.info(f"Контент обновлен: {content.title} (ID: {content.id})")
    return content


@router.delete("/{content_id}")
async def delete_content(
        content_id: int,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    """
    Удаление контента (только для staff)
    """
    content = session.get(models.Content, content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Контент не найден"
        )

    # Мягкое удаление
    content.is_available = False
    content.updated_at = datetime.utcnow()
    session.add(content)
    session.commit()

    logger.info(f"Контент удален: {content.title} (ID: {content.id})")

    return schemas.SuccessResponse(
        message="Контент удален"
    )


@router.get("/featured/today", response_model=List[schemas.ContentResponse])
async def get_todays_featured(
        limit: int = Query(default=10, le=50),
        session: Session = Depends(get_session),
        current_user: Optional[models.User] = Depends(dependencies.get_current_user)
):
    """
    Получение рекомендованного контента на сегодня
    """
    # Алгоритм рекомендаций:
    # 1. Featured контент
    # 2. Новинки
    # 3. Популярное
    # 4. Высокорейтинговое

    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # Featured контент
    featured = session.exec(
        select(models.Content).where(
            and_(
                models.Content.is_featured == True,
                models.Content.is_available == True,
                models.Content.available_from <= now,
                or_(
                    models.Content.available_to.is_(None),
                    models.Content.available_to >= now
                )
            )
        ).order_by(func.random()).limit(limit // 2)
    ).all()

    # Если недостаточно featured, добавляем новинки
    if len(featured) < limit:
        remaining = limit - len(featured)

        new_content = session.exec(
            select(models.Content).where(
                and_(
                    models.Content.is_new == True,
                    models.Content.created_at >= week_ago,
                    models.Content.is_available == True,
                    ~models.Content.id.in_([c.id for c in featured])
                )
            ).order_by(models.Content.created_at.desc()).limit(remaining)
        ).all()

        featured.extend(new_content)

    # Если все еще недостаточно, добавляем популярное
    if len(featured) < limit:
        remaining = limit - len(featured)

        popular = session.exec(
            select(models.Content).where(
                and_(
                    models.Content.is_popular == True,
                    models.Content.is_available == True,
                    ~models.Content.id.in_([c.id for c in featured])
                )
            ).order_by(
                models.Content.views_count.desc(),
                models.Content.watch_count.desc()
            ).limit(remaining)
        ).all()

        featured.extend(popular)

    # Если все еще недостаточно, добавляем высокорейтинговое
    if len(featured) < limit:
        remaining = limit - len(featured)

        high_rated = session.exec(
            select(models.Content).where(
                and_(
                    models.Content.is_available == True,
                    models.Content.our_rating >= 8.0,
                    ~models.Content.id.in_([c.id for c in featured])
                )
            ).order_by(
                models.Content.our_rating.desc().nullslast(),
                func.random()
            ).limit(remaining)
        ).all()

        featured.extend(high_rated)

    return featured


@router.get("/search/suggestions")
async def search_suggestions(
        query: str = Query(..., min_length=2, max_length=100),
        limit: int = Query(default=10, le=50),
        session: Session = Depends(get_session)
):
    """
    Получение поисковых подсказок
    """
    search_term = f"%{query}%"

    # Поиск по названию
    titles = session.exec(
        select(models.Content.title)
        .where(models.Content.title.ilike(search_term))
        .where(models.Content.is_available == True)
        .order_by(
            models.Content.views_count.desc(),
            models.Content.title
        )
        .limit(limit)
    ).all()

    # Поиск по жанрам
    genres = session.exec(
        select(models.Genre.name)
        .where(models.Genre.name.ilike(search_term))
        .order_by(models.Genre.name)
        .limit(5)
    ).all()

    # Поиск по актерам
    actors = session.exec(
        select(models.Actor.full_name)
        .where(models.Actor.full_name.ilike(search_term))
        .order_by(models.Actor.popularity.desc())
        .limit(5)
    ).all()

    return {
        "titles": titles,
        "genres": genres,
        "actors": actors,
        "query": query
    }