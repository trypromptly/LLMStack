(function () {
  // Create a custom HTML element 'promptly-app-embed'
  class PromptlyAppEmbed extends HTMLElement {
    constructor() {
      super();

      // Get the attributes from the custom element
      const publishedAppId = this.getAttribute("published-app-id");
      const chatBubble = this.getAttribute("chat-bubble");

      // Create an iframe element
      const iframe = document.createElement("iframe");

      // Set the iframe attributes
      iframe.setAttribute("id", `promptly-iframe-embed-${publishedAppId}`);
      iframe.setAttribute(
        "src",
        `https://trypromptly.com/app/${publishedAppId}/embed${
          chatBubble ? "/chatBubble" : ""
        }`,
      );
      iframe.setAttribute("width", this.getAttribute("width") || "100%");
      iframe.setAttribute("height", this.getAttribute("height") || "700");
      iframe.setAttribute("scrolling", this.getAttribute("scrolling") || "no");
      iframe.setAttribute("frameborder", this.getAttribute("style") || "0");
      iframe.setAttribute("style", this.getAttribute("style") || "");

      if (chatBubble) {
        iframe.setAttribute(
          "style",
          "position: fixed; bottom: 0; right: 0; z-index: 1000; height: auto; width: auto;",
        );
      }

      // Attach the iframe to the custom element
      this.appendChild(iframe);

      // Add a listener to the iframe to listen for messages
      window.addEventListener("message", (event) => {
        if (
          event.data.type === "promptly-embed-open" &&
          event.data.width &&
          event.data.height
        ) {
          iframe.style.width = event.data.width;
          iframe.style.height = event.data.height;
        } else if (
          event.data.type === "promptly-embed-resize" &&
          event.data.width &&
          event.data.height
        ) {
          iframe.width = event.data.width;
          iframe.height = event.data.width;
          iframe.style.width = event.data.width + 20 + "px";
          iframe.style.height = event.data.height + 20 + "px";
        } else if (event.data.type === "promptly-embed-close") {
          setTimeout(() => {
            iframe.style.width = "auto";
            iframe.style.height = "auto";
          }, 300);
        }
      });
    }
  }

  // Register the custom element
  customElements.define("promptly-app-embed", PromptlyAppEmbed);
})();
