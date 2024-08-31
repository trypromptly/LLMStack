import React, { useEffect, useState, useRef } from "react";
import { Stack, Box, Tab } from "@mui/material";
import { TabContext, TabList, TabPanel } from "@mui/lab";
import ApiBackendSelector from "../ApiBackendSelector";
import ThemedJsonForm from "../ThemedJsonForm";
import validator from "@rjsf/validator-ajv8";
import { useRecoilValue } from "recoil";
import { apiBackendSelectedState } from "../../data/atoms";
import TextFieldWithVars from "../apps/TextFieldWithVars";

export default function ProcessorRunForm({
  setData,
  providerSlug,
  processorSlug,
  processorInput,
  processorConfig,
  processorOutputTemplate,
}) {
  const apiBackendSelected = useRecoilValue(apiBackendSelectedState);
  const inputDataRef = useRef(processorInput || {});
  const configDataRef = useRef(processorConfig || {});
  const outputTemplateRef = useRef(
    processorOutputTemplate?.markdown ||
      apiBackendSelected?.output_template?.markdown ||
      "",
  );
  const [tabValue, setTabValue] = useState("input");

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  useEffect(() => {
    setData({
      processor_slug: apiBackendSelected?.slug,
      provider_slug: apiBackendSelected?.api_provider?.slug,
      output_template: {
        markdown: outputTemplateRef.current,
      },
      input: inputDataRef.current,
      config: configDataRef.current,
    });
  }, [apiBackendSelected, setData]);

  return (
    <Stack spacing={2}>
      <ApiBackendSelector
        hideDescription={true}
        defaultProvider={providerSlug}
        defaultProcessor={processorSlug}
      />
      <TabContext value={tabValue}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <TabList
            onChange={handleTabChange}
            aria-label="Processor run form tabs"
          >
            <Tab label="Input" value="input" />
            <Tab label="Config" value="config" />
            <Tab label="Output" value="output" />
          </TabList>
        </Box>
        <TabPanel value="input">
          <ThemedJsonForm
            schema={apiBackendSelected ? apiBackendSelected.input_schema : {}}
            uiSchema={
              apiBackendSelected ? apiBackendSelected.input_ui_schema : {}
            }
            formData={inputDataRef.current || {}}
            validator={validator}
            onChange={(e) => {
              setData({
                input: e.formData,
              });
              inputDataRef.current = e.formData;
            }}
            disableAdvanced={true}
          />
        </TabPanel>
        <TabPanel value="config">
          <ThemedJsonForm
            schema={apiBackendSelected ? apiBackendSelected.config_schema : {}}
            uiSchema={
              apiBackendSelected ? apiBackendSelected.config_ui_schema : {}
            }
            formData={configDataRef.current || {}}
            validator={validator}
            onChange={(e) => {
              setData({
                config: e.formData,
              });
              configDataRef.current = e.formData;
            }}
          />
        </TabPanel>
        <TabPanel value="output">
          <TextFieldWithVars
            label="Output Template"
            multiline
            value={outputTemplateRef.current}
            onChange={(text) => {
              setData({
                output_template: { markdown: text },
              });
              outputTemplateRef.current = text;
            }}
            sx={{ width: "100%" }}
            introText="Use the {{ }} syntax to reference data from the processor's own output."
            schemas={[
              {
                label: apiBackendSelected?.name,
                pillPrefix: `${apiBackendSelected?.api_provider?.name} / ${apiBackendSelected?.name} / `,
                items: apiBackendSelected?.output_schema,
                id: null,
              },
            ]}
          />
        </TabPanel>
      </TabContext>
    </Stack>
  );
}
