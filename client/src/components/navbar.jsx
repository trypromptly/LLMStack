import React from "react";
import {
  AppBar,
  Toolbar,
  Menu,
  MenuItem,
  IconButton,
  Link,
} from "@mui/material";
import { Menu as MenuIcon } from "@mui/icons-material";

const icon = require(`../assets/${
  process.env.REACT_APP_SITE_NAME
    ? process.env.REACT_APP_SITE_NAME.toLowerCase()
    : "llmstack"
}-icon.png`);

const navbarStyle = {
  width: "100%",
  color: "#000",
  backgroundColor: "#ffdfb21c",
  borderBottom: "solid 1px #ccc",
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
