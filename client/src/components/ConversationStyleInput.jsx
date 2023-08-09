import { useEffect, useState } from "react";
import { Button, Col, Input, Row, Select } from "antd";
import { useLocation } from "react-router-dom";
import { DeleteOutlined } from "@ant-design/icons";

export function ConversationStyleInput({ onChanged, messages }) {
  const [entries, setEntries] = useState([]);
  const location = useLocation();

  const roles = [
    { value: "user", label: "User" },
    { value: "system", label: "System" },
    { value: "assistant", label: "Assistant" },
  ];

  useEffect(() => {
    try {
      const parsedMessages = JSON.parse(messages).map(
        (message) => `${message.role}:${message.content}`,
      );
      if (parsedMessages.length > 0) setEntries(parsedMessages);
    } catch (error) {
      console.error(error);
    }
  }, [messages]);

  useEffect(() => {
    if (location.pathname === "/") {
      setEntries([]);
    }
  }, [location]);

  const updateMessages = (messages) => {
    const newMessages = messages.map((message) => {
      const [role, content] = message.split(":");
      return { role, content };
    });

    onChanged(JSON.stringify(newMessages));
  };

  const updateRoleForEntry = (index, value) => {
    const newEntries = [...entries];
    newEntries[index] = `${value}:${newEntries[index].split(":")[1]}`;
    setEntries(newEntries);

    updateMessages(newEntries);
  };

  const updateContentForEntry = (index, value) => {
    const newEntries = [...entries];
    newEntries[index] = `${newEntries[index].split(":")[0]}:${value}`;
    setEntries(newEntries);

    updateMessages(newEntries);
  };

  const deleteMessageEntry = (index) => {
    const newEntries = [...entries];
    newEntries.splice(index, 1);
    setEntries(newEntries);

    updateMessages(newEntries);
  };

  return (
    <Col>
      <Row>
        <p>
          ChatGPT takes in a conversation as a list of messages with roles
          attached to each message entry. Use the below form to add your list of
          messages along with the role. For more details about the roles, refer
          to ChatGPT API documentation at{" "}
          <a
            href="https://platform.openai.com/docs/guides/chat"
            rel="noreferrer"
            target="_blank"
          >
            https://platform.openai.com/docs/guides/chat
          </a>
          . You can also use template variables using &#123;&#123;&#125;&#125;
          in the message content
        </p>
      </Row>
      {entries.map((entry, index) => (
        <Row key={index} style={{ marginBottom: "5px" }}>
          <Col>
            <Select
              options={roles}
              onChange={(value) => updateRoleForEntry(index, value)}
              defaultValue={
                entries[index] && entries[index].split(":")[0] !== ""
                  ? entries[index].split(":")[0]
                  : "Select a Role"
              }
            />
          </Col>
          <Col style={{ width: "75%" }}>
            <Input
              value={entry.split(":")[1]}
              onChange={(e) => updateContentForEntry(index, e.target.value)}
              placeholder="Your Message"
            />
          </Col>
          <Col>
            <Button
              icon={<DeleteOutlined />}
              onClick={() => {
                deleteMessageEntry(index);
              }}
            />
          </Col>
        </Row>
      ))}
      <Row style={{ marginTop: "10px" }}>
        <Button type="primary" onClick={() => setEntries([...entries, ":"])}>
          Add Message Entry
        </Button>
      </Row>
    </Col>
  );
}
