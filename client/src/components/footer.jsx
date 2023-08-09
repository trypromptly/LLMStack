import { Layout } from "antd";

const { Footer } = Layout;

const footerStyle = {
  textAlign: "center",
  color: "#fff",
  backgroundColor: "#7dbcea",
};

export default function AppFooter() {
  return <Footer style={footerStyle} />;
}
