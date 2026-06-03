import django

DJANGO_GTE_3 = django.VERSION >= (3, 0)
DJANGO_GTE_4 = django.VERSION >= (4, 0)
DJANGO_GTE_5 = django.VERSION >= (5, 0)

if DJANGO_GTE_5:
    from django.http import HttpResponseBase
else:
    from django.http.response import HttpResponseBase as _H
    HttpResponseBase = _H
