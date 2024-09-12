import React, { useEffect, useState, useRef } from "react";
import { Stack, Box, Tab } from "@mui/material";
import { TabContext, TabList, TabPanel } from "@mui/lab";
import ProcessorSelector from "../ProcessorSelector";
import ThemedJsonForm from "../ThemedJsonForm";
import validator from "@rjsf/validator-ajv8";

import TextFieldWithVars from "../apps/TextFieldWithVars";

function getJsonpathTemplateString(variable, widget) {
  let templateString = `$.${variable}`;
  return templateString;
}

function liquidTemplateVariabletoJsonPath(variable) {
  if (!variable) {
    return "";
  }
  return variable.replace(/{{\s*(\S+)\s*}}/g, "$.$1");
}

export default function ProcessorRunForm({
  setData,
  providerSlug,
  processorSlug,
  processorInput,
  processorConfig,
  processorOutputTemplate,
}) {
  const [selectedProcessor, setSelectedProcessor] = useState(null);
  const inputDataRef = useRef(processorInput || {});
  const configDataRef = useRef(processorConfig || {});
  const outputTemplateRef = useRef(
    processorOutputTemplate?.jsonpath ||
      liquidTemplateVariabletoJsonPath(
        selectedProcessor?.output_template?.markdown,
      ) ||
      "",
  );
  const [tabValue, setTabValue] = useState("input");

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  useEffect(() => {
    setData({
      processor_slug: selectedProcessor?.slug,
      provider_slug: selectedProcessor?.provider?.slug,
      output_template: {
        jsonpath:
          outputTemplateRef.current ||
          liquidTemplateVariabletoJsonPath(
            selectedProcessor?.output_template?.markdown,
          ),
      },
      input: inputDataRef.current,
      config: configDataRef.current,
    });
  }, [selectedProcessor, setData]);

  useEffect(() => {
    inputDataRef.current = processorInput;
    configDataRef.current = processorConfig;
    outputTemplateRef.current = processorOutputTemplate?.jsonpath;
  }, [processorInput, processorConfig, processorOutputTemplate]);

  return (
    <Stack spacing={2}>
      <ProcessorSelector
        hideDescription={true}
        defaultProviderSlug={providerSlug}
        defaultProcessorSlug={processorSlug}
        onProcessorChange={(processor) => {
          setSelectedProcessor(processor);
        }}
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
            schema={selectedProcessor ? selectedProcessor.input_schema : {}}
            uiSchema={
              selectedProcessor ? selectedProcessor.input_ui_schema : {}
            }
            formData={processorInput || {}}
            validator={validator}
            onChange={(e) => {
              setData({
                input: e.formData,
                config: configDataRef.current || {},
                output_template: {
                  jsonpath:
                    outputTemplateRef.current ||
                    liquidTemplateVariabletoJsonPath(
                      selectedProcessor?.output_template?.markdown,
                    ) ||
                    "",
                },
                processor_slug: selectedProcessor?.slug,
                provider_slug: selectedProcessor?.provider?.slug,
              });
              inputDataRef.current = e.formData;
            }}
            disableAdvanced={true}
          />
        </TabPanel>
        <TabPanel value="config">
          <ThemedJsonForm
            schema={selectedProcessor ? selectedProcessor.config_schema : {}}
            uiSchema={
              selectedProcessor ? selectedProcessor.config_ui_schema : {}
            }
            formData={processorConfig || {}}
            validator={validator}
            onChange={(e) => {
              setData({
                input: inputDataRef.current || {},
                config: e.formData,
                output_template: {
                  jsonpath:
                    outputTemplateRef.current ||
                    liquidTemplateVariabletoJsonPath(
                      selectedProcessor?.output_template?.markdown,
                    ) ||
                    "",
                },
                processor_slug: selectedProcessor?.slug,
                provider_slug: selectedProcessor?.provider?.slug,
              });
              configDataRef.current = e.formData;
            }}
          />
        </TabPanel>
        <TabPanel value="output">
          <TextFieldWithVars
            label="Output Template"
            multiline
            value={
              outputTemplateRef.current ||
              liquidTemplateVariabletoJsonPath(
                selectedProcessor?.output_template?.markdown,
              )
            }
            templateStringResolver={getJsonpathTemplateString}
            onChange={(text) => {
              setData({
                input: inputDataRef.current || {},
                config: configDataRef.current || {},
                output_template: {
                  jsonpath: text,
                },
                processor_slug: selectedProcessor?.slug,
                provider_slug: selectedProcessor?.provider?.slug,
              });
              outputTemplateRef.current = text;
            }}
            sx={{ width: "100%" }}
            introText="Use JSON Path to pick data from the processor's output."
            schemas={[
              {
                label: selectedProcessor?.name,
                pillPrefix: `${selectedProcessor?.provider?.name} / ${selectedProcessor?.name} / `,
                items: selectedProcessor?.output_schema,
                id: null,
              },
            ]}
          />
        </TabPanel>
      </TabContext>
    </Stack>
  );
}
