import { Box } from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import ThemedJsonForm from "./ThemedJsonForm";

export function InputThemedForm(props) {
  const { input, setInput, schema, uiSchema } = props;

  return (
    <ThemedJsonForm
      schema={schema}
      uiSchema={uiSchema}
      formData={input}
      validator={validator}
      onChange={({ formData }) => {
        setInput(formData);
      }}
      disableAdvanced={true}
    />
  );
}

export default function InputForm(props) {
  const { input, setInput } = props;
  let schema = props.schema ? JSON.parse(JSON.stringify(props.schema)) : {};
  let uiSchema = props.uiSchema
    ? JSON.parse(JSON.stringify(props.uiSchema))
    : {};
  if (props?.schema?.title) {
    schema.title = "";
    schema.description = "";
  }

  return (
    <Box sx={{ width: "100%" }}>
      <InputThemedForm
        schema={schema}
        uiSchema={uiSchema}
        input={input}
        setInput={setInput}
        submitBtn={props.submitBtn}
      />
    </Box>
  );
}
