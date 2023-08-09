import React, { useState, useRef } from "react";
import { Button } from "@mui/material";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { CircularProgress, Grid } from "@mui/material";
import { stitchObjects } from "../../data/utils";
import FileUploadWidget from "../form/DropzoneFileWidget";
import { Errors } from "../Output";
import MarkdownRenderer from "./MarkdownRenderer";
import { LexicalRenderer } from "./lexical/LexicalRenderer";
import Form from "@rjsf/mui";
import validator from "@rjsf/validator-ajv8";
import { Liquid } from "liquidjs";
import "./WebAppRenderer.css";
import VoiceRecorderWidget from "../form/VoiceRecorderWidget";

const defaultTheme = createTheme({
  components: {
    MuiInputBase: {
      defaultProps: {
        autoComplete: "off",
      },
    },
    MuiTextField: {
      defaultProps: {
        variant: "outlined",
      },
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": {
            "& > fieldset": { border: "1px solid #ccc" },
          },
        },
      },
    },
  },
});

function CustomFileWidget(props) {
  return <FileUploadWidget {...props} />;
}

function CustomVoiceRecorderWidget(props) {
  return <VoiceRecorderWidget {...props} />;
}

export function WebAppRenderer({ app, ws }) {
  const [appSessionId, setAppSessionId] = useState(null);
  const [output, setOutput] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [userFormData, setUserFormData] = useState({});
  const [errors, setErrors] = useState(null);
  const templateEngine = new Liquid();
  const outputTemplate = templateEngine.parse(
    app?.output_template?.markdown || "",
  );
  const chunkedOutput = useRef({});
  const streamStarted = useRef(false);

  const SubmitButton = (props) => {
    const submitButtonText =
      props.uiSchema["ui:submitButtonOptions"]?.submitText || "Submit";
    const style = props.uiSchema["ui:submitButtonOptions"]?.props?.style || {};

    if (props.uiSchema["ui:submitButtonOptions"]?.norender) {
      return null;
    }

    return (
      <Button
        size="medium"
        variant="contained"
        type="submit"
        sx={{
          textTransform: "none",
          ...style,
          backgroundColor: isRunning ? "grey" : "primary",
        }}
      >
        {isRunning ? "Cancel" : submitButtonText}
      </Button>
    );
  };

  if (ws) {
    ws.setOnMessage((evt) => {
      const message = JSON.parse(evt.data);
      // Merge the new output with the existing output
      if (message.output) {
        // Set the streamStarted flag if the output has more than input data
        chunkedOutput.current = stitchObjects(
          chunkedOutput.current,
          message.output,
        );
      }

      // If we get session info, that means the stream has started
      if (!streamStarted.current && (message.session || message.errors)) {
        streamStarted.current = true;
      }

      if (message.session) {
        setAppSessionId(message.session.id);
      }

      if (message.event && message.event === "done") {
        streamStarted.current = false;
        setIsRunning(false);
      }

      if (message.errors && message.errors.length > 0) {
        setErrors({ errors: message.errors });
        setIsRunning(false);
      }

      templateEngine
        .render(outputTemplate, chunkedOutput.current)
        .then((response) => {
          setOutput(response);
        });
    });
  }

  const runApp = (input) => {
    setIsRunning(true);
    setErrors(null);
    streamStarted.current = false;
    chunkedOutput.current = {};

    ws.send(
      JSON.stringify({
        event: "run",
        input,
        session_id: appSessionId,
      }),
    );
    setIsRunning(true);
  };

  return (
    <div
      style={{
        maxWidth: 1200,
        margin: "0 auto",
        width: "100%",
        padding: "0 10px",
        textAlign: "left",
      }}
    >
      <LexicalRenderer text={app.config?.input_template} />
      <ThemeProvider theme={defaultTheme}>
        <Form
          schema={app.input_schema}
          uiSchema={{
            ...app.input_ui_schema,
            ...{
              "ui:submitButtonOptions": { props: { disabled: isRunning } },
            },
          }}
          validator={validator}
          formData={userFormData}
          onSubmit={({ formData }) => {
            if (!isRunning) {
              setUserFormData(formData);
              runApp(formData);
            } else {
              ws.send(
                JSON.stringify({
                  event: "stop",
                  session_id: appSessionId,
                }),
              );
              setIsRunning(false);
            }
          }}
          templates={{ ButtonTemplates: { SubmitButton } }}
          widgets={{
            FileWidget: CustomFileWidget,
            voice: CustomVoiceRecorderWidget,
          }}
        />
      </ThemeProvider>
      <div style={{ marginTop: 50 }}>
        {isRunning && !streamStarted.current && !errors && (
          <Grid
            sx={{
              margin: "auto",
              textAlign: "center",
            }}
          >
            <CircularProgress />
          </Grid>
        )}
        <MarkdownRenderer className="webapp-output">{output}</MarkdownRenderer>
        {errors && <Errors runError={errors} />}
      </div>
    </div>
  );
}
