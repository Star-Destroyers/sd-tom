from PIL import Image, ImageDraw
from io import BytesIO
import base64
from django import template
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
import pytz
import logging

from tom_targets.models import Target

register = template.Library()
logger = logging.getLogger('__name__')


def draw_point(draw, x, y, color):
    draw.ellipse((x, y, x + 6, y + 6), fill=color, outline=color)


def draw_nodetection(draw, x, y, color):
    color = (*color, 200)
    draw.polygon([(x - 2, y), (x + 2, y), (x, y + 2)], fill=color)


def pil2datauri(img):
    # converts PIL image to datauri
    data = BytesIO()
    img.save(data, "PNG")
    data64 = base64.b64encode(data.getvalue())
    return u'data:img/png;base64,' + data64.decode('utf-8')


@register.inclusion_tag('pipeline/partials/sparkline.html')
def sparkline(target, height, spacing=5, color_map=None):
    if not color_map:
        color_map = {
            'r': (200, 0, 0),
            'g': (0, 200, 0),
            'i': (0, 0, 0)
        }

    vals = target.reduceddatum_set.filter(
        timestamp__gte=datetime.utcnow() - timedelta(days=32)
    ).values('value', 'timestamp')

    if len(vals) < 1:
        return {'sparkline': None}

    vals = [v for v in vals if v['value']]
    min_mag = min([val['value']['magnitude'] for val in vals if val['value'].get('magnitude')])
    max_mag = max([val['value']['magnitude'] for val in vals if val['value'].get('magnitude')])
    # The following values are used if we want the graph's y range to extend to the values of non-detections
    # min_limit = min([val['value']['limit'] for val in vals if val['value'].get('limit')])
    # max_limit = max([val['value']['limit'] for val in vals if val['value'].get('limit')])
    distinct_filters = set([val['value']['filter'] for val in vals])
    by_filter = {f: [(None, None)] * 32 for f in distinct_filters}

    for val in vals:
        day_index = (val['timestamp'].replace(tzinfo=pytz.UTC) - timezone.now()).days
        by_filter[val['value']['filter']][day_index] = (val['value'].get('magnitude'), val['value'].get('limit'))

    graph_min = min_mag  # min(min_mag, min_limit)
    graph_max = max_mag  # max(max_mag, max_limit)
    val_range = graph_max - graph_min
    image_width = (spacing + 1) * (32 - 1)
    image_height = height + 10

    image = Image.new("RGBA", (image_width, image_height), (255, 255, 255, 0))
    try:
        pixels_per_unit = height / val_range
    except ZeroDivisionError:
        # return blank image
        data_uri = pil2datauri(image)
        return {'sparkline': data_uri}
    d = ImageDraw.Draw(image)
    for d_filter, day_mags in by_filter.items():
        x = 0
        color = color_map.get(d_filter, 'r')
        for (mag, limit) in day_mags:
            if mag:
                y = ((mag - graph_min) * pixels_per_unit)
                draw_point(d, x, y, color)
            if limit:
                y = ((limit - graph_min) * pixels_per_unit)
                draw_nodetection(d, x, y, color)
            x += spacing

    data_uri = pil2datauri(image)
    return {'sparkline': data_uri}


@register.filter
def badge(list_name):
    names = {
        'New': 'badge-warning',
        'Uninteresting': 'badge-secondary',
        'Interesting': 'badge-primary'
    }
    return names.get(list_name, 'badge-dark')


@register.filter
def latest_mag(target: Target):
    mag_cache_key = f'latest_mag_{target.id}'
    latest_mag = cache.get(mag_cache_key)
    if not latest_mag:
        try:
            latest_mag = target.reduceddatum_set.first().value.get('magnitude')
        except Exception:
            latest_mag = None
            logger.warn('Could not cache latest mag.')
        cache.set(mag_cache_key, latest_mag, timeout=60 * 60 * 24 * 30)  # Cache for 30 days

    return latest_mag


@register.inclusion_tag('pipeline/partials/brokerlinks.html')
def broker_links(target):
    return {'target': target}


@register.inclusion_tag('pipeline/partials/classifications.html')
def classifications(target):
    return {'target': target}
