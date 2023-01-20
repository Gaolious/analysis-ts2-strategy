from hashlib import md5

from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser, PermissionsMixin):
    # from FRIDA
    # function getContext() {
    #   return Java.use('android.app.ActivityThread').currentApplication().getApplicationContext().getContentResolver();
    # }
    # function logAndroidId() {
    #   Logger.INFO('Android Id ', Java.use('android.provider.Settings$Secure').getString(getContext(), 'android_id'));
    # }
    android_id = models.CharField(_('android_id'), max_length=20, blank=False, null=False)

    ###########################################################################
    # update by login response.
    player_id = models.CharField(_('player id'), max_length=20, blank=True, null=False, default='')
    game_access_token = models.CharField(_('game_access_token'), max_length=50, blank=True, null=False, default='')
    authentication_token = models.CharField(_('authentication_token'), max_length=50, blank=True, null=False, default='')
    remember_me_token = models.TextField(_('authentication_token'), max_length=10000, blank=True, null=False, default='')
    support_url = models.TextField(_('support_url'), max_length=10000, blank=True, null=False, default='')

    ###########################################################################
    # update by logic
    has_error = models.BooleanField(_('has error'), blank=True, null=False, default=False)

    next_event = models.DateTimeField(_('next_event'), blank=True, null=True, default=None)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    @property
    def device_token(self) -> str:
        return md5(self.android_id.encode('utf-8')).hexdigest()
