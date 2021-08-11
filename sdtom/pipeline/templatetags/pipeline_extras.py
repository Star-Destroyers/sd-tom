from PIL import Image, ImageDraw
from io import BytesIO
import base64
from django import template
from datetime import datetime, timedelta
from django.utils import timezone
import pytz

register = template.Library()


def draw_point(draw, x, y, color):
    draw.ellipse([(x, y), (x + 5, y + 5)], fill=color, outline=color)


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
            'i': (255, 0, 0),
            'g': (0, 255, 0),
            'r': (0, 0, 255)
        }

    vals = target.reduceddatum_set.filter(
        timestamp__gte=datetime.utcnow() - timedelta(days=32)
    ).values('value', 'timestamp')

    if len(vals) < 1:
        return {'sparkline': None}

    min_mag = min([val['value']['magnitude'] for val in vals])
    max_mag = max([val['value']['magnitude'] for val in vals])

    distinct_filters = set([val['value']['filter'] for val in vals])
    by_filter = {f: [None] * 32 for f in distinct_filters}

    for val in vals:
        day_index = (val['timestamp'].replace(tzinfo=pytz.UTC) - timezone.now()).days
        by_filter[val['value']['filter']][day_index] = val['value']['magnitude']

    val_range = max_mag - min_mag
    pixels_per_unit = height / val_range
    image_width = (spacing + 1) * (32 - 1)
    image_height = height + 10

    image = Image.new("RGBA", (image_width, image_height), (255, 255, 255, 0))
    d = ImageDraw.Draw(image)
    for d_filter, day_mags in by_filter.items():
        x = 0
        color = color_map.get(d_filter, 'r')
        for mag in day_mags:
            if mag:
                y = ((mag - min_mag) * pixels_per_unit)
                draw_point(d, x, y, color)
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
