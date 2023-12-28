import { Alert, Box, Stack } from "@mui/material";
import { useRecoilValue } from "recoil";
import { profileFlagsState } from "../../data/atoms";
import { EmbedCodeSnippet } from "./EmbedCodeSnippets";
import { AppSaveButtons } from "./AppSaveButtons";
import ThemedJsonForm from "../ThemedJsonForm";
import { createRef } from "react";
import validator from "@rjsf/validator-ajv8";

const twilioConfigSchema = {
  type: "object",
  properties: {
    account_sid: {
      type: "string",
      title: "Account SID",
      description:
        "Twilio Account SID can be found on the Twilio Console dashboard under Account Info.",
    },
    auth_token: {
      type: "string",
      title: "Auth Token",
      description:
        "Twilio Auth token Auth Token can be found on the Twilio Console dashboard under Account Info.",
    },
    phone_numbers: {
      type: "array",
      title: "Twilio Phone Numbers",
      description: "Add Twilio phone numbers",
      items: {
        type: "string",
      },
    },
  },
};

const twilioConfigUISchema = {
  account_sid: {
    "ui:widget": "text",
    "ui:emptyValue": "",
  },
  auth_token: {
    "ui:widget": "password",
    "ui:emptyValue": "",
  },
  phone_numbers: {
    "ui:emptyValue": [],
  },
};

export function AppTwilioConfigEditor(props) {
  const profileFlags = useRecoilValue(profileFlagsState);
  const formRef = createRef();

  function twilioConfigValidate(formData, errors, uiSchema) {
    return errors;
  }

  return profileFlags.CAN_ADD_TWILIO_INTERGRATION ? (
    <Box>
      <Stack direction="column" gap={2}>
        <ThemedJsonForm
          schema={twilioConfigSchema}
          uiSchema={twilioConfigUISchema}
          formData={props.twilioConfig || {}}
          onChange={(e) => props.setTwilioConfig(e.formData)}
          disableAdvanced={true}
          validator={validator}
          formRef={formRef}
          customValidate={twilioConfigValidate}
        />
        <EmbedCodeSnippet app={props.app} integration="twilio" />
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
  ) : (
    <Alert severity="warning" sx={{ margin: "10px" }}>
      <span>
        This account is not eligible to use Twilio integration. Please upgrade
        your account to trigger this app from Twilio.
        <br />
        To upgrade your plan, click on <b>Manage Subscription</b> in the{" "}
        <a href="/settings">Settings</a> page.
      </span>
    </Alert>
  );
}
