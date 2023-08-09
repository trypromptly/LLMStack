import { useState } from "react";

import {
  Button,
  Card,
  Col,
  Collapse,
  Input,
  Modal,
  Row,
  Space,
  Spin,
  Tag,
} from "antd";
import { Result } from "./Output";
import { ThemedJsonForm } from "../components/JsonForm";

const cardStyle = {
  margin: "2px",
};

const ExpandableTagList = ({ tags, x }) => {
  const [expanded, setExpanded] = useState(false);

  const visibleTags = expanded ? tags : tags.slice(0, x);

  const handleClick = () => {
    setExpanded(!expanded);
  };

  return (
    <>
      {visibleTags.map((tag, index) => (
        <Tag key={index}>{tag}</Tag>
      ))}
      {tags.length > x && (
        <Tag onClick={handleClick} color="blue">
          {expanded ? "- less" : `+${tags.length - x} more`}
        </Tag>
      )}
    </>
  );
};

function ModalHeader({ shareName, shareTags }) {
  const renderTags = shareTags && shareTags.length > 0;
  return (
    <Row style={{ marginRight: "10px" }}>
      <Space style={{ width: "100%", justifyContent: "space-between" }}>
        <div>{shareName}</div>
        {renderTags && (
          <div>
            <ExpandableTagList tags={shareTags || []} x={1} />
          </div>
        )}
        <Button type="text">Edit</Button>
      </Space>
    </Row>
  );
}

export default function SharePlaygroundModal({
  sharePlaygroundModalVisibility,
  handleCancelCb,
  shareName,
  shareTags,
  shareDescription,
  outputLoading,
  output,
  runError,
  endpointSelected,
  setPromptCb,
  schema,
  formData,
  atomState,
}) {
  return (
    <Modal
      className="share-playground-modal"
      title={<ModalHeader shareName={shareName} shareTags={shareTags} />}
      open={false}
      onCancel={handleCancelCb}
      footer={null}
      style={{ top: 10, left: 0 }}
      width="100vw"
    >
      <div style={{ height: "100%" }}>
        <Row>
          <Space style={{ width: "100%", justifyContent: "space-between" }}>
            <div>{shareDescription}</div>
          </Space>
        </Row>
        <Row>
          <Col xs={24} md={12}>
            <Card
              bodyStyle={{ height: "100%", display: "flex", padding: "0px" }}
              title={null}
              style={cardStyle}
              actions={[<Button type="primary">Execute</Button>]}
            >
              <Collapse defaultActiveKey={["1"]} style={{ width: "100%" }}>
                <Collapse.Panel header="Prompt Form" key="1">
                  <ThemedJsonForm schema={schema} atomState={atomState} />
                </Collapse.Panel>
                <Collapse.Panel header="Full Prompt" key="2">
                  <Input.TextArea
                    value={prompt}
                    placeholder="Enter prompt here. You can use {{}} to add variables. For example, {{name}} will allow you to replace name with a value when calling the endpoint."
                    onChange={(x) => setPromptCb(x.target.value)}
                  />
                </Collapse.Panel>
              </Collapse>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card
              bodyStyle={{
                height: "100%",
                display: "flex",
                justifyContent: "center",
              }}
              title={
                <div style={{ display: "flex", justifyContent: "center" }}>
                  Result
                </div>
              }
              style={{
                textAlign: "left",
                width: "100%",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                boxShadow: "0 0 3px #ccc",
              }}
            >
              <Spin spinning={outputLoading} tip={"Running the prompt"}>
                <Result
                  result={output}
                  endpoint={endpointSelected}
                  error={runError}
                />
              </Spin>
            </Card>
          </Col>
        </Row>
        <Row style={{ justifyContent: "center" }}>
          <Space direction="horizontal"></Space>
        </Row>
      </div>
    </Modal>
  );
}
