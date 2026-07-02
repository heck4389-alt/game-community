from app.models import User


def display_author(user: User | None) -> str:
    if not user:
        return "익명"
    if user.is_admin:
        return "관리자"
    return user.username
