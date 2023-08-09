import React from "react";
import { Modal, Button, Select } from "antd";
import { axios } from "../../data/axios";

export default function ShareDataSourceModal(props) {
  const { id, open, onOk, onCancel, title, dataSource } = props;
  const [visibility, setVisibility] = React.useState(dataSource?.visibility);

  const onOkClick = () => {
    let action = "noop";
    if (visibility !== dataSource.visibility) {
      if (dataSource.visibility === 0 && visibility === 1) {
        // If the visibility is changing from 1 to 0, then we need to make the entry private
        axios()
          .post(`api/org/datasources/${dataSource.uuid}/add_entry`)
          .then((res) => {
            onOk(action, dataSource);
          });
      } else if (dataSource.visibility === 1 && visibility === 0) {
        // If the visibility is changing from 1 to 0, then we need to make the entry org public
        axios()
          .delete(`api/org/datasources/${dataSource.uuid}`)
          .then((res) => {
            onOk(action, dataSource);
          });
      } else {
        onOk(action, dataSource);
      }
    } else {
      onOk(action, dataSource);
    }
  };

  const visibilityOptions = [
    {
      value: 1,
      label: "Organization",
      description: "Members of your organization can access this datasource",
    },
    {
      value: 0,
      label: "You",
      description: "Only you can access this datasource",
    },
  ];

  return (
    <Modal
      title={title}
      open={open}
      onOk={onOk}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={() => onCancel(id)}>
          Cancel
        </Button>,
        <Button key="submit" type="primary" onClick={() => onOkClick(id)}>
          Done
        </Button>,
      ]}
    >
      <h5>Choose who can access this datasource</h5>
      <Select
        style={{ width: "100%" }}
        value={visibility}
        onChange={(value) => setVisibility(value)}
      >
        {visibilityOptions.map((option) => (
          <Select.Option key={option.value} value={option.value}>
            {option.label}
            <br />
            <small>{option.description}</small>
          </Select.Option>
        ))}
      </Select>
    </Modal>
  );
}
