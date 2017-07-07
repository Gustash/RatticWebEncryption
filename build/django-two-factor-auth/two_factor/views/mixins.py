from django.template.response import TemplateResponse
from two_factor.utils import default_device

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.shortcuts import redirect


class OTPRequiredMixin(object):
    """
    View mixin which verifies that the user logged in using OTP.

    .. note::
       This mixin should be the left-most base class.
    """
    raise_anonymous = False
    """
    Whether to raise PermissionDenied if the user isn't logged in.
    """

    login_url = None
    """
    If :attr:`raise_anonymous` is set to `False`, this defines where the user
    will be redirected to. Defaults to ``settings.LOGIN_URL``.
    """

    redirect_field_name = REDIRECT_FIELD_NAME
    """
    URL query name to use for providing the destination URL.
    """

    raise_unverified = False
    """
    Whether to raise PermissionDenied if the user isn't verified.
    """

    verification_url = None
    """
    If :attr:`raise_unverified` is set to `False`, this defines where the user
    will be redirected to. If set to ``None``, an explanation will be shown to
    the user on why access was denied.
    """

    def get_login_url(self):
        """
        Returns login url to redirect to.
        """
        login_url = self.login_url or settings.LOGIN_URL
        if not login_url:
            raise ImproperlyConfigured(
                "Define %(cls)s.login_url or settings.LOGIN_URL or override "
                "%(cls)s.get_login_url()." % {"cls": self.__class__.__name__})
        return str(login_url)

    def get_verification_url(self):
        """
        Returns verification url to redirect to.
        """
        return self.verification_url and str(self.verification_url)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated() or \
                (not request.user.is_verified() and default_device(request.user)):
            # If the user has not authenticated raise or redirect to the login
            # page. Also if the user just enabled two-factor authentication and
            # has not yet logged in since should also have the same result. If
            # the user receives a 'you need to enable TFA' by now, he gets
            # confuses as TFA has just been enabled. So we either raise or
            # redirect to the login page.
            if self.raise_anonymous:
                raise PermissionDenied()
            else:
                return redirect('%s?%s' % (
                    self.get_login_url(),
                    urlencode({self.redirect_field_name: request.get_full_path()})
                ))

        if not request.user.is_verified():
            if self.raise_unverified:
                raise PermissionDenied()
            elif self.get_verification_url():
                return redirect('%s?%s' % (
                    self.verification_url,
                    urlencode({self.redirect_field_name: request.get_full_path()})
                ))
            else:
                return TemplateResponse(
                    request=request,
                    template='two_factor/core/otp_required.html',
                    status=403,
                )
        return super(OTPRequiredMixin, self).dispatch(request, *args, **kwargs)
