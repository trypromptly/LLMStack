import { Empty, Input, Space, Spin, Tabs, Tag, Row, Col } from "antd";
import { List, ListItem } from "@mui/material";
import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/theme-github";
import { createTheme } from "@mui/material/styles";

import validator from "@rjsf/validator-ajv8";
import ThemedJsonForm from "./ThemedJsonForm";

const { TextArea } = Input;

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

const textAreaStyle = {
  fontFamily: "Source Code Pro, monospace",
  color: "#000",
  fontWeight: "500",
  background: "#fffaec",
  minHeight: 150,
  height: "100%",
};

export function Errors(props) {
  let errors = props.runError?.errors || [];

  return (
    <List>
      {errors.map((error) => (
        <ListItem key={error}>
          <Tag color="red" style={{ whiteSpace: "break-spaces" }}>
            {error}
          </Tag>
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
    <Col span={24}>
      <Row style={{ width: "100%" }}>
        <ThemedJsonForm
          validator={validator}
          schema={props.schema}
          uiSchema={props.uiSchema}
          formData={formData}
          readonly={true}
          theme={outputTheme}
          className="output-form"
        ></ThemedJsonForm>
      </Row>
    </Col>
  ) : (
    <Empty description="No output" />
  );
}

function Api(props) {
  let api = `Save endpoint to see API usage`;
  if (api && props.endpoint && !props.endpoint.draft) {
    api = `curl -X POST https://trypromptly.com/api/endpoints/${props.endpoint.parent_uuid} \\
    -H 'Content-Type: application/json' \\
    -H 'Authorization: Token <PROMPTLY_TOKEN>' \\
    -d '{"template_values": <KEY_VALUE_JSON>}'`;
  }
  return <TextArea value={api} disabled={true} style={textAreaStyle} />;
}

function Python(props) {
  let python = `Save endpoint to see example code`;
  if (python && props.endpoint && !props.endpoint.draft) {
    python = `import requests

PROMPTLY_API_KEY = <Your Promptly API Key>

url = 'https://trypromptly.com/api/endpoints/${props.endpoint.parent_uuid}'
headers = { 'Authorization': 'Token ' + PROMPTLY_API_KEY }
body = {'template_values': {'key': 'value'}}
    
response = requests.post(url, headers=headers, json = body)`;
  }

  return (
    <AceEditor
      style={{
        width: "100%",
        fontFamily: "Source Code Pro, monospace",
        fontSize: "14px",
      }}
      mode="python"
      theme="github"
      value={python}
      wrapEnabled={true}
      editorProps={{ $blockScrolling: true }}
      readOnly={true}
      setOptions={{
        useWorker: false,
        showGutter: false,
      }}
    />
  );
}

export default function Output(props) {
  return (
    <Tabs
      type="card"
      defaultActiveKey="1"
      items={[
        {
          key: "1",
          label: "Output",
          children: props.loading ? (
            <Spin tip={props.loadingTip} style={{ width: "100%" }} />
          ) : (
            <div>
              <Space
                style={{
                  position: "absolute",
                  zIndex: 1,
                  right: "17px",
                  height: "56px",
                }}
              >
                {props.tokenCount && <Tag>{`${props.tokenCount} Tokens`}</Tag>}
              </Space>
              <Result {...props} />
              <Errors {...props} />
            </div>
          ),
        },
        {
          key: "2",
          label: "API",
          children: <Api result={props.result} endpoint={props.endpoint} />,
        },
        {
          key: "3",
          label: "Python",
          children: <Python result={props.result} endpoint={props.endpoint} />,
        },
      ]}
    />
  );
}
