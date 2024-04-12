from datetime import datetime
from typing import Literal, Optional, Union

import httpx
import requests
from openai._base_client import make_request_options  # type: ignore # noqa: F401
from openai._types import NOT_GIVEN, Body, FileTypes, Headers, Query
from openai.resources import Images as OpenAIImages
from openai.resources.images import ImagesWithRawResponse
from openai.types import ImageGenerateParams

from llmstack.common.utils.sslr.constants import PROVIDER_OPENAI, PROVIDER_STABILITYAI
from llmstack.common.utils.sslr.types.image import Image

from .._utils import cached_property, maybe_transform
from ..types import images_response


class Images(OpenAIImages):
    @cached_property
    def with_raw_response(self) -> ImagesWithRawResponse:
        return ImagesWithRawResponse(self)

    def create_variation(
        self,
        *,
        image: FileTypes,
        model: Union[str, Literal["dall-e-2"], None] = NOT_GIVEN,
        n: Optional[int] = NOT_GIVEN,
        response_format: Optional[Literal["url", "b64_json"]] = NOT_GIVEN,
        size: Optional[Literal["256x256", "512x512", "1024x1024"]] = NOT_GIVEN,
        user: Optional[str] = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: Optional[float | httpx.Timeout | None] = NOT_GIVEN,
    ) -> images_response.ImagesResponse:
        return self.create_variation(
            image=image,
            model=model,
            n=n,
            response_format=response_format,
            size=size,
            user=user,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            timeout=timeout,
        )

    def edit(
        self,
        *,
        image: FileTypes,
        prompt: str,
        mask: Union[FileTypes] = NOT_GIVEN,
        model: Union[str, Literal["dall-e-2"], None] = NOT_GIVEN,
        n: Optional[int] = NOT_GIVEN,
        response_format: Optional[Literal["url", "b64_json"]] = NOT_GIVEN,
        size: Optional[Literal["256x256", "512x512", "1024x1024"]] = NOT_GIVEN,
        user: str = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: Union[float, httpx.Timeout, None] = NOT_GIVEN,
    ) -> images_response.ImagesResponse:
        return super().edit(
            image=image,
            prompt=prompt,
            mask=mask,
            model=model,
            n=n,
            response_format=response_format,
            size=size,
            user=user,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            timeout=timeout,
        )

    def generate(
        self,
        *,
        prompt: str,
        model: Union[str, Literal["dall-e-2", "dall-e-3"], None] = NOT_GIVEN,
        n: Optional[int] = NOT_GIVEN,
        quality: Literal["standard", "hd"] = NOT_GIVEN,
        response_format: Optional[Literal["url", "b64_json"]] = NOT_GIVEN,
        size: Optional[Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]] = "1024x1024",
        style: Optional[Literal["vivid", "natural"]] = NOT_GIVEN,
        user: Union[str] = NOT_GIVEN,
        seed: Optional[int] = NOT_GIVEN,
        negative_prompt: Optional[str] = NOT_GIVEN,
        aspect_ratio: Optional[float] = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: Union[float, httpx.Timeout, None] = NOT_GIVEN,
        **kwargs,
    ) -> images_response.ImagesResponse:
        if self._client._llm_router_provider == PROVIDER_OPENAI:
            path = "/images/generations"
            body = maybe_transform(
                {
                    "prompt": prompt,
                    "model": model,
                    "n": n,
                    "quality": quality,
                    "response_format": response_format,
                    "size": size,
                    "style": style,
                    "user": user,
                    "seed": seed,
                    "negative_prompt": negative_prompt,
                    "aspect_ratio": aspect_ratio,
                },
                ImageGenerateParams,
            )
        elif self._client._llm_router_provider == PROVIDER_STABILITYAI:
            if model == "core":
                path = "/v2beta/stable-image/generate/core"
                body = {"prompt": prompt, "output_format": "png"}
                if aspect_ratio:
                    body["aspect_ratio"] = aspect_ratio
                if negative_prompt:
                    body["negative_prompt"] = negative_prompt
                if seed:
                    body["seed"] = seed
                if style:
                    body["style_preset"] = style

                response_format = "url"
                url = f"{self._client._base_url}{path}"
                header_accept = "application/json;type=image/png"
                response = requests.post(
                    url=url,
                    headers={"authorization": "Bearer " + self._client.api_key, "accept": header_accept},
                    data=body,
                    files={"none": ""},
                )
                if response.status_code == 200:
                    finish_reason = response.headers.get("finish_reason")
                    if finish_reason == "CONTENT_FILTERED":
                        raise self._client._make_status_error("Content filtered.", body=body, response=response)
                    content_type = "image/png"
                    seed = response.headers.get("seed")
                    timestamp = int(datetime.now().timestamp())
                    image_b64_str = response.json().get("image")
                    timestamp = int(datetime.now().timestamp())
                    return images_response.ImagesResponse(
                        created=timestamp,
                        data=[Image(b64_json=image_b64_str, mime_type=content_type, metadata={"seed": seed})],
                    )

                else:
                    raise self._client._make_status_error("Error in generating image.", body=body, response=response)
            elif (
                model == "stable-diffusion-xl-1024-v1-0"
                or model == "stable-diffusion-v1-6"
                or model == "stable-diffusion-xl-beta-v2-2-2"
            ):
                path = f"/v1/generation/{model}/text-to-image"
                text_prompts = []
                if prompt:
                    text_prompts.append({"text": prompt, "weight": 1.0})
                if negative_prompt:
                    text_prompts.append({"text": negative_prompt, "weight": -1.0})
                body = {
                    "height": int(size.split("x")[1]),
                    "width": int(size.split("x")[0]),
                    "text_prompts": text_prompts,
                    "cfg_scale": kwargs.get("cfg_scale", 7),
                    "samples": 1,
                    "steps": kwargs.get("steps", 30),
                    "clip_guidance_preset": kwargs.get("clip_guidance_preset", "NONE"),
                }
                url = f"{self._client._base_url}{path}"
                response = requests.post(
                    url=url,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Authorization": f"Bearer {self._client.api_key}",
                    },
                    json=body,
                )
                if response.status_code == 200:
                    finish_reason = response.headers.get("Finish-Reason")
                    if finish_reason == "CONTENT_FILTERED":
                        raise self._client._make_status_error("Content filtered.", body=body, response=response)

                    seed = response.headers.get("Seed")
                    content_type = response.headers.get("Content-Type")
                    timestamp = int(datetime.now().timestamp())
                    image_b64_str = response.json().get("artifacts")[0]["base64"]

                    return images_response.ImagesResponse(
                        created=timestamp,
                        data=[Image(b64_json=image_b64_str, mime_type="image/png", metadata={"seed": seed})],
                    )
            else:
                raise ValueError("Invalid model for StabilityAI")
        result = self._post(
            path,
            body=body,
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=images_response.ImagesResponse,
        )
        return result
