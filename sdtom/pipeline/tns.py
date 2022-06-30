from tom_alerts.brokers.tns import TNSBroker, TNS_SEARCH_URL, TNS_OBJECT_URL
from tom_targets.models import Target, TargetList
from django.conf import settings
from django.utils import timezone
from typing import Optional, List
import requests
from datetime import date, timedelta
from zipfile import ZipFile
from tom_targets.groups import move_selected_to_grouping
import json
import logging
import io
import csv


logger = logging.getLogger(__name__)


def get_tns_classification(name: str) -> Optional[str]:
    tns_broker = TNSBroker()
    data = {
        'api_key': settings.BROKERS['TNS']['api_key'],
        'data': json.dumps(
            {
                'internal_name': name,
            }
        ),
    }
    response = requests.post(TNS_SEARCH_URL, data, headers=tns_broker.tns_headers())
    transients = response.json()

    for transient in transients['data']['reply']:
        # We will go through results until we find one with a classification otherwise
        # return None
        data = {
            'api_key': settings.BROKERS['TNS']['api_key'],
            'data': json.dumps(
                {
                    'objname': transient['objname'],
                    'photometry': 1,
                    'spectroscopy': 0,
                }
            ),
        }
        response = requests.post(TNS_OBJECT_URL, data, headers=tns_broker.tns_headers())
        try:
            return response.json()['data']['reply']['object_type']['name']
        except KeyError:
            continue

    return None


def download_tns_csv(d: date = date.today()) -> str:
    d = d - timedelta(days=1)
    tns_broker = TNSBroker()
    csv_name = f'tns_public_objects_{d.strftime("%Y%m%d")}.csv'
    url = f'https://www.wis-tns.org/system/files/tns_public_objects/{csv_name}.zip'
    data = {'api_key': settings.BROKERS['TNS']['api_key']}
    headers = tns_broker.tns_headers()
    response = requests.post(url, data, headers=headers)
    response.raise_for_status()
    with ZipFile(io.BytesIO(response.content)) as zipfile:
        with zipfile.open(csv_name) as csv_file:
            csv_str = csv_file.read().decode('utf-8')
            # delete first line
            return '\n'.join(csv_str.split('\n')[1:])


def process_csv(csv_str: str) -> List[dict]:
    reader = csv.DictReader(io.StringIO(csv_str))
    return [r for r in reader]


def move_to_uninteresting(target):
    uninteresting, _ = TargetList.objects.get_or_create(name='Uninteresting')
    target.targetlist_set.clear()
    uninteresting.targets.add(target)


def update_tns_data():
    for day_back in range(3):
        day_to_fetch = date.today() - timedelta(days=day_back)
        csv_str = download_tns_csv(day_to_fetch)
        named_targets = process_csv(csv_str)

        for tns_target in named_targets:
            matching_targets = (
                Target.objects.all()
                .filter(
                    name__in=tns_target['internal_names'].replace(' ', '').split(',')
                )
                .exclude(targetlist__name='Uninteresting')
            )
            for target in matching_targets:
                logger.info('Adding TNS classification and names to ' + str(target))
                extras = {}
                names = [tns_target['name']]
                if tns_target.get('type'):
                    extras['classification'] = tns_target['type']
                    if 'SN' in tns_target['type'].upper():
                        move_to_uninteresting(target)
                target.modified = timezone.now()
                target.save(extras=extras, names=names)
