import { Box, Stack } from "@mui/material";
import { EmbedCodeSnippet } from "./EmbedCodeSnippets";
import { AppSaveButtons } from "./AppSaveButtons";
import validator from "@rjsf/validator-ajv8";

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

  function slackConfigValidate(formData, errors, uiSchema) {
    if ((formData.bot_token || "").length < 5) {
      errors.bot_token.addError("Bot token is required");
    }
    if ((formData.verification_token || "").length < 5) {
      errors.verification_token.addError("Verification token is required");
    }
    if ((formData.signing_secret || "").length < 5) {
      errors.signing_secret.addError("Signing secret is required");
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
