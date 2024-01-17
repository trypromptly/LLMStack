import { LogoutOutlined } from "@mui/icons-material";
import { postData } from "../pages/dataUtil";

export const onLogoutClick = async () => {
  postData(
    "/api/logout",
    {},
    () => {},
    (result) => {
      window.location.reload();
    },
    () => {},
  );
};

export default function Logout() {
  return (
    <a
      href="/#"
      onClick={onLogoutClick}
      style={{ color: "#000", fontSize: "32px" }}
    >
      <LogoutOutlined />
    </a>
  );
}
