import * as React from "react";

import validator from "@rjsf/validator-ajv8";
import { useRecoilState, useRecoilValue } from "recoil";
import { inputValueState, templateValueState } from "../data/atoms";
import ThemedJsonForm from "./ThemedJsonForm";
import { createTheme } from "@mui/material/styles";

import { Box, Tab } from "@mui/material";
import { TabContext, TabList, TabPanel } from "@mui/lab";

import { Empty as EmptyComponent } from "./form/Empty";

const theme = createTheme({
  spacing: 2,
  typography: {
    fontSize: 12,
  },
  components: {
    MuiTextField: {
      defaultProps: {
        variant: "standard",
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          overflow: "scroll",
          textAlign: "left",
          "& .MuiTypography-root.MuiTypography-h5": {
            font: "inherit",
            fontSize: "1rem",
            fontWeight: "600",
            margin: "0.5rem 0.2rem",
            color: "#757575",
          },
          "& .MuiTypography-root.MuiTypography-subtitle2": {
            fontSize: "0.75rem",
          },
          "& .MuiBox-root .form-group .MuiFormControl-root .MuiBox-root": {
            display: "None",
          },
          "& .MuiBox-root .form-group .MuiFormControl-root .MuiFormHelperText-root":
            {
              display: "block",
            },
          "& .MuiBox-root .form-group .MuiFormControl-root .MuiFormHelperText-root.Mui-focused":
            {
              display: "block",
            },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        select: {
          textTransform: "capitalize",
        },
      },
    },
    MuiFormControl: {
      styleOverrides: {
        root: {
          padding: "2px",
          "& .MuiFormHelperText-root": {
            textAlign: "left",
            margin: "2px",
          },
          "& .MuiFormControl-root:has(.MuiSlider-root) label": {
            fontSize: "0.75rem",
            textAlign: "start",
          },
        },
      },
    },
  },
});

const getTemplateVariables = (input) => {
  const data = typeof input === "string" ? input : JSON.stringify(input);
  const regex = /{{(.*?)}}/g;
  const matches = data.matchAll(regex);
  const keys = Array.from(matches, (m) => m[1]);
  return keys;
};
// Parses given text and returns list of template keys defined as {{<template_key>}}
const getPromptValuesSchema = (input) => {
  const keys = getTemplateVariables(input);
  const schema = {
    type: "object",
    properties: {},
  };
  keys.forEach((key) => {
    schema.properties[key] = {
      type: "string",
      title: key,
    };
  });
  return schema;
};

export function InputThemedForm(props) {
  const [data, setData] = useRecoilState(inputValueState);

  return (
    <ThemedJsonForm
      schema={props.schema}
      uiSchema={props.uiSchema}
      formData={data}
      validator={validator}
      onChange={({ formData }) => {
        setData(formData);
      }}
      theme={theme}
    ></ThemedJsonForm>
  );
}

export function TemplateVariablesThemedForm(props) {
  const [data, setData] = useRecoilState(templateValueState);
  const input = useRecoilValue(inputValueState);

  return (
    <ThemedJsonForm
      schema={input && input !== "" ? getPromptValuesSchema(input) : {}}
      uiSchema={props.uiSchema}
      formData={data}
      validator={validator}
      onChange={({ formData }) => {
        setData(formData);
      }}
    >
      <div></div>
    </ThemedJsonForm>
  );
}

export default function InputForm(props) {
  const input = useRecoilValue(inputValueState);
  const [value, setValue] = React.useState("form");

  let schema = props.schema ? JSON.parse(JSON.stringify(props.schema)) : {};
  let uiSchema = props.uiSchema
    ? JSON.parse(JSON.stringify(props.uiSchema))
    : {};
  let input_form_label = null;

  input_form_label = props?.schema?.title ? props?.schema?.title : "Input Form";

  if (props?.schema?.title) {
    schema.title = "";
    schema.description = "";
  }
  return (
    <Box sx={{ width: "100%" }}>
      <TabContext value={value}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <TabList
            onChange={(event, newValue) => {
              setValue(newValue);
            }}
            aria-label="Config form tabs"
          >
            <Tab label="Input Form" value="form" />
          </TabList>
        </Box>
        <TabPanel value="form" sx={{ padding: "4px" }}>
          {Object.keys(props.schema).length === 0 ? (
            <EmptyComponent {...props} />
          ) : (
            <InputThemedForm
              schema={schema}
              uiSchema={uiSchema}
              submitBtn={props.submitBtn}
            />
          )}
        </TabPanel>
      </TabContext>
    </Box>
  );
}
