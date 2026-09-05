"""
NeuroNex — Review Router
Analyst approve / reject / flag insights; logs a ReviewAction row.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_sql import get_db
from app.models_sql import Insight, ReviewAction
from app.schemas import ReviewDecision, ReviewActionOut

router = APIRouter(prefix="/api/review", tags=["review"])


@router.post("/{insight_id}", response_model=ReviewActionOut, status_code=201)
async def review_insight(
    insight_id: int,
    payload: ReviewDecision,
    db: AsyncSession = Depends(get_db),
):
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(404, "Insight not found")

    insight.status = payload.decision
    action = ReviewAction(
        insight_id=insight_id,
        analyst_id=payload.analyst_id,
        decision=payload.decision,
        notes=payload.notes,
    )
    db.add(action)
    await db.commit()
    await db.refresh(action)
    return action
