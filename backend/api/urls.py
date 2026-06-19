from django.urls import path

from .views import AoiDashboardView, ShipmentDatesView


urlpatterns = [
    path("aoi-dashboard/", AoiDashboardView.as_view(), name="aoi-dashboard"),
    path(
        "aoi-dashboard/shipment-dates/",
        ShipmentDatesView.as_view(),
        name="aoi-dashboard-shipment-dates",
    ),
]
