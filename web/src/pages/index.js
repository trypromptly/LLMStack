import React from "react";
import clsx from "clsx";
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";
import HomepageFeatures from "@site/src/components/HomepageFeatures";
import GitHubButton from "react-github-btn";

import styles from "./index.module.css";

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={clsx("hero hero--primary", styles.heroBanner)}>
      <div className="container">
        <h1 className="hero__title">{siteConfig.title}</h1>
        <p className="hero__subtitle">
          Open-source platform to build AI apps, chatbots and agents with your
          data
        </p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            href="https://trypromptly.com"
          >
            Try Cloud Offering
          </Link>
          <Link className="button button--primary button--lg" to="/docs/">
            Deploy LLMStack
          </Link>
        </div>
        <div className={styles.githubButtons}>
          <GitHubButton
            href="https://github.com/trypromptly/LLMStack"
            data-size="large"
            data-show-count="true"
            aria-label="Star trypromptly/LLMStack on GitHub"
          >
            Star
          </GitHubButton>
        </div>
      </div>
    </header>
  );
}

export default function Home() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} | ${siteConfig.tagline}`}
      description="No-code platform to build generative AI apps, chatbots and agents with your data."
    >
      <HomepageHeader />
      <main>
        <div
          style={{
            position: "relative",
            paddingBottom: "64.92335437330928%",
            height: 0,
          }}
        >
          <iframe
            src="https://www.loom.com/embed/1399a39c19394d9cad224e2e62c15285?sid=24115d9b-7ad4-4e5f-bdd9-110895fc1bae"
            frameborder="0"
            webkitallowfullscreen
            mozallowfullscreen
            allowfullscreen
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
            }}
          ></iframe>
        </div>
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
