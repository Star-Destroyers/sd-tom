from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import classonlymethod
from django.views.generic import View
from tom_targets.models import Target
from tom_targets.views import TargetDetailView
from sd_alert_pipe.common import gather_data
from sd_alert_pipe.alerce import AlerceService
import asyncio
import json

from sdtom.pipeline.jobs import update_datums_from_mars


class UpdateDatumsFromMarsView(View):
    def get(self, request, *args, **kwargs):
        target = get_object_or_404(Target, pk=request.GET.get('target_id'))
        update_datums_from_mars(target)
        return redirect(target.get_absolute_url())


class SlugTargetDetailView(TargetDetailView):
    slug_field = 'name'


class ClassificationView(View):

    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        view._is_coroutine = asyncio.coroutines._is_coroutine
        return view

    async def get(self, request, *args, **kwargs):
        alerce = AlerceService()
        result = await alerce.get_probabilities(request.GET.get('name'))
        top_10 = json.dumps({'antares': [r.dict() for r in result[:10]]})
        return HttpResponse(top_10, content_type='application/json')

