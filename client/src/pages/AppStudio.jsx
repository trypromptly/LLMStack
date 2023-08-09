import { Typography } from "@mui/material";
import { Col, Divider, Row } from "antd";
import { AppTypeSelector } from "../components/apps/AppTypeSelector";
import { AppList } from "../components/apps/AppList";
import { AppTemplatesList } from "../components/apps/AppTemplatesList";
import { SharedAppList } from "../components/apps/SharedAppList";

const AppStudioPage = () => {
  return (
    <div id="app-studio-page" style={{ margin: 10 }}>
      <Col span={24}>
        <Row>
          <Typography
            style={{
              textAlign: "left",
              width: "100%",
              fontFamily: "Lato, sans-serif",
              marginBottom: "10px",
              padding: "5px 10px",
              fontWeight: 600,
              borderRadius: "5px",
              color: "#1c3c5a",
              fontSize: "18px",
              borderBottom: "solid 3px #1c3c5a",
              borderLeft: "solid 1px #ccc",
              borderRight: "solid 1px #ccc",
            }}
            variant="h6"
          >
            Quickstart App Templates
          </Typography>
          <AppTemplatesList />
        </Row>
        <Divider />
        <Row>
          <Typography
            style={{
              textAlign: "left",
              width: "100%",
              fontFamily: "Lato, sans-serif",
              marginBottom: "10px",
              padding: "5px 10px",
              fontWeight: 600,
              borderRadius: "5px",
              color: "#1c3c5a",
              fontSize: "18px",
              borderBottom: "solid 3px #1c3c5a",
              borderLeft: "solid 1px #ccc",
              borderRight: "solid 1px #ccc",
            }}
            variant="h6"
          >
            Create a new App from scratch
          </Typography>
          <AppTypeSelector />
        </Row>
        <Divider />
        <Row>
          <Typography
            style={{
              textAlign: "left",
              width: "100%",
              fontFamily: "Lato, sans-serif",
              marginBottom: "10px",
              padding: "5px 10px",
              fontWeight: 600,
              borderRadius: "5px",
              color: "#1c3c5a",
              fontSize: "18px",
              borderBottom: "solid 3px #1c3c5a",
              borderLeft: "solid 1px #ccc",
              borderRight: "solid 1px #ccc",
            }}
            variant="h6"
          >
            Your Apps
          </Typography>
          <AppList />
        </Row>
        <Divider />
        <Row>
          <Typography
            style={{
              textAlign: "left",
              width: "100%",
              fontFamily: "Lato, sans-serif",
              marginBottom: "10px",
              padding: "5px 10px",
              fontWeight: 600,
              borderRadius: "5px",
              color: "#1c3c5a",
              fontSize: "18px",
              borderBottom: "solid 3px #1c3c5a",
              borderLeft: "solid 1px #ccc",
              borderRight: "solid 1px #ccc",
            }}
            variant="h6"
          >
            Apps Shared With You
          </Typography>
          <SharedAppList />
        </Row>
      </Col>
    </div>
  );
};

export default AppStudioPage;
