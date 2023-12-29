import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useRecoilValue } from "recoil";
import { isLoggedInState, profileState } from "../data/atoms";
import {
  Avatar,
  Box,
  Button,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  CssBaseline,
  Divider,
  ListItemIcon,
  Typography,
  SvgIcon,
} from "@mui/material";
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
  PlayArrowOutlined,
  SettingsOutlined,
  SourceOutlined,
} from "@mui/icons-material";
import { onLogoutClick } from "./logout";
import { ReactComponent as GithubIcon } from "../assets/images/icons/github.svg";
import { LoggedOutModal } from "./LoggedOutModal";

import * as React from "react";
import { styled } from "@mui/material/styles";
import MuiDrawer from "@mui/material/Drawer";

const SITE_NAME = process.env.REACT_APP_SITE_NAME || "LLMStack";

const icon = require(`../assets/${SITE_NAME.toLowerCase()}-icon.png`);

const logoStyle = {
  width: "36px",
  borderRadius: SITE_NAME === "Promptly" ? "5px" : "inherit",
  border: SITE_NAME === "Promptly" ? "solid 1px #183a58" : "inherit",
};

const getNavItemIcon = (itemLabel) => {
  const iconMap = {
    Playground: <PlayArrowOutlined />,
    Home: <HomeOutlined />,
    History: <HistoryOutlined />,
    Settings: <SettingsOutlined />,
    Discover: <LightbulbOutlined />,
    Apps: <AppsOutlined />,
    Data: <SourceOutlined />,
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
  boxShadow: "0px 0px 10px #999",
});

const closedMixin = (theme) => ({
  transition: theme.transitions.create("width", {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
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
  zIndex: "2000",
  whiteSpace: "nowrap",
  boxSizing: "border-box",
  "& .MuiListItemButton-root": {
    margin: "0px 10px",
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
  const profile = useRecoilValue(profileState);
  const [loggedOutModalVisibility, setLoggedOutModalVisibility] =
    useState(false);
  const [open, setOpen] = React.useState(false);

  const isSelected = (link) =>
    (location.pathname.startsWith(link) && link !== "/") ||
    (link === "/" && location.pathname === "/") ||
    (link === "/" && location.pathname.startsWith("/apps"));

  return (
    <Box sx={{ display: "flex" }}>
      <CssBaseline />
      <Drawer
        variant="permanent"
        anchor="left"
        open={open}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
      >
        <List>
          <ListItem>
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

                  if (isLoggedIn) {
                    navigate(item.link);
                  } else {
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
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
        <List sx={{ position: "absolute", bottom: 0, minWidth: "150px" }}>
          <ListItem key={"docs"} disablePadding>
            <ListItemButton
              sx={{
                minHeight: 32,
                justifyContent: open ? "initial" : "center",
                px: 2.5,
              }}
              component={"a"}
              href={"https://llmstack.ai/docs"}
              target="_blank"
            >
              <ListItemIcon
                sx={(theme) => ({
                  minWidth: 0,
                  mr: open ? 1 : "auto",
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
                minHeight: 32,
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
                  mr: open ? 1 : "auto",
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
                  color: "#666",
                  margin: 0,
                }}
              />
            </ListItemButton>
          </ListItem>
          {SITE_NAME === "LLMStack" && (
            <ListItem key={"help"} disablePadding>
              <ListItemButton
                sx={{
                  minHeight: 32,
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
                    mr: open ? 1 : "auto",
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
                    color: "#666",
                    margin: 0,
                  }}
                />
              </ListItemButton>
            </ListItem>
          )}
          {isLoggedIn && <Divider sx={{ margin: "5px 0" }} />}
          {isLoggedIn && (
            <ListItem key={"logout"} disablePadding>
              <ListItemButton
                sx={{
                  minHeight: 32,
                  justifyContent: open ? "initial" : "center",
                  px: 2.5,
                }}
                onClick={onLogoutClick}
              >
                <ListItemIcon
                  sx={(theme) => ({
                    minWidth: 0,
                    mr: open ? 1 : "auto",
                    justifyContent: "center",
                    color: "#666",
                  })}
                >
                  <LogoutOutlined />
                </ListItemIcon>
                <ListItemText
                  primary={"Logout"}
                  sx={{
                    opacity: open ? 1 : 0,
                    display: open ? "block" : "none",
                    color: "#666",
                    margin: 0,
                  }}
                />
              </ListItemButton>
            </ListItem>
          )}
          {isLoggedIn && (
            <ListItem key={"profile-icon"} disablePadding>
              <ListItemButton
                sx={{
                  minHeight: 32,
                  justifyContent: open ? "initial" : "center",
                  px: 2.5,
                }}
              >
                <ListItemIcon
                  sx={(theme) => ({
                    minWidth: 0,
                    mr: open ? 1 : "auto",
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
                    color: "#666",
                    margin: 0,
                  }}
                />
              </ListItemButton>
            </ListItem>
          )}
        </List>
      </Drawer>
      <LoggedOutModal
        visibility={!isLoggedIn && loggedOutModalVisibility}
        handleCancelCb={() => setLoggedOutModalVisibility(false)}
        title={"Logged Out"}
        message={
          <p>
            You are logged out. Please{" "}
            <Button
              type="link"
              onClick={() => (window.location.href = "/login")}
              sx={{ padding: "0px" }}
            >
              login
            </Button>{" "}
            to proceed.
          </p>
        }
      />
    </Box>
  );
}
