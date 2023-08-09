import { useEffect } from "react";
import { fetchData } from "./dataUtil";
import { Form, Space, Table, Button, Input, Modal } from "antd";
import { useState } from "react";
import { useRecoilValue } from "recoil";
import { endpointsState } from "../data/atoms";

const AddTestCaseModal = (props) => {
  const endpoints = useRecoilValue(endpointsState);
  const [, setEndpoint] = useState(props.endpoint);
  const [form] = Form.useForm();

  console.log(props);

  // Get latest versioned endpoint from endpoints recoil state
  useEffect(() => {
    if (props.endpoint) {
      const endpoint = endpoints
        .filter(
          (endpoint) => endpoint.parent_uuid === props.endpoint.parent_uuid,
        )
        .reduce((a, b) => (a.version > b.version ? a : b));
      form.setFieldsValue({
        prompt: endpoint.prompt,
      });
      setEndpoint(endpoint);
    }
  }, [props.endpoint, endpoints, form]);

  const onAddTestCase = () => {
    form.validateFields().then((values) => {
      console.log(values);
      props.onCancelCb();
    });
  };

  return (
    <Modal
      title="Add Test Case"
      open={props.open}
      onCancel={() => props.onCancelCb()}
      onOk={onAddTestCase}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label="Test Name"
          required={true}
          help="A descriptive name for this test"
        >
          <Input />
        </Form.Item>
        <Form.Item name="prompt_values" label="Prompt Values">
          <Input.TextArea autoSize={true} />
        </Form.Item>
        <Form.Item label="Prompt">
          <Input.TextArea
            autoSize={true}
            value={props?.endpoint?.prompt}
            disabled={true}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

const TestPage = () => {
  const [testsetEndpointsData, setTestsetEndpointsData] = useState([]);
  const [showAddTestCaseModal, setShowAddTestCaseModal] = useState(false);
  const [endpointToAddTest, setEndpointToAddTest] = useState(null);

  useEffect(() => {
    fetchData(
      "api/endpoints",
      () => {},
      (endpoints_result) => {
        let endpoints_result_sorted = endpoints_result.sort((a, b) =>
          a.created_on < b.created_on ? 1 : -1,
        );
        const endpoints = {};

        for (let i = 0; i < endpoints_result_sorted.length; i++) {
          if (endpoints_result_sorted[i].draft) continue;

          endpoints[endpoints_result_sorted[i].parent_uuid] = {
            key: i,
            endpoint: endpoints_result_sorted[i],
            testsets: [],
          };
        }
        fetchData(
          "api/testsets",
          () => {},
          (testset_result) => {
            for (let i = 0; i < testset_result.length; i++) {
              let endpoint_id = testset_result[i].endpoint.uuid;
              if (endpoint_id in endpoints) {
                endpoints[endpoint_id].testsets.push({
                  key: testset_result[i].uuid,
                  uuid: testset_result[i].uuid,
                  param_values: testset_result[i].param_values,
                  testcases: testset_result[i].testcases,
                });
              }
            }
            setTestsetEndpointsData(Object.values(endpoints));
          },
          () => {},
        );
      },
      () => {},
    );
  }, []);

  // Endpoints Table Column
  const columns = [
    {
      title: "Endpoint Name",
      dataIndex: "endpoint",
      key: "endpoint_name",
      render: (record) => {
        return <div>{record.name}</div>;
      },
    },
    {
      title: "Provider",
      dataIndex: "endpoint",
      key: "endpoint_provider",
      render: (record) => {
        return <div>{record.api_backend.api_provider.name}</div>;
      },
    },
    {
      title: "Backend",
      dataIndex: "endpoint",
      key: "endpoint_backend",
      render: (record) => {
        return <div>{record.api_backend.api_endpoint}</div>;
      },
    },
    {
      title: "Action",
      dataIndex: "endpoint",
      key: "action",
      render: (record) => {
        return (
          <Space size="middle">
            <Button
              style={{ color: "#1677ff" }}
              type="text"
              onClick={() => {
                setEndpointToAddTest(record);
                setShowAddTestCaseModal(true);
              }}
            >
              Add Tests
            </Button>
          </Space>
        );
      },
    },
  ];

  const testCaseExpandedRowRenderer = (data) => {
    const testcases_data = data["testcases"];
    // Test Set Table Column
    const testcases_column = [
      {
        title: "Testcase Name",
        dataIndex: "name",
        key: "testcase_name",
      },
      {
        title: "Prompt Value",
        dataIndex: "prompt_values",
        key: "testcase_prompt_values",
        render: (record) => {
          return (
            <Input.TextArea
              defaultValue={JSON.stringify(record)}
              readOnly={true}
            ></Input.TextArea>
          );
        },
      },
      {
        title: "Expected Output",
        dataIndex: "expected_output",
        key: "testcase_expected_output",
      },
      {
        title: "Action",
        dataIndex: "uuid",
        key: "testcase_action",
        render: (testcase_id) => {
          return (
            <Space size="middle">
              <Button
                style={{ color: "#1677ff" }}
                type="text"
                onClick={() => {}}
              >
                Run
              </Button>
            </Space>
          );
        },
      },
    ];
    return (
      <Table
        columns={testcases_column}
        dataSource={testcases_data}
        pagination={false}
        rowKey={(record) => record.uuid}
      />
    );
  };

  const testSetExpandedRowRenderer = (data) => {
    const testset_data = data["testsets"];
    // Testset Column
    const testset_columns = [
      {
        title: "Test Id",
        dataIndex: "key",
        key: "testset_id",
      },
      {
        title: "Param Values",
        dataIndex: "param_values",
        key: "testset_param_values",
        render: (record) => {
          return (
            <Input.TextArea
              defaultValue={JSON.stringify(record)}
              readOnly={true}
            ></Input.TextArea>
          );
        },
      },
      {
        title: "Action",
        dataIndex: "key",
        key: "testset_actions",
        render: (testset_id) => {
          return (
            <div>
              <Space size="middle">
                <Button
                  style={{ color: "#1677ff" }}
                  type="text"
                  onClick={() => {}}
                >
                  Add Test Case
                </Button>
              </Space>
              <Space size="middle">
                <Button
                  style={{ color: "#1677ff" }}
                  type="text"
                  onClick={() => {}}
                >
                  Run
                </Button>
              </Space>
            </div>
          );
        },
      },
    ];

    return (
      <Table
        columns={testset_columns}
        dataSource={testset_data}
        expandable={{ expandedRowRender: testCaseExpandedRowRenderer }}
        pagination={false}
        rowKey={(record) => record.uuid}
      />
    );
  };

  return (
    <>
      <Table
        columns={columns}
        expandable={{ expandedRowRender: testSetExpandedRowRenderer }}
        dataSource={testsetEndpointsData}
        rowKey={(record) => record.endpoint.uuid}
      />
      <AddTestCaseModal
        open={showAddTestCaseModal}
        onCancelCb={() => setShowAddTestCaseModal(false)}
        endpoint={endpointToAddTest}
      />
    </>
  );
};

export default TestPage;
