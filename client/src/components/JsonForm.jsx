import {
  materialRenderers,
  materialCells,
} from "@jsonforms/material-renderers";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { JsonForms } from "@jsonforms/react";
import { Empty, Tabs } from "antd";
import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-json";
import "ace-builds/src-noconflict/theme-github";
import { useRecoilState } from "recoil";

const theme = createTheme({
  typography: {
    fontSize: 12,
  },
});

export function ThemedJsonForm(props) {
  const [data, setData] = useRecoilState(props.atomState);

  return (
    <ThemeProvider theme={theme}>
      <JsonForms
        schema={props.schema}
        uischema={props.uischema}
        data={data}
        renderers={materialRenderers}
        cells={materialCells}
        onChange={({ data, _errors }) => {
          setData(data);
        }}
      />
    </ThemeProvider>
  );
}

export function ThemedJsonEditor(props) {
  const [data, setData] = useRecoilState(props.atomState);

  return (
    <AceEditor
      mode="json"
      theme="github"
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

export default function JsonForm(props) {
  if (Object.keys(props.schema).length === 0) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_DEFAULT}
        description={
          props.emptyMessage ? props.emptyMessage : "Schema not found"
        }
        style={{ color: "#838383" }}
      />
    );
  }

  return (
    <Tabs
      defaultActiveKey="1"
      items={[
        {
          key: "1",
          label: "Form",
          children: <ThemedJsonForm {...props} />,
        },
        {
          key: "2",
          label: "JSON",
          children: <ThemedJsonEditor {...props} />,
        },
      ]}
    />
  );
}
