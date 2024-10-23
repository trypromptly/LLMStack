import {
  Box,
  IconButton,
  Tooltip,
  Typography,
  Button,
  ButtonGroup,
  Grow,
  Paper,
  Popper,
  MenuItem,
  MenuList,
} from "@mui/material";
import { useTour } from "@reactour/tour";
import { useEffect, useState, useRef } from "react";
import { useCookies } from "react-cookie";
import { AppList } from "../components/apps/AppList";
import AppTemplatesContainer from "../components/apps/AppTemplatesContainer";
import { AppFromTemplateDialog } from "../components/apps/AppFromTemplateDialog";

import { SharedAppList } from "../components/apps/SharedAppList";
import "../index.css";
import GetAppOutlinedIcon from "@mui/icons-material/GetAppOutlined";
import { AppImportModal } from "../components/apps/AppImporter";
import { useRecoilValue } from "recoil";
import { isLoggedInState } from "../data/atoms";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import ClickAwayListener from "@mui/material/ClickAwayListener";
import { AddOutlined } from "@mui/icons-material";

function CreateAppButton({ onClick }) {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef(null);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const options = ["Agent", "Workflow", "Chatbot"];
  const slugs = ["_blank_agent", "_blank_web", "_blank_text-chat"];
  const descriptions = [
    "Create an AI agent.",
    "Create a workflow.",
    "Create a chatbot.",
  ];

  const handleMenuItemClick = (event, index) => {
    setSelectedIndex(index);
    setOpen(false);
  };

  const handleToggle = () => {
    setOpen((prevOpen) => !prevOpen);
  };

  const handleClose = (event) => {
    if (anchorRef.current && anchorRef.current.contains(event.target)) {
      return;
    }

    setOpen(false);
  };

  return (
    <Box
      sx={{
        float: "right",
        height: "100%",
        marginTop: "12px",
        marginRight: "10px",
      }}
    >
      <ButtonGroup
        variant="contained"
        ref={anchorRef}
        aria-label="split button"
        sx={{
          borderRadius: "10px",
        }}
      >
        <Tooltip title={descriptions[selectedIndex]}>
          <Button
            startIcon={<AddOutlined />}
            onClick={() => {
              onClick(slugs[selectedIndex]);
            }}
            sx={{ paddingRight: "0px" }}
          >
            {options[selectedIndex]}
          </Button>
        </Tooltip>
        <Button
          size="small"
          aria-controls={open ? "split-button-menu" : undefined}
          aria-expanded={open ? "true" : undefined}
          aria-label="select merge strategy"
          aria-haspopup="menu"
          onClick={handleToggle}
          sx={{ paddingLeft: "0px" }}
        >
          <ArrowDropDownIcon />
        </Button>
      </ButtonGroup>
      <Popper
        open={open}
        anchorEl={anchorRef.current}
        role={undefined}
        transition
        disablePortal
      >
        {({ TransitionProps, placement }) => (
          <Grow
            {...TransitionProps}
            style={{
              transformOrigin:
                placement === "bottom" ? "center top" : "center bottom",
            }}
          >
            <Paper>
              <ClickAwayListener onClickAway={handleClose}>
                <MenuList id="split-button-menu">
                  {options.map((option, index) => (
                    <MenuItem
                      key={option}
                      selected={index === selectedIndex}
                      onClick={(event) => handleMenuItemClick(event, index)}
                    >
                      {option}
                    </MenuItem>
                  ))}
                </MenuList>
              </ClickAwayListener>
            </Paper>
          </Grow>
        )}
      </Popper>
    </Box>
  );
}
const AppStudioPage = () => {
  const { steps, setSteps, setIsOpen } = useTour();
  const [cookies, setCookie] = useCookies(["app-studio-tour"]);
  const containerRef = useRef(null);
  const [appImportModalOpen, setAppImportModalOpen] = useState(false);
  const isLoggedIn = useRecoilValue(isLoggedInState);
  const [openAppFromTemplateDialog, setOpenAppFromTemplateDialog] =
    useState(false);
  const [selectedAppTemplateSlug, setSelectedAppTemplateSlug] = useState(null);

  if (!process.env.REACT_APP_ENABLE_APP_STORE && !isLoggedIn) {
    window.location.href = "/login";
  }

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
    <Box ref={containerRef} sx={{ m: 1 }}>
      <Box sx={{ marginBottom: "20px" }} className="app-template-list">
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
      <AppImportModal
        isOpen={appImportModalOpen}
        setIsOpen={setAppImportModalOpen}
      />
      <AppFromTemplateDialog
        open={openAppFromTemplateDialog}
        setOpen={setOpenAppFromTemplateDialog}
        appTemplateSlug={selectedAppTemplateSlug}
      />
      <Box style={{ marginBottom: "20px" }} className="your-apps">
        <CreateAppButton
          onClick={(slug) => {
            setOpenAppFromTemplateDialog(true);
            setSelectedAppTemplateSlug(slug);
          }}
        />
        <Tooltip arrow={true} title={"Import an app from YAML configuration."}>
          <IconButton
            style={{ float: "right", margin: "0.5em", color: "#1c3c5a" }}
            onClick={() => {
              setAppImportModalOpen(true);
            }}
          >
            <GetAppOutlinedIcon />
          </IconButton>
        </Tooltip>
        <Typography variant="h5" className="section-header">
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
    </Box>
  );
};

export default AppStudioPage;
