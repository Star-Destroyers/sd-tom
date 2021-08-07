from django.urls import path

from sdtom.pipeline.views import UpdateDatumsFromMarsView

app_name = 'sdtom.pipeline'

urlpatterns = [
    path('marsdatums', UpdateDatumsFromMarsView.as_view(), name='mars-datums'),
]
