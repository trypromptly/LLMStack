(function () {
  // Create a custom HTML element 'promptly-app-embed'
  class PromptlyAppEmbed extends HTMLElement {
    constructor() {
      super();

      // Get the attributes from the custom element
      const publishedAppId = this.getAttribute("published-app-id");
      const chatBubble = this.getAttribute("chat-bubble");
      const minWidth = this.getAttribute("min-width");
      const minHeight = this.getAttribute("min-height");
      const maxWidth = this.getAttribute("max-width");
      const maxHeight = this.getAttribute("max-height");

      // Create an iframe element
      const iframe = document.createElement("iframe");

      // Set the iframe attributes
      iframe.setAttribute("id", `promptly-iframe-embed-${publishedAppId}`);
      iframe.setAttribute(
        "src",
        `${
          this.getAttribute("host") || "https://trypromptly.com"
        }/app/${publishedAppId}/embed${chatBubble ? "/chatBubble" : ""}`
      );
      iframe.setAttribute("width", this.getAttribute("width") || "100%");
      iframe.setAttribute("height", this.getAttribute("height") || "700");
      iframe.setAttribute("scrolling", this.getAttribute("scrolling") || "no");
      iframe.setAttribute(
        "frameborder",
        this.getAttribute("frameborder") || "0"
      );

      if (chatBubble) {
        iframe.setAttribute(
          "style",
          "position: fixed; bottom: 0; right: 0; z-index: 1000; height: auto; width: auto;"
        );
      }

      // Set the iframe style attribute if it exists
      if (this.getAttribute("style")) {
        iframe.setAttribute("style", this.getAttribute("style"));
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

          if (minWidth) {
            iframe.style.width = minWidth;
          }

          if (minHeight) {
            iframe.style.height = minHeight;
          }

          if (maxWidth) {
            iframe.style.maxWidth = maxWidth;
          }

          if (maxHeight) {
            iframe.style.maxHeight = maxHeight;
          }
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

  class PromptlyDatasourceEmbed extends HTMLElement {
    constructor() {
      super();

      // Get the attributes from the custom element
      const datasourceId = this.getAttribute("datasource-id");
      const signature = this.getAttribute("signature");
      const minWidth = this.getAttribute("min-width");
      const minHeight = this.getAttribute("min-height");
      const maxWidth = this.getAttribute("max-width");
      const maxHeight = this.getAttribute("max-height");

      // Create an iframe element
      const iframe = document.createElement("iframe");

      // Set the iframe attributes
      iframe.setAttribute("id", `promptly-iframe-embed-${datasourceId}`);
      iframe.setAttribute(
        "src",
        `${
          this.getAttribute("host") || "https://trypromptly.com"
        }/datasources/${datasourceId}/embed?_signature=${signature}`
      );
      iframe.setAttribute("width", this.getAttribute("width") || "100%");
      iframe.setAttribute("height", this.getAttribute("height") || "700");
      iframe.setAttribute("scrolling", this.getAttribute("scrolling") || "no");
      iframe.setAttribute(
        "frameborder",
        this.getAttribute("frameborder") || "0"
      );

      // Set the iframe style attribute if it exists
      if (this.getAttribute("style")) {
        iframe.setAttribute("style", this.getAttribute("style"));
      }

      // Attach the iframe to the custom element
      this.appendChild(iframe);

      console.log("iframe", iframe);
      // Add a listener to the iframe to listen for messages
      window.addEventListener("message", (event) => {
        if (
          event.data.type === "promptly-embed-open" &&
          event.data.width &&
          event.data.height
        ) {
          iframe.style.width = event.data.width;
          iframe.style.height = event.data.height;

          if (minWidth) {
            iframe.style.width = minWidth;
          }

          if (minHeight) {
            iframe.style.height = minHeight;
          }

          if (maxWidth) {
            iframe.style.maxWidth = maxWidth;
          }

          if (maxHeight) {
            iframe.style.maxHeight = maxHeight;
          }
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
  customElements.define("promptly-datasource-embed", PromptlyDatasourceEmbed);
})();
