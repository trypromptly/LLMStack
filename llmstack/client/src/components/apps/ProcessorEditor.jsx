import React, { useEffect, useState } from "react";
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CardContent,
  Typography,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import validator from "@rjsf/validator-ajv8";
import ThemedJsonForm from "../ThemedJsonForm";
import { TextFieldWithVars } from "./TextFieldWithVars";
import { AppSelector } from "./AppSelector";
import { AppStepCard } from "./AppStepCard";
import { appsState } from "../../data/atoms";
import { useRecoilValue } from "recoil";
import "./AppEditor.css";

import { useValidationErrorsForAppComponents } from "../../data/appValidation";

function PromptlyAppStepCard({
  appId,
  processor,
  apiBackend,
  index,
  activeStep,
  setActiveStep,
  errors,
  processors,
  setProcessors,
  outputSchemas,
}) {
  const apps = (useRecoilValue(appsState) || []).filter(
    (app) => app.published_uuid && app.uuid !== appId,
  );
  const selectedApp = apps.find(
    (app) => app.published_uuid === processor.config.app_id,
  );

  const appInput = { properties: {}, required: [] };
  const appInputUISchema = {};
  (selectedApp?.data?.input_fields || []).forEach((inputField) => {
    appInput.properties[inputField.name] = {
      title: inputField.name,
      type: inputField.type,
    };
    if (inputField.required) {
      appInput.required.push(inputField.name);
    }
    appInputUISchema[inputField.name] = {
      "ui:description": inputField.description,
      "ui:label": inputField.name,
    };
  });
  const appInputDataStr = processor.input;
  let appInputData = {};
  try {
    appInputData = JSON.parse(appInputDataStr["input"]);
  } catch (e) {}

  return (
    <AppStepCard
      icon={apiBackend?.icon || apiBackend?.api_provider?.name}
      title={apiBackend?.name}
      description={apiBackend?.description}
      setDescription={(description) => {
        processors[index].description = description;
        setProcessors([...processors]);
      }}
      stepNumber={index + 2}
      activeStep={activeStep}
      setActiveStep={setActiveStep}
      errors={errors}
      action={
        index === processors.length - 1 ? (
          <DeleteIcon
            style={{ color: "#888", cursor: "pointer", marginTop: "3px" }}
            onClick={() => {
              setProcessors(processors.slice(0, -1));
            }}
          />
        ) : null
      }
    >
      <CardContent style={{ maxHeight: 400, overflow: "auto" }}>
        <Accordion defaultExpanded={true}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="config-content"
            id="config-header"
            style={{ backgroundColor: "#dce8fb" }}
          >
            <Typography>Configure Application</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <ThemedJsonForm
              schema={{
                ...apiBackend?.config_schema,
                ...{ title: "", description: "" },
              }}
              validator={validator}
              uiSchema={{
                ...apiBackend?.config_ui_schema,
                ...{
                  "ui:submitButtonOptions": {
                    norender: true,
                  },
                },
              }}
              formData={processors[index].config}
              onChange={({ formData }) => {
                processors[index].config = formData;
                setProcessors([...processors]);
              }}
              widgets={{
                appselect: (props) => (
                  <AppSelector
                    {...props}
                    apps={apps}
                    value={processor.config.app_id}
                    onChange={(appId) => {
                      let oldFormData = processors[index].config;
                      processors[index].config = {
                        ...oldFormData,
                        app_id: appId,
                      };
                      setProcessors([...processors]);
                    }}
                  />
                ),
              }}
            />
          </AccordionDetails>
        </Accordion>
        <Accordion defaultExpanded={true}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="input-content"
            id="input-header"
            style={{ backgroundColor: "#dce8fb" }}
          >
            <Typography>Application Input</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <ThemedJsonForm
              schema={{
                ...appInput,
                ...{ title: "", description: "" },
              }}
              validator={validator}
              uiSchema={{
                ...appInputUISchema,
                ...{
                  "ui:submitButtonOptions": {
                    norender: true,
                  },
                },
              }}
              formData={appInputData}
              onChange={({ formData }) => {
                processors[index].input = { input: JSON.stringify(formData) };
                setProcessors([...processors]);
              }}
              widgets={{
                TextWidget: (props) => {
                  return (
                    <TextFieldWithVars
                      {...props}
                      schemas={outputSchemas.slice(0, index + 1)}
                    />
                  );
                },
              }}
            />
          </AccordionDetails>
        </Accordion>
      </CardContent>
    </AppStepCard>
  );
}

