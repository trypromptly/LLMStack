import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import validator from "@rjsf/validator-ajv8";
import {
  Alert,
  Box,
  Button,
  ButtonGroup,
  CircularProgress,
  Stack,
  Step,
  Stepper,
  StepLabel,
  Typography,
} from "@mui/material";
import { useRecoilValue } from "recoil";
import { isMobileState } from "../../data/atoms";
import { get, set } from "lodash";
import ThemedJsonForm from "../ThemedJsonForm";
import { TextFieldWithVars } from "./TextFieldWithVars";
import { AppSaveButtons } from "./AppSaveButtons";

function AppTemplatePage(props) {
  const { appData, setAppData, page } = props;
  const [userFormData, setUserFormData] = useState({});

  const updateApp = useCallback(
    (formData) => {
      // For each property in the formData, set the corresponding property in the app based on the path in the property in schema
      const properties = page.schema.properties;
      Object.keys(formData).forEach((key) => {
        if (!properties[key] || !properties[key].path) {
          return;
        }
        const path = properties[key].path;
        set(appData, path, formData[key] === undefined ? "" : formData[key]);
      });

      setAppData({ ...appData });
    },
    [appData, page, setAppData],
  );

  useEffect(() => {
    if (!page) {
      return;
    }

    const newFormData = Object.keys(page?.schema?.properties || {}).reduce(
      (acc, key) => {
        const path = page.schema.properties[key].path;
        set(acc, key, get(appData, path, null));
        return acc;
      },
      {},
    );
    setUserFormData((oldUserFormData) => ({
      ...oldUserFormData,
      ...newFormData,
    }));
  }, [appData, page]);

  if (!page) {
    return null;
  }

  return (
    <Box>
      <ThemedJsonForm
        schema={{ ...page.schema, ...{ title: "", description: "" } }}
        uiSchema={page.ui_schema}
        validator={validator}
        formData={userFormData}
        onChange={({ formData }) => {
          setUserFormData(formData);
          updateApp(formData);
        }}
        widgets={{
          richtext: (props) => <TextFieldWithVars {...props} richText={true} />,
        }}
      />
    </Box>
  );
}

function SavedAppActions(props) {
  const { app } = props;
  const navigate = useNavigate();

  return (
    <Box mt={5} mb={5}>
      <Stack gap={2}>
        <Alert severity="success" icon={false}>
          🎉 Congratulations! You have now saved your app. Follow the links
          below to test, publish and integrate the app into other surfaces
        </Alert>
        <Typography variant="h6">Test your app</Typography>
        <ButtonGroup variant="outlined" aria-label="outlined button group">
          <Button
            sx={{ textTransform: "none" }}
            onClick={() => navigate(`/apps/${app.uuid}/preview`)}
          >
            Preview
          </Button>
        </ButtonGroup>
        <Typography variant="h6">
          Use the below links to embed your app into your Website, Slack or
          Discord channels
        </Typography>
        <ButtonGroup variant="outlined" aria-label="outlined button group">
          <Button
            sx={{ textTransform: "none" }}
            onClick={() => navigate(`/apps/${app.uuid}/integrations/website`)}
          >
            Website
          </Button>
          <Button
            sx={{ textTransform: "none" }}
            onClick={() => navigate(`/apps/${app.uuid}/integrations/discord`)}
          >
            Discord
          </Button>
          <Button
            sx={{ textTransform: "none" }}
            onClick={() => navigate(`/apps/${app.uuid}/integrations/slack`)}
          >
            Slack
          </Button>
          <Button
            sx={{ textTransform: "none" }}
            onClick={() => navigate(`/apps/${app.uuid}/integrations/twilio`)}
            >
            Twilio
            </Button>
        </ButtonGroup>
      </Stack>
    </Box>
  );
}

export function AppTemplate(props) {
  const { app, setApp, saveApp, appTemplate } = props;
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [appSaved, setAppSaved] = useState(false);
  const isMobile = useRecoilValue(isMobileState);
  const steps = appTemplate?.pages || [];

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
    setAppSaved(false);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
    setAppSaved(false);
  };

  const handleSave = () => {
    setLoading(true);
    setActiveStep(steps.length);
    setLoading(false);
    setAppSaved(true);
  };

  if (!app?.template || !appTemplate) {
    return null;
  }

  return (
    <Box sx={{ textAlign: "left" }}>
      <Stepper
        activeStep={activeStep}
        orientation={isMobile ? "vertical" : "horizontal"}
      >
        {steps.map((page, index) => {
          return (
            <Step key={index}>
              <StepLabel
                optional={
                  <Typography variant="caption">{page.description}</Typography>
                }
              >
                {page.title}
              </StepLabel>
            </Step>
          );
        })}
      </Stepper>
      <p></p>
      <React.Fragment>
        {steps.map((page, index) => {
          return (
            <AppTemplatePage
              key={index}
              appData={app?.data}
              setAppData={(appData) => {
                setApp({ data: { ...app?.data, ...appData } });
              }}
              page={index === activeStep ? page : null}
            />
          );
        })}
        {loading && <CircularProgress />}
        {!loading && appSaved && <SavedAppActions app={app} />}
        <Box sx={{ display: "flex", flexDirection: "row", pt: 2 }}>
          <Button
            color="inherit"
            disabled={activeStep === 0}
            onClick={handleBack}
            sx={{ mr: 1, textTransform: "none", margin: "20px 0 70px 0" }}
            variant="outlined"
          >
            Back
          </Button>
          <Box sx={{ flex: "1 1 auto" }} />
          {activeStep === steps.length - 1 && (
            <AppSaveButtons saveApp={saveApp} postSave={handleSave} />
          )}
          {activeStep < steps.length - 1 && (
            <Button
              onClick={handleNext}
              variant="contained"
              sx={{ textTransform: "none", margin: "20px 0" }}
            >
              Next
            </Button>
          )}
        </Box>
      </React.Fragment>
    </Box>
  );
}
