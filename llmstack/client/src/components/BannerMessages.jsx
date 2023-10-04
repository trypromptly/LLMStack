import React from "react";
import { Alert, Stack } from "@mui/material";
import { useRecoilValue } from "recoil";
import { profileFlagsState } from "../data/atoms";

function BannerMessages() {
  const profileFlags = useRecoilValue(profileFlagsState);
  let bannerMessages = [];

  if (profileFlags.HAS_EXCEEDED_MONTHLY_PROCESSOR_RUN_QUOTA) {
    bannerMessages.push({
      message: (
        <span>
          You have exceeded monthly usage limits for your plan. Please upgrade
          your account to continue running apps.
          <br />
          To upgrade your plan, click on <b>Manage Subscription</b> in the{" "}
          <a href="/settings">Settings</a> page.
        </span>
      ),
      variant: "error",
    });
  }

  if (bannerMessages.length === 0) {
    return null;
  }

  return (
    <Stack sx={{ margin: "5px", textAlign: "left" }}>
      {bannerMessages.map((message, index) => (
        <Alert
          key={index}
          severity={message.variant}
          sx={{
            "& .MuiAlert-icon": { marginTop: "auto", marginBottom: "auto" },
          }}
        >
          {message.message}
        </Alert>
      ))}
    </Stack>
  );
}

export default BannerMessages;
