import { Box, Stack, TextField } from "@mui/material";
import { EmbedCodeSnippet } from "./EmbedCodeSnippets";
import { AppSaveButtons } from "./AppSaveButtons";

export function AppDiscordConfigEditor(props) {
  const { app, discordConfig, saveApp, setDiscordConfig } = props;

  return (
    <Box>
      <Stack direction="column" gap={2}>
        <TextField
          id="app_id"
          label="Application ID"
          helperText="App ID of the Discord app. Your application's ID can be found in the URL of the your application console."
          onChange={(e) =>
            setDiscordConfig({
              ...discordConfig,
              app_id: e.target.value,
            })
          }
          defaultValue={discordConfig?.app_id || ""}
          size="small"
        />
        <TextField
          id="slash_command_name"
          label="Slash Command Name"
          helperText="The name of the slash command that will be used to trigger the app."
          onChange={(e) =>
            setDiscordConfig({
              ...discordConfig,
              slash_command_name: e.target.value,
            })
          }
          defaultValue={discordConfig?.slash_command_name || ""}
          size="small"
        />
        <TextField
          id="slash_command_description"
          label="Slash Command Description"
          helperText="The description of the slash command that will be used to trigger the app."
          onChange={(e) =>
            setDiscordConfig({
              ...discordConfig,
              slash_command_description: e.target.value,
            })
          }
          defaultValue={discordConfig?.slash_command_description || ""}
          size="small"
        />
        <TextField
          id="bot_token"
          label="Bot Token"
          helperText="Bot token of the Discord app. Your bot's token can be found in the Bot section of the your application console."
          onChange={(e) =>
            setDiscordConfig({
              ...discordConfig,
              bot_token: e.target.value,
            })
          }
          defaultValue={discordConfig?.bot_token || ""}
          size="small"
        />
        <TextField
          id="public_key"
          label="Public Key"
          helperText="Public key of the Discord app. Your public key can be found in the Bot section of the your application console."
          onChange={(e) =>
            setDiscordConfig({
              ...discordConfig,
              public_key: e.target.value,
            })
          }
          defaultValue={discordConfig?.public_key || ""}
          size="small"
        />
        <TextField
          id="slash_command_id"
          label="Slash Command ID"
          helperText="Slash command ID of the Discord app. Your slash command ID can be found in the Slash Commands section of the your application console."
          disabled={true}
          onChange={(e) =>
            setDiscordConfig({
              ...discordConfig,
              slash_command_id: e.target.value,
            })
          }
          defaultValue={discordConfig?.slash_command_id || ""}
          size="small"
        />
        <EmbedCodeSnippet app={app} integration="discord" />
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
