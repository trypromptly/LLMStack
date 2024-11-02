import { Box, Button, ButtonGroup, Stack, Tooltip } from "@mui/material";
import yaml from "js-yaml";
import { useEffect, useRef, useState } from "react";
import AceEditor from "react-ace";
import { getJSONSchemaFromInputFields } from "../../data/utils";
import { useRecoilValue } from "recoil";
import { processorsState } from "../../data/atoms";
import { AddProcessorDivider } from "./AddProcessorDivider";
import { AppConfigEditor } from "./AppConfigEditor";
import { AppOutputEditor } from "./AppOutputEditor";
import { AppSaveButtons } from "./AppSaveButtons";
import { ProcessorEditor } from "./ProcessorEditor";

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
  const processorList = useRecoilValue(processorsState);
  const yamlContent = useRef("");

  useEffect(() => {
    const { schema } = getJSONSchemaFromInputFields(appInputFields);
    setOutputSchemas([
      {
        label: "1. Input",
        items: schema,
        pillPrefix: "[1] Input / ",
        id: "_inputs0",
      },
      ...processors.map((p, index) => {
        const processor = processorList.find(
          (x) =>
            x.provider?.slug === p.provider_slug && x.slug === p.processor_slug,
        );

        return {
          label: `${index + 2}. ${processor?.name}`,
          pillPrefix: `[${index + 2}] ${processor?.provider?.name} / ${
            processor?.name
          } / `,
          items: processor?.output_schema,
          id: p?.id || `${processor?.slug}${index + 1}`,
        };
      }),
    ]);
  }, [appInputFields, processors, processorList]);

  return (
    <Box>
      {editorType === "yaml" ? (
        <Box>
          <AceEditor
            mode="yaml"
            theme="dracula"
            value={yaml.dump(
              {
                ...app?.data,
                is_published: app?.is_published || false,
                type_slug: app?.type?.slug,
                web_config: app?.web_config,
                twilio_config: app?.twilio_config,
                slack_config: app?.slack_config,
                discord_config: app?.discord_config,
              } || {},
            )}
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
              yamlContent.current = value;
            }}
            onBlur={(value) => {
              try {
                if (!yamlContent.current) return;
                const data = yaml.load(yamlContent.current);
                setApp({ ...app, data });
                setProcessors(data.processors);
                setAppConfig(data.config);
                setAppInputFields(data.input_fields);
                setAppOutputTemplate(data.output_template);
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
              isAgent={app.app_type_slug === "agent"}
            />
          </Stack>
          {processors.map((processor, index) => (
            <Stack style={{ justifyContent: "center" }} key={index}>
              <AddProcessorDivider
                showProcessorSelector={false}
                isTool={
                  app.app_type_slug === "agent" ||
                  app.app_type_slug === "voice-agent"
                }
              />
              <ProcessorEditor
                appId={app.uuid}
                index={index}
                processors={processors}
                setProcessors={setProcessors}
                activeStep={activeStep}
                setActiveStep={setActiveStep}
                outputSchemas={outputSchemas}
                isTool={
                  app.app_type_slug === "agent" ||
                  app.app_type_slug === "voice-agent"
                }
              />
            </Stack>
          ))}
          <Stack style={{ justifyContent: "center" }}>
            <AddProcessorDivider
              showProcessorSelector={true}
              setProcessorBackend={(processor) => {
                const newProcessors = [...processors];
                newProcessors.push({
                  id: `${processor?.slug}${newProcessors.length + 1}`,
                  processor: processor,
                  processor_slug: processor?.slug,
                  provider_slug: processor?.provider?.slug,
                  input: null,
                  config: null,
                  output_template: processor?.output_template,
                  dependencies: [],
                });
                setProcessors(newProcessors);
                setActiveStep(newProcessors.length + 1);
              }}
              isTool={
                app.app_type_slug === "agent" ||
                app.app_type_slug === "voice-agent"
              }
            />
          </Stack>
          <Stack>
            {app.app_type_slug !== "agent" &&
              app.app_type_slug !== "voice-agent" && (
                <AppOutputEditor
                  index={processors.length}
                  activeStep={activeStep}
                  setActiveStep={setActiveStep}
                  outputTemplate={appOutputTemplate}
                  setOutputTemplate={setAppOutputTemplate}
                  outputSchemas={outputSchemas}
                  isTool={
                    app.app_type_slug === "agent" ||
                    app.app_type_slug === "voice-agent"
                  }
                />
              )}
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
