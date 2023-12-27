import React, { useState, useRef, useEffect } from "react";
import ReactGA from "react-ga4";
import { Button } from "@mui/material";
import { CircularProgress, Grid } from "@mui/material";
import { getJSONSchemaFromInputFields, stitchObjects } from "../../data/utils";
import FileUploadWidget from "../form/DropzoneFileWidget";
import { Errors } from "../Output";
import MarkdownRenderer from "./MarkdownRenderer";
import { LexicalRenderer } from "./lexical/LexicalRenderer";
import Form from "@rjsf/mui";
import { useSetRecoilState } from "recoil";
import { get } from "lodash";
import { streamChunksState } from "../../data/atoms";
import validator from "@rjsf/validator-ajv8";
import { Liquid } from "liquidjs";
import "./WebAppRenderer.css";
import VoiceRecorderWidget from "../form/VoiceRecorderWidget";
import { ContentCopyOutlined } from "@mui/icons-material";

function CustomFileWidget(props) {
  return <FileUploadWidget {...props} />;
}

function CustomVoiceRecorderWidget(props) {
  return <VoiceRecorderWidget {...props} />;
}

export function WebAppRenderer({ app, ws }) {
  const outputRef = useRef(null);
  const { schema, uiSchema } = getJSONSchemaFromInputFields(
    app?.data?.input_fields,
  );
  const [appSessionId, setAppSessionId] = useState(null);
  const [output, setOutput] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [userFormData, setUserFormData] = useState({});
  const [errors, setErrors] = useState(null);
  const templateEngine = new Liquid();
  const outputTemplate = templateEngine.parse(
    app?.data?.output_template?.markdown || "",
  );
  const setStreamChunks = useSetRecoilState(streamChunksState);
  const chunkedOutput = useRef({});
  const streamStarted = useRef(false);

  useEffect(() => {
    if (outputRef.current) {
      window.scrollTo(0, outputRef.current.scrollHeight);
    }
  }, [output]);

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
        const [newChunkedOutput, streamPaths] = stitchObjects(
          chunkedOutput.current,
          message.output,
        );
        chunkedOutput.current = newChunkedOutput;

        // Update streamChunks recoil state
        for (const path of streamPaths) {
          setStreamChunks((prevChunks) => {
            return {
              ...prevChunks,
              [path.replace(/_base64_chunks$/g, "")]: get(
                chunkedOutput.current,
                path,
                null,
              ),
            };
          });
        }
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

    ReactGA.event({
      category: "App",
      action: "Run Web App",
      label: app?.name,
      transport: "beacon",
    });
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
      <LexicalRenderer text={app.data?.config?.input_template} />
      <Form
        schema={schema}
        uiSchema={{
          ...uiSchema,
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
      <div style={{ marginTop: 10 }} ref={outputRef}>
        {output && !isRunning && (
          <Button
            startIcon={<ContentCopyOutlined />}
            onClick={() => navigator.clipboard.writeText(output)}
            sx={{
              justifyContent: "flex-end",
              textTransform: "none",
              width: "100%",
            }}
          >
            Copy
          </Button>
        )}
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
