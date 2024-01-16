import ComputerTwoToneIcon from "@mui/icons-material/ComputerTwoTone";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ForumTwoToneIcon from "@mui/icons-material/ForumTwoTone";
import SmartButtonIcon from "@mui/icons-material/SmartButton";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  CardContent,
  Typography,
} from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import { useEffect, useState } from "react";
import { useValidationErrorsForAppComponents } from "../../data/appValidation";
import ThemedJsonForm from "../ThemedJsonForm";
import "./AppEditor.css";
import { AppInputSchemaEditor } from "./AppInputSchemaEditor";
import { AppStepCard } from "./AppStepCard";

export function AppConfigEditor({
  appType,
  activeStep,
  setActiveStep,
  inputFields,
  setInputFields,
  config,
  setConfig,
  isAgent,
}) {
  const [errors, setErrors] = useState([]);
  const [setValidationErrorsForId, clearValidationErrorsForId] =
    useValidationErrorsForAppComponents("appConfig");

  useEffect(() => {
    if (!isAgent) {
      if (errors.length > 0) {
        setValidationErrorsForId("appConfig", {
          id: "appConfig",
          name: "Application Input",
          errors: errors,
        });
      } else {
        clearValidationErrorsForId("appConfig");
      }
    }
  }, [errors, isAgent, setValidationErrorsForId, clearValidationErrorsForId]);

  return (
    <AppStepCard
      icon={
        appType?.name?.toLowerCase().includes("chat") ? (
          <ForumTwoToneIcon
            style={{
              color: activeStep === 1 ? "white" : "black",
              fontSize: 40,
            }}
          />
        ) : appType?.name?.toLowerCase().includes("agent") ? (
          <SmartButtonIcon
            style={{
              color: activeStep === 1 ? "white" : "black",
              fontSize: 40,
            }}
          />
        ) : (
          <ComputerTwoToneIcon
            style={{
              color: activeStep === 1 ? "white" : "black",
              fontSize: 40,
            }}
          />
        )
      }
      title={appType?.name}
      description={appType?.description}
      stepNumber={1}
      activeStep={activeStep}
      setActiveStep={setActiveStep}
      errors={errors}
    >
      <CardContent style={{ maxHeight: 400, overflow: "auto" }}>
        <Accordion defaultExpanded={!isAgent}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="input-content"
            id="input-header"
            className="app-editor-section-header"
          >
            App Input
          </AccordionSummary>
          <AccordionDetails>
            <AppInputSchemaEditor
              fields={
                isAgent
                  ? [
                      {
                        name: "task",
                        title: "Task",
                        description: "What do you want the agent to perform?",
                        type: "string",
                        required: true,
                      },
                    ]
                  : inputFields
              }
              setFields={setInputFields}
              readOnly={isAgent}
              setErrors={setErrors}
            />
          </AccordionDetails>
        </Accordion>
        <Accordion defaultExpanded={true}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="config-content"
            id="config-header"
            className="app-editor-section-header"
          >
            Configuration
          </AccordionSummary>
          <AccordionDetails>
            <ThemedJsonForm
              schema={{
                ...appType?.config_schema,
                ...{ title: "", description: "" },
              }}
              validator={validator}
              uiSchema={{
                ...appType?.config_ui_schema,
                ...{
                  "ui:submitButtonOptions": {
                    norender: true,
                  },
                },
              }}
              formData={config}
              onChange={({ formData }) => {
                setConfig(formData);
              }}
            />
          </AccordionDetails>
        </Accordion>
        <Accordion style={{ display: "none" }}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="transformer-content"
            id="transformer-header"
            className="app-editor-section-header"
          >
            <Typography>Data Transformer</Typography>
          </AccordionSummary>
          <AccordionDetails></AccordionDetails>
        </Accordion>
      </CardContent>
    </AppStepCard>
  );
}
