import { UserOutlined } from "@ant-design/icons";
import { Avatar, Col, Image, Layout, Row } from "antd";
import logo from "../assets/promptly-logo.png";

const { Header } = Layout;

const headerStyle = {
  textAlign: "center",
  color: "#fff",
  height: 64,
  paddingInline: 50,
  lineHeight: "64px",
  backgroundColor: "#fff",
};

export default function AppHeader() {
  return (
    <Header style={headerStyle}>
      <Row>
        <Col span={12} style={{ textAlign: "left" }}>
          <Image width={200} src={logo} preview={false} />
        </Col>
        <Col span={12} style={{ textAlign: "right" }}>
          <Avatar size={48} icon={<UserOutlined />} />
        </Col>
      </Row>
    </Header>
  );
}
