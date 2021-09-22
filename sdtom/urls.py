from django.urls import path, include

from sdtom.pipeline.views import SlugTargetDetailView

urlpatterns = [
    path('', include('tom_common.urls')),
    path('pipeline/', include('sdtom.pipeline.urls', namespace='pipeline')),
    path('targets/<str:slug>/', SlugTargetDetailView.as_view(), name='target-slug-detail'),
]
