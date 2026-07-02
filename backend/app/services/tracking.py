from sqlalchemy.orm import Session

from app.models import PostView, SearchLog


def record_post_view(db: Session, post_id: int, visitor_key: str | None) -> None:
    db.add(PostView(post_id=post_id, visitor_key=visitor_key))
    db.commit()


def record_search(
    db: Session,
    query: str,
    category_id: int | None = None,
    visitor_key: str | None = None,
) -> None:
    normalized = query.strip().lower()[:100]
    if not normalized:
        return
    db.add(SearchLog(query=normalized, category_id=category_id, visitor_key=visitor_key))
    db.commit()


def match_category_id(db: Session, query: str) -> int | None:
    from sqlalchemy import select

    from app.models import Category

    normalized = query.strip().lower()
    category = db.scalar(
        select(Category).where(
            (Category.slug == normalized) | (Category.name.ilike(f"%{normalized}%"))
        )
    )
    return category.id if category else None
