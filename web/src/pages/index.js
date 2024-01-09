import React from "react";
import clsx from "clsx";
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";
import HomepageFeatures from "@site/src/components/HomepageFeatures";
import GitHubButton from "react-github-btn";
import ReactPlayer from "react-player";

import styles from "./index.module.css";

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={clsx("hero hero--primary", styles.heroBanner)}>
      <div className="container">
        <h1 className="hero__title">{siteConfig.title}</h1>
        <p className="hero__subtitle">
          Open-source platform to build AI Agents, workflows and applications
          with your data
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
        <p></p>
        <ReactPlayer
          style={{ margin: "auto" }}
          playing
          url="https://www.youtube.com/watch?v=P9VoR8WPy7E"
          loop
          muted
          width={"900px"}
          height={"505px"}
          config={{
            youtube: {
              playerVars: {
                showinfo: 0,
                autoplay: 1,
                controls: 1,
              },
            },
          }}
        />
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
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
