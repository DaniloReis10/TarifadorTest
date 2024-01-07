# Python Imports
import hashlib
import logging

from datetime import datetime
from datetime import timedelta
from smtplib import SMTPException

# Django Imports
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string

# Third Party Imports
import markdown

logger = logging.getLogger(__name__)


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def make_random_password(length=10,
                         allowed_chars='abcdefghjkmnpqrstuvwxyz'
                                       'ABCDEFGHJKLMNPQRSTUVWXYZ'
                                       '23456789'
                                       '!#$%&()*+,-./:;<=>?@[\]^_`{|}~'):
    """
    Generate a random password with the given length and given
    allowed_chars. The default value of allowed_chars does not have "I" or
    "O" or letters and digits that look similar -- just to avoid confusion.
    """
    return get_random_string(length, allowed_chars)


def make_username(email):
    name = email.split('@')[0]
    size = len(name)

    username = name
    count = 1
    while User.objects.filter(username=username).exists():
        h = hashlib.sha3_512(f'{ name }-{ count }'.encode('utf-8'))
        username = f'{ name }-{ h.hexdigest() }'[:size + 6]
        count += 1
    return username


def get_range_date(params):
    date_gt = params.get('date_gt')
    try:
        date_gt = datetime.strptime(date_gt, '%d/%m/%Y').date()
    except Exception:
        date_gt = None
    date_lt = params.get('date_lt')
    try:
        date_lt = datetime.strptime(date_lt, '%d/%m/%Y').date()
    except Exception:
        date_lt = None
    return date_gt, date_lt


def time_format(seconds, show_day=False):
    if show_day:
        return str(timedelta(seconds=seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}"


def get_amount_ust(price_ust, cost_ust_sum):
    if price_ust > 0.0:
        return round(round(float(cost_ust_sum), 4) / round(float(price_ust), 4), 4)
    return 0.0


def invite_by_email(organization, user, context):
    template = 'emails/invite.md'
    context.update({'email': user.email})

    html_message = render_to_string(template, context)
    html_message = markdown.markdown(html_message)

    try:
        if organization.settings.email:
            send_mail(
                subject='Tarifador VoIP - Acesso',
                message='',
                from_email=organization.settings.email,
                recipient_list=[user.email],
                fail_silently=False,
                html_message=html_message
            )
        else:
            user.email_user(
                subject='Tarifador VoIP - Acesso',
                message='',
                html_message=html_message
            )
    except SMTPException as error:
        logger.error(error)


def batch_qs(qs, batch_size=1000):
    """
    Returns a (start, end, total, queryset) tuple for each batch in the given
    queryset.

    Usage:
        # Make sure to order your querset
        article_qs = Article.objects.order_by('id')
        for start, end, total, qs in batch_qs(article_qs):
            print "Now processing %s - %s of %s" % (start + 1, end, total)
            for article in qs:
                print article.body
    """
    total = qs.count()
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        yield (start, end, total, qs[start:end])


def get_values_proportionality(date_lt, date_gt, proportionality=False):
    if proportionality:
        diff = date_lt - date_gt
        multiplier = diff.days + 1
        divider = 30
    else:
        multiplier = date_lt.month - date_gt.month + 1
        divider = 1
    return multiplier, divider
