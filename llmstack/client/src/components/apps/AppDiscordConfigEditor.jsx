import { Box, Stack, TextField } from "@mui/material";
import { EmbedCodeSnippet } from "./EmbedCodeSnippets";
import { AppSaveButtons } from "./AppSaveButtons";
import validator from "@rjsf/validator-ajv8";
import { useValidationErrorsForAppComponents } from "../../data/appValidation";

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
  required: [
    "app_id",
    "slash_command_name",
    "slash_command_description",
    "bot_token",
    "public_key",
  ],
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
  const [setValidationErrorsForId, clearValidationErrorsForId] =
    useValidationErrorsForAppComponents("discordIntegrationConfig");

  function discordConfigValidate(formData, errors, uiSchema) {
    if (
      formData.app_id ||
      formData.bot_token ||
      formData.public_key ||
      formData.slash_command_name ||
      formData.slash_command_description
    ) {
      if (!formData.app_id) {
        errors.app_id.addError("App ID is required");
      }
      if (!formData.slash_command_name) {
        errors.slash_command_name.addError("Slash Command Name is required");
      }
      if (!formData.slash_command_description) {
        errors.slash_command_description.addError(
          "Slash Command Description is required",
        );
      }
      if (!formData.bot_token) {
        errors.bot_token.addError("Bot Token is required");
      }
      if (!formData.public_key) {
        errors.public_key.addError("Public Key is required");
      }
    }
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
              const errors = formRef.current.validate(props.discordConfig);
              if (errors.errors && errors.errors.length > 0) {
                setValidationErrorsForId("discordIntegrationConfig", {
                  id: "discordIntegrationConfig",
                  name: "Discord Integration Config",
                  errors: errors.errors,
                });
              } else {
                clearValidationErrorsForId("discordIntegrationConfig");
              }
              props.saveApp().then(resolve).catch(reject);
            });
          }}
        />
      </Stack>
    </Box>
  );
}
