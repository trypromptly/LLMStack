import { useState } from "react";
import { Modal, Button, Input, Space, Divider } from "antd";
import { axios } from "../../data/axios";
import validator from "@rjsf/validator-ajv8";
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
    <Modal
      title={modalTitle}
      open={open}
      onCancel={handleCancelCb}
      footer={[
        <Button key="back" onClick={handleCancelCb}>
          Cancel
        </Button>,
        <Button
          key="submit"
          type="primary"
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
        </Button>,
      ]}
    >
      <Space direction="vertical" style={{ width: "100%" }}>
        <Input
          value={testSetName}
          onChange={(e) => setTestSetName(e.target.value)}
          placeholder="Test Set Name"
          disabled={testSet ? true : false}
          required={true}
          defaultValue={testSet?.name || "Untitled"}
          status={testSetNameError ? "error" : ""}
        />
        <Divider orientation="center" style={{ marginBottom: "-10px" }}>
          Input
        </Divider>
        <ThemedJsonForm
          schema={app?.input_schema || {}}
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
      </Space>
    </Modal>
  );
}
