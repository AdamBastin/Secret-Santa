MAX_WISHLIST_ITEMS = 5
MAX_ITEM_LENGTH = 200


def collect_wishlist_items(form):
    submitted_items = form.getlist("items")
    items = [item.strip() for item in submitted_items if item.strip()]

    if not items:
        return items, "Add at least one item to your wishlist."

    if len(items) > MAX_WISHLIST_ITEMS:
        return items, f"Your wishlist can contain up to {MAX_WISHLIST_ITEMS} items."

    if any(len(item) > MAX_ITEM_LENGTH for item in items):
        return items, f"Each wishlist item must be {MAX_ITEM_LENGTH} characters or fewer."

    return items, None
