from tom_targets.models import Target
from tom_alerts.brokers.mars import MARSBroker


def update_datums_from_mars(target: Target):
    mars = MARSBroker()
    alerts = mars.fetch_alerts({'objectId': target.name})

    # always get the latest alert
    alert = next(alerts)

    mars.process_reduced_data(target, alert)
