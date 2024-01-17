import { TabContext, TabList, TabPanel } from "@mui/lab";
import {
  Alert,
  Box,
  CircularProgress,
  List,
  ListItem,
  Tab,
} from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import * as React from "react";
import { Empty } from "./form/Empty";
import ThemedJsonForm from "./ThemedJsonForm";

export function Errors(props) {
  let errors = props.runError?.errors || props.runError || [];

  return (
    <List>
      {errors.map((error) => (
        <ListItem key={error}>
          <Alert severity="error">{error}</Alert>
        </ListItem>
      ))}
    </List>
  );
}

export function Result(props) {
  let formData = { ...(props.formData || {}) };

  if (formData?.api_response) {
    delete formData.api_response;
  }

  return Object.keys(props?.formData || {}).length > 0 ? (
    <ThemedJsonForm
      validator={validator}
      schema={props.schema}
      uiSchema={props.uiSchema}
      formData={formData}
      readonly={true}
      className="output-form"
      disableAdvanced={true}
    />
  ) : (
    <Empty emptyMessage="No output" />
  );
}

export default function Output(props) {
  const [value, setValue] = React.useState("form");

  return (
    <Box sx={{ width: "100%" }}>
      <TabContext value={value}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <TabList
            onChange={(event, newValue) => {
              setValue(newValue);
            }}
            aria-label="Output form tabs"
          >
            <Tab label="Output" value="form" />
          </TabList>
        </Box>
        <TabPanel value="form" sx={{ padding: "4px" }}>
          {props.loading ? (
            <CircularProgress />
          ) : (
            <Box>
              <Result {...props} />
              <Errors {...props} />
            </Box>
          )}
        </TabPanel>
      </TabContext>
    </Box>
  );
}
