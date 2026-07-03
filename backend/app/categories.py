GUIDE_SLUG = "guide"
NOTICE_SLUG = "notice"
FREE_SLUG = "free"

NON_GAME_SLUGS = {FREE_SLUG, GUIDE_SLUG, NOTICE_SLUG}
ADMIN_ONLY_SLUGS = {NOTICE_SLUG}


def can_post_in_category(user, category) -> bool:
    if not user or not category:
        return False
    if category.slug in ADMIN_ONLY_SLUGS:
        return user.is_admin
    return True


def writable_categories(categories, user) -> list:
    return [category for category in categories if can_post_in_category(user, category)]
