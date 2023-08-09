import { Layout } from "antd";

const { Content } = Layout;

const contentStyle = {
  textAlign: "center",
  height: "100%",
  paddingBottom: "50px",
  backgroundColor: "#fff",
  overflow: "auto",
};

export default function Container({ children }) {
  return <Content style={contentStyle}>{children}</Content>;
}
