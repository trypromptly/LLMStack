import {
  AppsOutlined,
  CorporateFareOutlined,
  DescriptionOutlined,
  EventRepeatOutlined,
  HelpOutlineOutlined,
  HistoryOutlined,
  HomeOutlined,
  LightbulbOutlined,
  LogoutOutlined,
  TerminalOutlined,
  SettingsOutlined,
  FolderOutlined,
  LoginOutlined,
} from "@mui/icons-material";
import TwitterIcon from "@mui/icons-material/Twitter";
import {
  Avatar,
  Box,
  CssBaseline,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  SvgIcon,
  Typography,
} from "@mui/material";
import MuiDrawer from "@mui/material/Drawer";
import { styled } from "@mui/material/styles";
import * as React from "react";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useRecoilValue } from "recoil";
import { ReactComponent as GithubIcon } from "../assets/images/icons/github.svg";
import { isLoggedInState, profileSelector } from "../data/atoms";
import { onLogoutClick } from "./logout";
import LoginDialog from "./LoginDialog";

const SITE_NAME = process.env.REACT_APP_SITE_NAME || "LLMStack";

const icon =
  SITE_NAME === "Promptly"
    ? require(`../assets/icon-transparent.png`)
    : require(`../assets/llmstack-icon.png`);

const logoStyle = {
  width: "24px",
};

const getNavItemIcon = (itemLabel) => {
  const iconMap = {
    Playground: <TerminalOutlined />,
    Home: <HomeOutlined />,
    History: <HistoryOutlined />,
    Settings: <SettingsOutlined />,
    Discover: <LightbulbOutlined />,
    Apps: <AppsOutlined />,
    Data: <FolderOutlined />,
    Organization: <CorporateFareOutlined />,
    Jobs: <EventRepeatOutlined />,
  };
  return iconMap[itemLabel];
};

const drawerWidth = 150;

const openedMixin = (theme) => ({
  width: drawerWidth,
  transition: theme.transitions.create("width", {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.enteringScreen,
  }),
  overflowX: "hidden",
  borderRight: "solid 1px #E8EBEE",
  boxShadow: "0px 2px 4px -2px #1018280F, 0px 4px 8px -2px #1018281F",
});

