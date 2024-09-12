import { TabContext, TabList, TabPanel } from "@mui/lab";
import { Box, Tab } from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import { useState } from "react";
import { Empty as EmptyComponent } from "./form/Empty";
import ThemedJsonForm from "./ThemedJsonForm";

export function InputThemedForm(props) {
  const { input, setInput, schema, uiSchema } = props;

  return (
    <ThemedJsonForm
      schema={schema}
      uiSchema={uiSchema}
      formData={input}
      validator={validator}
      onChange={({ formData }) => {
        setInput(formData);
      }}
      disableAdvanced={true}
    />
  );
}

export default function InputForm(props) {
  const { input, setInput } = props;
  const [tabValue, setTabValue] = useState("form");

  let schema = props.schema ? JSON.parse(JSON.stringify(props.schema)) : {};
  let uiSchema = props.uiSchema
    ? JSON.parse(JSON.stringify(props.uiSchema))
    : {};
  let input_form_label = props?.schema?.title
    ? props?.schema?.title
    : "Input Form";

  if (props?.schema?.title) {
    schema.title = "";
    schema.description = "";
  }

  return (
    <Box sx={{ width: "100%" }}>
      <TabContext value={tabValue}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <TabList
            onChange={(event, newValue) => {
              setTabValue(newValue);
            }}
            aria-label="Config form tabs"
          >
            <Tab
              label={input_form_label ? input_form_label : "Input Form"}
              value="form"
            />
          </TabList>
        </Box>
        <TabPanel value="form" sx={{ padding: "4px" }}>
          {Object.keys(props.schema).length === 0 ? (
            <EmptyComponent {...props} />
          ) : (
            <InputThemedForm
              schema={schema}
              uiSchema={uiSchema}
              input={input}
              setInput={setInput}
              submitBtn={props.submitBtn}
            />
          )}
        </TabPanel>
      </TabContext>
    </Box>
  );
}
