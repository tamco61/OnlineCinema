"""
Роутер аналитики и статистики
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func, and_, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
import logging
import json

from database import get_session
import dependencies
import models
import schemas

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/popular", response_model=List[schemas.PopularContentResponse])
async def get_popular_content(
        days: int = Query(default=7, ge=1, le=365, description="За сколько дней анализировать"),
        limit: int = Query(default=10, le=100),
        content_type_id: Optional[int] = None,
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    """
    Получение самого популярного контента за период
    """
    since_date = datetime.utcnow() - timedelta(days=days)

    # Базовый запрос для статистики просмотров
    query = select(
        models.Content,
        func.count(models.WatchHistory.id).label("views"),
        func.sum(models.WatchHistory.watch_duration_seconds).label("watch_time"),
        func.avg(models.Rating.rating_value).label("avg_rating")
    ).join(
        models.WatchHistory,
        models.WatchHistory.content_id == models.Content.id,
        isouter=True
    ).join(
        models.Rating,
        models.Rating.content_id == models.Content.id,
        isouter=True
    ).where(
        models.WatchHistory.watched_at >= since_date
    )

    if content_type_id:
        query = query.where(models.Content.content_type_id == content_type_id)

    query = query.group_by(models.Content.id).order_by(
        func.count(models.WatchHistory.id).desc()
    ).limit(limit)

    results = session.exec(query).all()

    popular_content = []
    for content, views, watch_time, avg_rating in results:
        # Вычисляем процент завершения
        completed_views = session.exec(
            select(func.count(models.WatchHistory.id)).where(
                and_(
                    models.WatchHistory.content_id == content.id,
                    models.WatchHistory.progress_percentage >= 90,
                    models.WatchHistory.watched_at >= since_date
                )
            )
        ).first() or 0

        completion_rate = (completed_views / views * 100) if views > 0 else 0

        popular_content.append(schemas.PopularContentResponse(
            content=schemas.ContentShortResponse.from_orm(content),
            views=views or 0,
            watch_time_minutes=(watch_time or 0) // 60,
            average_rating=float(avg_rating) if avg_rating else None,
            completion_rate=completion_rate
        ))

    return popular_content


@router.get("/user-activity", response_model=schemas.UserActivityResponse)
async def get_user_activity_stats(
        start_date: Optional[datetime] = Query(None, description="Начальная дата (ISO 8601)"),
        end_date: Optional[datetime] = Query(None, description="Конечная дата (ISO 8601)"),
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    """
    Статистика активности пользователей за период
    """
    # Устанавливаем даты по умолчанию
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    if start_date >= end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Дата начала должна быть раньше даты окончания"
        )

    # Новые пользователи
    new_users = session.exec(
        select(func.count(models.User.id)).where(
            models.User.created_at.between(start_date, end_date)
        )
    ).first() or 0

    # Активные пользователи (с хотя бы одним просмотром)
    active_users = session.exec(
        select(func.count(func.distinct(models.WatchHistory.user_id))).where(
            models.WatchHistory.watched_at.between(start_date, end_date)
        )
    ).first() or 0

    # Возвращающиеся пользователи
    returning_users = session.exec(
        select(func.count(func.distinct(models.WatchHistory.user_id))).where(
            and_(
                models.WatchHistory.watched_at.between(start_date, end_date),
                models.User.created_at < start_date
            )
        )
    ).first() or 0

    # Общее время просмотра
    total_watch_time = session.exec(
        select(func.sum(models.WatchHistory.watch_duration_seconds)).where(
            models.WatchHistory.watched_at.between(start_date, end_date)
        )
    ).first() or 0

    # Среднее время просмотра на пользователя
    avg_watch_time = total_watch_time / active_users if active_users > 0 else 0

    # Самый популярный контент
    popular_content_query = select(
        models.Content,
        func.count(models.WatchHistory.id).label("views")
    ).join(
        models.WatchHistory,
        models.WatchHistory.content_id == models.Content.id
    ).where(
        models.WatchHistory.watched_at.between(start_date, end_date)
    ).group_by(
        models.Content.id
    ).order_by(
        func.count(models.WatchHistory.id).desc()
    ).limit(5)

    popular_content = []
    for content, views in session.exec(popular_content_query).all():
        popular_content.append(schemas.PopularContentResponse(
            content=schemas.ContentShortResponse.from_orm(content),
            views=views,
            watch_time_minutes=0,  # Можно добавить расчет
            average_rating=None,
            completion_rate=0
        ))

    return schemas.UserActivityResponse(
        period={"start": start_date, "end": end_date},
        new_users=new_users,
        active_users=active_users,
        returning_users=returning_users,
        total_watch_hours=total_watch_time / 3600,
        average_watch_time_per_user=avg_watch_time / 3600,
        most_popular_content=popular_content
    )


@router.get("/daily-stats")
async def get_daily_stats(
        days: int = Query(default=30, ge=1, le=365),
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    """
    Ежедневная статистика за период
    """
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)

    # Генерируем все даты в периоде
    all_dates = []
    current_date = start_date
    while current_date <= end_date:
        all_dates.append(current_date)
        current_date += timedelta(days=1)

    # Статистика по дням
    daily_stats = []

    for stat_date in all_dates:
        next_date = stat_date + timedelta(days=1)

        # Новые пользователи
        new_users = session.exec(
            select(func.count(models.User.id)).where(
                models.User.created_at.between(stat_date, next_date)
            )
        ).first() or 0

        # Активные пользователи
        active_users = session.exec(
            select(func.count(func.distinct(models.WatchHistory.user_id))).where(
                models.WatchHistory.watched_at.between(stat_date, next_date)
            )
        ).first() or 0

        # Время просмотра
        watch_time = session.exec(
            select(func.sum(models.WatchHistory.watch_duration_seconds)).where(
                models.WatchHistory.watched_at.between(stat_date, next_date)
            )
        ).first() or 0

        # Новый контент
        new_content = session.exec(
            select(func.count(models.Content.id)).where(
                models.Content.created_at.between(stat_date, next_date)
            )
        ).first() or 0

        # Новые оценки
        new_ratings = session.exec(
            select(func.count(models.Rating.id)).where(
                models.Rating.created_at.between(stat_date, next_date)
            )
        ).first() or 0

        daily_stats.append(schemas.DailyStats(
            date=stat_date,
            new_users=new_users,
            active_users=active_users,
            watch_time_minutes=watch_time // 60,
            new_content=new_content,
            new_ratings=new_ratings
        ))

    return daily_stats


@router.get("/subscription-stats")
async def get_subscription_stats(
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    """
    Статистика по подпискам
    """
    # Распределение пользователей по тарифам
    tier_stats = session.exec(
        select(
            models.SubscriptionTier.name,
            func.count(models.User.id).label("user_count")
        ).join(
            models.User,
            models.User.subscription_tier_id == models.SubscriptionTier.id
        ).where(
            models.User.is_active == True
        ).group_by(
            models.SubscriptionTier.id
        )
    ).all()

    # Общая статистика
    total_users = session.exec(
        select(func.count(models.User.id)).where(models.User.is_active == True)
    ).first() or 0

    premium_users = session.exec(
        select(func.count(models.User.id)).where(
            and_(
                models.User.is_active == True,
                models.User.subscription_tier_id.in_([2, 3, 4])  # basic, premium, family
            )
        )
    ).first() or 0

    conversion_rate = (premium_users / total_users * 100) if total_users > 0 else 0

    # Ежемесячный доход (оценочный)
    monthly_revenue = session.exec(
        select(
            func.sum(
                case(
                    (models.SubscriptionTier.price_monthly.is_not(None), models.SubscriptionTier.price_monthly),
                    else_=0
                )
            )
        ).join(
            models.User,
            models.User.subscription_tier_id == models.SubscriptionTier.id
        ).where(
            models.User.is_active == True
        )
    ).first() or 0

    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "free_users": total_users - premium_users,
        "conversion_rate": round(conversion_rate, 2),
        "monthly_revenue": monthly_revenue,
        "tier_distribution": [
            {"tier": tier, "users": count} for tier, count in tier_stats
        ]
    }


@router.get("/content-stats")
async def get_content_stats(
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    """
    Статистика по контенту
    """
    # Общая статистика
    total_content = session.exec(
        select(func.count(models.Content.id)).where(models.Content.is_available == True)
    ).first() or 0

    # По типам контента
    by_type = session.exec(
        select(
            models.ContentType.name,
            func.count(models.Content.id).label("count")
        ).join(
            models.Content,
            models.Content.content_type_id == models.ContentType.id
        ).where(
            models.Content.is_available == True
        ).group_by(
            models.ContentType.id
        )
    ).all()

    # По жанрам
    by_genre = session.exec(
        select(
            models.Genre.name,
            func.count(models.ContentGenre.content_id).label("count")
        ).join(
            models.ContentGenre,
            models.ContentGenre.genre_id == models.Genre.id
        ).group_by(
            models.Genre.id
        ).order_by(
            func.count(models.ContentGenre.content_id).desc()
        ).limit(10)
    ).all()

    # Самый просматриваемый контент
    most_viewed = session.exec(
        select(
            models.Content.title,
            models.Content.views_count
        ).where(
            models.Content.is_available == True
        ).order_by(
            models.Content.views_count.desc()
        ).limit(10)
    ).all()

    # Контент с лучшим рейтингом
    best_rated = session.exec(
        select(
            models.Content.title,
            models.Content.our_rating
        ).where(
            and_(
                models.Content.is_available == True,
                models.Content.our_rating.is_not(None)
            )
        ).order_by(
            models.Content.our_rating.desc()
        ).limit(10)
    ).all()

    return {
        "total_content": total_content,
        "by_type": [{"type": t, "count": c} for t, c in by_type],
        "top_genres": [{"genre": g, "count": c} for g, c in by_genre],
        "most_viewed": [{"title": t, "views": v} for t, v in most_viewed],
        "best_rated": [{"title": t, "rating": r} for t, r in best_rated]
    }


@router.get("/user-retention")
async def get_user_retention(
        cohort_days: int = Query(default=30, ge=7, le=90),
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    """
    Анализ удержания пользователей
    """
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=cohort_days)

    # Когортный анализ
    cohorts = []

    # Разбиваем на недельные когорты
    current_cohort_start = start_date
    while current_cohort_start <= end_date:
        cohort_end = current_cohort_start + timedelta(days=6)
        if cohort_end > end_date:
            cohort_end = end_date

        # Пользователи в когорте
        cohort_users = session.exec(
            select(models.User.id).where(
                models.User.created_at.between(current_cohort_start, cohort_end)
            )
        ).all()

        if cohort_users:
            # Анализ активности по неделям
            week_activity = []

            for week in range(4):  # Анализируем 4 недели
                week_start = cohort_end + timedelta(days=week * 7)
                week_end = week_start + timedelta(days=6)

                active_users = session.exec(
                    select(func.count(func.distinct(models.WatchHistory.user_id))).where(
                        and_(
                            models.WatchHistory.user_id.in_(cohort_users),
                            models.WatchHistory.watched_at.between(week_start, week_end)
                        )
                    )
                ).first() or 0

                retention_rate = (active_users / len(cohort_users) * 100) if cohort_users else 0
                week_activity.append({
                    "week": week + 1,
                    "active_users": active_users,
                    "retention_rate": round(retention_rate, 2)
                })

            cohorts.append({
                "cohort": f"{current_cohort_start} - {cohort_end}",
                "users": len(cohort_users),
                "weekly_activity": week_activity
            })

        current_cohort_start = cohort_end + timedelta(days=1)

    return {
        "analysis_period": f"{start_date} - {end_date}",
        "cohort_days": cohort_days,
        "cohorts": cohorts
    }


@router.get("/performance")
async def get_performance_metrics(
        session: Session = Depends(get_session),
        current_user: models.User = Depends(dependencies.get_current_staff_user)
):
    """
    Ключевые метрики производительности
    """
    # Сегодняшние метрики
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    def get_metric(query_date, label):
        return {
            "date": query_date,
            "new_users": session.exec(
                select(func.count(models.User.id)).where(
                    models.User.created_at.between(query_date, query_date + timedelta(days=1))
                )
            ).first() or 0,
            "active_users": session.exec(
                select(func.count(func.distinct(models.WatchHistory.user_id))).where(
                    models.WatchHistory.watched_at.between(query_date, query_date + timedelta(days=1))
                )
            ).first() or 0,
            "watch_time_hours": (session.exec(
                select(func.sum(models.WatchHistory.watch_duration_seconds)).where(
                    models.WatchHistory.watched_at.between(query_date, query_date + timedelta(days=1))
                )
            ).first() or 0) / 3600,
            "new_ratings": session.exec(
                select(func.count(models.Rating.id)).where(
                    models.Rating.created_at.between(query_date, query_date + timedelta(days=1))
                )
            ).first() or 0,
            "label": label
        }

    return {
        "today": get_metric(today, "сегодня"),
        "yesterday": get_metric(yesterday, "вчера"),
        "this_week": {
            "start": week_ago,
            "end": today,
            "new_users": session.exec(
                select(func.count(models.User.id)).where(
                    models.User.created_at.between(week_ago, tomorrow)
                )
            ).first() or 0,
            "active_users": session.exec(
                select(func.count(func.distinct(models.WatchHistory.user_id))).where(
                    models.WatchHistory.watched_at.between(week_ago, tomorrow)
                )
            ).first() or 0
        },
        "this_month": {
            "start": month_ago,
            "end": today,
            "new_users": session.exec(
                select(func.count(models.User.id)).where(
                    models.User.created_at.between(month_ago, tomorrow)
                )
            ).first() or 0,
            "active_users": session.exec(
                select(func.count(func.distinct(models.WatchHistory.user_id))).where(
                    models.WatchHistory.watched_at.between(month_ago, tomorrow)
                )
            ).first() or 0
        }
    }