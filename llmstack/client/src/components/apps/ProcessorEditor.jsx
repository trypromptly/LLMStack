import DeleteIcon from "@mui/icons-material/Delete";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  CardContent,
  FormControlLabel,
  Checkbox,
  Typography,
} from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import { lazy, useEffect, useRef, useState, useMemo } from "react";
import { useRecoilValue } from "recoil";
import { useValidationErrorsForAppComponents } from "../../data/appValidation";
import { processorsState } from "../../data/atoms";
import "./AppEditor.css";

const ThemedJsonForm = lazy(() => import("../ThemedJsonForm"));
const AppStepCard = lazy(() => import("./AppStepCard"));
const TextFieldWithVars = lazy(() => import("./TextFieldWithVars"));
const AppInputSchemaEditor = lazy(() => import("./AppInputSchemaEditor"));

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
  const processorList = useRecoilValue(processorsState);
  const processorData = processors[index];
  const [errors, setErrors] = useState([]);
  const inputFields = useRef(processorData?.input_fields || []);
  const toolOutputTemplate = useRef(
    processorData?.output_template?.markdown || "",
  );

  const processor = processorList.find(
    (p) =>
      p.provider?.slug === processorData?.provider_slug &&
      p.slug === processorData?.processor_slug,
  );
  const [inputFieldsEnabled, setInputFieldsEnabled] = useState(
    processorData?.input_fields?.length > 0,
  );

  useEffect(() => {
    let newErrors = [];
    if (!isTool && processor?.input_schema?.required) {
      processor?.input_schema?.required.forEach((requiredField) => {
        if (!processorData?.input[requiredField]) {
          newErrors.push({
            message: `Missing required field: ${requiredField}`,
          });
        } else if (Array.isArray(processorData?.input[requiredField])) {
          if (
            processorData?.input[requiredField].length === 0 ||
            processorData?.input[requiredField].includes("")
          ) {
            newErrors.push({
              message: `${requiredField} should contain at least one item`,
            });
          }
        }
      });
    }

    if (processor?.config_schema?.required) {
      processor?.config_schema.required.forEach((requiredField) => {
        if (!processorData.config[requiredField]) {
          newErrors.push({
            message: `Missing required field: ${requiredField}`,
          });
        } else if (Array.isArray(processorData.config[requiredField])) {
          if (
            processorData.config[requiredField].length === 0 ||
            processorData.config[requiredField].includes("")
          ) {
            newErrors.push({
              message: `${requiredField} should contain at least one item`,
            });
          }
        }
      });
    }

    setErrors(newErrors);
  }, [
    isTool,
    processor,
    processorData.input,
    processorData.config,
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

  const memoizedTextFieldWithVars = useMemo(() => {
    return (props) => (
      <TextFieldWithVars
        {...props}
        schemas={outputSchemas.slice(0, index + 1)}
      />
    );
  }, [outputSchemas, index]);
  console.log(processorData);
  return (
    <AppStepCard
      icon={processor?.icon || processor?.provider?.name}
      title={processor?.name || processor?.provider?.name}
      description={processor?.description || processor?.provider?.description}
      setDescription={(description) => {
        processors[index].description =
          description || processor?.provider?.description;
        setProcessors([...processors]);
      }}
      stepNumber={index + 2}
      activeStep={activeStep}
      setActiveStep={setActiveStep}
      errors={isTool ? [] : errors}
      action={
        index === processors.length - 1 || isTool ? (
          <DeleteIcon
            style={{ color: "#888", cursor: "pointer", marginTop: "3px" }}
            onClick={() => {
              let newProcessors = processors.slice();
              newProcessors.splice(index, 1);
              setProcessors(newProcessors);
            }}
          />
        ) : null
      }
    >
      <CardContent style={{ maxHeight: 400, overflow: "auto" }}>
        {isTool && (
          <Accordion defaultExpanded={inputFields.length > 0}>
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              aria-controls="input-fields-content"
              id="input-fields-header"
              style={{ backgroundColor: "#dce8fb" }}
              className="app-editor-section-header"
            >
              Input Fields
            </AccordionSummary>
            <AccordionDetails>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={inputFieldsEnabled}
                    onChange={(e) => {
                      setInputFieldsEnabled(e.target.checked);
                      if (!e.target.checked) {
                        inputFields.current = null;
                        processors[index].input_fields = null;
                        setProcessors([...processors]);
                      } else {
                        inputFields.current = processorData?.input_fields || [];
                        processors[index].input_fields =
                          processorData?.input_fields || [];
                        setProcessors([...processors]);
                      }
                    }}
                  />
                }
                label="Enable Input Fields for custom tool schema to Agent"
                sx={{ mb: 2, mt: 2 }}
              />
              {inputFieldsEnabled && (
                <AppInputSchemaEditor
                  fields={inputFields.current}
                  setFields={(fields) => {
                    inputFields.current = fields;
                    processors[index].input_fields = fields;
                    setProcessors([...processors]);
                  }}
                  setErrors={setErrors}
                  message={
                    "Define the input fields you want to expose to the agent from this tool. You must use these fields as input to the processor with template variables in order to complete the tool call using {{field_name}}."
                  }
                />
              )}
            </AccordionDetails>
          </Accordion>
        )}
        <Accordion
          defaultExpanded={
            processorData?.provider_slug === "promptly" &&
            processorData.processor_slug === "promptly_app"
              ? false
              : true
          }
        >
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
                ...processor?.input_schema,
                ...{ title: "", description: "" },
              }}
              validator={validator}
              uiSchema={{
                ...processor?.input_ui_schema,
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
                TextWidget: memoizedTextFieldWithVars,
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
                ...processor?.config_schema,
                ...{ title: "", description: "" },
              }}
              validator={validator}
              uiSchema={{
                ...processor?.config_ui_schema,
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
              aria-controls="output-template-content"
              id="output-template-header"
              style={{ backgroundColor: "#dce8fb" }}
              className="app-editor-section-header"
            >
              Output Template
            </AccordionSummary>
            <AccordionDetails>
              <TextFieldWithVars
                label="Output Template"
                multiline
                value={toolOutputTemplate.current}
                onChange={(text) => {
                  toolOutputTemplate.current = text;
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
