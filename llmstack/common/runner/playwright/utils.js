window.clearTags = () => {
  const tags = document.querySelectorAll('[id^="__llmstack-"]');
  tags.forEach((tag) => tag.remove());
};

const addBoundingBox = (element, tag) => {
  element.style.outline = "1px solid red";
  const text = document.createElement("div");
  text.id = "__llmstack-" + tag;
  text.textContent = tag;
  text.style.position = "absolute";
  text.style.top = element.offsetTop + "px";
  text.style.left = element.offsetLeft + "px";
  text.style.color = "red";
  text.style.fontSize = "12px";
  text.style.backgroundColor = "white";

  const locatorParent = element.parentElement;
  locatorParent ? locatorParent.appendChild(text) : element.appendChild(text);
};

const skipElement = (el) => {
  const rect = el.getBoundingClientRect();

  if (rect.width === 0 || rect.height === 0) return true;

  if (el.disabled || el.hidden) return true;

  if (el.style?.display === "none") return true;

  if (el.tagName === "SCRIPT" || el.tagName === "STYLE") return true;
};

window.addTags = () => {
  // Clear existing tags
  clearTags();

  // Get text from the page
  const text = document.body.innerText;

  const getAllElements = (selector) => {
    return Array.from(document.querySelectorAll(selector))
      .map((element, index) => {
        // Skip if the element is disabled or not visible
        if (skipElement(element)) return null;

        let tag = `${selector.slice(0, 1)}=${index}`;
        if (selector === "textarea") {
          tag = `ta=${index}`;
        } else if (selector === "input") {
          tag = `in=${index}`;
        }

        addBoundingBox(element, tag);

        return {
          text: element.textContent.trim(),
          type: element.type || "",
          url: element.href || "",
          tag: tag,
        };
      })
      .filter((el) => el !== null);
  };

  return {
    buttons: getAllElements("button"),
    inputs: getAllElements("input"),
    selects: getAllElements("select"),
    textareas: getAllElements("textarea"),
    links: getAllElements("a"),
    text: text,
  };
};
