from tom_targets.models import Target, TargetList
from tom_alerts.brokers.mars import MARSBroker

from tom_alerts.models import BrokerQuery
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache

from sdtom.pipeline.tns import update_tns_data

import logging

from sdtom.alerts.lasair_iris import LasairIrisBroker

logger = logging.getLogger(__name__)


def find_new_tns_classifications():
    update_tns_data()


def update_datums_from_mars(target: Target):
    mars = MARSBroker()
    alerts = mars.fetch_alerts({'objectId': target.name})

    # always get the latest alert
    try:
        alert = next(alerts)
    except StopIteration:
        logger.info('No alerts for this target')
        return

    mars.process_reduced_data(target, alert)
    try:
        cache.set(f'latest_mag_{target.id}', target.reduceddatum_set.first().value.get('magnitude'), timeout=60 * 60 * 24 * 30)
    except Exception:
        logger.warn('Could not cache latest magnitude.')


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
                target.save(extras={'query_name': query.parameters['query_name']})
                update_datums_from_mars(target)
            except StopIteration:
                break
        logger.info('Finished importing new lasair targets')
        query.last_run = timezone.now()
        query.save()
