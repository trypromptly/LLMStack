import { Box, createTheme, ThemeProvider } from "@mui/material";
import CircularProgress from "@mui/material/CircularProgress";
import { TourProvider } from "@reactour/tour";
import React, { lazy } from "react";
import { CookiesProvider } from "react-cookie";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { RecoilRoot } from "recoil";
import "./index.css";
import reportWebVitals from "./reportWebVitals";

const App = lazy(() => import("./App"));
const ErrorPage = lazy(() => import("./pages/error"));
const PlaygroundPage = lazy(() => import("./pages/playground"));
const LoginPage = lazy(() => import("./pages/login"));
const SignupPage = lazy(() => import("./pages/signup"));
const DashboardPage = lazy(() => import("./pages/dashboard"));
const HistoryPage = lazy(() => import("./pages/history"));
const SettingPage = lazy(() => import("./pages/setting"));
const OrganizationPage = lazy(() => import("./pages/organization"));
const AppRenderPage = lazy(() => import("./pages/AppRender"));
const AppStudioPage = lazy(() => import("./pages/AppStudio"));
const AppConsolePage = lazy(() => import("./pages/AppConsole"));
const DataPage = lazy(() => import("./pages/data"));
const Discover = lazy(() => import("./pages/discover"));
const SchedulePage = lazy(() => import("./pages/schedule"));
const AddAppRunSchedulePage = lazy(() => import("./pages/AddAppRunSchedule"));
const AddDatasourceRefreshSchedulePage = lazy(
  () => import("./pages/AddDatasourceRefreshSchedule"),
);
const SessionExpiredPage = lazy(() => import("./pages/SessionExpired"));

const defaultTheme = createTheme({
  spacing: 4,
  typography: {
    fontFamily: "Lato, sans-serif",
    fontSize: 14,
  },
  palette: {
    primary: {
      main: "#0a398d",
      light: "#0a398d",
      dark: "#1b4ca3",
      contrastText: "#fff",
    },
    secondary: {
      main: "#1e88e5",
      light: "#1e88e5",
      dark: "#1e88e5",
      contrastText: "#fff",
    },
    error: {
      main: "#d0625a",
      light: "#d0625a",
      dark: "#e74c41",
      contrastText: "#fff",
    },
    warning: {
      main: "#e86a1f",
      light: "#e86a1f",
      dark: "#ff9800",
      contrastText: "#fff",
    },
    info: {
      main: "#2196f3",
      light: "#2196f3",
      dark: "#2196f3",
      contrastText: "#fff",
    },
    success: {
      main: "#3a923e",
      light: "#3a923e",
      dark: "#58b65c",
      contrastText: "#fff",
    },
  },
  components: {
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: "0.2rem",
          margin: "0.1rem",
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          fontSize: "1.2rem",
          fontWeight: "600",
          color: "#0a398d",
        },
      },
    },
    MuiImageList: {
      styleOverrides: {
        root: {
          width: "100% !important",
          height: "100% !important",
        },
      },
    },
    MuiImageListItem: {
      styleOverrides: {
        root: {
          whiteSpace: "pre-wrap",
        },
        img: {
          width: "auto",
          height: "auto",
        },
      },
    },
    MuiInputBase: {
      defaultProps: {
        autoComplete: "off",
      },
      styleOverrides: {
        root: {
          "& textarea": {
            whiteSpace: "pre-wrap",
            padding: "0.6rem",
          },
        },
      },
    },
    MuiSlider: {
      defaultProps: {
        size: "small",
      },
    },
    MuiSelect: {
      defaultProps: {
        variant: "outlined",
        size: "small",
      },
      styleOverrides: {
        select: {
          textAlign: "left",
          margin: "0.1rem",
        },
      },
    },
    MuiFormControl: {
      styleOverrides: {
        root: {
          padding: "2px",

          "& .MuiFormHelperText-root": {
            overflow: "hidden",
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            textOverflow: "ellipsis",
            whiteSpace: "normal",
            textAlign: "left",
            margin: "2px",
            lineHeight: "1.6em",
            maxHeight: "3.2em",
          },

          "& .MuiInputBase-root": {
            padding: "0.1rem",
          },

          "& .MuiTypography-body1": {
            fontSize: "0.9rem",
            fontWeight: "600",
            textAlign: "left",
          },

          "& .form-group": {
            textAlign: "left",
          },

          "& .field-boolean .MuiTypography-subtitle2": {
            display: "none",
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: "1px solid #efefefa1",
        },
      },
    },
    MuiTextField: {
      defaultProps: {
        variant: "outlined",
        size: "small",
      },
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": {
            "& > fieldset": {
              border: "1px solid rgb(204, 204, 204)",
            },
            "&.Mui-focused > fieldset": { border: "1px solid #0f477e" },
            "&:hover > fieldset": { border: "1px solid #0f477e" },
            "&.Mui-error > fieldset": { border: "1px solid #fcc" },
          },
        },
      },
    },
    MuiFormLabel: {
      styleOverrides: {
        root: {
          fontWeight: "550",
          lineHeight: "1.66",
          textAlign: "left",
          textTransform: "capitalize",
        },
      },
    },
    MuiCheckbox: {
      styleOverrides: {
        root: {
          padding: "0.1rem",
          marginLeft: "0.5rem",
          marginRight: "0.2rem",
        },
      },
    },
    MuiTypography: {
      styleOverrides: {
        caption: {
          fontSize: "0.7rem",
          marginLeft: 2,
        },
        h5: {
          fontSize: "1rem",
          fontWeight: "600",
          margin: "0.5rem 0.2rem",
          textAlign: "left",
        },

        subtitle2: {
          textAlign: "left",
        },
      },
    },
    MuiButtonBase: {
      styleOverrides: {
        root: {
          "&.MuiButton-contained": {
            textTransform: "none",
          },
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          fontWeight: "600",
          textTransform: "capitalize",
        },
      },
    },
  },
});

