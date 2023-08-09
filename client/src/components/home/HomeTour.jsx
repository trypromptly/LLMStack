import { useState } from "react";
import { useCookies } from "react-cookie";

import { Tour } from "antd";

export default function HomeTour({
  tourRef1,
  tourRef2,
  tourRef3,
  tourRef4,
  tourRef5,
  tourRef6,
}) {
  const tourSteps = [
    {
      title: "Welcome to Promptly",
      description:
        "Test, version and share your prompts with others. Create Endpoints and call from your application to invoke LLMs with saved prompts.",
    },
    {
      title: "Pick your LLM Provider",
      description:
        "Use this toggle to use an existing endpoint or pick a new backend. Update model parameters to the right. Use Discover on left to find new Prompts",
      target: () => tourRef1.current,
    },
    {
      title: "Prompt Editor",
      description:
        "This is where you can write your prompt. Use {{}} to add variables and form in next tab to fill the values.",
      target: () => tourRef4.current,
    },
    {
      title: "Share Prompt",
      description:
        "Use this button to share your Prompt and output. API keys and Endpoints are NOT shared!",
      target: () => tourRef5.current,
    },
    {
      title: "Test Prompt",
      description:
        "Click this to Test Your Prompt. Add your API keys in the settings for better results. Go Click Now!",
      target: () => tourRef6.current,
    },
  ];
  const [cookies, setCookie] = useCookies(["tour"]);
  const [showTour, setShowTour] = useState(cookies["tour"] === undefined);

  return (
    <Tour
      open={showTour}
      onClose={() => {
        setShowTour(false);
        setCookie("tour", "1");
      }}
      steps={tourSteps}
      style={{ width: "100%" }}
    />
  );
}
