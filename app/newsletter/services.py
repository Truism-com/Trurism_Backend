from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from app.newsletter.models import NewsletterSubscriber


async def create_subscriber(db: AsyncSession, email: str):
    result = await db.execute(
        select(NewsletterSubscriber).where(NewsletterSubscriber.email == email)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return None

    subscriber = NewsletterSubscriber(email=email)

    db.add(subscriber)
    await db.commit()
    await db.refresh(subscriber)

    return subscriber


async def get_subscribers(db: AsyncSession, skip: int, limit: int):
    total_result = await db.execute(
        select(func.count()).select_from(NewsletterSubscriber)
    )
    total = total_result.scalar()

    result = await db.execute(
        select(NewsletterSubscriber).offset(skip).limit(limit)
    )
    data = result.scalars().all()

    return total, data


async def delete_subscriber(db: AsyncSession, subscriber_id: int):
    result = await db.execute(
        select(NewsletterSubscriber).where(NewsletterSubscriber.id == subscriber_id)
    )
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        return None

    await db.delete(subscriber)
    await db.commit()

    return subscriber