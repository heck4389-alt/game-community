from app.models import Comment, Post, User


def can_manage_post(user: User | None, post: Post) -> bool:
    if not user:
        return False
    return user.is_admin or user.id == post.author_id


def can_manage_comment(user: User | None, comment: Comment) -> bool:
    if not user:
        return False
    return user.is_admin or user.id == comment.author_id
