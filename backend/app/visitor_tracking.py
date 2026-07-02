import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.database import SessionLocal
from app.models import UniqueVisit


def should_track_visit(request: Request) -> bool:
    if request.method != "GET":
        return False

    path = request.url.path
    if path.startswith("/static") or path in {"/health", "/favicon.ico"}:
        return False

    return True


def record_unique_visit(visitor_key: str, visit_date: date) -> bool:
    db = SessionLocal()
    try:
        exists = db.scalar(
            select(UniqueVisit.id).where(
                UniqueVisit.visitor_key == visitor_key,
                UniqueVisit.visit_date == visit_date,
            )
        )
        if exists:
            return False

        db.add(UniqueVisit(visitor_key=visitor_key, visit_date=visit_date))
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False
    finally:
        db.close()


class VisitorTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not should_track_visit(request):
            return await call_next(request)

        visitor_key = request.cookies.get(settings.visitor_cookie_name)
        is_new_cookie = not visitor_key
        if is_new_cookie:
            visitor_key = str(uuid.uuid4())

        record_unique_visit(visitor_key, date.today())
        response = await call_next(request)

        if is_new_cookie or settings.visitor_cookie_name not in request.cookies:
            response.set_cookie(
                key=settings.visitor_cookie_name,
                value=visitor_key,
                max_age=settings.visitor_cookie_max_age,
                httponly=True,
                samesite="lax",
                secure=settings.app_env == "production",
            )

        return response
