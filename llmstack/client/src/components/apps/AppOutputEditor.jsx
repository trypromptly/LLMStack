import { CardContent } from "@mui/material";
import { AppStepCard } from "./AppStepCard";
import TextField from "@mui/material/TextField";
import WebTwoToneIcon from "@mui/icons-material/WebTwoTone";
import { TextFieldWithVars } from "./TextFieldWithVars";

export function AppOutputEditor({
  index,
  activeStep,
  setActiveStep,
  outputTemplate,
  setOutputTemplate,
  outputSchemas,
  isAgent,
}) {
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
    >
      <CardContent style={{ maxHeight: 400, overflow: "auto" }}>
        <div style={{ position: "relative" }}>
          {isAgent ? (
            <TextField
              variant="outlined"
              value={"{{agent}}"}
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
