import { useEffect, useRef, useState } from "react";
import {
  Box,
  FormGroup,
  FormControlLabel,
  Switch,
  TextField,
  Typography,
  Stack
} from "@mui/material";
import { enqueueSnackbar } from "notistack";

function SlackIntegrationSnippet({ app }) {
  const inputRef = useRef(null);
  const url = `${window.location.origin}/api/apps/${app?.uuid}/slack/run`;
  return (
    <Box>
      <Typography sx={{ textAlign: "left" }}>
        Copy the following URL in the Event Subscriptions Section in your Slack
        App
      </Typography>
      <TextField
        inputRef={inputRef}
        value={url}
        variant="outlined"
        fullWidth
        InputProps={{
          readOnly: true,
          style: { fontFamily: "monospace", color: "#666" },
        }}
        onClick={(e) => {
          e.target.select();
          navigator.clipboard.writeText(e.target.value);
          enqueueSnackbar("Code copied successfully", { variant: "success" });
        }}
      />
      <Typography sx={{ textAlign: "left !important" }} variant="subtitle2">
        Make sure to add app_mention scope in the Subscribe to bot events
        section
      </Typography>
    </Box>
  );
}

function DiscordIntegrationSnippet({ app }) {
  const inputRef = useRef(null);
  const url = `${window.location.origin}/api/apps/${app?.uuid}/discord/run`;
  return (
    <Box>
      <Typography sx={{ textAlign: "left" }}>
        Copy the following URL in the INTERACTIONS ENDPOINT URL Section in your
        Discord App
      </Typography>
      <TextField
        inputRef={inputRef}
        value={url}
        variant="outlined"
        fullWidth
        InputProps={{
          readOnly: true,
          style: { fontFamily: "monospace", color: "#666" },
        }}
        onClick={(e) => {
          e.target.select();
          navigator.clipboard.writeText(e.target.value);
          enqueueSnackbar("Code copied successfully", { variant: "success" });
        }}
      />
      <Typography sx={{ textAlign: "left" }} variant="subtitle2">
        Make sure to add bot scopes in the OAuth2 URL Generator section of your
        app.
      </Typography>
    </Box>
  );
}

function WebIntegrationSnippet({ app }) {
  const inputRef = useRef(null);
  const textChatApp = app?.type?.slug === "text-chat";
  const [embedChatBubble, setEmbedChatBubble] = useState(textChatApp);
  const embedCode = app?.is_published
    ? `<script async src="${
        process.env.PUBLIC_URL || window.location.origin
      }/static/js/embed-v1.js"></script>
<promptly-app-embed published-app-id="${app?.published_uuid}"${
        embedChatBubble ? ' chat-bubble="true"' : ""
      } host="${window.location.origin}"></promptly-app-embed>`
    : "Please publish the app to get the embed code";

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.select();
    }
  }, []);

  return (
    <Box>
      <Typography sx={{ textAlign: "left" }}>
        Copy the following code and paste it in your website body section to
        embed this app on your page.
      </Typography>
      <TextField
        inputRef={inputRef}
        multiline
        rows={6}
        value={embedCode}
        variant="outlined"
        fullWidth
        InputProps={{
          readOnly: true,
          style: { fontFamily: "monospace", color: "#666" },
        }}
        autoFocus
        onClick={(e) => {
          e.target.select();
          navigator.clipboard.writeText(e.target.value);
          enqueueSnackbar("Code copied successfully", { variant: "success" });
        }}
      />
      {app?.type?.slug === "text-chat" && (
        <FormGroup>
          <FormControlLabel
            control={
              <Switch
                checked={embedChatBubble}
                onChange={(e) => setEmbedChatBubble(e.target.checked)}
              />
            }
            label="Chat Bubble"
          />
        </FormGroup>
      )}
    </Box>
  );
}

function TwilioIntegrationSnippet({ app }) {
  const inputRef = useRef(null);
  const showTwilioVoiceUrl =
    app?.twilio_config?.use_twilio_transcription ||
    app?.twilio_config?.voicemail_greeting || 
    app?.twilio_config?.voicemail_length || false;
  const smsUrl = `${window.location.origin}/api/apps/${app?.uuid}/twiliosms/run`;
  const voiceUrl = `${window.location.origin}/api/apps/${app?.uuid}/twiliovoice/run`;

  return (
    <Stack>
      <Typography sx={{ textAlign: "left" }}>
        Copy the following URL in the Messaging Configuration URL Section in
        your Twilio Phone Number
      </Typography>
      <TextField
        inputRef={inputRef}
        value={smsUrl}
        variant="outlined"
        fullWidth
        InputProps={{
          readOnly: true,
          style: { fontFamily: "monospace", color: "#666" },
        }}
        onClick={(e) => {
          e.target.select();
          navigator.clipboard.writeText(e.target.value);
          enqueueSnackbar("Code copied successfully", { variant: "success" });
        }}
      />
      {showTwilioVoiceUrl && (
        <div>
          <Typography sx={{ textAlign: "left" }}>
            Copy the following URL in the Voice Configuration URL Section in
            your Twilio Phone Number
          </Typography>
          <TextField
            inputRef={inputRef}
            value={voiceUrl}
            variant="outlined"
            fullWidth
            InputProps={{
              readOnly: true,
              style: { fontFamily: "monospace", color: "#666" },
            }}
            onClick={(e) => {
              e.target.select();
              navigator.clipboard.writeText(e.target.value);
              enqueueSnackbar("Code copied successfully", {
                variant: "success",
              });
            }}
          />
        </div>
      )}
    </Stack>
  );
}

export function EmbedCodeSnippet({ app, integration }) {
  if (integration === "slack") {
    return <SlackIntegrationSnippet app={app} />;
  } else if (integration === "discord") {
    return <DiscordIntegrationSnippet app={app} />;
  } else if (integration === "twilio") {
    return <TwilioIntegrationSnippet app={app} />;
  } else {
    return <WebIntegrationSnippet app={app} />;
  }
}
