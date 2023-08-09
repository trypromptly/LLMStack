import { Modal, Button } from "antd";

export function LoggedOutModal({
  visibility,
  handleCancelCb,
  data,
  title,
  message,
}) {
  // fuction to store state in local storage before redirecting to login page
  const handleLogin = () => {
    if (data) localStorage.setItem("shareCode", data);
    window.location.href = "/login";
  };

  return (
    <Modal
      title={title ? title : "Logged Out"}
      open={visibility}
      onCancel={handleCancelCb}
      footer={null}
    >
      {message ? (
        message
      ) : (
        <p>
          You are logged out. Please{" "}
          <Button type="link" onClick={handleLogin} style={{ padding: "0px" }}>
            login
          </Button>{" "}
          or{" "}
          <Button type="link" onClick={handleLogin} style={{ padding: "0px" }}>
            signup
          </Button>{" "}
          to proceed.
        </p>
      )}
    </Modal>
  );
}
