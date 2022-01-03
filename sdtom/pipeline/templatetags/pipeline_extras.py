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
