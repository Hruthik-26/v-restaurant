from .models import RestaurantSettings


def restaurant_settings(request):
    settings = RestaurantSettings.objects.first()
    if not settings:
        settings = RestaurantSettings.objects.create()
    return {"settings": settings}
