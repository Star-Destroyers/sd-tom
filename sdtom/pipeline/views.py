from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View
from tom_targets.models import Target

from sdtom.pipeline.jobs import update_datums_from_mars


class UpdateDatumsFromMarsView(View):
    def get(self, request, *args, **kwargs):
        target = get_object_or_404(Target, pk=request.GET.get('target_id'))
        update_datums_from_mars(target)
        return redirect(target.get_absolute_url())
