import React from "react";

import { useState } from "react";
import { useRecoilValue } from "recoil";
import { useNavigate } from "react-router-dom";

import {
  Col,
  Row,
  Table,
  Space,
  Button,
  Drawer,
  Select,
  Input,
  Typography,
  Modal,
} from "antd";
import { endpointTableDataState } from "../data/atoms";
import ReactDiffViewer from "react-diff-viewer-continued";
import { axios } from "../data/axios";

function EndpointVersionCompareModal({ visible, versions, onCancel }) {
  const defaultLeftVersion = versions[0];
  const defaultRightVersion = versions[1];
  const [leftVersion, setLeftVersion] = useState({
    config: defaultLeftVersion.config,
    input: defaultLeftVersion.input,
  });
  const [rightVersion, setRightVersion] = useState({
    config: defaultRightVersion.config,
    input: defaultRightVersion.input,
  });
  const [leftSelectorValue, setLeftSelectorValue] = useState(
    defaultLeftVersion.version,
  );
  const [rightSelectorValue, setRightSelectorValue] = useState(
    defaultRightVersion.version,
  );

  return (
    <Drawer
      onClose={onCancel}
      open={visible}
      title={`Compare ${versions[0].name} Versions`}
      placement="left"
      size="large"
      width="100%"
    >
      <Row>
        <Col span={12}>
          <Row>
            <Select
              defaultValue={versions[0].version}
              value={leftSelectorValue}
              style={{
                width: 120,
              }}
              onChange={(value) => {
                setLeftSelectorValue(value);
                const selectedVersion = versions.find(
                  (entry) => entry.version === value,
                );
                setLeftVersion({
                  config: selectedVersion.config,
                  input: selectedVersion.input,
                });
              }}
              options={versions.map((entry) => {
                return { label: entry.version, value: entry.version };
              })}
            ></Select>
          </Row>
          <Row>
            <Input.TextArea
              autoSize={{ minRows: 6, maxRows: 10 }}
              disabled={true}
              value={leftVersion ? JSON.stringify(leftVersion) : ""}
            ></Input.TextArea>
          </Row>
        </Col>
        <Col span={12}>
          <Row>
            <Select
              defaultValue={versions[1].version}
              value={rightSelectorValue}
              style={{
                width: 120,
              }}
              onChange={(value) => {
                setRightSelectorValue(value);
                const selectedVersion = versions.find(
                  (entry) => entry.version === value,
                );
                setRightVersion({
                  config: selectedVersion.config,
                  input: selectedVersion.input,
                });
              }}
              options={versions.map((entry) => {
                return { label: entry.version, value: entry.version };
              })}
            ></Select>
          </Row>
          <Row>
            <Input.TextArea
              disabled={true}
              value={rightVersion ? JSON.stringify(rightVersion) : ""}
              autoSize={{ minRows: 6, maxRows: 10 }}
            ></Input.TextArea>
          </Row>
        </Col>
      </Row>
      {leftVersion && rightVersion && (
        <Row>
          <Col span={24}>
            <Row>
              <Typography.Title level={4}>Configuration Diff</Typography.Title>
            </Row>
            <Row>
              <ReactDiffViewer
                oldValue={JSON.stringify(leftVersion.config)}
                newValue={JSON.stringify(rightVersion.config)}
                showDiffOnly={true}
              ></ReactDiffViewer>
            </Row>
            <Row>
              <Typography.Title level={4}>Input Diff</Typography.Title>
            </Row>
            <Row>
              <ReactDiffViewer
                oldValue={JSON.stringify(leftVersion.input)}
                newValue={JSON.stringify(rightVersion.input)}
                showDiffOnly={true}
              ></ReactDiffViewer>
            </Row>
          </Col>
        </Row>
      )}
    </Drawer>
  );
}

function DeleteConfirmationModal({ visible, onCancel, onConfirm }) {
  return (
    <Modal open={visible} onCancel={onCancel} onOk={onConfirm}>
      <Typography.Title level={4}>
        Are you sure you want to delete this endpoint?
      </Typography.Title>
    </Modal>
  );
}

