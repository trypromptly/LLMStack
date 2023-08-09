import { Modal, Form, Input, Select, Checkbox, Collapse } from "antd";
import { useEffect, useState } from "react";
import EndpointDiffViewer from "./EndpointDiffViewer";
import { useRecoilState, useRecoilValue } from "recoil";
import {
  apiBackendSelectedState,
  endpointSelectedState,
  endpointConfigValueState,
  templateValueState,
  inputValueState,
  saveEndpointModalVisibleState,
  saveEndpointVersionModalVisibleState,
} from "../data/atoms";

import { axios } from "../data/axios";
import { useReloadEndpoints } from "../data/init";

const { Panel } = Collapse;

export function CreateEndpointModal({
  visibility,
  handleOkCb,
  handleCancelCb,
  apiBackendOptions,
}) {
  const [form] = Form.useForm();

  const handleCreateModalOk = async () => {
    form.validateFields().then((values) => {
      handleOkCb(values);
    });
  };

  return (
    <Modal
      title="Create Endpoint"
      open={visibility}
      onOk={handleCreateModalOk}
      onCancel={handleCancelCb}
      okText="Submit"
    >
      <Form
        form={form}
        labelCol={{ span: 6 }}
        className="create-endpoint-form"
        layout="vertical"
      >
        <Form.Item
          name="name"
          label="Name"
          rules={[{ required: true, message: "Please specify a name" }]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          name="api_backend"
          label="API Backend"
          rules={[
            { required: true, message: "Please select a valid API backend" },
          ]}
        >
          <Select
            options={apiBackendOptions.map((apibackend) => ({
              value: apibackend.id,
              label: apibackend.api_provider.name + " » " + apibackend.name,
            }))}
          />
        </Form.Item>
        <Form.Item name="param_values" label="Param Values" initialValue={"{}"}>
          <Input.TextArea></Input.TextArea>
        </Form.Item>
        <Form.Item name="prompt" label="Prompt">
          <Input.TextArea />
        </Form.Item>
      </Form>
    </Modal>
  );
}

export function EditEndpointModal({
  visibility,
  handleOkCb,
  handleCancelCb,
  endpoint_data,
}) {
  const [form] = Form.useForm();
  const [is_live, setLiveState] = useState(false);

  const okButtonClick = async () => {
    form.validateFields().then((values) => {
      let form_data = {
        param_values: values.param_values,
        post_processor: values.post_processor,
        prompt: values.prompt,
        is_live: is_live,
        description: values.description,
      };
      handleOkCb(form_data, endpoint_data.uuid);
    });
  };

  useEffect(() => {
    if (endpoint_data) {
      let form_values = { ...endpoint_data };
      if (typeof endpoint_data.param_values != "string") {
        form_values.param_values = JSON.stringify(endpoint_data.param_values);
      }
      form.setFieldsValue(form_values);
      setLiveState(form.getFieldValue("is_live"));
    }
  }, [endpoint_data, form]);

  return (
    <Modal
      title="Edit Endpoint Form"
      style={{ top: "10px" }}
      width={"100%"}
      centered={false}
      open={visibility}
      onOk={okButtonClick}
      onCancel={handleCancelCb}
      okText={"Save Changes"}
    >
      <Form form={form} labelCol={{ span: 2 }} className="edit-endpoint-form">
        <Form.Item name="name" label="Endpoint Name">
          <Input readOnly={true} />
        </Form.Item>
        <Form.Item name="param_values" label="Param Values">
          <Input.TextArea />
        </Form.Item>
        <Form.Item name="prompt" label="Prompt">
          <Input.TextArea autoSize={true} />
        </Form.Item>
        <Form.Item name="post_processor" label="Post Processor">
          <Input />
        </Form.Item>
        <Form.Item name="is_live" label="Is Live">
          <Checkbox
            checked={is_live}
            onClick={() => {
              setLiveState(!is_live);
            }}
          />
        </Form.Item>
        <Form.Item name="created_on" label="Last Updated">
          <Input readOnly={true} />
        </Form.Item>
        <Form.Item name="description" label="Description">
          <Input />
        </Form.Item>
      </Form>
    </Modal>
  );
}

export function DeleteEndpointModal({
  visibility,
  handleOkCb,
  handleCancelCb,
}) {
  return (
    <Modal
      title="Delete Endpoint Confirmation"
      open={visibility}
      onOk={handleOkCb}
      onCancel={handleCancelCb}
    ></Modal>
  );
}

export function VersionedEndpointListModal({
  visibility,
  handleCancelCb,
  data,
}) {
  return (
    <Modal
      title="Versioned Endpoints"
      style={{ top: "10px" }}
      width={"100%"}
      centered={false}
      open={visibility}
      footer={null}
      onCancel={handleCancelCb}
    >
      <Collapse>
        {data.map((entry) => {
          return (
            <Collapse.Panel
              header={`Versioned Endpoint: ${entry.version}`}
              key={entry.version}
            >
              <Form labelCol={{ span: 2 }}>
                <Form.Item label="Param Values">
                  <Input.TextArea
                    autoSize={true}
                    readOnly
                    value={
                      typeof entry.param_values != "string"
                        ? JSON.stringify(entry.param_values)
                        : entry.param_values
                    }
                  />
                </Form.Item>
                <Form.Item hidden={true} label="Post Processor">
                  <Input readOnly defaultValue={entry.post_processor} />
                </Form.Item>
                <Form.Item label="Prompt">
                  <Input.TextArea
                    autoSize={true}
                    readOnly
                    value={entry.prompt}
                  ></Input.TextArea>
                </Form.Item>
                <Form.Item label="Is Live" readOnly>
                  <Checkbox checked={entry.is_live}></Checkbox>
                </Form.Item>
              </Form>
            </Collapse.Panel>
          );
        })}
      </Collapse>
    </Modal>
  );
}

export function SaveEndpointModal() {
  const [form] = Form.useForm();
  const [isLive, setIsLive] = useState(false);
  const [endpointSelected, setEndpointSelected] = useRecoilState(
    endpointSelectedState,
  );
  const [saveModalVisible, setSaveEndpointModalVisibility] = useRecoilState(
    saveEndpointModalVisibleState,
  );
  const input = useRecoilValue(inputValueState);
  const paramValues = useRecoilValue(endpointConfigValueState);
  const reloadEndpoints = useReloadEndpoints();

  const saveAsEndpoint = async (values) => {
    axios()
      .patch("/api/endpoints", {
        name: values.endpoint.name,
        parent_uuid: endpointSelected.parent_uuid,
        version: 0,
        description: values.endpoint.description,
        is_live: values.endpoint.isLive,
        draft: false,
        config: paramValues,
        input: input,
      })
      .then((response) => {
        reloadEndpoints();
        setEndpointSelected(response.data);
      })
      .catch((error) => {
        console.error(error);
      })
      .then(() => {
        setSaveEndpointModalVisibility(false);
      });
  };

  const okButtonClick = async () => {
    form
      .validateFields()
      .then((values) => {
        saveAsEndpoint(values);
        form.resetFields();
      })
      .catch((error) => console.error(error));
  };

  return (
    <Modal
      title="Save as Endpoint"
      style={{ top: "10px" }}
      centered
      open={saveModalVisible}
      onOk={okButtonClick}
      onCancel={() => {
        form.resetFields();
        setSaveEndpointModalVisibility(false);
      }}
    >
      <br />
      <Form
        form={form}
        labelCol={{ span: 8 }}
        wrapperCol={{
          span: 16,
        }}
        className="save-endpoint-form"
        style={{
          maxWidth: 600,
        }}
      >
        <Form.Item
          name={["endpoint", "name"]}
          label="Endpoint Name"
          rules={[
            {
              required: true,
            },
          ]}
        >
          <Input placeholder="Identifier for endpoint" />
        </Form.Item>
        <Form.Item
          name={["endpoint", "description"]}
          label="Description"
          rules={[
            {
              required: true,
            },
          ]}
        >
          <Input placeholder="Brief description for endpoint" />
        </Form.Item>
        <Form.Item
          name={["endpoint", "isLive"]}
          valuePropName="checked"
          help="Marking as live will make the platform serve this prompt and params"
          label="Live"
        >
          <Checkbox
            checked={isLive}
            onClick={() => {
              setIsLive(!isLive);
            }}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}

export function SaveVersionModal({ prompt }) {
  const [form] = Form.useForm();
  const [isLive, setIsLive] = useState(false);
  const [endpointSelected, setEndpointSelected] = useRecoilState(
    endpointSelectedState,
  );
  const [saveVersionModalVisible, setSaveVersionModalVisibility] =
    useRecoilState(saveEndpointVersionModalVisibleState);
  const input = useRecoilValue(inputValueState);
  const paramValues = useRecoilValue(endpointConfigValueState);
  const reloadEndpoints = useReloadEndpoints();
  const apiBackendSelected = useRecoilValue(apiBackendSelectedState);
  const promptValues = useRecoilValue(templateValueState);

  const saveAsVersion = async (values) => {
    axios()
      .post(`/api/endpoints`, {
        name: `Playground`,
        description: values.endpoint.description,
        is_live: values.endpoint.isLive,
        api_backend: apiBackendSelected.id,
        draft: false,
        input: input,
        param_values: paramValues,
        prompt_values: promptValues,
        config: paramValues,
        post_processor: "",
        parent_uuid: endpointSelected.parent_uuid,
      })
      .then((response) => {
        reloadEndpoints();
        setEndpointSelected(response.data);
      })
      .catch((error) => {
        console.error(error);
      })
      .then(() => {
        setSaveVersionModalVisibility(false);
      });
  };

  const okButtonClick = async () => {
    form
      .validateFields()
      .then((values) => {
        saveAsVersion(values);
        form.resetFields();
      })
      .catch((error) => console.error(error));
  };

  return (
    <Modal
      title="Save New Version"
      style={{ top: "10px" }}
      centered
      open={saveVersionModalVisible}
      onOk={okButtonClick}
      onCancel={() => {
        form.resetFields();
        setSaveVersionModalVisibility(false);
      }}
    >
      <br />
      <Form
        form={form}
        labelCol={{ span: 5 }}
        wrapperCol={{
          span: 16,
        }}
        className="save-version-form"
        style={{
          maxWidth: 600,
        }}
      >
        <Form.Item
          name={["endpoint", "description"]}
          label="Description"
          rules={[
            {
              required: true,
            },
          ]}
        >
          <Input placeholder="Brief description for this change" />
        </Form.Item>
        <Form.Item
          name={["endpoint", "isLive"]}
          valuePropName="checked"
          help="Marking as live will make the platform serve this prompt and params"
          label="Live"
        >
          <Checkbox
            checked={isLive}
            onClick={() => {
              setIsLive(!isLive);
            }}
          />
        </Form.Item>
      </Form>
      <Collapse ghost>
        <Panel header="Compare With Previous Versions" key="1">
          <EndpointDiffViewer
            endpoint={endpointSelected}
            prompt={JSON.stringify(input)}
            paramValues={paramValues}
          />
        </Panel>
      </Collapse>
    </Modal>
  );
}

export function EndpointCompareModal({
  visibility,
  endpoints,
  handleOkCb,
  handleCancelCb,
}) {
  let endpoint = null;
  let prompt = "";
  let paramValues = {};

  if (endpoints && endpoints.length > 1) {
    let sortedEndpoints = [...endpoints];
    sortedEndpoints = sortedEndpoints.sort((a, b) => a.version - b.version);

    endpoint = sortedEndpoints[endpoints.length - 2];
    prompt = sortedEndpoints[endpoints.length - 1].prompt;
    paramValues = sortedEndpoints[endpoints.length - 1].param_values;
  }

  return (
    endpoints && (
      <Modal
        title="Compare Versions"
        style={{ top: "10px" }}
        centered
        open={visibility}
        onOk={handleOkCb}
        onCancel={handleCancelCb}
      >
        <EndpointDiffViewer
          endpoint={endpoint}
          prompt={prompt}
          paramValues={paramValues}
        />
      </Modal>
    )
  );
}
