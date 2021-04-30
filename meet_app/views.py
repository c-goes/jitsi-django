import datetime

import jwt

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from meet_app.util import verify, meeting_exists_or_staff_user, meeting_exists, sign, get_statistics


# Create your views here.

def statistics(request):
    s = get_statistics()
    return JsonResponse(s)

def guest_waiting(request, name, ts, sig):
    if not verify(name, ts, sig):
        return HttpResponse("ERROR2", status=400)

    if not meeting_exists(name):
        return render(request, "meet_app/waiting.html",
                      context={
                          'name': name
                      }
                      )
    else:
        guest_join_jwt_token = jwt.encode(
            {
                "aud": settings.JWT_APPID,
                "iss": settings.JWT_APPID,
                "sub": settings.MEET_HOST,
                "room": name,
                "moderator": False,
                "exp": timezone.datetime.utcnow() + datetime.timedelta(hours=12),
                "context": {
                    "user": {
                        "name": ""
                    }
                }
            },
            settings.JWT_APPSECRET,
            algorithm="HS256",
        )
        return render(request, "meet_app/join.html", context={
            'name': name,
            'personal_token': guest_join_jwt_token,
            'meet_host': settings.MEET_HOST,
            'guest': True
        })


# check token

@login_required
def waiting(request, name):
    if meeting_exists_or_staff_user(name, request.user):
        if request.user.last_name and request.user.first_name:
            fullname = f"{request.user.last_name}, {request.user.first_name}"
        else:
            fullname = request.user.username

        personal_token = jwt.encode(
            {
                "aud": settings.JWT_APPID,
                "iss": settings.JWT_APPID,
                "sub": settings.MEET_HOST,
                "room": name,
                "moderator": True if request.user.is_staff or request.user.is_superuser else False,
                "exp": timezone.datetime.utcnow() + datetime.timedelta(hours=12),
                "context": {
                    "user": {
                        "name": f"{fullname} ({request.user.username})"
                    }
                }
            },
            settings.JWT_APPSECRET,
            algorithm="HS256",
        )
        guest_token = None

        dt = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        dt = dt.replace(hour=23, minute=59)

        if request.user.is_staff or request.user.is_superuser:
            guest_token = sign(name, int(dt.strftime('%s')))
        return render(request, "meet_app/join.html", context={
            'name': name,
            'guest_time': int(dt.strftime('%s')),
            'guest_time_dt': dt,
            'guest_token': guest_token,
            'personal_token': personal_token,
            'meet_host': settings.MEET_HOST

        })
    else:
        return render(request, "meet_app/waiting.html",
                      context={
                          'name': name
                      }
                      )
