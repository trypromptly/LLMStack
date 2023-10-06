import { useEffect, useState } from "react";
import { Box, Stack } from "@mui/material";
import { ProcessorEditor } from "./ProcessorEditor";
import { AppConfigEditor } from "./AppConfigEditor";
import { AppOutputEditor } from "./AppOutputEditor";
import { AddProcessorDivider } from "./AddProcessorDivider";
import { getJSONSchemaFromInputFields } from "../../data/utils";
import { AppSaveButtons } from "./AppSaveButtons";

export function AppEditor(props) {
  const {
    app,
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
      <Stack
        direction="row"
        gap={1}
        sx={{
          flexDirection: "row-reverse",
          maxWidth: "900px",
          margin: "auto",
        }}
      >
        <AppSaveButtons saveApp={saveApp} />
      </Stack>
    </Box>
  );
}
