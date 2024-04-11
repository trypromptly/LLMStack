import WebTwoToneIcon from "@mui/icons-material/WebTwoTone";
import { CardContent } from "@mui/material";
import TextField from "@mui/material/TextField";
import { lazy, useEffect, useState } from "react";
import { useValidationErrorsForAppComponents } from "../../data/appValidation";

const AppStepCard = lazy(() => import("./AppStepCard"));
const TextFieldWithVars = lazy(() => import("./TextFieldWithVars"));

export function AppOutputEditor({
  index,
  activeStep,
  setActiveStep,
  outputTemplate,
  setOutputTemplate,
  outputSchemas,
  isAgent,
}) {
  const [errors, setErrors] = useState([]);

  const [setValidationErrorsForId, clearValidationErrorsForId] =
    useValidationErrorsForAppComponents();

  useEffect(() => {
    if (!isAgent) {
      let newErrors = [];
      if (!(outputTemplate?.markdown || "").trim()) {
        newErrors.push({ message: "Application Output cannot be empty" });
      }
      setErrors(newErrors);
    }
  }, [isAgent, outputTemplate]);

  useEffect(() => {
    if (errors.length > 0) {
      setValidationErrorsForId("outputTemplate", {
        id: "outputTemplate",
        name: "Application Output",
        errors: errors,
      });
    } else {
      clearValidationErrorsForId("outputTemplate");
    }
  }, [errors, setValidationErrorsForId, clearValidationErrorsForId]);

  return (
    <AppStepCard
      icon={
        <WebTwoToneIcon
          style={{
            color: index + 2 === activeStep ? "white" : "black",
            fontSize: 40,
          }}
        />
      }
      title="Application Output"
      description="Configure how the application will output data"
      stepNumber={index + 2}
      activeStep={activeStep}
      setActiveStep={setActiveStep}
      errors={errors}
    >
      <CardContent style={{ maxHeight: 400, overflow: "auto" }}>
        <div style={{ position: "relative" }}>
          {isAgent ? (
            <TextField
              variant="outlined"
              value={"{{agent.content}}"}
              disabled
              fullWidth
            />
          ) : (
            <TextFieldWithVars
              label="Output Template"
              multiline
              value={outputTemplate?.markdown || ""}
              onChange={(text) => {
                setOutputTemplate({ markdown: text });
              }}
              sx={{ width: "100%" }}
              placeholder="Use the {{ }} syntax to reference data from the input. For example, {{ name }}."
              schemas={outputSchemas}
            />
          )}
        </div>
      </CardContent>
    </AppStepCard>
  );
}
