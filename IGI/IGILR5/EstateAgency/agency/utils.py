import calendar
import datetime
import time

from django.conf import settings
import requests
from django.contrib.auth.models import Group
from django.db.models import Q

from .models import User
import zoneinfo

from django.utils import timezone

def get_ip_adress(request):


    if settings.DEBUG:
        response = requests.get('https://api.ipify.org/?format=json')
        my_ip = response.json()['ip']
        return my_ip
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip

def get_info_user_by_ip(ip):
    response = requests.get(f'https://ipinfo.io/{ip}/geo')
    return response.json()

def get_all_employees():
    employee_group,created = Group.objects.get_or_create(name='Employee')
    all_employees = User.objects.filter(groups=employee_group)
    return all_employees
    #return User.objects.all()

def get_all_clients():
    employee_group,created = Group.objects.get_or_create(name='Employee')
    all_clients = User.objects.filter(~Q(groups=employee_group), is_superuser=False)
    return all_clients
    #return User.objects.all()


def filter_sort_realties(request, realties):
    min_input = request.GET.get('min_price')
    max_input = request.GET.get('max_price')
    search = request.GET.get('search_name')
    selectedEmployee = request.GET.get('selectedEmployee')
    selectedSort = request.GET.get('selectedSort')
    if selectedSort:
        realties = realties.order_by(selectedSort)
    else:
        realties = realties.order_by('name')
    if selectedEmployee:
        employee = User.objects.get(username=selectedEmployee)
        realties = realties.filter(owner=employee)
    if search:
        realties = realties.filter(name__icontains=search)
    if min_input and max_input:
        realties = realties.filter(price__lte=max_input, price__gte=min_input)
    elif min_input:
        realties = realties.filter(price__gte=min_input)
    elif max_input:
        realties = realties.filter(price__lte=max_input)
    return realties





class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        tzname = request.session.get("django_timezone")
        if tzname:
            timezone.activate(zoneinfo.ZoneInfo(tzname))
        else:
            response = get_info_user_by_ip(get_ip_adress(request))
            if 'timezone' in response:
                tzname = response['timezone']
            else:
                tzname =settings.TIME_ZONE
            request.session["django_timezone"] = tzname
            timezone.activate(zoneinfo.ZoneInfo(tzname))

        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if hasattr(response,'context_data'):
            tzname = request.session.get("django_timezone")
            c = calendar.TextCalendar()
            today = datetime.datetime.now(zoneinfo.ZoneInfo(tzname))
            s = c.formatmonth(today.year, today.month)
            if response.context_data:
                response.context_data['calendar'] = s
            else:
                response.context_data = {'calendar': s}
        return response



