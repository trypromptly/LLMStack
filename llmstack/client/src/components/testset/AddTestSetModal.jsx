import {
  Button as MuiButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Stack,
  TextField,
} from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import { useState } from "react";
import { axios } from "../../data/axios";
import { getJSONSchemaFromInputFields } from "../../data/utils";
import ThemedJsonForm from "../ThemedJsonForm";

const TESTCASE_UI_SCHEMA = {
  "ui:order": ["expected_output"],
  "ui:options": {
    label: false,
  },
  expected_output: {
    "ui:widget": "textarea",
    "ui:options": {
      rows: 5,
    },
  },
};

const TESTCASE_SCHEMA = {
  type: "object",
  properties: {
    expected_output: {
      type: "string",
      title: "Add your expected output here",
    },
  },
  required: ["expected_output"],
};

export function AddTestSetModal({
  open,
  handleCancelCb,
  onSubmitCb,
  modalTitle = "Create a Test Set",
  testSet,
  app,
}) {
  const [testSetName, setTestSetName] = useState(testSet?.name || "");
  const [testSetNameError, setTestSetNameError] = useState(false);
  const [inputFormData, setInputFormData] = useState({});
  const [testcaseFormData, setTestcaseFormData] = useState({});
  return (
    <Dialog open={open} onClose={handleCancelCb}>
      <DialogTitle>{modalTitle}</DialogTitle>
      <DialogContent sx={{ minWidth: "400px" }}>
        <Stack spacing={2}>
          <TextField
            label="Test Set Name"
            value={testSetName}
            onChange={(e) => setTestSetName(e.target.value)}
            disabled={testSet ? true : false}
            required={true}
            defaultValue={testSet?.name || "Untitled"}
            size="small"
            style={{ width: "100%", marginTop: "6px" }}
            error={testSetNameError}
          />
          <Divider orientation="center" style={{ marginBottom: "-10px" }}>
            Input
          </Divider>
          <ThemedJsonForm
            schema={
              getJSONSchemaFromInputFields(app?.data?.input_fields || [])
                ?.schema
            }
            validator={validator}
            uiSchema={{
              ...(app?.input_ui_schema || {}),
              ...{
                "ui:submitButtonOptions": {
                  norender: true,
                },
                "ui:DescriptionFieldTemplate": () => null,
                "ui:TitleFieldTemplate": () => null,
              },
            }}
            formData={inputFormData}
            onChange={({ formData }) => {
              setInputFormData(formData);
            }}
          />
          <Divider orientation="center" style={{ marginBottom: "-10px" }}>
            Expected Output
          </Divider>
          <ThemedJsonForm
            schema={TESTCASE_SCHEMA}
            validator={validator}
            uiSchema={{
              ...TESTCASE_UI_SCHEMA,
              ...{
                "ui:submitButtonOptions": {
                  norender: true,
                },
                "ui:DescriptionFieldTemplate": () => null,
                "ui:TitleFieldTemplate": () => null,
              },
            }}
            formData={testcaseFormData}
            onChange={({ formData }) => {
              setTestcaseFormData(formData);
            }}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <MuiButton onClick={handleCancelCb}>Cancel</MuiButton>,
        <MuiButton
          variant="contained"
          onClick={() => {
            if (testSet) {
              axios()
                .post(`/api/apptestsets/${testSet.uuid}/add_entry`, {
                  ...testcaseFormData,
                  input_data: inputFormData,
                })
                .then((response) => {
                  testSet.testcases = [...testSet.testcases, response.data];

                  onSubmitCb({
                    ...testSet,
                  });
                });
            } else {
              if (testSetName === "") {
                setTestSetNameError(true);
                return;
              }
              axios()
                .post(`/api/apps/${app.uuid}/testsets`, {
                  name: testSetName,
                })
                .then((response) => {
                  const testSetResponse = response.data;
                  axios()
                    .post(
                      `/api/apptestsets/${testSetResponse.uuid}/add_entry`,
                      {
                        ...testcaseFormData,
                        input_data: inputFormData,
                      },
                    )
                    .then((response) => {
                      testSetResponse.testcases = [response.data];
                      onSubmitCb({ ...testSetResponse });
                    });
                });
            }
          }}
        >
          Submit
        </MuiButton>
      </DialogActions>
    </Dialog>
  );
}
