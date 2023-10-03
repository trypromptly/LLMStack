import {
  Box,
  Stack,
  TextField,
} from "@mui/material";
import { EmbedCodeSnippet } from "./EmbedCodeSnippets";
import { AppSaveButtons } from "./AppSaveButtons";

export function AppTwilioConfigEditor(props) {
  const { app, saveApp, twilioConfig, setTwilioConfig } = props;

  return (
    <Box>
      <Stack direction="column" gap={2}>
        <TextField
          id="account_sid"
          label="Account SID"
          helperText="Account SID"
          onChange={(e) =>
            setTwilioConfig({ ...twilioConfig, account_sid: e.target.value })
          }
          defaultValue={twilioConfig?.account_sid || ""}
          size="small"
        />
        <TextField
          id="auth_token"
          label="Auth Token"
          helperText="Auth token"
          onChange={(e) =>
            setTwilioConfig({ ...twilioConfig, auth_token: e.target.value })
          }
          defaultValue={twilioConfig?.auth_token || ""}
          size="small"
        />
        <TextField
          id="twilio_number"
          label="Twilio Phone Number"
          helperText="Twilio Phone Number"
          onChange={(e) =>
            setTwilioConfig({
              ...twilioConfig,
              phone_number: e.target.value,
            })
          }
          defaultValue={twilioConfig?.phone_number || ""}
          size="small"
        />
        <EmbedCodeSnippet app={app} integration="twilio" />
      </Stack>
      <Stack
        direction="row"
        gap={1}
        sx={{
          flexDirection: "row-reverse",
          maxWidth: "900px",
          margin: "auto",
        }}
      >
        <AppSaveButtons saveApp={saveApp} />
      </Stack>
    </Box>
  );
}
