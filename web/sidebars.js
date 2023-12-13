/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docSidebar: [
    "introduction",
    {
      type: "category",
      label: "Getting Started",
      link: { type: "doc", id: "getting-started/introduction" },
      items: [
        "getting-started/ui",
        "getting-started/first-app",
        "getting-started/config",
        "getting-started/deployment",
        "getting-started/administration",
        "getting-started/development",
      ],
    },
    {
      type: "category",
      label: "Processors",
      link: { type: "doc", id: "processors/introduction" },
      items: [
        "processors/promptly",
        "processors/openai",
        "processors/azure",
        "processors/google",
        "processors/cohere",
        "processors/stability",
        "processors/elevenlabs",
        "processors/localai",
      ],
    },
    {
      type: "category",
      label: "Apps",
      link: { type: "doc", id: "apps/introduction" },
      items: [
        "apps/types",
        "apps/builder",
        "apps/variables",
        "apps/templates",
        "apps/sharing",
        {
          type: "category",
          label: "Integrations",
          items: [
            "apps/integrations/web",
            "apps/integrations/embed",
            "apps/integrations/api",
            "apps/integrations/discord",
            "apps/integrations/slack",
            "apps/integrations/whatsapp",
          ],
        },
      ],
    },
    {
      type: "category",
      label: "Datasources",
      link: { type: "doc", id: "datasources/introduction" },
      items: [],
    },
    {
      type: "category",
      label: "Connections",
      link: { type: "doc", id: "connections/introduction" },
      items: [],
    },
    {
      type: "category",
      label: "Jobs",
      link: { type: "doc", id: "jobs/introduction" },
      items: [],
    },
    {
      type: "category",
      label: "APIs",
      link: { type: "doc", id: "apis/introduction" },
      items: [],
    },
    {
      type: "category",
      label: "Development",
      link: { type: "doc", id: "development/introduction" },
      items: [],
    },
    {
      type: "category",
      label: "Guides",
      items: [
        "guides/contributing",
        "guides/add-custom-processor",
        "guides/add-external-datasource",
      ],
    },
    "promptly",
  ],
};

module.exports = sidebars;
