import { useRecoilValue } from "recoil";
import { isLoggedInState } from "../data/atoms";
import LoginDialog from "./LoginDialog";

// HOC to wrap components that require login. Shows a LoginDialog if not logged in.
export default function WithLogin({ loginMessage = "", children }) {
  const isLoggedIn = useRecoilValue(isLoggedInState);

  if (!isLoggedIn) {
    return (
      <LoginDialog
        open={!isLoggedIn}
        redirectPath={window.location.pathname}
        loginMessage={loginMessage || "Please login to use the platform."}
      />
    );
  }

  return children;
}
