from django.urls import path, include

from sdtom.pipeline.views import SlugTargetDetailView, ClassificationView

urlpatterns = [
    path('', include('tom_common.urls')),
    path('pipeline/', include('sdtom.pipeline.urls', namespace='pipeline')),
    path('targets/classification/', ClassificationView.as_view(), name='target-classification'),
    path('targets/<str:slug>/', SlugTargetDetailView.as_view(), name='target-slug-detail'),
]
