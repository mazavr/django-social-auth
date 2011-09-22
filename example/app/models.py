# Define a custom User class to work with django-social-auth
from django.db import models

class CustomUserManager(models.Manager):
    def create_user(self, username, email):
        return self.model._default_manager.create(username=username)


class CustomUser(models.Model):
    username = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = CustomUserManager()

    def is_authenticated(self):
        return True

from django.contrib.auth.models import User

class MySiteProfile(models.Model):
    # This is the only required field
    user = models.ForeignKey(User, unique=True)

    # The rest is completely up to you...
    favorite_band = models.CharField(max_length=100, blank=True, null=True)

from social_auth.signals import pre_update
from social_auth.backends.facebook import FacebookBackend

def _get_or_create_user_profile(user):
    if getattr(user, 'is_fake', False):
        if not getattr(user, 'profile', False):
            user.profile = MySiteProfile(user=user)
        return user.profile
    profile, created = MySiteProfile.objects.get_or_create(user=user)
    return profile

def _save_profile(profile):
    if not getattr(profile.user, 'is_fake', False):
        profile.save()

def facebook_extra_values(sender, user, response, details, **kwargs):
    profile = _get_or_create_user_profile(user)
    
    profile.favorite_band = 'la la la'
    _save_profile(profile)
    return True

pre_update.connect(facebook_extra_values, sender=FacebookBackend)


