import { Button, Paper, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { useRecoilValue } from "recoil";
import {
  organizationState,
  profileState,
  profileFlagsState,
} from "../data/atoms";
import SubscriptionUpdateModal from "./SubscriptionUpdateModal";
import { formatStorage } from "../data/utils";

function Subscription(props) {
  const [subscriptionUpdateModalOpen, setSubscriptionUpdateModalOpen] =
    useState(false);
  const profileFlags = useRecoilValue(profileFlagsState);
  const profile = useRecoilValue(profileState);
  const organization = useRecoilValue(organizationState);

  return (
    <Stack sx={{ margin: "0 10px 60px 10px" }}>
      <Stack>
        <Typography
          variant="h6"
          className="section-header"
          sx={{ marginBottom: "8px" }}
        >
          Storage
          <span style={{ float: "right", fontWeight: 400, fontSize: "16px" }}>
            Used:{" "}
            <b>{`${Math.round(
              profile?.credits?.used_storage / profile?.credits?.total_storage,
            )}% of ${formatStorage(profile?.credits?.total_storage)}`}</b>
          </span>
        </Typography>
        <br />
        <Typography
          variant="h6"
          className="section-header"
          sx={{ marginBottom: "8px" }}
        >
          Subscription
          <span style={{ float: "right", fontWeight: 400, fontSize: "16px" }}>
            Remaining Credits: <b>{profile?.credits?.available / 1000}</b>
          </span>
        </Typography>
        <Stack>
          <Paper>
            <Stack>
              <p
                style={{
                  display: profileFlags.IS_ORGANIZATION_MEMBER
                    ? "none"
                    : "block",
                }}
              >
                Logged in as&nbsp;<strong>{props.user_email}</strong>. You are
                currently subscribed to&nbsp;
                <strong>
                  {profileFlags.IS_PRO_SUBSCRIBER
                    ? "Pro"
                    : profileFlags.IS_BASIC_SUBSCRIBER
                      ? "Basic"
                      : "Free"}
                </strong>
                &nbsp;tier. Click on the Manage Subscription button below to
                change your plan.&nbsp;
                <br />
                <br />
                <i>
                  Note: You will be redirected to Stripe payment portal to
                  complete the upgrade payment process.
                </i>
              </p>
              <p
                style={{
                  display: profileFlags.IS_ORGANIZATION_MEMBER
                    ? "block"
                    : "none",
                }}
              >
                Logged in as <strong>{props.user_email}</strong>. Your account
                is managed by your organization,&nbsp;
                <strong>{organization?.name}</strong>. Please contact your admin
                to manage your subscription.
              </p>
            </Stack>
          </Paper>
        </Stack>
        {subscriptionUpdateModalOpen && (
          <SubscriptionUpdateModal
            open={subscriptionUpdateModalOpen}
            handleCloseCb={() => {
              setSubscriptionUpdateModalOpen(false);
            }}
          />
        )}
      </Stack>
      {!profileFlags.IS_ORGANIZATION_MEMBER && (
        <Button
          variant="contained"
          sx={{
            marginTop: "10px",
            display: profileFlags.IS_ORGANIZATION_MEMBER ? "none" : "inherit",
            alignSelf: "end",
          }}
          onClick={() => {
            setSubscriptionUpdateModalOpen(true);
          }}
          disabled={profileFlags.IS_PRO_SUBSCRIBER}
        >
          Manage Subscription
        </Button>
      )}
    </Stack>
  );
}

export default Subscription;
