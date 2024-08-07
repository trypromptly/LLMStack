import logging

logger = logging.getLogger(__name__)


def get_asset_by_objref_internal(objref):
    """
    Get asset by objref if one exists.
    """
    from llmstack.apps.models import AppDataAssets, AppSessionFiles
    from llmstack.data.models import DataSourceEntryFiles

    if not objref:
        return None

    asset = None

    try:
        category, uuid = objref.strip().split("//")[1].split("/")
        model_cls = None

        if category == "sessionfiles":
            model_cls = AppSessionFiles
        elif category == "appdata":
            model_cls = AppDataAssets
        elif category == "datasource_entries":
            model_cls = DataSourceEntryFiles
        else:
            return None

        asset = model_cls.objects.get(uuid=uuid)
    except Exception as e:
        logger.error(f"Error retrieving asset: {e}")

    return asset


def get_asset_by_objref(objref, request_user, request_session):
    """
    Get asset by objref if one exists and is accessible by the user.
    """
    asset = get_asset_by_objref_internal(objref)
    if not asset or not asset.is_accessible(request_user, request_session):
        return None

    return asset
