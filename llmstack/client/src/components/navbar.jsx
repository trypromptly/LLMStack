import { Menu as MenuIcon } from "@mui/icons-material";
import {
  AppBar,
  IconButton,
  Link,
  Menu,
  MenuItem,
  Toolbar,
} from "@mui/material";
import React from "react";

const SITE_NAME = process.env.REACT_APP_SITE_NAME || "LLMStack";
const icon =
  SITE_NAME === "Promptly"
    ? require(`../assets/icon-transparent.png`)
    : require(`../assets/llmstack-icon.png`);

const navbarStyle = {
  width: "100%",
  color: "#647B8F",
  backgroundColor: "#fff",
  padding: "4px 12px",
  marginBottom: "4px",
  boxShadow: "0px 1px 2px 0px #1018280F, 0px 1px 3px 0px #1018281A",
};

export default function NavBar({ menuItems }) {
  const [anchorEl, setAnchorEl] = React.useState(null);

  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  return (
    <AppBar
      position="static"
      color="transparent"
      elevation={1}
      style={navbarStyle}
    >
      <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
        <IconButton
          edge="start"
          color="inherit"
          href="/"
          onClick={(e) => {
            e.preventDefault();
            window.location.href = "/";
          }}
        >
          <img src={icon} alt={icon} width="32px" />
        </IconButton>

        <IconButton edge="end" color="inherit" onClick={handleMenuClick}>
          <MenuIcon />
        </IconButton>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          {menuItems.map((item) => (
            <MenuItem key={item.key} onClick={handleMenuClose}>
              <Link href={item.link} underline="none">
                {item.label}
              </Link>
            </MenuItem>
          ))}
        </Menu>
      </Toolbar>
    </AppBar>
  );
}