export default function EndpointPage() {
  const [diffModalVisible, setDiffModalVisible] = useState(false);
  const [endpointDeletionModalVisible, setEndpointDeletionModalVisible] =
    useState(false);
  const [endpointDeletionModalData, setEndpointDeletionModalData] =
    useState(null);

  const endpointTableData = useRecoilValue(endpointTableDataState);
  const [selectedRows, setSelectedRows] = useState([]);
  const navigate = useNavigate();

  function nestedTable(data) {
    const nestedColumns = [
      {
        title: "Version",
        dataIndex: "version",
      },
      {
        title: "Change Message",
        dataIndex: "description",
      },
      {
        title: "Is App Endpoint",
        dataIndex: "is_app",
        render: (record) => {
          return <div>{record ? "Yes" : "No"}</div>;
        },
      },
      {
        title: "Is Live",
        dataIndex: "is_live",
        render: (record) => {
          return <div>{record ? "Yes" : "No"}</div>;
        },
      },
      {
        title: "Action",
        render: (record) => {
          return (
            <Space size="middle">
              <Button
                style={{ color: "#1677ff" }}
                type="text"
                onClick={() => {}}
              >
                View
              </Button>
              <Button
                style={{ color: "#1677ff" }}
                type="text"
                onClick={() => {
                  setEndpointDeletionModalVisible(true);
                  setEndpointDeletionModalData(record);
                }}
              >
                Delete
              </Button>
            </Space>
          );
        },
      },
    ];
    return <Table dataSource={data.versions} columns={nestedColumns}></Table>;
  }

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Provider",
      dataIndex: "api_backend",
      key: "provider",
      render: (record) => {
        return <div>{record.api_provider.name}</div>;
      },
    },
    {
      title: "Backend",
      dataIndex: "api_backend",
      key: "backend",
      render: (record) => {
        return <div>{record.api_endpoint}</div>;
      },
    },
    {
      title: "Versions",
      dataIndex: "versions",
      key: "versions",
      render: (records) => {
        return (
          <Space size="middle">
            <Button style={{ color: "#1677ff" }} type="text" onClick={() => {}}>
              {records.length + 1}
            </Button>
          </Space>
        );
      },
    },
    {
      title: "Actions",
      key: "action",
      render: (record) => {
        const versions = [...[record], ...record.versions];
        return (
          <Space size="middle">
            <Button
              style={{ color: "#1677ff" }}
              type="text"
              onClick={() => {
                navigate("/");
              }}
            >
              Edit
            </Button>
            <Button
              style={{ color: "#1677ff" }}
              type="text"
              onClick={() => {
                setEndpointDeletionModalVisible(true);
                setEndpointDeletionModalData(record);
              }}
            >
              Delete
            </Button>
            {record.versions.length > 1 && (
              <Button
                style={{ color: "#1677ff" }}
                type="text"
                onClick={() => {
                  setSelectedRows(versions);
                  setDiffModalVisible(true);
                }}
              >
                Compare
              </Button>
            )}
          </Space>
        );
      },
    },
  ];

  return (
    <div id="endpoint-page">
      <Row>
        <Col span={24}>
          <Table
            dataSource={endpointTableData}
            columns={columns}
            expandable={{ expandedRowRender: nestedTable }}
          />
        </Col>
      </Row>
      {diffModalVisible && (
        <EndpointVersionCompareModal
          visible={diffModalVisible}
          versions={selectedRows}
          onCancel={() => {
            setDiffModalVisible(false);
            setSelectedRows([]);
          }}
        />
      )}
      {endpointDeletionModalVisible && (
        <DeleteConfirmationModal
          visible={endpointDeletionModalVisible}
          onConfirm={() => {
            if (endpointDeletionModalData)
              axios()
                .delete(`/api/endpoints/${endpointDeletionModalData.uuid}`)
                .then((response) => {})
                .finally(() => {
                  setEndpointDeletionModalVisible(false);
                  setEndpointDeletionModalData(null);
                  window.location.reload();
                });
          }}
          onCancel={() => {
            setEndpointDeletionModalVisible(false);
            setEndpointDeletionModalData(null);
          }}
        />
      )}
    </div>
  );
}
