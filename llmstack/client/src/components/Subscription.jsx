import { useState } from "react";

import { Button, Paper, Typography, Stack } from "@mui/material";

import { organizationState, profileFlagsState } from "../data/atoms";
import { useRecoilValue } from "recoil";
import SubscriptionUpdateModal from "./SubscriptionUpdateModal";

function Subscription(props) {
  const [subscriptionUpdateModalOpen, setSubscriptionUpdateModalOpen] =
    useState(false);
  const profileFlags = useRecoilValue(profileFlagsState);
  const organization = useRecoilValue(organizationState);

  return (
    <Stack>
      <Stack>
        <Typography variant="h6" className="section-header">
          Subscription
        </Typography>
        ;
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
            margin: "8px 10px 60px 0",
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
