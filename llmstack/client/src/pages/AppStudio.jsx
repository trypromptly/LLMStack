import { useEffect, useRef } from "react";
import { useTour } from "@reactour/tour";
import { useCookies } from "react-cookie";
import { Box, Container, Typography } from "@mui/material";
import { AppList } from "../components/apps/AppList";
import { SharedAppList } from "../components/apps/SharedAppList";
import "../index.css";
import AppTemplatesContainer from "../components/apps/AppTemplatesContainer";

const AppStudioPage = () => {
  const { steps, setSteps, setIsOpen } = useTour();
  const [cookies, setCookie] = useCookies(["app-studio-tour"]);
  const containerRef = useRef(null);

  // Tour
  useEffect(() => {
    if (
      containerRef.current &&
      !steps &&
      cookies["app-studio-tour"] !== "true"
    ) {
      setSteps([
        {
          selector: ".main",
          content: `Welcome to ${
            process.env.REACT_APP_SITE_NAME || "LLMStack"
          }. You can build generative AI apps, chatbot and agents here.`,
          position: "center",
        },
        {
          selector: ".sidebar",
          content: "Use the sidebar to navigate to different pages.",
        },
        {
          selector: ".app-template-list",
          content:
            "Use our curated app templates to get started quickly. Click on any template, fill the form and save the app to create a new app.",
        },
        {
          selector: ".create-new-app",
          content: "You can also create a new app from scratch.",
        },
        {
          selector: ".your-apps",
          content: "You can see all your apps here.",
        },
        {
          selector: ".shared-apps",
          content: "You can see all the apps shared with you here.",
          actionAfter: () => {
            setCookie("app-studio-tour", true, {
              maxAge: 8640000,
            });
          },
        },
      ]);

      setIsOpen(true);
    }
  });

  return (
    <Container
      maxWidth="md"
      style={{ minWidth: "100%", padding: 5 }}
      ref={containerRef}
    >
      <Box
        style={{ marginTop: "5px", marginBottom: "20px" }}
        className="app-template-list"
      >
        <Typography variant="h5" className="section-header">
          App Templates
          <br />
          <Typography variant="caption" sx={{ color: "#666" }}>
            You can use these templates to quickly create apps. Use blank
            templates to create apps from scratch.
          </Typography>
        </Typography>
        <AppTemplatesContainer />
      </Box>
      <Box style={{ marginBottom: "20px" }} className="your-apps">
        <Typography variant="h6" className="section-header">
          Your Apps
          <br />
          <Typography variant="caption" sx={{ color: "#666" }}>
            These are the apps you have created.
          </Typography>
        </Typography>
        <AppList />
      </Box>
      <Box style={{ marginBottom: "60px" }} className="shared-apps">
        <Typography variant="h5" className="section-header">
          Shared Apps
          <br />
          <Typography variant="caption" sx={{ color: "#666" }}>
            These apps have been shared with you. You can view and edit them
            depending on the permissions.
          </Typography>
        </Typography>
        <SharedAppList />
      </Box>
    </Container>
  );
};

export default AppStudioPage;
