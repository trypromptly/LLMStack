import * as React from "react";
// eslint-disable-next-line
import AceEditor from "react-ace";

import { List, ListItem } from "@mui/material";

import { Box, Tab, CircularProgress, Alert } from "@mui/material";
import { TabContext, TabList, TabPanel } from "@mui/lab";

import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/theme-github";
import { createTheme } from "@mui/material/styles";

import validator from "@rjsf/validator-ajv8";
import ThemedJsonForm from "./ThemedJsonForm";
import { Empty } from "./form/Empty";

const outputTheme = createTheme({
  typography: {
    fontFamily: "Lato, sans-serif",
    fontSize: 14,
    color: "#000",
  },
  components: {
    MuiFormControl: {
      styleOverrides: {
        root: {
          "& .Mui-disabled": {
            color: "#000",
          },
        },
      },
    },
    MuiImageList: {
      styleOverrides: {
        root: {
          width: "100% !important",
          height: "100% !important",
        },
      },
    },
    MuiListItemText: {
      styleOverrides: {
        root: {
          whiteSpace: "pre-wrap",
        },
      },
    },
    MuiImageListItem: {
      styleOverrides: {
        img: {
          width: "auto",
          height: "auto",
        },
      },
    },
  },
});

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
      theme={outputTheme}
      className="output-form"
    ></ThemedJsonForm>
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
