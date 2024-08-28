import React, { useEffect, useState } from "react";
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
  columns,
}) {
  const apiBackendSelected = useRecoilValue(apiBackendSelectedState);
  const [tabValue, setTabValue] = useState("input");

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  useEffect(() => {
    setData({
      processor_slug: apiBackendSelected?.slug,
      provider_slug: apiBackendSelected?.api_provider?.slug,
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
            formData={processorInput}
            validator={validator}
            onChange={(e) => {
              setData({
                input: e.formData,
              });
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
            formData={processorConfig}
            validator={validator}
            onChange={(e) => {
              setData({
                config: e.formData,
              });
            }}
          />
        </TabPanel>
        <TabPanel value="output">
          <TextFieldWithVars
            label="Output Template"
            multiline
            value={
              processorOutputTemplate?.markdown ||
              apiBackendSelected?.output_template?.markdown ||
              ""
            }
            onChange={(text) => {
              setData({
                output_template: { markdown: text },
              });
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
