import { Box, Stack } from "@mui/material";
import { EmbedCodeSnippet } from "./EmbedCodeSnippets";
import { AppSaveButtons } from "./AppSaveButtons";
import validator from "@rjsf/validator-ajv8";
import ThemedJsonForm from "../ThemedJsonForm";
import { createRef } from "react";

const webConfigSchema = {
  type: "object",
  properties: {
    allowed_sites: {
      type: "array",
      title: "Allowed Sites",
      description: "Domains that are allowed to embed this app.",
      items: {
        type: "string",
      },
    },
  },
};

const webConfigUISchema = {
  allowed_sites: {
    "ui:emptyValue": [],
  },
};

export function AppWebConfigEditor(props) {
  const formRef = createRef();

  function webConfigValidate(formData, errors, uiSchema) {
    return errors;
  }

  return (
    <Box>
      <Stack direction="column" gap={2}>
        <ThemedJsonForm
          schema={webConfigSchema}
          uiSchema={webConfigUISchema}
          formData={props.webConfig || {}}
          onChange={(e) => props.setWebConfig(e.formData)}
          validator={validator}
          disableAdvanced={true}
          formRef={formRef}
          customValidate={webConfigValidate}
        />
        <EmbedCodeSnippet app={props.app} integration="web" />
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
