import { Tabs } from "antd";
import { useRecoilState } from "recoil";
import AceEditor from "react-ace";
import validator from "@rjsf/validator-ajv8";
import "ace-builds/src-noconflict/mode-json";
import "ace-builds/src-noconflict/theme-chrome";

import ThemedJsonForm from "./ThemedJsonForm";
import { endpointConfigValueState } from "../data/atoms";
import CustomObjectFieldTemplate from "../components/ConfigurationFormObjectFieldTemplate";
import { Empty as EmptyComponent } from "../components/form/Empty";

export function ThemedForm(props) {
  const [data, setData] = useRecoilState(endpointConfigValueState);
  return (
    <ThemedJsonForm
      schema={props.schema}
      uiSchema={props.uiSchema}
      formData={data}
      onChange={({ formData }) => {
        setData(formData);
      }}
      validator={validator}
      templates={{ ObjectFieldTemplate: CustomObjectFieldTemplate }}
    >
      <div></div>
    </ThemedJsonForm>
  );
}

export function ThemedJsonEditor() {
  const [data, setData] = useRecoilState(endpointConfigValueState);

  return (
    <AceEditor
      mode="json"
      theme="chrome"
      value={JSON.stringify(data, null, 2)}
      onChange={(data) => {
        setData(JSON.parse(data));
      }}
      editorProps={{ $blockScrolling: true }}
      setOptions={{
        useWorker: false,
        showGutter: false,
      }}
    />
  );
}

export default function ConfigForm(props) {
  let schema = props.schema ? JSON.parse(JSON.stringify(props.schema)) : {};

  if (props?.schema?.title) {
    schema.title = null;

    schema.description = null;
  }

  return (
    <Tabs
      type="card"
      style={{ width: "100%" }}
      defaultActiveKey="1"
      items={[
        {
          key: "1",
          label: "Config Form",
          children:
            Object.keys(props.schema).length === 0 ? (
              <EmptyComponent {...props} />
            ) : (
              <ThemedForm schema={schema} uiSchema={props.uiSchema} />
            ),
        },
        {
          key: "2",
          label: "JSON",
          children:
            Object.keys(props.schema).length === 0 ? (
              <EmptyComponent {...props} />
            ) : (
              <ThemedJsonEditor {...props} />
            ),
        },
      ]}
    />
  );
}