const closedMixin = (theme) => ({
  transition: theme.transitions.create("width", {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  borderRight: "solid 1px #E8EBEE",
  boxShadow: "0px 2px 4px -2px #1018281F, 0px 4px 8px -2px #1018282A",
  overflowX: "hidden",
  width: `calc(${theme.spacing(14)} + 1px)`,
  [theme.breakpoints.up("sm")]: {
    width: `calc(${theme.spacing(16)} + 1px)`,
  },
});

const Drawer = styled(MuiDrawer, {
  shouldForwardProp: (prop) => prop !== "open",
})(({ theme, open }) => ({
  position: "fixed",
  width: drawerWidth,
  flexShrink: 0,
  zIndex: "200",
  whiteSpace: "nowrap",
  boxSizing: "border-box",
  "& .MuiListItemButton-root": {
    margin: "0px 4px",
  },
  "& .MuiListItemText-root": {
    "& .MuiTypography-root": {
      fontSize: "0.9rem",
    },
  },
  ...(open && {
    ...openedMixin(theme),
    "& .MuiDrawer-paper": openedMixin(theme),
  }),
  ...(!open && {
    ...closedMixin(theme),
    "& .MuiDrawer-paper": closedMixin(theme),
  }),
}));

export default function Sidebar({ menuItems }) {
  const navigate = useNavigate();
  const location = useLocation();
  const isLoggedIn = useRecoilValue(isLoggedInState);
  const profile = useRecoilValue(profileSelector);
  const [loggedOutModalVisibility, setLoggedOutModalVisibility] =
    useState(false);
  const [open, setOpen] = React.useState(false);
  const [loginRedirectPath, setLoginRedirectPath] = useState("/");

  const isSelected = (link) =>
    (location.pathname.startsWith(link) && link !== "/") ||
    (link === "/" && location.pathname === "/") ||
    (link === "/" && location.pathname.startsWith("/a/"));

  return (
    <Box
      sx={{
        display: "flex",
        "& .Mui-selected": {
          borderRadius: "8px",
          backgroundColor: "#E8EBEE !important",

          "& .MuiListItemIcon-root": {
            color: "#183A58",
          },
        },
        "& .MuiListItemButton-root": {
          borderRadius: "8px",
          padding: "0 16px",
          margin: "0 4px",
        },
      }}
    >
      <CssBaseline />
      <Drawer
        variant="permanent"
        anchor="left"
        open={open}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
      >
        <List>
          <ListItem sx={{ justifyContent: "center" }}>
            <a
              href="https://www.trypromptly.com"
              target="_blank"
              rel="noreferrer"
              style={{
                textDecoration: "none",
                color: "#183a58",
                display: "flex",
                alignItems: "center",
                marginTop: "24px",
                marginBottom: "32px",
              }}
            >
              <img style={logoStyle} src={icon} alt="logo" />
              <Typography
                variant="h5"
                sx={{
                  margin: "0 8px",
                  opacity: open ? 1 : 0,
                  display: open ? "block" : "none",
                }}
              >
                {SITE_NAME}
              </Typography>
            </a>
          </ListItem>
        </List>
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.key} disablePadding sx={{ display: "block" }}>
              <ListItemButton
                sx={{
                  minHeight: 48,
                  justifyContent: open ? "initial" : "center",
                  px: 2.5,
                }}
                selected={isSelected(item.link)}
                onClick={(e) => {
                  e.preventDefault();

                  if (
                    isLoggedIn ||
                    item.link === "/" ||
                    item.link === "/playground"
                  ) {
                    navigate(item.link);
                  } else {
                    setLoginRedirectPath(item.link);
                    setLoggedOutModalVisibility(true);
                  }
                }}
              >
                <ListItemIcon
                  sx={(theme) => ({
                    minWidth: 0,
                    mr: open ? 3 : "auto",
                    justifyContent: "center",
                    color: isSelected(item.link)
                      ? theme.palette.primary.main
                      : "#666",
                  })}
                >
                  {getNavItemIcon(item.label)}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  sx={{
                    opacity: open ? 1 : 0,
                    display: open ? "block" : "none",
                    padding: 0,
                    margin: 0,
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
        <List sx={{ position: "absolute", bottom: 0, width: "100%" }}>
          <ListItem key={"docs"} disablePadding>
            <ListItemButton
              sx={{
                minHeight: 48,
                justifyContent: open ? "initial" : "center",
                px: 2.5,
              }}
              component={"a"}
              href={"https://docs.trypromptly.com"}
              target="_blank"
            >
              <ListItemIcon
                sx={(theme) => ({
                  minWidth: 0,
                  mr: open ? 3 : "auto",
                  justifyContent: "center",
                  color: "#666",
                })}
              >
                <DescriptionOutlined />
              </ListItemIcon>
              <ListItemText
                primary={"Docs"}
                sx={{
                  opacity: open ? 1 : 0,
                  display: open ? "block" : "none",
                  color: "#666",
                  margin: 0,
                }}
              />
            </ListItemButton>
          </ListItem>
          <ListItem key={"help"} disablePadding>
            <ListItemButton
              sx={{
                minHeight: 48,
                justifyContent: open ? "initial" : "center",
                px: 2.5,
              }}
              component={"a"}
              href={"https://discord.gg/3JsEzSXspJ"}
              target="_blank"
            >
              <ListItemIcon
                sx={(theme) => ({
                  minWidth: 0,
                  mr: open ? 3 : "auto",
                  justifyContent: "center",
                  color: "#666",
                })}
              >
                <HelpOutlineOutlined />
              </ListItemIcon>
              <ListItemText
                primary={"Help"}
                sx={{
                  opacity: open ? 1 : 0,
                  display: open ? "block" : "none",
                  margin: 0,
                }}
              />
            </ListItemButton>
          </ListItem>
          {SITE_NAME === "LLMStack" && (
            <ListItem key={"github"} disablePadding>
              <ListItemButton
                sx={{
                  minHeight: 48,
                  justifyContent: open ? "initial" : "center",
                  px: 2.5,
                }}
                component={"a"}
                href={"https://github.com/trypromptly/LLMStack"}
                target="_blank"
              >
                <ListItemIcon
                  sx={(theme) => ({
                    minWidth: 0,
                    mr: open ? 3 : "auto",
                    justifyContent: "center",
                    color: "#666",
                  })}
                >
                  <SvgIcon component={GithubIcon} viewBox="-1 -1 18 18" />
                </ListItemIcon>
                <ListItemText
                  primary={"Github"}
                  sx={{
                    opacity: open ? 1 : 0,
                    display: open ? "block" : "none",
                    margin: 0,
                  }}
                />
              </ListItemButton>
            </ListItem>
          )}
          <ListItem key={"twitter"} disablePadding>
            <ListItemButton
              sx={{
                minHeight: 48,
                justifyContent: open ? "initial" : "center",
                px: 2.5,
              }}
              component={"a"}
              href={"https://twitter.com/trypromptly"}
              target="_blank"
            >
              <ListItemIcon
                sx={(theme) => ({
                  minWidth: 0,
                  mr: open ? 3 : "auto",
                  justifyContent: "center",
                  color: "#666",
                })}
              >
                <TwitterIcon />
              </ListItemIcon>
              <ListItemText
                primary={"Updates"}
                sx={{
                  opacity: open ? 1 : 0,
                  display: open ? "block" : "none",
                  margin: 0,
                }}
              />
            </ListItemButton>
          </ListItem>
          <ListItem key={isLoggedIn ? "logout" : "login"} disablePadding>
            <ListItemButton
              sx={{
                minHeight: 48,
                justifyContent: open ? "initial" : "center",
                px: 2.5,
              }}
              onClick={
                isLoggedIn
                  ? onLogoutClick
                  : () => setLoggedOutModalVisibility(true)
              }
            >
              <ListItemIcon
                sx={(theme) => ({
                  minWidth: 0,
                  mr: open ? 3 : "auto",
                  justifyContent: "center",
                  color: "#666",
                })}
              >
                {isLoggedIn ? <LogoutOutlined /> : <LoginOutlined />}
              </ListItemIcon>
              <ListItemText
                primary={isLoggedIn ? "Logout" : "Login"}
                sx={{
                  opacity: open ? 1 : 0,
                  display: open ? "block" : "none",
                  margin: 0,
                }}
              />
            </ListItemButton>
          </ListItem>
          {isLoggedIn &&
            process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT && (
              <Divider sx={{ margin: "5px 0" }} />
            )}
          {isLoggedIn &&
            process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT && (
              <ListItem key={"profile-icon"} disablePadding>
                <ListItemButton
                  sx={{
                    minHeight: 48,
                    justifyContent: open ? "initial" : "center",
                    px: 2.5,
                  }}
                  onClick={(e) => {
                    e.preventDefault();

                    if (isLoggedIn && profile?.username) {
                      navigate(`/u/${profile?.username}`);
                    }
                  }}
                >
                  <ListItemIcon
                    sx={(theme) => ({
                      minWidth: 0,
                      mr: open ? 3 : "auto",
                      justifyContent: "center",
                      color: "#666",
                    })}
                  >
                    {" "}
                    {profile && profile.avatar ? (
                      <Avatar
                        alt={profile.name}
                        src={profile.avatar}
                        sx={{
                          width: 26,
                          height: 26,
                          cursor: "pointer",
                          border: "1px solid #728bd0",
                          margin: "0 auto",
                        }}
                      />
                    ) : (
                      <Avatar
                        sx={{
                          width: 26,
                          height: 26,
                          fontSize: "0.8rem",
                          cursor: "pointer",
                          border: "1px solid #728bd0",
                          margin: "0 auto",
                        }}
                      >{`${
                        profile?.name
                          ?.split(" ")
                          .map((x) => x[0])
                          .join("") || "P"
                      }`}</Avatar>
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      profile && profile.name && profile.name.length > 0
                        ? profile.name
                        : "Human"
                    }
                    sx={{
                      opacity: open ? 1 : 0,
                      display: open ? "block" : "none",
                      margin: 0,
                      maxWidth: "72px",
                      "& .MuiTypography-root": {
                        fontSize: "clamp(9px, 2vw, 16px)",
                        whiteSpace: "normal",
                      },
                    }}
                  />
                </ListItemButton>
              </ListItem>
            )}
        </List>
      </Drawer>
      <LoginDialog
        open={!isLoggedIn && loggedOutModalVisibility}
        loginMessage="Please sign in to continue."
        handleClose={() => setLoggedOutModalVisibility(false)}
        redirectPath={loginRedirectPath}
      />
    </Box>
  );
}
