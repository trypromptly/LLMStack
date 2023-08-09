import React from "react";
import clsx from "clsx";
import styles from "./styles.module.css";

const FeatureList = [
  {
    title: "Model Chaining",
    Svg: require("@site/static/img/undraw_docusaurus_mountain.svg").default,
    description: (
      <>
        LLMStack supports all major model providers, like OpenAI, Cohere,
        Stability AI, Hugging Face, and more. Easily use these models to build
        powerful apps.
      </>
    ),
  },
  {
    title: "Bring your own Data",
    Svg: require("@site/static/img/undraw_docusaurus_tree.svg").default,
    description: (
      <>
        Import your own data and connect it to LLM models to supercharge your
        generative AI applications and chatbots. Promptly supports a wide
        variety of data sources, including Web URLs, Sitemaps, PDFs, Audio,
        PPTs, Google Drive, Notion imports etc.
      </>
    ),
  },
  {
    title: "Build Apps Collaboratively",
    Svg: require("@site/static/img/undraw_docusaurus_react.svg").default,
    description: (
      <>
        Share apps publicly with everyone on the internet or restrict access to
        only certain individuals using our granular permission model. Viewer and
        collaborator roles to allow multiple users to modify and build the app
        together.
      </>
    ),
  },
];

function Feature({ Svg, title, description }) {
  return (
    <div className={clsx("col col--4")}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
