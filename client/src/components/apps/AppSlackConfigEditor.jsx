import { Box, Button, Stack, TextField } from "@mui/material";
import { EmbedCodeSnippet } from "./EmbedCodeSnippets";

export function AppSlackConfigEditor(props) {
  const { app, saveApp, slackConfig, setSlackConfig } = props;

  return (
    <Box>
      <Stack direction="column" gap={2}>
        <TextField
          id="app_id"
          label="App ID"
          helperText="Application ID"
          onChange={(e) =>
            setSlackConfig({ ...slackConfig, app_id: e.target.value })
          }
          defaultValue={slackConfig?.app_id || ""}
          size="small"
        />
        <TextField
          id="bot_token"
          label="Bot Token"
          helperText="Bot token to use for sending messages to Slack. Make sure the Bot has access to app_mentions:read and chat:write scopes. This token is available at Features > OAuth & Permissions in your app page. More details https://api.slack.com/authentication/oauth-v2"
          onChange={(e) =>
            setSlackConfig({ ...slackConfig, bot_token: e.target.value })
          }
          defaultValue={slackConfig?.bot_token || ""}
          size="small"
        />
        <TextField
          id="verification_token"
          label="Verification Token"
          helperText="Verification token to verify the request from Slack. This token is available at Features > Basic Information in your app page. More details https://api.slack.com/authentication/verifying-requests-from-slack"
          onChange={(e) =>
            setSlackConfig({
              ...slackConfig,
              verification_token: e.target.value,
            })
          }
          defaultValue={slackConfig?.verification_token || ""}
          size="small"
        />
        <TextField
          id="signing_secret"
          label="Signing Secret"
          helperText="Signing secret to verify the request from Slack. This secret is available at Features > Basic Information in your app page. More details https://api.slack.com/authentication/verifying-requests-from-slack"
          onChange={(e) =>
            setSlackConfig({ ...slackConfig, signing_secret: e.target.value })
          }
          defaultValue={slackConfig?.signing_secret || ""}
          size="small"
        />
        <EmbedCodeSnippet app={app} integration="slack" />
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
        <Button
          onClick={saveApp}
          variant="contained"
          style={{ textTransform: "none", margin: "20px 0" }}
        >
          Save App
        </Button>
      </Stack>
    </Box>
  );
}
