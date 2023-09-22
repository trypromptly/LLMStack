import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CardContent,
  Typography,
} from "@mui/material";
import ComputerTwoToneIcon from "@mui/icons-material/ComputerTwoTone";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ForumTwoToneIcon from "@mui/icons-material/ForumTwoTone";
import validator from "@rjsf/validator-ajv8";
import ThemedJsonForm from "../ThemedJsonForm";
import { AppInputSchemaEditor } from "./AppInputSchemaEditor";
import { AppStepCard } from "./AppStepCard";
import { TextFieldWithVars } from "./TextFieldWithVars";
import CustomObjectFieldTemplate from "../../components/ConfigurationFormObjectFieldTemplate";

export function AppConfigEditor({
  appType,
  activeStep,
  setActiveStep,
  inputFields,
  setInputFields,
  config,
  setConfig,
}) {
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
    >
      <CardContent style={{ maxHeight: 400, overflow: "auto" }}>
        <Accordion defaultExpanded={true}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="input-content"
            id="input-header"
            style={{ backgroundColor: "#dce8fb" }}
          >
            <Typography>App Input</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <AppInputSchemaEditor
              fields={inputFields}
              setFields={setInputFields}
              readOnly={appType?.slug === "slack"}
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
              widgets={{
                richtext: (props) => (
                  <TextFieldWithVars {...props} richText={true} />
                ),
              }}
              templates={{ ObjectFieldTemplate: CustomObjectFieldTemplate }}
            />
          </AccordionDetails>
        </Accordion>
        <Accordion style={{ display: "none" }}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="transformer-content"
            id="transformer-header"
            style={{ backgroundColor: "#dce8fb" }}
          >
            <Typography>Data Transformer</Typography>
          </AccordionSummary>
          <AccordionDetails></AccordionDetails>
        </Accordion>
      </CardContent>
    </AppStepCard>
  );
}
