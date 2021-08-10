from tom_targets.models import Target, TargetExtra, TargetList
from tom_alerts.brokers.mars import MARSBroker
from tom_alerts.models import BrokerQuery
from datetime import timedelta, datetime
from django.utils import timezone
import logging

from sdtom.alerts.lasair_iris import LasairIrisBroker

logger = logging.getLogger(__name__)


def update_datums_from_mars(target: Target):
    mars = MARSBroker()
    alerts = mars.fetch_alerts({'objectId': target.name})

    # always get the latest alert
    alert = next(alerts)

    mars.process_reduced_data(target, alert)


def add_queryname_to_extras(target, query_name):
    try:
        te = target.targetextra_set.get(key='query_name')
        if query_name not in te.value:
            te.value = te.value + ' ' + query_name
            te.save()
    except TargetExtra.DoesNotExist:
        TargetExtra.objects.create(target=target, key='query_name', value=query_name)


def fetch_new_lasair_alerts():
    queries = BrokerQuery.objects.filter(broker=LasairIrisBroker.name)
    lasair_broker = LasairIrisBroker()
    for query in queries:
        last_run = query.last_run or datetime.utcnow() - timedelta(days=1)
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
                add_queryname_to_extras(target, query.parameters['query_name'])
                query.last_run = timezone.now()
            except StopIteration:
                break
                logger.info('Finished importing new lasair targets')