let router = null;

const root = ReactDOM.createRoot(document.getElementById("root"));

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
        <PlaygroundPage isSharedPageMode={false} />
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
        <AppConsolePage />
      </App>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: "/apps/:appId",
    element: (
      <App>
        <AppConsolePage />
      </App>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: "/apps/:appId/preview",
    element: (
      <App>
        <AppConsolePage page="preview" />
      </App>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: "/apps/:appId/template",
    element: (
      <App>
        <AppConsolePage page="template" />
      </App>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: "/apps/:appId/editor",
    element: (
      <App>
        <AppConsolePage page="editor" />
      </App>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: "/apps/:appId/history",
    element: (
      <App>
        <AppConsolePage page="history" />
      </App>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: "/apps/:appId/tests",
    element: (
      <App>
        <AppConsolePage page="tests" />
      </App>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: "/apps/:appId/versions",
    element: (
      <App>
        <AppConsolePage page="versions" />
      </App>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: "/apps/:appId/integrations/website",
    element: (
      <App>
        <AppConsolePage page="integrations/website" />
      </App>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: "/apps/:appId/integrations/api",
    element: (
      <App>
        <AppConsolePage page="integrations/api" />
      </App>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: "/apps/:appId/integrations/slack",
    element: (
      <App>
        <AppConsolePage page="integrations/slack" />
      </App>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: "/apps/:appId/integrations/discord",
    element: (
      <App>
        <AppConsolePage page="integrations/discord" />
      </App>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: "/apps/:appId/integrations/twilio",
    element: (
      <App>
        <AppConsolePage page="integrations/twilio" />
      </App>
    ),
    errorElement: <ErrorPage />,
  },
  {
    path: "/apps/:appId/preview",
    element: (
      <App>
        <AppConsolePage page="preview" />
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
        <PlaygroundPage isSharedPageMode={true} />
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
    path: "/jobs",
    element: (
      <App>
        <SchedulePage />
      </App>
    ),
  },
  {
    path: "/jobs/add_app_run",
    element: (
      <App>
        <AddAppRunSchedulePage />
      </App>
    ),
  },
  {
    path: "/jobs/add_datasource_refresh",
    element: (
      <App>
        <AddDatasourceRefreshSchedulePage />
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
  {
    path: "/session-expired",
    element: <SessionExpiredPage />,
  },
]);

root.render(
  <React.StrictMode>
    <RecoilRoot>
      <ThemeProvider theme={defaultTheme}>
        <TourProvider>
          <CookiesProvider>
            <Box
              sx={{
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
            </Box>
          </CookiesProvider>
        </TourProvider>
      </ThemeProvider>
    </RecoilRoot>
  </React.StrictMode>,
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
