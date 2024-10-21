import ast
import logging

import openai
from django.conf import settings

logger = logging.getLogger(__name__)


openai_client = openai.Client(api_key=settings.DEFAULT_AUTOGEN_OPENAI_API_KEY)


def generate_app_session_share_metadata(app_name, messages, image_assets=[]) -> dict:
    """
    Generate metadata for the app session share. This metadata is used to store
    additional information about the app session share.

    Args:
        app_name (str): The name of the app.
        messages (list): The messages exchanged during the app session.
        assets (list): The assets generated during the app session.

    Returns:
        dict: The generated metadata containing
            - slug: The slug for the app session share based on the messages and assets. Uses app name if other information is not sufficient.
            - title: The title for the app session share.
            - description: The description for the app session share optimized for SEO.
            - cover_image: The cover image for the app session share.
            - additional_images: The additional images for the app session share.
    """

    full_prompt = f"""Generate metadata for the given session for SEO purposes. App name is "{app_name}". The metadata should include a slug, title, description, cover image, and additional images. DO NOT use app name or the word "session" in the metadata unless it appears in the messages.

The session contains the following messages between the user and the app:

{messages}.


It also contains the following assets generated during the session:

{image_assets}.

Example metadata:
{{
    "slug": "short-slug-based-on-messages-and-assets",
    "title": "Short descriptive title",
    "description": "Summary of the activity.",
    "cover_image": "objref://sessionfiles/cover_image_asset_uuid",
    "additional_images": [
        "objref://sessionfiles/additional_image_1_asset_uuid",
        "objref://sessionfiles/additional_image_2_asset_uuid",
    ]
}}

- slug should be short and descriptive of the messages and assets in the session.
- title should be concise for the app session. It should capture a summary of the messages.
- description shouldn't directly refer to the messages or assets but should be a summary of the app session share. Consider the SEO implications.
- cover image should be the primary image that represents the app session share.
- additional images should be other images that complement the cover image. Maximum of 6 images.
"""

    system_message = {
        "role": "system",
        "content": "You are an assistant helping generate metadata in JSON for the provided app activity.",
    }

    user_message = {
        "role": "user",
        "content": full_prompt,
    }

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[system_message, user_message],
        temperature=1,
        stream=False,
        response_format={"type": "json_object"},
    )

    metadata = response.choices[0].message.content if len(response.choices) > 0 and response.choices[0].message else ""

    logger.info(f"Generated metadata for app session share: {metadata}")

    return ast.literal_eval(metadata) if metadata else {}
