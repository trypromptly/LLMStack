import React, { lazy } from "react";
import ReactDOM from "react-dom/client";
import "./index.css";

import reportWebVitals from "./reportWebVitals";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { RecoilRoot } from "recoil";
import { ConfigProvider, Layout } from "antd";
import CircularProgress from "@mui/material/CircularProgress";

const App = lazy(() => import("./App"));
const ErrorPage = lazy(() => import("./pages/error"));
const HomePage = lazy(() => import("./pages/home"));
const LoginPage = lazy(() => import("./pages/login"));
const SignupPage = lazy(() => import("./pages/signup"));
const DashboardPage = lazy(() => import("./pages/dashboard"));
const HistoryPage = lazy(() => import("./pages/history"));
const HistoryPageOld = lazy(() => import("./pages/historyold"));
const SettingPage = lazy(() => import("./pages/setting"));
const OrganizationPage = lazy(() => import("./pages/organization"));
const TestPage = lazy(() => import("./pages/tests"));
const AppRenderPage = lazy(() => import("./pages/AppRender"));
const AppStudioPage = lazy(() => import("./pages/AppStudio"));
const AppEditPage = lazy(() => import("./pages/AppEdit"));
const DataPage = lazy(() => import("./pages/data"));
const Discover = lazy(() => import("./pages/discover"));

let router = null;

const root = ReactDOM.createRoot(document.getElementById("root"));

if (
  window.location.host.split(".").length === 4 &&
  window.location.host.split(".")[1] === "app"
) {
  let subdomain = window.location.host.split(".")[1];
  if (subdomain === "app") {
    const publishedAppIdParam = window.location.host.split(".")[0];
    router = createBrowserRouter([
      {
        path: "/",
        element: (
          <AppRenderPage
            headless={true}
            publishedAppIdParam={publishedAppIdParam}
          />
        ),
        errorElement: <ErrorPage />,
      },
    ]);
  }
} else {
  router = createBrowserRouter([
    {
      path: "/",
      element: (
        <App>
          <AppStudioPage />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/playground",
      element: (
        <App>
          <HomePage isSharedPageMode={false} />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps",
      element: (
        <App>
          <AppStudioPage />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/templates/:appTemplateSlug",
      element: (
        <App>
          <AppStudioPage />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appTypeSlug/create",
      element: (
        <App>
          <AppEditPage />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appId",
      element: (
        <App>
          <AppEditPage />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appId/preview",
      element: (
        <App>
          <AppEditPage page="preview" />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appId/template",
      element: (
        <App>
          <AppEditPage page="template" />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appId/editor",
      element: (
        <App>
          <AppEditPage page="editor" />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appId/editor",
      element: (
        <App>
          <AppEditPage page="editor" />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appId/history",
      element: (
        <App>
          <AppEditPage page="history" />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appId/tests",
      element: (
        <App>
          <AppEditPage page="tests" />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appId/versions",
      element: (
        <App>
          <AppEditPage page="versions" />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appId/integrations/website",
      element: (
        <App>
          <AppEditPage page="integrations/website" />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appId/integrations/api",
      element: (
        <App>
          <AppEditPage page="integrations/api" />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appId/integrations/slack",
      element: (
        <App>
          <AppEditPage page="integrations/slack" />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appId/integrations/discord",
      element: (
        <App>
          <AppEditPage page="integrations/discord" />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/apps/:appId/preview",
      element: (
        <App>
          <AppEditPage page="preview" />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/app/:publishedAppId/:embed?/:chatBubble?",
      element: <AppRenderPage headless={true} />,
      errorElement: <ErrorPage />,
    },
    {
      path: "/hub",
      element: (
        <App>
          <Discover />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/s/:shareId",
      element: (
        <App>
          <HomePage isSharedPageMode={true} />
        </App>
      ),
      errorElement: <ErrorPage />,
    },
    {
      path: "/dashboard",
      element: (
        <App>
          <DashboardPage />
        </App>
      ),
    },
    {
      path: "/history",
      element: (
        <App>
          <HistoryPage />
        </App>
      ),
    },
    {
      path: "/historyold",
      element: (
        <App>
          <HistoryPageOld />
        </App>
      ),
    },
    {
      path: "/test",
      element: (
        <App>
          <TestPage />
        </App>
      ),
    },
    {
      path: "/settings",
      element: (
        <App>
          <SettingPage />
        </App>
      ),
    },
    {
      path: "/organization",
      element: (
        <App>
          <OrganizationPage />
        </App>
      ),
    },
    {
      path: "/data",
      element: (
        <App>
          <DataPage />
        </App>
      ),
    },
    {
      path: "/login",
      element: <LoginPage />,
    },
    {
      path: "/signup",
      element: <SignupPage />,
    },
  ]);
}
root.render(
  <React.StrictMode>
    <RecoilRoot>
      <ConfigProvider
        theme={{
          token: {
            fontFamily: "Lato, sans-serif",
          },
        }}
      >
        <Layout
          style={{
            minHeight: "100vh",
            background:
              window.location.href.endsWith("/embed") ||
              window.location.href.endsWith("/embed/chatBubble")
                ? "transparent"
                : "#f5f5f5",
          }}
        >
          <RouterProvider
            router={router}
            fallbackElement={<CircularProgress />}
          />
        </Layout>
      </ConfigProvider>
    </RecoilRoot>
  </React.StrictMode>,
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
