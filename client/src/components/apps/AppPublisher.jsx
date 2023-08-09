import React, { useState } from "react";
import { profileFlagsState } from "../../data/atoms";
import { axios } from "../../data/axios";
import { useRecoilValue } from "recoil";
import { message, Modal, Button, Select, Spin } from "antd";

function PublishModalInternal({
  show,
  setShow,
  app,
  setIsPublished,
  setAppVisibility = null,
  editSharing = false,
}) {
  const [isPublishing, setIsPublishing] = useState(false);
  const [done, setDone] = useState(false);
  const [visibility, setVisibility] = useState(app?.visibility);
  const [accessibleBy, setAccessibleBy] = useState(app?.accessible_by || []);
  const [accessPermission, setAccessPermission] = useState(
    app?.access_permission || 0,
  );
  const profileFlags = useRecoilValue(profileFlagsState);

  const accessPermissionOptions = [
    {
      label: "Viewer",
      value: 0,
      description: "Users can view the app",
    },
    {
      label: "Collaborator",
      value: 1,
      description: "Users can collaborate on the app",
    },
  ];

  let visibilityOptions = [];

  if (profileFlags.CAN_PUBLISH_PUBLIC_APPS || app?.visibility === 3) {
    visibilityOptions.push({
      label: "Public",
      value: 3,
      description: "Anyone can access this app",
    });
  }

  if (profileFlags.CAN_PUBLISH_UNLISTED_APPS || app?.visibility === 2) {
    visibilityOptions.push({
      label: "Unlisted",
      value: 2,
      description: "Anyone with the app's published url can access this app",
    });
  }

  if (profileFlags.CAN_PUBLISH_ORG_APPS || app?.visibility === 1) {
    visibilityOptions.push({
      label: "Organization",
      value: 1,
      description: "Only members of your organization can access this app",
    });
  }

  if (profileFlags.CAN_PUBLISH_PRIVATE_APPS || app?.visibility === 0) {
    visibilityOptions.push({
      label: "Private",
      value: 0,
      description: "Only you and the selected users can access this app",
    });
  }

  const publishApp = () => {
    if (done) {
      setShow(false);
      setDone(false);
      return;
    }

    setIsPublishing(true);
    axios()
      .post(`/api/apps/${app.uuid}/publish`, {
        visibility: visibility,
        accessible_by: accessibleBy,
        access_permission: accessPermission,
      })
      .then(() => {
        setIsPublished(true);
        setDone(true);
        if (setAppVisibility) {
          setAppVisibility(visibility);
        }
      })
      .catch((error) => {
        message.error(error.response?.data?.message || "Error publishing app");
      })
      .finally(() => {
        setIsPublishing(false);
      });
  };

  return (
    <Modal
      title={editSharing ? "App Sharing" : "Publish App"}
      open={show}
      onOk={() => {
        setDone(false);
        setShow(false);
      }}
      onCancel={() => {
        setDone(false);
        setShow(false);
      }}
      footer={[
        <Button key="back" onClick={() => setShow(false)}>
          Cancel
        </Button>,
        <Button key="submit" type="primary" onClick={publishApp}>
          {isPublishing ? (
            <Spin />
          ) : done ? (
            <a
              href={`/app/${app.published_uuid}`}
              target="_blank"
              rel="noreferrer"
            >
              View Published App
            </a>
          ) : editSharing ? (
            "Save App"
          ) : (
            "Publish App"
          )}
        </Button>,
      ]}
    >
      {done && <p>App {editSharing ? "saved" : "published"} successfully!</p>}
      {!done && (
        <div>
          <h5>Choose who can access this App</h5>
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
          {visibility === 0 && (
            <div style={{ marginTop: 10, margin: "auto" }}>
              <p>
                Select users who can access the app. Only users with given email
                addresses will be able to access the app.
              </p>
              <Select
                mode="tags"
                style={{ width: "75%" }}
                placeholder="Enter valid email addresses"
                value={accessibleBy}
                onChange={(value) => setAccessibleBy(value)}
                notFoundContent={null}
              />
              <Select
                style={{ width: "25%" }}
                placeholder="Select permissions"
                value={accessPermission}
                onChange={(value) => setAccessPermission(value)}
              >
                {accessPermissionOptions.map((option) => (
                  <Select.Option key={option.value} value={option.value}>
                    {option.label}
                    <br />
                    <small>{option.description}</small>
                  </Select.Option>
                ))}
              </Select>
              &nbsp;
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}

export function PublishModal({
  show,
  setShow,
  app,
  setIsPublished,
  setAppVisibility,
}) {
  return (
    <PublishModalInternal
      show={show}
      setShow={setShow}
      app={app}
      setIsPublished={setIsPublished}
      setAppVisibility={setAppVisibility}
    />
  );
}

export function EditSharingModal({
  show,
  setShow,
  app,
  setIsPublished,
  setAppVisibility,
}) {
  return (
    <PublishModalInternal
      show={show}
      setShow={setShow}
      app={app}
      setIsPublished={setIsPublished}
      setAppVisibility={setAppVisibility}
      editSharing={true}
    />
  );
}

export function UnpublishModal({ show, setShow, app, setIsPublished }) {
  const [isUnpublishing, setIsUnpublishing] = useState(false);
  const [done, setDone] = useState(false);

  const unpublishApp = () => {
    if (done) {
      setShow(false);
      setDone(false);
      return;
    }

    setIsUnpublishing(true);
    axios()
      .post(`/api/apps/${app.uuid}/unpublish`)
      .then(() => {
        setIsPublished(false);
        setDone(true);
      })
      .catch((error) => {
        message.error(
          error.response?.data?.message || "Error unpublishing app",
        );
      })
      .finally(() => {
        setIsUnpublishing(false);
      });
  };

  return (
    <Modal
      title={"Unpublish App"}
      open={show}
      onOk={() => {
        setDone(false);
        setShow(false);
      }}
      onCancel={() => {
        setDone(false);
        setShow(false);
      }}
      footer={[
        <Button key="back" onClick={() => setShow(false)}>
          Cancel
        </Button>,
        <Button key="submit" type="primary" onClick={unpublishApp}>
          {isUnpublishing ? <Spin /> : done ? "Done" : "Yes, Unpublish App"}
        </Button>,
      ]}
    >
      {done && <p>App unpublished successfully!</p>}
      {!done && (
        <p>
          Are you sure want to unpublish the app? This will make the app
          unaccessible to anyone it was already shared with.
        </p>
      )}
    </Modal>
  );
}
