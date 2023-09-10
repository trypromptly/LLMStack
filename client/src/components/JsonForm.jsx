import {
  materialRenderers,
  materialCells,
} from "@jsonforms/material-renderers";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { JsonForms } from "@jsonforms/react";
import { Box, Tab } from "@mui/material";
import { TabContext, TabList, TabPanel } from "@mui/lab";

import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-json";
import "ace-builds/src-noconflict/theme-github";
import { useRecoilState } from "recoil";
import { Empty } from "./form/Empty";

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
  const [value, setValue] = React.useState("form");

  if (Object.keys(props.schema).length === 0) {
    return <Empty emptyMessage={props.emptyMessage} />;
  }

  return (
    <Box sx={{ width: "100%" }}>
      <TabContext value={value}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <TabList
            onChange={(event, newValue) => {
              setValue(newValue);
            }}
            aria-label="Json form tabs"
          >
            <Tab label="Form" value="form" />
            <Tab label="JSON" value="json" />
          </TabList>
        </Box>
        <TabPanel value="form" sx={{ padding: "4px" }}>
          <ThemedJsonForm {...props} />
        </TabPanel>
        <TabPanel value="json" sx={{ padding: "4px" }}>
          <ThemedJsonEditor {...props} />
        </TabPanel>
      </TabContext>
    </Box>
  );
}
