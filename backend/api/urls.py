from django.urls import path

from .views import AoiDashboardView, AoiSerialsView, ShipmentDatesView


urlpatterns = [
    path("aoi-dashboard/", AoiDashboardView.as_view(), name="aoi-dashboard"),
    path(
        "aoi-dashboard/shipment-dates/",
        ShipmentDatesView.as_view(),
        name="aoi-dashboard-shipment-dates",
    ),
    path(
        "aoi-dashboard/serials/",
        AoiSerialsView.as_view(),
        name="aoi-dashboard-serials",
    ),
]