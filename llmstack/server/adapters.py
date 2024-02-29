import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    def post_login(self, request, user, *, email_verification, signal_kwargs, email, signup, redirect_url):
        if "redirectUrl" in request.session:
            redirect_url = request.session["redirectUrl"]
            del request.session["redirectUrl"]

        return super().post_login(
            request,
            user,
            email_verification=email_verification,
            signal_kwargs=signal_kwargs,
            email=email,
            signup=signup,
            redirect_url=redirect_url,
        )

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, False)
        if not user.username:
            user.username = user.email

        # Apple login doesn't seem to provide email, so we use username as
        # email
        if not user.email:
            user.email = user.username

        if commit:
            user.save()
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        if not user.username:
            user.username = user.email

        # Apple login doesn't seem to provide email, so we use username as
        # email
        if not user.email:
            user.email = user.username

        return user

    def get_connect_redirect_url(self, request, socialaccount):
        logger.debug(f"get_connect_redirect_url: params: {request.GET}")
        return request.GET.get("redirectUrl", "/")
