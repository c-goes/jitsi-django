from django.db import models

# Create your models here.

from django.dispatch import receiver

from django_auth_ldap.backend import populate_user, LDAPBackend




@receiver(populate_user)
def user_flag(sender, user, ldap_user, **kwargs):
    # print(str(user))
    # print(str(ldap_user.dn))
    if "ou=schueler" in ldap_user.dn:
        pass
    elif "ou=lehrer" in ldap_user.dn:
        user.is_staff = True
        user.is_superuser = True
        user.save()
