def has_active_subscription(user):
    return user.get("active", False)
