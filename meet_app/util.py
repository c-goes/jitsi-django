import datetime
import string
import time
import urllib.parse
from hashlib import blake2b
from hmac import compare_digest

import jwt
import requests
from django.conf import settings
from django.utils import timezone

SIG_LEN = 8  # len() == 8*2


def get_statistics():
    try:
        r = requests.get("http://127.0.0.1:8080/colibri/stats")
        data = r.json()
        return {
            'participants': data['participants'],
            'conferences': data['conferences']
        }
    except:
        return {
            'participants': -1,
            'conferences': -1
        }


def sign(cookie, expire: int):
    h = blake2b(digest_size=SIG_LEN, key=settings.JWT_APPSECRET.encode("utf8"))
    h.update(cookie.lower().encode("utf8"))
    h.update(b"||||")
    h.update(str(expire).encode("utf8"))
    return h.hexdigest()


def verify(cookie: str, expire: int, sig: str):
    if len(sig) != SIG_LEN * 2:
        print("ERROR->length is not matching")
        return False
    if not all(x in string.hexdigits for x in sig):
        print("ERROR->not hex")
        return False
    good_sig = sign(cookie.lower(), expire)
    if expire < int(time.time()):
        print(f"ERROR->expired: {expire} < {int(time.time())}")
        return False
    return compare_digest(good_sig, sig)


def meeting_exists_or_staff_user(name: str, user):
    if user.is_staff:
        return True
    return meeting_exists(name)


def meeting_exists(name):
    check_token = jwt.encode(
        {
            "aud": settings.JWT_APPID,
            "iss": settings.JWT_APPID,
            "sub": settings.MEET_HOST,
            "room": name,
            "exp": timezone.datetime.utcnow() + datetime.timedelta(hours=12)
        },
        settings.JWT_APPSECRET,
        algorithm="HS256",
    )
    r = requests.get(
        f"http://localhost:5280/room-size?domain={urllib.parse.quote(settings.MEET_HOST)}&room={urllib.parse.quote(name)}&token={urllib.parse.quote(check_token)}")
    return r.status_code == 200
