from typing import Optional
from tom_targets.models import Target, TargetExtra, TargetList
from tom_alerts.brokers.mars import MARSBroker
from tom_alerts.brokers.tns import TNSBroker, TNS_SEARCH_URL, TNS_OBJECT_URL
from tom_alerts.models import BrokerQuery
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
import requests
import logging
import json

from sdtom.alerts.lasair_iris import LasairIrisBroker

logger = logging.getLogger(__name__)


def update_datums_from_mars(target: Target):
    mars = MARSBroker()
    alerts = mars.fetch_alerts({'objectId': target.name})

    # always get the latest alert
    alert = next(alerts)

    mars.process_reduced_data(target, alert)


def add_item_to_extras(target, key, value):
    try:
        te = target.targetextra_set.get(key=key)
        te.value = value
        te.save()
    except TargetExtra.DoesNotExist:
        TargetExtra.objects.create(target=target, key='query_name', value=value)


def get_tns_classification(name: str) -> Optional[str]:
    tns_broker = TNSBroker()
    data = {
        'api_key': settings.BROKERS['TNS']['api_key'],
        'data': json.dumps({
            'internal_name': name,
        })
    }
    response = requests.post(TNS_SEARCH_URL, data, headers=tns_broker.tns_headers())
    transients = response.json()

    for transient in transients['data']['reply']:
        # We will go through results until we find one with a classification otherwise
        # return None
        data = {
            'api_key': settings.BROKERS['TNS']['api_key'],
            'data': json.dumps({
                'objname': transient['objname'],
                'photometry': 1,
                'spectroscopy': 0,
            })
        }
        response = requests.post(TNS_OBJECT_URL, data, headers=tns_broker.tns_headers())
        try:
            return response.json()['data']['reply']['object_type']['name']
        except KeyError:
            continue

    return None


def find_new_tns_classifications():
    logger.info('Updating TNS classifications')
    targets = Target.objects.all().order_by('-created')[:10]
    for target in targets:
        classification = get_tns_classification(target.name)
        if classification:
            add_item_to_extras(target, 'classification', classification)


def fetch_new_lasair_alerts():
    queries = BrokerQuery.objects.filter(broker=LasairIrisBroker.name)
    lasair_broker = LasairIrisBroker()
    for query in queries:
        last_run = query.last_run or timezone.now() - timedelta(days=1)
        alerts = lasair_broker.fetch_alerts({'since': last_run, **query.parameters})
        while True:
            try:
                generic_alert = lasair_broker.to_generic_alert(next(alerts))
                try:
                    target = Target.objects.get(name=generic_alert.name)
                    logger.info('Updating target ' + str(target))
                except Target.DoesNotExist:
                    target, extras, _ = generic_alert.to_target()
                    target.save(extras=extras)
                    target_list, _ = TargetList.objects.get_or_create(name='New')
                    target_list.targets.add(target)
                    logger.info('Created target ' + str(target))
                update_datums_from_mars(target)
                add_item_to_extras(target, 'query_name', query.parameters['query_name'])
                try:
                    classification = get_tns_classification(generic_alert.name)
                    if classification:
                        add_item_to_extras(target, key='classification', value=classification)
                except Exception as e:
                    logger.warn('Got exception fetching classification from TNS %s', e)
            except StopIteration:
                break
        logger.info('Finished importing new lasair targets')
        query.last_run = timezone.now()
