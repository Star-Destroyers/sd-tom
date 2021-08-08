from PIL import Image, ImageDraw
from io import BytesIO
import base64
from django import template

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

    vals = list(target.reduceddatum_set.all().order_by('timestamp').values_list('value'))
    if len(vals) < 1:
        return {'sparkline': None}

    min_mag = min([val[0]['magnitude'] for val in vals])
    max_mag = max([val[0]['magnitude'] for val in vals])
    val_range = max_mag - min_mag
    pixels_per_unit = height / val_range
    image_width = (spacing + 1) * (len(vals) - 1)
    image_height = height + 10

    image = Image.new("RGBA", (image_width, image_height), (255, 255, 255, 0))
    d = ImageDraw.Draw(image)
    x = 0
    for val in vals:
        color = color_map.get(val[0]['filter'], 'r')
        y = ((val[0]['magnitude'] - min_mag) * pixels_per_unit)
        draw_point(d, x, y, color)
        x += spacing

    data_uri = pil2datauri(image)
    return {'sparkline': data_uri}
