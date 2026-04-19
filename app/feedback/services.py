from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.feedback.models import Feedback


async def create_feedback(db: AsyncSession, data):
    feedback = Feedback(**data.dict())

    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return feedback


async def get_feedback_list(db: AsyncSession, skip: int, limit: int):
    total_result = await db.execute(
        select(func.count()).select_from(Feedback)
    )
    total = total_result.scalar()

    result = await db.execute(
        select(Feedback).offset(skip).limit(limit)
    )
    data = result.scalars().all()

    return total, data


async def get_feedback_by_id(db: AsyncSession, feedback_id: int):
    result = await db.execute(
        select(Feedback).where(Feedback.id == feedback_id)
    )
    return result.scalar_one_or_none()


async def delete_feedback(db: AsyncSession, feedback_id: int):
    feedback = await get_feedback_by_id(db, feedback_id)

    if not feedback:
        return None

    await db.delete(feedback)
    await db.commit()

    return feedback