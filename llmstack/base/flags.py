from flags import conditions
from flags.sources import Condition
from flags.state import flag_enabled

from llmstack.apps.models import App, AppVisibility
from llmstack.organizations.models import OrganizationSettings

from .models import Profile


class FlagSource(object):
    def get_flags(self):
        flags = {
            "IS_PRO_SUBSCRIBER": [
                Condition("pro_subscriber", False),
            ],
            "IS_BASIC_SUBSCRIBER": [
                Condition("basic_subscriber", False),
            ],
            "IS_ORGANIZATION_MEMBER": [
                Condition("organization_member", False),
            ],
            "IS_ORGANIZATION_OWNER": [
                Condition("organization_owner", False),
            ],
            "CAN_UPLOAD_APP_LOGO": [
                Condition("can_upload_app_logo", False),
            ],
            "CAN_PUBLISH_PUBLIC_APPS": [
                Condition("can_make_app_public_visible", True),
            ],
            "CAN_PUBLISH_UNLISTED_APPS": [
                Condition("can_make_app_unlisted_visible", True),
            ],
            "CAN_PUBLISH_ORG_APPS": [
                Condition("can_make_app_organization_visible", False),
            ],
            "CAN_PUBLISH_PRIVATE_APPS": [
                Condition("can_make_app_private_visible", False),
            ],
            "CAN_ADD_KEYS": [
                Condition("can_add_keys", True),
            ],
            "CAN_ADD_APP_DOMAIN": [
                Condition("can_add_app_domain", True),
            ],
            "HAS_EXCEEDED_MONTHLY_PROCESSOR_RUN_QUOTA": [
                Condition("has_exceeded_monthly_processor_run_quota", False),
            ],
            "HAS_EXCEEDED_STORAGE_QUOTA": [
                Condition("has_exceeded_storage_quota", False),
            ],
            "HAS_EXCEEDED_APP_CREATE_QUOTA": [
                Condition("has_exceeded_app_create_quota", False),
            ],
            "CAN_ADD_TWILIO_INTERGRATION": [
                Condition("can_add_twilio_integration", True),
            ],
            "CAN_EXPORT_HISTORY": [
                Condition("can_export_history", False),
            ],
        }

        return flags


@conditions.register("pro_subscriber")
def is_pro_subscriber(value, request=None, **kwargs):
    profile = Profile.objects.get(user=request.user)
    if not profile:
        return False

    return True


@conditions.register("basic_subscriber")
def is_basic_subscriber(value, request=None, **kwargs):
    profile = Profile.objects.get(user=request.user)
    if not profile:
        return False

    return False


@conditions.register("organization_member")
def is_organization_member(value, request=None, **kwargs):
    profile = Profile.objects.get(user=request.user)
    if not profile:
        return False

    return profile.organization is not None


@conditions.register("organization_owner")
def is_organization_owner(value, request=None, **kwargs):
    profile = Profile.objects.get(user=request.user)
    if not profile or profile.organization is None:
        return False

    return request.user.email == profile.organization.admin_email


@conditions.register("can_upload_app_logo")
def can_upload_app_logo(value, request=None, **kwargs):
    if flag_enabled(
        "IS_PRO_SUBSCRIBER",
        request=request,
    ) or flag_enabled(
        "IS_ORGANIZATION_MEMBER",
        request=request,
    ):
        return True

    return False


@conditions.register("can_make_app_public_visible")
def can_make_app_public_visible(value, request=None, **kwargs):
    user = request.user
    profile = Profile.objects.get(user=user)
    if not profile or profile.organization is None:
        return True

    # Get organization settings from the user's organization
    organization = profile.organization
    organization_settings = OrganizationSettings.objects.filter(
        organization=organization,
    ).first()
    if organization_settings and organization_settings.max_app_visibility != AppVisibility.PUBLIC:
        return False

    return True


@conditions.register("can_make_app_unlisted_visible")
def can_make_app_unlisted_visible(value, request=None, **kwargs):
    if flag_enabled(
        "IS_BASIC_SUBSCRIBER",
        request=request,
    ) or flag_enabled(
        "IS_PRO_SUBSCRIBER",
        request=request,
    ):
        return True

    if flag_enabled("IS_ORGANIZATION_MEMBER", request=request):
        user = request.user
        profile = Profile.objects.get(user=user)
        organization = profile.organization
        organization_settings = OrganizationSettings.objects.filter(
            organization=organization,
        ).first()
        if organization_settings and organization_settings.max_app_visibility >= AppVisibility.UNLISTED:
            return True

    return False


@conditions.register("can_make_app_organization_visible")
def can_make_app_organization_visible(value, request=None, **kwargs):
    user = request.user
    profile = Profile.objects.get(user=user)
    if not profile or profile.organization is None:
        return False

    # Get organization settings from the user's organization
    organization = profile.organization
    organization_settings = OrganizationSettings.objects.filter(
        organization=organization,
    ).first()
    if organization_settings and organization_settings.max_app_visibility >= AppVisibility.ORGANIZATION:
        return True

    return False


@conditions.register("can_make_app_private_visible")
def can_make_app_private_visible(value, request=None, **kwargs):
    if not request.user.is_authenticated:
        return False

    if flag_enabled(
        "IS_PRO_SUBSCRIBER",
        request=request,
    ) or flag_enabled(
        "IS_ORGANIZATION_MEMBER",
        request=request,
    ):
        return True

    published_private_apps = App.objects.filter(
        owner=request.user,
        is_published=True,
        visibility=AppVisibility.PRIVATE,
    )

    if len(published_private_apps) < 1 or (
        flag_enabled(
            "IS_BASIC_SUBSCRIBER",
            request=request,
        )
        and len(published_private_apps) < 10
    ):
        return True

    return False


@conditions.register("can_add_keys")
def can_add_keys(value, request=None, **kwargs):
    if flag_enabled("IS_ORGANIZATION_MEMBER", request=request):
        profile = Profile.objects.get(user=request.user)
        organization_settings = OrganizationSettings.objects.filter(
            organization=profile.organization,
        ).first()
        if profile and organization_settings and organization_settings.allow_user_keys:
            return True
        else:
            return False

    return True


@conditions.register("can_add_app_domain")
def can_add_app_domain(value, request=None, **kwargs):
    return False


@conditions.register("has_exceeded_monthly_processor_run_quota")
def has_exceeded_monthly_processor_run_quota(value, request=None, **kwargs):
    return False


@conditions.register("has_exceeded_storage_quota")
def has_exceeded_storage_quota(value, request=None, **kwargs):
    return False


@conditions.register("has_exceeded_app_create_quota")
def has_exceeded_app_create_quota(value, request=None, **kwargs):
    return False


@conditions.register("can_add_twilio_integration")
def can_add_twilio_integration(value, request=None, **kwargs):
    return True


@conditions.register("can_export_history")
def can_export_history(value, request=None, **kwargs):
    return True
