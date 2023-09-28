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
  Popover,
  Stack,
} from "@mui/material";
import {
  AppsOutlined,
  CorporateFareOutlined,
  HistoryOutlined,
  HomeOutlined,
  LightbulbOutlined,
  PlayArrowOutlined,
  SettingsOutlined,
  SourceOutlined,
} from "@mui/icons-material";
import { onLogoutClick } from "./logout";
import { LoggedOutModal } from "./LoggedOutModal";

const logo = require(`../assets/${
  process.env.REACT_APP_SITE_NAME
    ? process.env.REACT_APP_SITE_NAME.toLowerCase()
    : "llmstack"
}-icon.png`);

const siderStyle = {
  textAlign: "center",
  lineHeight: "20px",
  color: "#000",
  backgroundColor: "#ffdfb21c",
  minWidth: "80px",
  borderRight: "solid 1px #ccc",
};

const logoStyle = {
  width: "54px",
  borderRadius: process.env.REACT_APP_SITE_NAME ? "5px" : "inherit",
  border: process.env.REACT_APP_SITE_NAME ? "solid 1px #183a58" : "inherit",
  // paddingTop: "10px",
};

const menuItemStyle = {
  color: "#000",
  textDecoration: "none",
};

function getNavItemIcon(itemLabel) {
  const iconMap = {
    Playground: <PlayArrowOutlined />,
    Home: <HomeOutlined />,
    History: <HistoryOutlined />,
    Settings: <SettingsOutlined />,
    Discover: <LightbulbOutlined />,
    Apps: <AppsOutlined />,
    Data: <SourceOutlined />,
    Organization: <CorporateFareOutlined />,
  };
  return iconMap[itemLabel];
}

function Menu({ menuItems }) {
  const location = useLocation();
  const navigate = useNavigate();
  const isLoggedIn = useRecoilValue(isLoggedInState);
  const [loggedOutModalVisibility, setLoggedOutModalVisibility] =
    useState(false);
  const isSelected = (link) =>
    (location.pathname.startsWith(link) && link !== "/") ||
    (link === "/" && location.pathname === "/") ||
    (link === "/" && location.pathname.startsWith("/apps"));

  return (
    <Stack sx={{ padding: "10px 0", width: "100%" }} spacing={1}>
      {menuItems.map((item) => (
        <div
          style={
            isSelected(item.link) ? { boxShadow: "inset 3px 0 0 #6a4ea8" } : {}
          }
          key={item.key}
        >
          <a
            href={item.link}
            style={menuItemStyle}
            onClick={(e) => {
              e.preventDefault();

              if (isLoggedIn) {
                navigate(item.link);
              } else {
                setLoggedOutModalVisibility(true);
              }
            }}
          >
            <span
              style={
                isSelected(item.link) ? { color: "#385090" } : { color: "#999" }
              }
            >
              {getNavItemIcon(item.label)}
            </span>
            <p
              style={{
                fontSize: "12px",
                fontWeight: "bold",
                margin: "0px 0 5px 0",
              }}
            >
              {item.label}
            </p>
          </a>
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
        </div>
      ))}
    </Stack>
  );
}

export default function Sidebar({ menuItems }) {
  const navigate = useNavigate();
  const isLoggedIn = useRecoilValue(isLoggedInState);
  const profile = useRecoilValue(profileState);
  const [showPopover, setShowPopover] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);

  return (
    <Stack sx={siderStyle}>
      <Box
        align={"top"}
        style={{ justifyContent: "center", margin: "15px auto" }}
      >
        <a
          href="/apps"
          onClick={(e) => {
            e.preventDefault();
            navigate("/apps");
          }}
        >
          <img style={logoStyle} src={logo} alt="logo" />
        </a>
      </Box>
      <Box style={{ justifyContent: "center" }}>
        <Menu menuItems={menuItems} />
      </Box>
      <Box
        sx={{
          position: "absolute",
          bottom: "5px",
          padding: "10px 0",
          justifyContent: "center",
          width: "80px",
        }}
      >
        {profile && profile.avatar ? (
          <Avatar
            alt={profile.name}
            src={profile.avatar}
            sx={{
              width: 42,
              height: 42,
              cursor: "pointer",
              border: "1px solid #728bd0",
              margin: "0 auto",
            }}
            onClick={(e) => {
              setAnchorEl(e.currentTarget);
              setShowPopover(true);
            }}
            aria-describedby={"profile-popover"}
          />
        ) : (
          <Avatar
            sx={{
              width: 42,
              height: 42,
              cursor: "pointer",
              border: "1px solid #728bd0",
              margin: "0 auto",
            }}
            onClick={(e) => {
              setAnchorEl(e.currentTarget);
              setShowPopover(true);
            }}
            aria-describedby={"profile-popover"}
          >{`${
            profile?.name
              ?.split(" ")
              .map((x) => x[0])
              .join("") || "P"
          }`}</Avatar>
        )}
        <Popover
          id={"profile-popover"}
          anchorEl={anchorEl}
          anchorOrigin={{
            vertical: "top",
            horizontal: "right",
          }}
          transformOrigin={{
            vertical: "bottom",
            horizontal: "left",
          }}
          open={showPopover}
          onClose={() => setShowPopover(false)}
        >
          <List>
            <ListItem disablePadding>
              <ListItemButton
                component={"a"}
                href={"https://docs.trypromptly.com"}
                target="_blank"
              >
                <ListItemText primary="Docs" />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton
                component={"a"}
                href={"https://discord.gg/3JsEzSXspJ"}
                target="_blank"
              >
                <ListItemText primary="Help" />
              </ListItemButton>
            </ListItem>
            {isLoggedIn && (
              <ListItem disablePadding>
                <ListItemButton component="a" onClick={onLogoutClick}>
                  <ListItemText primary="Logout" />
                </ListItemButton>
              </ListItem>
            )}
          </List>
        </Popover>
      </Box>
    </Stack>
  );
}
