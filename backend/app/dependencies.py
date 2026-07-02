from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(request: Request, db: DbSession) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.scalar(select(User).where(User.id == user_id))
    return user


CurrentUser = Annotated[User | None, Depends(get_current_user)]
