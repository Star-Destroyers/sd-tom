from tom_targets.models import TargetExtra


def add_item_to_extras(target, key, value):
    try:
        te = target.targetextra_set.get(key=key)
        te.value = value
        te.save()
    except TargetExtra.DoesNotExist:
        TargetExtra.objects.create(target=target, key='query_name', value=value)