export function ProcessorEditor({
  appId,
  index,
  processors,
  setProcessors,
  activeStep,
  setActiveStep,
  outputSchemas,
  isTool,
}) {
  const [setValidationErrorsForId, clearValidationErrorsForId] =
    useValidationErrorsForAppComponents(index);
  const processor = processors[index];
  const apiBackend = processor?.api_backend;
  const [errors, setErrors] = useState([]);

  useEffect(() => {
    let newErrors = [];
    if (!isTool && processor?.api_backend?.input_schema?.required) {
      processor?.api_backend?.input_schema?.required.forEach(
        (requiredField) => {
          if (!processor?.input[requiredField]) {
            newErrors.push({
              message: `Missing required field: ${requiredField}`,
            });
          } else if (Array.isArray(processor?.input[requiredField])) {
            if (
              processor?.input[requiredField].length === 0 ||
              processor?.input[requiredField].includes("")
            ) {
              newErrors.push({
                message: `${requiredField} should contain at least one item`,
              });
            }
          }
        },
      );
    }

    if (processor?.api_backend?.config_schema?.required) {
      processor?.api_backend?.config_schema.required.forEach(
        (requiredField) => {
          if (!processor.config[requiredField]) {
            newErrors.push({
              message: `Missing required field: ${requiredField}`,
            });
          } else if (Array.isArray(processor.config[requiredField])) {
            if (
              processor.config[requiredField].length === 0 ||
              processor.config[requiredField].includes("")
            ) {
              newErrors.push({
                message: `${requiredField} should contain at least one item`,
              });
            }
          }
        },
      );
    }

    setErrors(newErrors);
  }, [
    isTool,
    processor,
    processor.input,
    processor.config,
    processor.input_schema,
    processor.config_schema,
  ]);

  useEffect(() => {
    if (errors.length > 0) {
      setValidationErrorsForId(index, {
        id: index + 1,
        name: processor.name,
        errors,
      });
    } else {
      clearValidationErrorsForId(index);
    }
  }, [
    errors,
    index,
    processor.name,
    setValidationErrorsForId,
    clearValidationErrorsForId,
  ]);

  return processor?.provider_slug === "promptly" &&
    processor?.processor_slug === "app" ? (
    <PromptlyAppStepCard
      appId={appId}
      apiBackend={apiBackend}
      processor={processor}
      index={index}
      activeStep={activeStep}
      setActiveStep={setActiveStep}
      errors={errors}
      processors={processors}
      setProcessors={setProcessors}
      outputSchemas={outputSchemas}
    />
  ) : (
    <AppStepCard
      icon={apiBackend?.icon || apiBackend?.api_provider?.name}
      title={processors[index].name || apiBackend?.name}
      description={processors[index].description || apiBackend?.description}
      setDescription={(description) => {
        processors[index].description = description || apiBackend?.description;
        setProcessors([...processors]);
      }}
      stepNumber={index + 2}
      activeStep={activeStep}
      setActiveStep={setActiveStep}
      errors={isTool ? [] : errors}
      action={
        index === processors.length - 1 ? (
          <DeleteIcon
            style={{ color: "#888", cursor: "pointer", marginTop: "3px" }}
            onClick={() => {
              setProcessors(processors.slice(0, -1));
            }}
          />
        ) : null
      }
    >
      <CardContent style={{ maxHeight: 400, overflow: "auto" }}>
        <Accordion defaultExpanded={true}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="input-content"
            id="input-header"
            className="app-editor-section-header"
          >
            Input
          </AccordionSummary>
          <AccordionDetails>
            <ThemedJsonForm
              schema={{
                ...apiBackend?.input_schema,
                ...{ title: "", description: "" },
              }}
              validator={validator}
              uiSchema={{
                ...apiBackend?.input_ui_schema,
                ...{
                  "ui:submitButtonOptions": {
                    norender: true,
                  },
                },
              }}
              formData={processors[index].input}
              onChange={({ formData }) => {
                processors[index].input = formData;
                setProcessors([...processors]);
              }}
              widgets={{
                TextWidget: (props) => {
                  return (
                    <TextFieldWithVars
                      {...props}
                      schemas={outputSchemas.slice(0, index + 1)}
                    />
                  );
                },
              }}
              disableAdvanced={true}
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
                ...apiBackend?.config_schema,
                ...{ title: "", description: "" },
              }}
              validator={validator}
              uiSchema={{
                ...apiBackend?.config_ui_schema,
                ...{
                  "ui:submitButtonOptions": {
                    norender: true,
                  },
                },
              }}
              formData={processors[index].config}
              onChange={({ formData }) => {
                processors[index].config = formData;
                setProcessors([...processors]);
              }}
            />
          </AccordionDetails>
        </Accordion>
        {isTool && (
          <Accordion defaultExpanded={true}>
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              aria-controls="config-content"
              id="config-header"
              style={{ backgroundColor: "#dce8fb" }}
            >
              <Typography>Output Template</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <TextFieldWithVars
                label="Output Template"
                multiline
                value={processor?.output_template?.markdown || ""}
                onChange={(text) => {
                  processors[index].output_template = { markdown: text };
                  setProcessors([...processors]);
                }}
                sx={{ width: "100%" }}
                placeholder="Use the {{ }} syntax to reference data from the processor's own output."
                schemas={outputSchemas.slice(index + 1, index + 2).map((s) => {
                  return {
                    label: s.label,
                    pillPrefix: s.pillPrefix,
                    items: s.items,
                    id: null,
                  };
                })}
              />
            </AccordionDetails>
          </Accordion>
        )}
        <Accordion>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="transformer-content"
            id="transformer-header"
            style={{ backgroundColor: "#dce8fb", display: "none" }}
          >
            <Typography>Data Transformer</Typography>
          </AccordionSummary>
          <AccordionDetails></AccordionDetails>
        </Accordion>
      </CardContent>
    </AppStepCard>
  );
}
