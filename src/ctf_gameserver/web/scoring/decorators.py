from functools import wraps

from django.shortcuts import redirect
from django.conf import settings
from django.http import JsonResponse
from django.utils.translation import ugettext as _
from django.contrib import messages

from .models import GameControl


def registration_open_required(view):
    """
    View decorator which prohibts access to the decorated view if registration is closed from the GameControl
    object.
    """

    @wraps(view)
    def func(request, *args, **kwargs):
        if not GameControl.get_instance().registration_open:
            messages.error(request, _('Sorry, registration is currently closed.'))
            return redirect(settings.HOME_URL)

        return view(request, *args, **kwargs)

    return func


def competition_started_required(resp_format):
    """
    View decorator which prohibts access to the decorated view if the competition has not yet started (i.e.
    it must be running or over).

    Args:
        resp_format: Format of the response when the competition has not yet started. Supported options are
                     'html' and 'json'.
    """

    def decorator(view):
        @wraps(view)
        def func(request, *args, **kwargs):
            game_control = GameControl.get_instance()
            if game_control.competition_running() or game_control.competition_over():
                return view(request, *args, **kwargs)

            if resp_format == 'json':
                return JsonResponse({'error': 'Not available yet'}, status=404)
            else:
                messages.error(request, _('Sorry, the page you requested is not available yet.'))
                return redirect(settings.HOME_URL)

        return func

    return decorator
