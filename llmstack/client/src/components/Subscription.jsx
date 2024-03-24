import { Button, Paper, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useRecoilValue } from "recoil";
import { organizationState, profileFlagsState } from "../data/atoms";
import SubscriptionUpdateModal from "./SubscriptionUpdateModal";
import { axios } from "../data/axios";

function Subscription(props) {
  const [subscriptionUpdateModalOpen, setSubscriptionUpdateModalOpen] =
    useState(false);
  const profileFlags = useRecoilValue(profileFlagsState);
  const organization = useRecoilValue(organizationState);
  const [creditsAvailable, setCreditsAvailable] = useState(0);

  useEffect(() => {
    axios()
      .get("/api/profiles/me/credits")
      .then((response) => {
        if (response.status === 200) {
          setCreditsAvailable(response.data.available_credits / 1000);
        }
      })
      .catch((error) => {
        console.error(error);
      });
  }, []);

  return (
    <Stack sx={{ margin: "0 10px 60px 10px" }}>
      <Stack>
        <Typography
          variant="h6"
          className="section-header"
          sx={{ marginBottom: "8px" }}
        >
          Subscription
          <span style={{ float: "right", fontWeight: 400, fontSize: "16px" }}>
            Remaining Credits: <b>{creditsAvailable}</b>
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
