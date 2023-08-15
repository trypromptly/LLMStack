import React from "react";
import { Button, Space, Image, Dropdown } from "antd";
import { MenuOutlined } from "@ant-design/icons";

const icon = require(`../assets/${
  process.env.REACT_APP_SITE_NAME
    ? process.env.REACT_APP_SITE_NAME.toLowerCase()
    : "llmstack"
}-icon.png`);

const iconStyle = {
  width: "32px",
};
const navbarStyle = {
  width: "100%",
  color: "#000",
  backgroundColor: "#ffdfb21c",
  borderBottom: "solid 1px #ccc",
};

export default function NavBar({ menuItems }) {
  return (
    <div>
      <nav className="navbar" style={navbarStyle}>
        <Space
          direction="horizontal"
          style={{
            padding: "5px",
            width: "100%",
            alignItems: "center",
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <a
            href="/"
            onClick={(e) => {
              e.preventDefault();
              window.location.href = "/";
            }}
          >
            <Image style={iconStyle} src={icon} preview={false} />
          </a>
          <Dropdown
            menu={{
              items: menuItems.map((item) => {
                return {
                  key: item.key,
                  label: <a href={item.link}>{item.label}</a>,
                };
              }),
            }}
            trigger={["click"]}
          >
            <Button
              className="nav-menu"
              icon={<MenuOutlined />}
              onClick={(e) => e.preventDefault()}
            ></Button>
          </Dropdown>
        </Space>
      </nav>
    </div>
  );
}
