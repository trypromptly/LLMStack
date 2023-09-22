import React from "react";
import { Box, Container, Typography } from "@mui/material";
import { AppTypeSelector } from "../components/apps/AppTypeSelector";
import { AppList } from "../components/apps/AppList";
import { AppTemplatesList } from "../components/apps/AppTemplatesList";
import { SharedAppList } from "../components/apps/SharedAppList";

const AppStudioPage = () => {
  return (
    <Container maxWidth="md" style={{ minWidth: "100%", padding: 5 }}>
      <Box style={{ marginTop: "5px", marginBottom: "20px" }}>
        <Typography
          variant="h6"
          style={{
            textAlign: "left",
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
        >
          Quickstart App Templates
        </Typography>
        <AppTemplatesList />
      </Box>
      <Box style={{ marginBottom: "20px" }}>
        <Typography
          variant="h6"
          style={{
            textAlign: "left",
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
        >
          Create a new App from scratch
        </Typography>
        <AppTypeSelector />
      </Box>
      <Box style={{ marginBottom: "20px" }}>
        <Typography
          variant="h6"
          style={{
            textAlign: "left",
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
        >
          Your Apps
        </Typography>
        <AppList />
      </Box>
      <Box style={{ marginBottom: "20px" }}>
        <Typography
          variant="h6"
          style={{
            textAlign: "left",
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
        >
          Apps Shared With You
        </Typography>
        <SharedAppList />
      </Box>
    </Container>
  );
};

export default AppStudioPage;
