import { useEffect, useState } from "react";
import { Box, Stack, Typography, Tab } from "@mui/material";
import { useRecoilValue } from "recoil";
import { profileState } from "../../data/atoms";
import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/mode-javascript";
import "ace-builds/src-noconflict/mode-sh";
import "ace-builds/src-noconflict/theme-dracula";
import TabContext from "@mui/lab/TabContext";
import TabList from "@mui/lab/TabList";
import TabPanel from "@mui/lab/TabPanel";

export function AppApiExamples(props) {
  const { app } = props;
  const [pythonCode, setPythonCode] = useState("");
  const [pythonCodeStreaming, setPythonCodeStreaming] = useState("");
  const [curlCode, setCurlCode] = useState("");
  const [curlCodeStreaming, setCurlCodeStreaming] = useState("");
  const [jsCode, setJsCode] = useState("");
  const [jsCodeStreaming, setJsCodeStreaming] = useState("");
  const [tabValue, setTabValue] = useState("1");
  const [streamingTabValue, setstreamingTabValue] = useState("1");

  const profile = useRecoilValue(profileState);

  useEffect(() => {
    setPythonCode(`import requests

PROMPTLY_TOKEN = '${profile?.token}'    
url = '${window.location.origin}/api/apps/${app?.uuid}/run'

payload = {
  "input": {
    ${app?.data.input_fields
      .map(({ name }) => `"${name}": "<${name}_value>"`)
      .join(",\n    ")}
  },
  "stream": False,
}
headers = {
  "Content-Type": "application/json",
  "Authorization": "Token " + PROMPTLY_TOKEN,
}

response = requests.request("POST", url, headers=headers, json=payload)

print(response.text.encode('utf8'))`);
    setPythonCodeStreaming(`import requests

PROMPTLY_TOKEN = '${profile?.token}'    
url = '${window.location.origin}/api/apps/${app?.uuid}/run'

payload = {
  "input": {
    ${app?.data.input_fields
      .map(({ name }) => `"${name}": "<${name}_value>"`)
      .join(",\n    ")}
  },
  "stream": True,
}
headers = {
  "Content-Type": "application/json",
  "Authorization": "Token " + PROMPTLY_TOKEN,
}

response = requests.post(url, headers=headers, json=payload, stream=True)
for line in response.iter_lines():
  if line:
    print(line.decode('utf8'))`);

    setCurlCode(`\ncurl --location --request POST \\
'${window.location.origin}/api/apps/${app?.uuid}/run' \\
--header 'Content-Type: application/json' \\
--header 'Authorization: Token ${profile?.token}' \\
--data-raw '{
  "input": {
    ${app?.data.input_fields
      .map(({ name }) => `"${name}": "<${name}_value>"`)
      .join(",\n    ")}
  },
  "stream": false
}'`);

    setCurlCodeStreaming(`\ncurl --location --request POST \\
'${window.location.origin}/api/apps/${app?.uuid}/run' \\
--header 'Content-Type: application/json' \\
--header 'Authorization: Token ${profile?.token}' \\
--data-raw '{
  "input": {
    ${app?.data.input_fields
      .map(({ name }) => `"${name}": "<${name}_value>"`)
      .join(",\n    ")}
  },
  "stream": true
}'`);

    setJsCode(`const axios = require('axios');

const url = '${window.location.origin}/api/apps/${app?.uuid}/run';
const PROMPTLY_TOKEN = '${profile?.token}';
const payload = {
  "input": {
    ${app?.data.input_fields
      .map(({ name }) => `"${name}": "<${name}_value>"`)
      .join(",\n    ")}
  },
  "stream": false,
}
const headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Token ' + PROMPTLY_TOKEN,

  }

axios.post(url, payload, { headers: headers})
  .then((response) => {
  console.log(response.data);
});`);

    setJsCodeStreaming(`const axios = require('axios');

const url = '${window.location.origin}/api/apps/${app?.uuid}/run';
const PROMPTLY_TOKEN = '${profile?.token}';
const payload = {
  "input": {
    ${app?.data.input_fields
      .map(({ name }) => `"${name}": "<${name}_value>"`)
      .join(",\n    ")}
  },
  "stream": true,
}
const headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Token ' + PROMPTLY_TOKEN,

  }
axios
  .post(url, payload, { headers, responseType: 'stream' })
  .then(response => {
    response.data.on('data', line => {
      if (line) {
        console.log(line.toString('utf8'));
      }
    });
  })
  .catch(error => {
    console.error(error);
  });

`);
  }, [app?.data?.input_fields, app?.uuid, profile?.token]);

  return (
    <div>
      <Box sx={{ textAlign: "left" }}>
        <Typography variant="h6">Non-Streaming</Typography>

        <TabContext value={tabValue}>
          <Box sx={{ borderBottom: 1 }}>
            <TabList
              onChange={(_, value) => {
                setTabValue(value);
              }}
              aria-label="Non streaming code examples"
            >
              <Tab label="Python" value="1" sx={{ textTransform: "none" }} />
              <Tab label="cURL" value="2" sx={{ textTransform: "none" }} />
              <Tab
                label="JavaScript"
                value="3"
                sx={{ textTransform: "none" }}
              />
            </TabList>
          </Box>
          <TabPanel value="1">
            <Stack gap={1}>
              <Typography variant="body2" mb={2}>
                Use the following code to run the app from your Python
                application
              </Typography>
            </Stack>
            <AceEditor
              mode="python"
              theme="dracula"
              value={pythonCode}
              editorProps={{ $blockScrolling: true }}
              setOptions={{
                useWorker: false,
                showGutter: false,
              }}
              style={{
                borderRadius: "5px",
                height: "300px",
                width: "100%",
                maxWidth: "600px",
              }}
              onLoad={(editor) => {
                editor.renderer.setScrollMargin(10, 0, 10, 0);
                editor.renderer.setPadding(10);
              }}
            />
          </TabPanel>
          <TabPanel value="2">
            <Stack gap={1}>
              <Typography variant="body2" mb={2}>
                Use the following code to run the app from your terminal
              </Typography>
            </Stack>
            <AceEditor
              mode="sh"
              theme="dracula"
              value={curlCode}
              editorProps={{ $blockScrolling: true }}
              setOptions={{
                useWorker: false,
                showGutter: false,
              }}
              style={{
                borderRadius: "5px",
                height: "300px",
                width: "100%",
                maxWidth: "600px",
              }}
              onLoad={(editor) => {
                editor.renderer.setScrollMargin(10, 0, 10, 0);
                editor.renderer.setPadding(10);
              }}
            />
          </TabPanel>
          <TabPanel value="3">
            <Stack gap={1}>
              <Typography variant="body2" mb={2}>
                Use the following code to run the app from your JavaScript app
              </Typography>
            </Stack>
            <AceEditor
              mode="javascript"
              theme="dracula"
              value={jsCode}
              editorProps={{ $blockScrolling: true }}
              setOptions={{
                useWorker: false,
                showGutter: false,
              }}
              style={{
                borderRadius: "5px",
                height: "300px",
                width: "100%",
                maxWidth: "600px",
              }}
              onLoad={(editor) => {
                editor.renderer.setScrollMargin(10, 0, 10, 0);
                editor.renderer.setPadding(10);
              }}
            />
          </TabPanel>
        </TabContext>
        <Typography variant="h6" mt={3}>
          Streaming
        </Typography>
        <TabContext value={streamingTabValue}>
          <Box sx={{ borderBottom: 1 }}>
            <TabList
              onChange={(_, value) => {
                setstreamingTabValue(value);
              }}
              aria-label="Non streaming code examples"
            >
              <Tab label="Python" value="1" sx={{ textTransform: "none" }} />
              <Tab label="cURL" value="2" sx={{ textTransform: "none" }} />
              <Tab
                label="JavaScript"
                value="3"
                sx={{ textTransform: "none" }}
              />
            </TabList>
          </Box>
          <TabPanel value="1">
            <Stack gap={1}>
              <Typography variant="body2" mb={2}>
                Use the following code to run the app from your Python
                application
              </Typography>
            </Stack>
            <AceEditor
              mode="python"
              theme="dracula"
              value={pythonCodeStreaming}
              editorProps={{ $blockScrolling: true }}
              setOptions={{
                useWorker: false,
                showGutter: false,
              }}
              style={{
                borderRadius: "5px",
                height: "350px",
                width: "100%",
                maxWidth: "600px",
              }}
              onLoad={(editor) => {
                editor.renderer.setScrollMargin(10, 0, 10, 0);
                editor.renderer.setPadding(10);
              }}
            />
          </TabPanel>
          <TabPanel value="2">
            <Stack gap={1}>
              <Typography variant="body2" mb={2}>
                Use the following code to run the app from your terminal
              </Typography>
            </Stack>
            <AceEditor
              mode="sh"
              theme="dracula"
              value={curlCodeStreaming}
              editorProps={{ $blockScrolling: true }}
              setOptions={{
                useWorker: false,
                showGutter: false,
              }}
              style={{
                borderRadius: "5px",
                height: "300px",
                width: "100%",
                maxWidth: "600px",
              }}
              onLoad={(editor) => {
                editor.renderer.setScrollMargin(10, 0, 10, 0);
                editor.renderer.setPadding(10);
              }}
            />
          </TabPanel>
          <TabPanel value="3">
            <Stack gap={1}>
              <Typography variant="body2" mb={2}>
                Use the following code to run the app from your JavaScript app
              </Typography>
            </Stack>
            <AceEditor
              mode="javascript"
              theme="dracula"
              value={jsCodeStreaming}
              editorProps={{ $blockScrolling: true }}
              setOptions={{
                useWorker: false,
                showGutter: false,
              }}
              style={{
                borderRadius: "5px",
                height: "350px",
                width: "100%",
                maxWidth: "600px",
              }}
              onLoad={(editor) => {
                editor.renderer.setScrollMargin(10, 0, 10, 0);
                editor.renderer.setPadding(10);
              }}
            />
          </TabPanel>
        </TabContext>
      </Box>
    </div>
  );
}
