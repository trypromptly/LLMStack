import { CircularProgress, Grid, Stack, IconButton } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { SnackbarProvider, closeSnackbar } from "notistack";
import { Suspense, useEffect } from "react";
import ReactGA from "react-ga4";
import { useLocation } from "react-router-dom";
import { useRecoilState, useRecoilValue } from "recoil";
import BannerMessages from "./components/BannerMessages";
import NavBar from "./components/navbar";
import Sidebar from "./components/sidebar";
import {
  isMobileState,
  profileFlagsSelector,
  isLoggedInState,
  providersState,
  processorsState,
  organizationState,
} from "./data/atoms";

const menuItems = [
  {
    key: "1",
    label: "Playground",
    link: "/playground",
  },
  {
    key: "7",
    label: "Data",
    link: "/data",
  },
  {
    key: "3",
    label: "History",
    link: "/history",
  },
  {
    key: "8",
    label: "Sheets",
    link: "/sheets",
  },
  {
    key: "5",
    label: "Settings",
    link: "/settings",
  },
];

export default function App({ children }) {
  const location = useLocation();
  const isLoggedIn = useRecoilValue(isLoggedInState);
  const providers = useRecoilValue(providersState); // eslint-disable-line
  const processors = useRecoilValue(processorsState); // eslint-disable-line
  const organization = useRecoilValue(organizationState); // eslint-disable-line

  let allMenuItems = menuItems;

  useEffect(() => {
    ReactGA.initialize(
      (process.env.REACT_APP_GA_MEASUREMENT_IDS || "G-WV60HC9CHD")
        .split(",")
        .map((measurementId) => {
          return {
            trackingId: measurementId,
          };
        }),
    );

    ReactGA.send({
      hitType: "pageview",
      page: location.pathname + location.search,
      title: location.pathname,
    });
  }, [location]);

  const [isMobile, setIsMobile] = useRecoilState(isMobileState);
  const profileFlags = useRecoilValue(profileFlagsSelector);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 900);
    };

    window.addEventListener("resize", handleResize);

    // Cleanup
    return () => window.removeEventListener("resize", handleResize);
  }, [setIsMobile]);

  allMenuItems = [
    {
      key: "2",
      label: "Home",
      link: "/",
    },
    {
      key: "4",
      label: "Apps",
      link: "/apps",
    },
    ...menuItems,
  ];

  if (profileFlags.IS_ORGANIZATION_OWNER) {
    allMenuItems.push({
      key: "8",
      label: "Organization",
      link: "/organization",
    });
  }

  if (isMobile) {
    allMenuItems.push({
      key: "9",
      label: "Docs",
      link: "https://docs.trypromptly.com",
    });
  }

  if (
    !process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT &&
    !location.pathname.startsWith("/app/") &&
    !isLoggedIn
  ) {
    // Redirect to login page if user is not logged in
    window.location.href = "/login";
  }

  return (
    <div id="app-container">
      <SnackbarProvider
        maxSnack={3}
        autoHideDuration={2000}
        anchorOrigin={{ horizontal: "center", vertical: "top" }}
        action={(key) => (
          <IconButton
            size="small"
            aria-label="close"
            color="inherit"
            onClick={() => closeSnackbar(key)}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        )}
      />
      <Stack direction={"row"}>
        {!isMobile && <Sidebar menuItems={allMenuItems} />}
        <Suspense
          fallback={
            <Grid
              sx={{
                margin: "auto",
              }}
            >
              <CircularProgress />
            </Grid>
          }
        >
          <Grid
            sx={{
              textAlign: "center",
              height: "100vh",
              width: "100%",
              paddingLeft: isMobile ? 0 : "65px",
              backgroundColor: "#fff",
              overflow: "auto",
            }}
          >
            <BannerMessages />
            {isMobile && <NavBar menuItems={allMenuItems} />}
            {children}
          </Grid>
        </Suspense>
      </Stack>
      {!isMobile &&
        process.env.REACT_APP_ENABLE_APP_STORE &&
        location.pathname !== "/" &&
        location.pathname !== "/playground" &&
        !location.pathname.startsWith("/u/") &&
        !location.pathname.startsWith("/a/") && (
          <div
            dangerouslySetInnerHTML={{
              __html:
                '<promptly-app-embed published-app-id="f4d7cb50-1805-4add-80c5-e30334bce53c" width="100px" chat-bubble="true"></promptly-app-embed>',
            }}
          ></div>
        )}
    </div>
  );
}
