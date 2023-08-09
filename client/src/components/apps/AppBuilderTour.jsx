import { useState } from "react";
import { useCookies } from "react-cookie";

import { Tour } from "antd";

export default function AppBuilderTour({
  tourRef1,
  tourRef2,
  tourRef3,
  tourRef4,
  tourRef5,
  tourRef6,
  page,
}) {
  const tourSteps = [
    {
      title: "Welcome to Promptly",
      description:
        "Here is a quick how-to video to get started with app builder. With Promptly, you can build AI apps and chatbots by chaining processors together. Platform documentation can be found at https://docs.trypromptly.com",
      cover: (
        <video width="100%" height="100%" autoPlay loop muted>
          <source
            src="https://storage.googleapis.com/trypromptly-static/static/images/promptly-app-builder-demo.mp4"
            type="video/mp4"
          />
        </video>
      ),
    },
    {
      title: "Name your App, preview and publish externally",
      description:
        "You can rename your app, preview it and publish it externally from this bar.",
      target: () => tourRef1.current,
    },
    {
      title: "App Input",
      description:
        "This is where you can define the input to your app. You can add inputs using the Add Fields button. This will be rendered as a form in the published app.",
      target: () => tourRef2.current,
    },
    {
      title: "Processor Chain",
      description:
        "Processor nodes are the building blocks of your app. You can add multiple processors and connect them to form a chain. Each processor is typically a LLM or an API call. For example, you can add Open AI's ChatGPT as a processor, configure it and connect its output to DALL-E in the next processor.",
      target: () => tourRef3.current,
    },
    {
      title: "App Output",
      description:
        "This is where you can define the output of your app. You can use Template Variables and insert user input data or the output from any processor as input in processors below it. Template variables can be used in the output of the app as well",
      target: () => tourRef4.current,
    },
    {
      title: "Save your App",
      description:
        "Click this to save your app before previewing. You can also publish it externally from the top bar. Make sure to add your Open AI or DreamStudio API keys in the settings page before running your app.",
      target: () => tourRef5.current,
    },
    {
      title: "App Menu",
      description:
        "Use this menu to navigate between different pages of the app like editor, preview, settings, integrations etc.",
      target: () => tourRef6.current,
    },
  ];
  const [cookies, setCookie] = useCookies([
    "app-builder-tour",
    "app-template-tour",
  ]);
  const [showTour, setShowTour] = useState(
    ((!page || page === "editor") &&
      cookies["app-builder-tour"] === undefined) ||
      (page === "template" && cookies["app-template-tour"] === undefined),
  );

  return (
    <Tour
      open={showTour}
      onClose={() => {
        setShowTour(false);
        !page || (page === "editor" && setCookie("app-builder-tour", "1"));
        page === "template" && setCookie("app-template-tour", "1");
      }}
      steps={
        !page || page === "editor"
          ? tourSteps
          : [tourSteps[0], tourSteps[1], tourSteps[6]]
      }
      style={{ width: "100%" }}
    />
  );
}
