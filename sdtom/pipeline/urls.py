from django.urls import path

from sdtom.pipeline.views import UpdateDatumsFromMarsView, UpdateDatumsFromAlerceView

app_name = "sdtom.pipeline"

urlpatterns = [
    path("marsdatums", UpdateDatumsFromMarsView.as_view(), name="mars-datums"),
    path("alercedatums", UpdateDatumsFromAlerceView.as_view(), name="alerce-datums"),
]
