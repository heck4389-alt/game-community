from datetime import date

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import UniqueVisit


def get_visitor_stats() -> tuple[int, int]:
    db = SessionLocal()
    try:
        today = date.today()
        today_visitors = db.scalar(
            select(func.count(UniqueVisit.id)).where(UniqueVisit.visit_date == today)
        ) or 0
        total_visitors = db.scalar(select(func.count(func.distinct(UniqueVisit.visitor_key)))) or 0
        return today_visitors, total_visitors
    finally:
        db.close()
