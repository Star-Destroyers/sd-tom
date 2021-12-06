from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import classonlymethod
from django.views.generic import View
from tom_targets.models import Target
from tom_targets.views import TargetDetailView
from sd_alert_pipe.alerce import AlerceService
import asyncio
import plotly.graph_objects as go
from plotly import offline

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
        probs = [res for res in result if res.classifier_name == 'lc_classifier']
        if len(probs) < 1:
            return HttpResponse('none')

        layout = go.Layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            width=250,
            height=250,
            margin={'l': 50, 'r': 50, 'b': 50, 't': 50},
            autosize=True,
        )
        data = go.Scatterpolar(
            r=[res.probability for res in probs],
            theta=[res.class_name for res in probs],
            fill='toself'
        )

        fig = go.Figure(data=data, layout=layout)

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=False,
                    ticks="",
                    color='#dcdcdc',
                    linecolor='#dcdcdc',
                    showgrid=False,
                    gridcolor='#dcdcdc'
                )
            ),
            showlegend=False
        )
        fig.update_polars(bgcolor='rgba(0,0,0,0)', angularaxis_color='#dcdcdc')

        graph = offline.plot(
            fig, output_type='div', show_link=False
        )

        return HttpResponse(graph)
