import React from "react";
import { Modal, Button } from "antd";

export default function DeleteConfirmationModal(props) {
  const { id, open, onOk, onCancel, title, text } = props;

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
        <Button key="submit" type="primary" onClick={() => onOk(id)}>
          Confirm
        </Button>,
      ]}
    >
      {text}
    </Modal>
  );
}
