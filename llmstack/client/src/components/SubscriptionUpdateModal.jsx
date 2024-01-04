import { useEffect, useState } from "react";

import {
  Button,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  RadioGroup,
  Card,
  CardContent,
  CardHeader,
  Radio,
  Typography,
  Divider,
} from "@mui/material";

import { axios } from "../data/axios";
import { LoadingButton } from "@mui/lab";
import { enqueueSnackbar } from "notistack";

const SubscriptionUpdateModal = ({ open, handleCloseCb }) => {
  const [subscriptionPrices, setSubscriptionPrices] = useState([]);
  const [subscription, setSubscription] = useState("");
  const [updateButtonLoading, setUpdateButtonLoading] = useState(false);
  const [updateButtonDisabled, setUpdateButtonDisabled] = useState(false);
  const [cancelButtonDisabled, setCancelButtonDisabled] = useState(false);

  useEffect(() => {
    axios()
      .get("/api/subscriptions/prices")
      .then((res) => {
        setSubscriptionPrices(res.data.prices || []);
      })
      .catch((err) => {
        enqueueSnackbar("Error loading subscription prices", {
          variant: "error",
        });
      });
  }, []);

  return (
    <Dialog open={open} onClose={handleCloseCb} fullWidth>
      <DialogTitle>{"Upgrade Subscription"}</DialogTitle>
      <DialogContent>
        <Typography variant="body1">
          Choose a subscription plan to upgrade to. To compare the features of
          each plan, please visit our{" "}
          <a
            href="https://www.trypromptly.com/#pricing"
            target="_blank"
            rel="noreferrer"
          >
            pricing page
          </a>
          .
        </Typography>
        <br />
        <FormControl>
          <RadioGroup
            overlay
            name="subscriptions"
            defaultValue=""
            row
            sx={{ gap: 4 }}
          >
            {subscriptionPrices.map((subscriptionPrice) => (
              <Card
                component="label"
                key={subscriptionPrice.id}
                sx={{ width: "150px", height: "150px" }}
              >
                <CardHeader
                  title={subscriptionPrice.product_name}
                  subheader={<Divider />}
                  sx={{ padding: 0 }}
                />
                <CardContent>
                  <Stack>
                    <Typography variant="h5">
                      ${subscriptionPrice.unit_amount} /{" "}
                      {subscriptionPrice.recurring_interval}
                    </Typography>
                    <Radio
                      variant="soft"
                      value={subscriptionPrice.id}
                      onChange={(e) => {
                        setSubscription(e.target.value);
                      }}
                      sx={{
                        mb: 4,
                      }}
                    />
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </RadioGroup>
        </FormControl>
      </DialogContent>
      <DialogActions>
        <Button
          disabled={cancelButtonDisabled}
          onClick={handleCloseCb}
          sx={{ textTransform: "none" }}
        >
          Cancel
        </Button>
        <LoadingButton
          disabled={updateButtonDisabled || !subscription}
          loading={updateButtonLoading}
          onClick={() => {
            setCancelButtonDisabled(true);
            setUpdateButtonDisabled(true);
            setUpdateButtonLoading(true);
            axios()
              .post("/api/subscriptions/checkout", {
                price_id: subscription,
              })
              .then((res) => {
                enqueueSnackbar("Loading Checkout Page", {
                  variant: "success",
                });
                window.location.href = res.data.checkout_session_url;
              })
              .catch((err) => {})
              .finally(() => {
                setCancelButtonDisabled(false);
                setUpdateButtonDisabled(false);
                setUpdateButtonLoading(false);
              });
          }}
          variant="contained"
        >
          Checkout
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

export default SubscriptionUpdateModal;
