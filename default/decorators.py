from functools import wraps

from dateutil import parser
from django.http import JsonResponse
from django.utils.translation import gettext as _


def clear_files(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        request.session['files'] = []
        return function(request, *args, **kwargs)

    return wrap


def require_files(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if 'files' not in request.session:
            return JsonResponse({'error': 'No files uploaded'}, status=400, reason='No files available for operation')
        return function(request, *args, **kwargs)

    return wrap


def published_date(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        published_date = request.GET.get('publishedDate', '')
        if published_date:
            try:
                parser.parse(published_date)
                kwargs['published_date'] = published_date
            except ValueError:
                kwargs['warnings'] = [
                    _('An invalid published date was submitted, and therefore ignored: %(date)s') % {
                        'date': published_date,
                    },
                ]
        return function(request, *args, **kwargs)

    return wrap
