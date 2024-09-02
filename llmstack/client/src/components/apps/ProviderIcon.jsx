import anthropicIcon_dark from "../../assets/images/anthropic-icon-dark.png";
import anthropicIcon_light from "../../assets/images/anthropic-icon-light.png";
import apolloIcon_dark from "../../assets/images/apollo-icon-dark.png";
import apolloIcon_light from "../../assets/images/apollo-icon-light.png";
import {
  default as azureIcon_dark,
  default as azureIcon_light,
} from "../../assets/images/azure-icon-light.png";
import cohereIcon_dark from "../../assets/images/cohere-icon-dark.png";
import cohereIcon_light from "../../assets/images/cohere-icon-light.png";
import elevenLabsIcon_dark from "../../assets/images/elevenlabs-icon-dark.png";
import elevenLabsIcon_light from "../../assets/images/elevenlabs-icon-light.png";
import heygenIcon_dark from "../../assets/images/heygen-icon-dark.png";
import heygenIcon_light from "../../assets/images/heygen-icon-light.png";
import linkedinIcon_dark from "../../assets/images/linkedin-icon-dark.png";
import linkedinIcon_light from "../../assets/images/linkedin-icon-light.png";
import localAiIcon_dark from "../../assets/images/localai-icon-dark.png";
import localAiIcon_light from "../../assets/images/localai-icon-light.png";
import openAiIcon_dark from "../../assets/images/openai-icon-dark.png";
import openAiIcon_light from "../../assets/images/openai-icon-light.png";
import promptlyIcon_light from "../../assets/images/promptly-icon-light.png";
import stabilityAiIcon_dark from "../../assets/images/stabilityai-icon-dark.png";
import stabilityAiIcon_light from "../../assets/images/stabilityai-icon-light.png";
import vertexAiIcon_dark from "../../assets/images/vertexai-icon-dark.png";
import vertexAiIcon_light from "../../assets/images/vertexai-icon-light.png";
import mistralAiIcon_light from "../../assets/images/mistral-icon-light.png";
import mistralAiIcon_dark from "../../assets/images/mistral-icon-dark.png";
import metaIcon_light from "../../assets/images/meta-icon-light.png";
import metaIcon_dark from "../../assets/images/meta-icon-dark.png";
import pineconeIcon_light from "../../assets/images/pinecone-icon-light.png";
import pineconeIcon_dark from "../../assets/images/pinecone-icon-dark.png";
import qdrantIcon_light from "../../assets/images/qdrant-icon-light.png";
import qdrantIcon_dark from "../../assets/images/qdrant-icon-dark.png";
import weaviateIcon_light from "../../assets/images/weaviate-icon-light.png";
import weaviateIcon_dark from "../../assets/images/weaviate-icon-dark.png";
import singlestoreIcon_light from "../../assets/images/singlestore-icon-light.png";
import singlestoreIcon_dark from "../../assets/images/singlestore-icon-dark.png";

export const getProviderIconImage = (icon, isActive) => {
  switch (icon?.replaceAll(" ", "").toLowerCase()) {
    case "promptly":
      return promptlyIcon_light;
    case "apollo":
      return isActive ? apolloIcon_dark : apolloIcon_light;
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
    case "linkedin":
      return isActive ? linkedinIcon_dark : linkedinIcon_light;
    case "heygen":
      return isActive ? heygenIcon_dark : heygenIcon_light;
    case "mistral":
      return isActive ? mistralAiIcon_dark : mistralAiIcon_light;
    case "meta":
      return isActive ? metaIcon_dark : metaIcon_light;
    case "pinecone":
      return isActive ? pineconeIcon_dark : pineconeIcon_light;
    case "qdrant":
      return isActive ? qdrantIcon_dark : qdrantIcon_light;
    case "weaviate":
      return isActive ? weaviateIcon_dark : weaviateIcon_light;
    case "singlestore":
      return isActive ? singlestoreIcon_dark : singlestoreIcon_light;
    default:
      return promptlyIcon_light;
  }
};

export function ProviderIcon({ providerSlug, isActive = false, style = null }) {
  return (
    <img
      src={getProviderIconImage(providerSlug, isActive)}
      alt={providerSlug}
      style={style || { width: 40, height: 40, marginRight: 10 }}
    />
  );
}
