import { Box, Stack } from "@mui/material";
import { EmbedCodeSnippet } from "./EmbedCodeSnippets";
import { AppSaveButtons } from "./AppSaveButtons";
import validator from "@rjsf/validator-ajv8";
import { useValidationErrorsForAppComponents } from "../../data/appValidation";

import ThemedJsonForm from "../ThemedJsonForm";
import { createRef } from "react";

const slackConfigSchema = {
  type: "object",
  properties: {
    app_id: {
      type: "string",
      title: "App ID",
      description: "Application ID",
    },
    bot_token: {
      type: "string",
      title: "Bot Token",
      description:
        "Bot token to use for sending messages to Slack. Make sure the Bot has access to app_mentions:read and chat:write scopes. This token is available at Features > OAuth & Permissions in your app page. More details https://api.slack.com/authentication/oauth-v2",
    },
    verification_token: {
      type: "string",
      title: "Verification Token",
      description:
        "Verification token to verify the request from Slack. This token is available at Features > Basic Information in your app page. More details https://api.slack.com/authentication/verifying-requests-from-slack",
    },
    signing_secret: {
      type: "string",
      title: "Signing Secret",
      description:
        "Signing secret to verify the request from Slack. This secret is available at Features > Basic Information in your app page. More details https://api.slack.com/authentication/verifying-requests-from-slack",
    },
  },
  required: ["app_id", "bot_token", "verification_token", "signing_secret"],
};

const slackConfigUISchema = {
  app_id: {
    "ui:widget": "text",
    "ui:emptyValue": "",
  },
  bot_token: {
    "ui:widget": "password",
    "ui:emptyValue": "",
  },
  verification_token: {
    "ui:widget": "password",
    "ui:emptyValue": "",
  },
  signing_secret: {
    "ui:widget": "password",
    "ui:emptyValue": "",
  },
};

export function AppSlackConfigEditor(props) {
  const formRef = createRef();
  const [setValidationErrorsForId, clearValidationErrorsForId] =
    useValidationErrorsForAppComponents("slackIntegrationConfig");

  function slackConfigValidate(formData, errors, uiSchema) {
    if (
      formData.app_id ||
      formData.bot_token ||
      formData.verification_token ||
      formData.signing_secret
    ) {
      if (!formData.app_id) {
        errors.app_id.addError("App ID is required");
      }
      if (!formData.bot_token) {
        errors.bot_token.addError("Bot Token is required");
      }
      if (!formData.verification_token) {
        errors.verification_token.addError("Verification Token is required");
      }
      if (!formData.signing_secret) {
        errors.signing_secret.addError("Signing Secret is required");
      }
    }

    return errors;
  }

  return (
    <Box>
      <Stack direction="column" gap={2}>
        <ThemedJsonForm
          schema={slackConfigSchema}
          uiSchema={slackConfigUISchema}
          formData={props.slackConfig || {}}
          onChange={(e) => props.setSlackConfig(e.formData)}
          validator={validator}
          disableAdvanced={true}
          formRef={formRef}
          customValidate={slackConfigValidate}
        />
        <EmbedCodeSnippet app={props.app} integration="slack" />
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
              const errors = formRef.current.validate(props.slackConfig);
              if (errors.errors && errors.errors.length > 0) {
                setValidationErrorsForId("slackIntegrationConfig", {
                  id: "slackIntegrationConfig",
                  name: "Slack Integration Config",
                  errors: errors.errors,
                });
              } else {
                clearValidationErrorsForId("slackIntegrationConfig");
              }
              props.saveApp().then(resolve).catch(reject);
            });
          }}
        />
      </Stack>
    </Box>
  );
}
