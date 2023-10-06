import { useEffect, useState } from "react";
import { Box, Button, ButtonGroup, Stack, Tooltip } from "@mui/material";
import yaml from "js-yaml";
import AceEditor from "react-ace";
import { ProcessorEditor } from "./ProcessorEditor";
import { AppConfigEditor } from "./AppConfigEditor";
import { AppOutputEditor } from "./AppOutputEditor";
import { AddProcessorDivider } from "./AddProcessorDivider";
import { getJSONSchemaFromInputFields } from "../../data/utils";
import { AppSaveButtons } from "./AppSaveButtons";
import "ace-builds/src-noconflict/mode-yaml";
import "ace-builds/src-noconflict/theme-dracula";

export function AppEditor(props) {
  const {
    app,
    setApp,
    saveApp,
    processors,
    setProcessors,
    appConfig,
    setAppConfig,
    appInputFields,
    setAppInputFields,
    appOutputTemplate,
    setAppOutputTemplate,
  } = props;
  const [activeStep, setActiveStep] = useState(1);
  const [outputSchemas, setOutputSchemas] = useState([]);
  const [editorType, setEditorType] = useState("ui");

  useEffect(() => {
    const { schema } = getJSONSchemaFromInputFields(appInputFields);
    setOutputSchemas([
      {
        label: "1. Input",
        items: schema,
        pillPrefix: "[1] Input / ",
      },
      ...processors.map((p, index) => {
        return {
          label: `${index + 2}. ${p.api_backend?.name}`,
          pillPrefix: `[${index + 2}] ${p.api_backend?.api_provider?.name} / ${
            p.api_backend?.name
          } / `,
          items: p.api_backend?.output_schema,
        };
      }),
    ]);
  }, [appInputFields, processors]);

  return (
    <Box>
      {editorType === "yaml" ? (
        <Box>
          <AceEditor
            mode="yaml"
            theme="dracula"
            value={yaml.dump(app?.data || {})}
            editorProps={{ $blockScrolling: true }}
            setOptions={{
              useWorker: false,
              showGutter: false,
            }}
            style={{
              borderRadius: "5px",
              width: "100%",
            }}
            onLoad={(editor) => {
              editor.renderer.setScrollMargin(10, 0, 10, 0);
              editor.renderer.setPadding(10);
            }}
            onChange={(value) => {
              try {
                const data = yaml.load(value);
                setApp({ ...app, data });
              } catch (e) {
                console.error(e);
              }
            }}
          />
        </Box>
      ) : (
        <Box>
          <Stack>
            <AppConfigEditor
              appType={app?.type}
              activeStep={activeStep}
              setActiveStep={setActiveStep}
              config={appConfig}
              setConfig={setAppConfig}
              inputFields={appInputFields}
              setInputFields={setAppInputFields}
              processors={processors}
              setProcessors={setProcessors}
              outputSchemas={outputSchemas}
            />
          </Stack>
          {processors.map((processor, index) => (
            <Stack style={{ justifyContent: "center" }} key={index}>
              <AddProcessorDivider showProcessorSelector={false} />
              <ProcessorEditor
                appId={app.uuid}
                index={index}
                processors={processors}
                setProcessors={setProcessors}
                activeStep={activeStep}
                setActiveStep={setActiveStep}
                outputSchemas={outputSchemas}
                isTool={app.app_type_slug === "agent"}
              />
            </Stack>
          ))}
          <Stack style={{ justifyContent: "center" }}>
            <AddProcessorDivider
              showProcessorSelector={true}
              setProcessorBackend={(apiBackend) => {
                const newProcessors = [...processors];
                newProcessors.push({
                  id: `_inputs${newProcessors.length + 1}`,
                  api_backend: apiBackend,
                  processor_slug: apiBackend?.slug,
                  provider_slug: apiBackend?.api_provider?.slug,
                  endpoint: null,
                  input: null,
                  config: null,
                });
                setProcessors(newProcessors);
                setActiveStep(newProcessors.length + 1);
              }}
            />
          </Stack>
          <Stack>
            <AppOutputEditor
              index={processors.length}
              activeStep={activeStep}
              setActiveStep={setActiveStep}
              outputTemplate={appOutputTemplate}
              setOutputTemplate={setAppOutputTemplate}
              outputSchemas={outputSchemas}
            />
          </Stack>
        </Box>
      )}
      <Stack
        direction="row"
        gap={1}
        sx={{
          maxWidth: "900px",
          margin: "auto",
          justifyContent: "space-between",
        }}
      >
        <Tooltip title="Toggle between UI and YAML editors">
          <ButtonGroup
            variant="outlined"
            color="primary"
            size="small"
            value={editorType}
            exclusive
            sx={{
              marginBottom: "50px",
              padding: "18px 0",
            }}
          >
            <Button
              value="ui"
              variant={editorType === "ui" ? "contained" : "outlined"}
              onClick={() => {
                setEditorType("ui");
              }}
            >
              UI
            </Button>
            <Button
              value="yaml"
              variant={editorType === "yaml" ? "contained" : "outlined"}
              onClick={() => {
                setEditorType("yaml");
              }}
            >
              YAML
            </Button>
          </ButtonGroup>
        </Tooltip>
        <AppSaveButtons saveApp={saveApp} />
      </Stack>
    </Box>
  );
}
