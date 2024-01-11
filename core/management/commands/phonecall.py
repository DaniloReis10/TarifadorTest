# python
import operator

from datetime import datetime
from datetime import timedelta
from functools import reduce
from time import time

# django
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db.models import Q

# project
from centers.models import Company
from organizations.models import Organization
from phonecalls.constants import VC1, VC2, VC3, LOCAL, LDN, LDI


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument(
            'model', choices=['org', 'company'])

        parser.add_argument(
            'id', type=str, nargs='+')

        parser.add_argument(
            '-a', '--action', choices=['list', 'update_price', 'update_call'])

        parser.add_argument(
            '--start-date', type=str, help='YYYY-MM-DD', required=False)

        parser.add_argument(
            '--stop-date', type=str, help='YYYY-MM-DD', required=False)

        parser.add_argument(
            '--verbose', action='store_true')

        parser.add_argument(
            '--debug', action='store_true')

    @staticmethod
    def get_date(sdate):
        if not sdate:
            return None

        try:
            return datetime.strptime(sdate, '%Y-%m-%d').date()
        except Exception as err:
            raise CommandError(err)

    @staticmethod
    def time_format(time_start):
        return timedelta(seconds=time() - time_start)

    def handle(self, *args, **options):
        model = options['model']
        slug_list = options['id']
        action = options['action']
        start_date = self.get_date(options['start_date'])
        stop_date = self.get_date(options['stop_date'])
        self.verbose = options['verbose']
        self.debug = options['debug']

        if model == 'org':
            self.org_phonecalls(slug_list, start_date, stop_date, action)

        elif model == 'company':
            self.company_phonecalls(slug_list, start_date, stop_date, action)

    def org_phonecalls(self, slug_list, start_date, stop_date, action):
        org_list = Organization.objects.filter(slug__in=slug_list)

        for org in org_list:
            if action == 'list':
                for company in org.company_set.only('name', 'slug'):
                    self.stdout.write(f'{company.name} ({company.slug})')

    def company_phonecalls(self, slug_list, start_date, stop_date, action):
        time_start = time()

        company_list = Company.objects.filter(slug__in=slug_list).only('name', 'call_pricetable')
        for company in company_list:
            if action == 'update_price':
                conditions = []
                if start_date:
                    conditions.append(Q(startdate__gte=start_date))
                if stop_date:
                    conditions.append(Q(startdate__lte=stop_date))
                phonecall_list = company.phonecall_set \
                    .filter(inbound=False, calltype__in=[LOCAL, VC1, VC2, VC3, LDN, LDI]) \
                    .filter(reduce(operator.and_, conditions)) \
                    .only('id')

                call_total = phonecall_list.count()
                call_count = 0

                for instance in phonecall_list.iterator():
                    instance.save(update_fields=['price_table', 'price', 'billedamount'])

                    call_count += 1
                    current_time = self.time_format(time_start)
                    self.stdout.write(f'{company.name} - {call_count}/{call_total} - '
                                      f'{100*call_count/call_total:.2f}% - {current_time}')
                self.stdout.write(self.style.SUCCESS(f'{call_total} chamadas originadas cobradas atualizadas'))
