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
import { AppStepCard } from "./AppStepCard";
import CustomObjectFieldTemplate from "../../components/ConfigurationFormObjectFieldTemplate";

export function ProcessorEditor({
  index,
  processors,
  setProcessors,
  activeStep,
  setActiveStep,
  outputSchemas,
}) {
  const processor = processors[index];
  const apiBackend = processor?.api_backend;
  const [errors, setErrors] = useState([]);

  useEffect(() => {
    let newErrors = [];
    if (processor?.api_backend?.input_schema?.required) {
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
    processor,
    processor.input,
    processor.config,
    processor.input_schema,
    processor.config_schema,
  ]);

  return (
    <AppStepCard
      icon={apiBackend?.icon || apiBackend?.api_provider?.name}
      title={apiBackend?.name}
      description={apiBackend?.description}
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
            aria-controls="input-content"
            id="input-header"
            style={{ backgroundColor: "#dce8fb" }}
          >
            <Typography>Input</Typography>
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
            />
          </AccordionDetails>
        </Accordion>
        <Accordion defaultExpanded={true}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="config-content"
            id="config-header"
            style={{ backgroundColor: "#dce8fb" }}
          >
            <Typography>Configuration</Typography>
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
              templates={{ ObjectFieldTemplate: CustomObjectFieldTemplate }}
            />
          </AccordionDetails>
        </Accordion>
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
