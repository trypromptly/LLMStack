import { Box, Stack, TextField } from "@mui/material";
import { EmbedCodeSnippet } from "./EmbedCodeSnippets";
import { AppSaveButtons } from "./AppSaveButtons";
import validator from "@rjsf/validator-ajv8";

import ThemedJsonForm from "../ThemedJsonForm";
import { createRef } from "react";

const discordConfigSchema = {
  type: "object",
  properties: {
    app_id: {
      type: "string",
      title: "App ID",
      description: "Application ID",
    },
    slash_command_name: {
      type: "string",
      title: "Slash Command Name",
      description:
        "The name of the slash command that will be used to trigger the app.",
    },
    slash_command_description: {
      type: "string",
      title: "Slash Command Description",
      description:
        "The description of the slash command that will be used to trigger the app.",
    },
    bot_token: {
      type: "string",
      title: "Bot Token",
      description:
        "Bot token to use for sending messages to Discord. This token is available in the Bot section of your application console.",
    },
    public_key: {
      type: "string",
      title: "Public Key",
      description:
        "Public key of the Discord app. Your public key can be found in the Bot section of the your application console.",
    },
  },
};

const discordConfigUISchema = {
  app_id: {
    "ui:widget": "text",
    "ui:emptyValue": "",
  },
  slash_command_name: {
    "ui:widget": "text",
    "ui:emptyValue": "",
  },
  slash_command_description: {
    "ui:widget": "text",
    "ui:emptyValue": "",
  },
  bot_token: {
    "ui:widget": "password",
    "ui:emptyValue": "",
  },
  public_key: {
    "ui:widget": "password",
    "ui:emptyValue": "",
  },
};

export function AppDiscordConfigEditor(props) {
  const formRef = createRef();

  function discordConfigValidate(formData, errors, uiSchema) {
    return errors;
  }

  return (
    <Box>
      <Stack direction="column" gap={2}>
        <ThemedJsonForm
          schema={discordConfigSchema}
          uiSchema={discordConfigUISchema}
          formData={props.discordConfig || {}}
          onChange={(e) => props.setDiscordConfig(e.formData)}
          validator={validator}
          disableAdvanced={true}
          formRef={formRef}
          customValidate={discordConfigValidate}
        />
        <TextField
          id="slash_command_id"
          label="Slash Command ID"
          helperText="Slash command ID of the Discord app. Your slash command ID can be found in the Slash Commands section of the your application console."
          disabled={true}
          defaultValue={props.discordConfig?.slash_command_id || ""}
          size="small"
        />
        <EmbedCodeSnippet app={props.app} integration="discord" />
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
        <AppSaveButtons
          saveApp={() => {
            return new Promise((resolve, reject) => {
              if (formRef.current.validateForm() === false) {
                resolve();
              } else {
                props.saveApp().then(resolve).catch(reject);
              }
            });
          }}
        />
      </Stack>
    </Box>
  );
}
