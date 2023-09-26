import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useRecoilValue } from "recoil";
import { isLoggedInState, profileState } from "../data/atoms";
import { Button, Col, Image, Layout, Row, Space } from "antd";
import {
  Avatar,
  Popover,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
} from "@mui/material";
import {
  AppstoreAddOutlined,
  BankOutlined,
  HistoryOutlined,
  HomeOutlined,
  PlaySquareOutlined,
  SettingOutlined,
  AppstoreOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import { onLogoutClick } from "./logout";
import { LoggedOutModal } from "./LoggedOutModal";

const icon = require(`../assets/${
  process.env.REACT_APP_SITE_NAME
    ? process.env.REACT_APP_SITE_NAME.toLowerCase()
    : "llmstack"
}-icon.png`);

const { Sider } = Layout;

const siderStyle = {
  textAlign: "center",
  lineHeight: "20px",
  color: "#000",
  backgroundColor: "#ffdfb21c",
  width: "50px",
  borderRight: "solid 1px #ccc",
};

const iconStyle = {
  width: "54px",
  borderRadius: process.env.REACT_APP_SITE_NAME ? "5px" : "inherit",
  border: process.env.REACT_APP_SITE_NAME ? "solid 1px #183a58" : "inherit",
};

const menuItemStyle = {
  color: "#000",
};

function getNavItemIcon(itemLabel) {
  const iconMap = {
    Playground: <PlaySquareOutlined />,
    Home: <HomeOutlined />,
    History: <HistoryOutlined />,
    Settings: <SettingOutlined />,
    Discover: <AppstoreOutlined />,
    Apps: <AppstoreAddOutlined />,
    Data: <DatabaseOutlined />,
    Organization: <BankOutlined />,
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
    <Space direction="vertical" style={{ padding: "15px 0", width: "100%" }}>
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
                isSelected(item.link)
                  ? { fontSize: "28px", color: "#385090" }
                  : { fontSize: "28px" }
              }
            >
              {getNavItemIcon(item.label)}
            </span>
            <p style={{ fontSize: "12px", margin: "4px 0" }}>{item.label}</p>
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
                  style={{ padding: "0px" }}
                >
                  login
                </Button>{" "}
                to proceed.
              </p>
            }
          />
        </div>
      ))}
    </Space>
  );
}

export default function Sidebar({ menuItems }) {
  const navigate = useNavigate();
  const isLoggedIn = useRecoilValue(isLoggedInState);
  const profile = useRecoilValue(profileState);
  const [showPopover, setShowPopover] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);

  return (
    <Sider style={siderStyle} width={80}>
      <Col style={{ height: "100vh" }}>
        <Row
          align={"top"}
          style={{ justifyContent: "center", lineHeight: "80px" }}
        >
          <a
            href="/apps"
            onClick={(e) => {
              e.preventDefault();
              navigate("/apps");
            }}
          >
            <Image style={iconStyle} src={icon} preview={false} />
          </a>
        </Row>
        <Row style={{ justifyContent: "center" }}>
          <Menu menuItems={menuItems} />
        </Row>
        <Row
          style={{
            position: "absolute",
            bottom: "5px",
            padding: "10px 0",
            justifyContent: "center",
            width: "100%",
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
        </Row>
      </Col>
    </Sider>
  );
}
