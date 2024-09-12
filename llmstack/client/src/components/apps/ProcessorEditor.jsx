import DeleteIcon from "@mui/icons-material/Delete";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  CardContent,
  Typography,
} from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import { lazy, useEffect, useRef, useState, useMemo } from "react";
import { useRecoilValue } from "recoil";
import { useValidationErrorsForAppComponents } from "../../data/appValidation";
import { appsState, processorsState } from "../../data/atoms";
import "./AppEditor.css";

const ThemedJsonForm = lazy(() => import("../ThemedJsonForm"));
const AppSelector = lazy(() => import("./AppSelector"));
const AppStepCard = lazy(() => import("./AppStepCard"));
const TextFieldWithVars = lazy(() => import("./TextFieldWithVars"));
const AppInputSchemaEditor = lazy(() => import("./AppInputSchemaEditor"));

function PromptlyAppStepCard({
  appId,
  processor,
  processorData,
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
    (app) => app.published_uuid === processorData.config.app_id,
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
  const appInputDataStr = processorData.input;
  let appInputData = {};
  try {
    appInputData = JSON.parse(appInputDataStr["input"]);
  } catch (e) {}

  return (
    <AppStepCard
      icon={processor?.icon || processor?.name}
      title={processorData?.name}
      description={processorData?.description}
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
              widgets={{
                appselect: (props) => (
                  <AppSelector
                    {...props}
                    apps={apps}
                    value={processorData.config.app_id}
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

  return processor?.provider_slug === "promptly" &&
    processor?.processor_slug === "app" ? (
    <PromptlyAppStepCard
      appId={appId}
      processor={processor}
      processorData={processorData}
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
        {false && isTool && (
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
              <AppInputSchemaEditor
                fields={inputFields.current}
                setFields={(fields) => {
                  inputFields.current = fields;
                  processors[index].input_fields = fields;
                  setProcessors([...processors]);
                }}
                setErrors={setErrors}
                message={
                  "Define the input fields you want to expose to the model. You must use these fields as input to the processor with template variables."
                }
              />
            </AccordionDetails>
          </Accordion>
        )}
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
