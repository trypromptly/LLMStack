import { useEffect, useRef, useState } from "react";
import { Box, MenuItem, Select } from "@mui/material";
import { useRecoilValue } from "recoil";
import validator from "@rjsf/validator-ajv8";
import { getJSONSchemaFromInputFields } from "../../data/utils";
import { storeAppsBriefState, storeAppState } from "../../data/atoms";
import ThemedJsonForm from "../ThemedJsonForm";
import TextFieldWithVars from "../apps/TextFieldWithVars";

const AppRunForm = ({ appSlug, appInput, setData }) => {
  const [selectedAppSlug, setSelectedAppSlug] = useState(
    appSlug || "super-agent",
  );
  const storeApps = useRecoilValue(storeAppsBriefState);
  const app = useRecoilValue(storeAppState(selectedAppSlug || "super-agent"));
  const [appInputSchema, setAppInputSchema] = useState({});
  const [appInputUiSchema, setAppInputUiSchema] = useState({});
  const formDataRef = useRef(appInput || {});

  const TextWidget = (props) => {
    return (
      <TextFieldWithVars
        {...props}
        introText={"Available columns"}
        value={props.formData}
      />
    );
  };

  useEffect(() => {
    if (app) {
      const { schema, uiSchema } = getJSONSchemaFromInputFields(
        app.data?.input_fields || [],
      );
      setAppInputSchema(schema);
      setAppInputUiSchema(uiSchema);
      setData({
        app_slug: app.slug,
        input: {},
      });
    }
  }, [app, setData]);

  return (
    <Box>
      <Select
        value={selectedAppSlug}
        id="app-select"
        helperText="Select the app to run"
        onChange={(e) => setSelectedAppSlug(e.target.value)}
        onClick={(e) => e.stopPropagation()}
      >
        {storeApps.map((app) => (
          <MenuItem value={app.slug} key={app.uuid}>
            {app.name}
          </MenuItem>
        ))}
      </Select>
      {app && (
        <ThemedJsonForm
          disableAdvanced={true}
          schema={appInputSchema}
          uiSchema={{
            ...appInputUiSchema,
            "ui:submitButtonOptions": {
              norender: true,
            },
          }}
          submitBtn={null}
          validator={validator}
          formData={formDataRef.current}
          onChange={(e) => {
            setData({
              app_slug: app.slug,
              input: e.formData,
            });
            formDataRef.current = e.formData;
          }}
          fields={{
            multi: TextWidget,
          }}
          widgets={{
            text: TextWidget,
            textarea: TextWidget,
            file: TextWidget,
          }}
        />
      )}
    </Box>
  );
};

export default AppRunForm;
