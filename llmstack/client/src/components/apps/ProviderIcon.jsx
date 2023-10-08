import promptlyIcon_light from "../../assets/images/promptly-icon-light.png";
import openAiIcon_light from "../../assets/images/openai-icon-light.png";
import openAiIcon_dark from "../../assets/images/openai-icon-dark.png";
import stabilityAiIcon_light from "../../assets/images/stabilityai-icon-light.png";
import stabilityAiIcon_dark from "../../assets/images/stabilityai-icon-dark.png";
import anthropicIcon_light from "../../assets/images/anthropic-icon-light.png";
import anthropicIcon_dark from "../../assets/images/anthropic-icon-dark.png";
import cohereIcon_light from "../../assets/images/cohere-icon-light.png";
import cohereIcon_dark from "../../assets/images/cohere-icon-dark.png";
import azureIcon_light from "../../assets/images/azure-icon-light.png";
import azureIcon_dark from "../../assets/images/azure-icon-light.png";
import elevenLabsIcon_light from "../../assets/images/elevenlabs-icon-light.png";
import elevenLabsIcon_dark from "../../assets/images/elevenlabs-icon-dark.png";
import vertexAiIcon_light from "../../assets/images/vertexai-icon-light.png";
import vertexAiIcon_dark from "../../assets/images/vertexai-icon-dark.png";
import localAiIcon_light from "../../assets/images/localai-icon-light.png";
import localAiIcon_dark from "../../assets/images/localai-icon-dark.png";

const getIconImage = (icon, isActive) => {
  switch (icon?.replaceAll(" ", "").toLowerCase()) {
    case "promptly":
      return promptlyIcon_light;
    case "anthropic":
      return isActive ? anthropicIcon_dark : anthropicIcon_light;
    case "openai":
      return isActive ? openAiIcon_dark : openAiIcon_light;
    case "stabilityai":
      return isActive ? stabilityAiIcon_dark : stabilityAiIcon_light;
    case "cohere":
      return isActive ? cohereIcon_dark : cohereIcon_light;
    case "azure":
      return isActive ? azureIcon_dark : azureIcon_light;
    case "elevenlabs":
      return isActive ? elevenLabsIcon_dark : elevenLabsIcon_light;
    case "google":
      return isActive ? vertexAiIcon_dark : vertexAiIcon_light;
    case "localai":
      return isActive ? localAiIcon_dark : localAiIcon_light;
    default:
      return promptlyIcon_light;
  }
};

export function ProviderIcon({
  provider_slug,
  isActive = false,
  style = null,
}) {
  return (
    <img
      src={getIconImage(provider_slug, isActive)}
      alt={provider_slug}
      style={style || { width: 40, height: 40, marginRight: 10 }}
    />
  );
}
