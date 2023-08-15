// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require("prism-react-renderer/themes/github");
const darkCodeTheme = require("prism-react-renderer/themes/dracula");

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "LLMStack",
  tagline: "AI Apps and Chatbots in Minutes | No-code AI App Builder",
  favicon: "img/llmstack-icon.png",

  // Set the production url of your site here
  url: "https://llmstack.ai",
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: "/",

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: "trypromptly", // Usually your GitHub org/user name.
  projectName: "LLMStack", // Usually your repo name.

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
        },
        blog: {
          showReadingTime: true,
        },
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image:
        "https://storage.googleapis.com/trypromptly-static/static/images/opengraph.jpg",
      navbar: {
        title: "",
        logo: {
          alt: "LLMStack",
          src: "img/logo.svg",
          srcDark: "img/logo-grayscale.svg",
        },
        items: [
          {
            type: "docSidebar",
            sidebarId: "tutorialSidebar",
            position: "left",
            label: "Docs",
          },
          {
            href: "https://github.com/trypromptly/LLMStack",
            label: "GitHub",
            position: "right",
          },
        ],
      },
      footer: {
        style: "dark",
        links: [
          {
            title: "Docs",
            items: [
              {
                label: "Application",
                to: "/docs/application/",
              },
              {
                label: "Processor",
                to: "/docs/processor/",
              },
              {
                label: "Data",
                to: "/docs/data/",
              },
              {
                label: "Contribution Guide",
                to: "/docs/guides/Contribution-Guide",
              },
            ],
          },
          {
            title: "Community",
            items: [
              {
                label: "Discord",
                href: "https://discord.gg/3JsEzSXspJ",
              },
              {
                label: "LinkedIn",
                href: "https://linkedin.com/company/trypromptly",
              },
              {
                label: "Twitter",
                href: "https://twitter.com/trypromptly",
              },
            ],
          },
          {
            title: "More",
            items: [
              {
                label: "Blog",
                href: "https://blog.trypromptly.com",
              },
              {
                label: "GitHub",
                href: "https://github.com/trypromptly/llmstack",
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} MakerDojo, Inc.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),
};

module.exports = config;
