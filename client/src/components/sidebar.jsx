import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useRecoilValue } from "recoil";
import { isLoggedInState, profileState } from "../data/atoms";
import {
  Alert,
  Button,
  Col,
  Collapse,
  Image,
  Layout,
  Modal,
  Row,
  Space,
} from "antd";
import {
  Avatar,
  Popover,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
} from "@mui/material";
import icon from "../assets/icon.png";
import {
  ApiOutlined,
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

const { Panel } = Collapse;
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
  borderRadius: "5px",
  border: "solid 1px #183a58",
};

const menuItemStyle = {
  color: "#000",
};

function getNavItemIcon(itemLabel) {
  const iconMap = {
    Playground: <PlaySquareOutlined />,
    Home: <HomeOutlined />,
    Endpoints: <ApiOutlined />,
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
  const [showHelp, setShowHelp] = useState(false);
  const isLoggedIn = useRecoilValue(isLoggedInState);
  const profile = useRecoilValue(profileState);
  const [showPopover, setShowPopover] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);

  const HelpModal = () => {
    return (
      <Modal
        title="Welcome to Promptly"
        open={showHelp}
        onCancel={() => setShowHelp(false)}
        footer={null}
        width={900}
      >
        <br />
        <Alert
          message={
            <p>
              You can find the platform documentation at{" "}
              <a
                href="https://docs.trypromptly.com"
                target={"_blank"}
                rel="noreferrer"
              >
                https://docs.trypromptly.com
              </a>
            </p>
          }
          type="info"
          showIcon
        />{" "}
        <br />
        <Space
          style={{
            textAlign: "center",
            width: "100%",
            justifyContent: "center",
          }}
        >
          <video
            src="https://storage.googleapis.com/trypromptly-static/static/images/promptly-app-builder-demo.mp4"
            controls
            autoPlay
            muted
            loop
            style={{ maxWidth: "800px" }}
          />
        </Space>
        <h3>Frequently Asked Questions</h3>
        <Collapse defaultActiveKey={["1"]} accordion>
          <Panel
            header="Where do I add my Open AI and other provider keys"
            key="1"
          >
            <p>
              Use Settings on the sidebar to add Open AI and other available
              provider keys
            </p>
          </Panel>
          <Panel header="How do I get my PROMPTLY_API_KEY" key="2">
            <p>
              Your Promptly API key is available in your profile. Click on
              Setting icon on the sidebar and you will find your token
            </p>
          </Panel>
          <Panel header="I need help. Where do I get more information?" key="3">
            <p>
              You can reach out to us at{" "}
              <a href="mailto:contact@trypromptly.com">
                contact@trypromptly.com
              </a>
              . Alternatively, you can also contact us on our Twitter handle{" "}
              <a
                href="https://twitter.com/trypromptly"
                rel="noreferrer"
                target="_blank"
              >
                @trypromptly
              </a>
            </p>
          </Panel>
        </Collapse>
      </Modal>
    );
  };

  return (
    <Sider style={siderStyle} width={80}>
      <Col style={{ height: "100%" }}>
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
        <HelpModal />
      </Col>
    </Sider>
  );
}
