import { useEffect, useState } from "react";

import {
  TextField,
  Button,
  FormGroup,
  InputLabel,
  Paper,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  Select,
} from "@mui/material";
import { axios } from "../data/axios";
import { LoadingButton } from "@mui/lab";
import { enqueueSnackbar } from "notistack";

const SubscriptionUpdateModal = ({ open, handleCloseCb, userEmail }) => {
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
      <DialogTitle>{"Manage Subscription"}</DialogTitle>
      <DialogContent>
        <FormGroup>
          <Stack spacing={2} sx={{ textAlign: "left", margin: "10px" }}>
            <Paper sx={{ marginBottom: "30px" }}>
              <TextField
                label="Email"
                value={userEmail}
                fullWidth
                variant="outlined"
              />
            </Paper>
            <Paper sx={{ marginBottom: "30px" }}>
              <InputLabel id="subscription-id">Subscription</InputLabel>
              <Select
                labelId="subscription-id"
                value={subscription}
                label="Subscription"
                fullWidth
                variant="outlined"
                onChange={(e) => {
                  setSubscription(e.target.value);
                }}
              >
                {subscriptionPrices.map((subscriptionPrice) => (
                  <MenuItem
                    key={subscriptionPrice.id}
                    value={subscriptionPrice.id}
                  >
                    {subscriptionPrice.name}
                  </MenuItem>
                ))}
              </Select>
            </Paper>
          </Stack>
        </FormGroup>
      </DialogContent>
      <DialogActions>
        <Button disabled={cancelButtonDisabled} onClick={handleCloseCb}>
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
          Update
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

export default SubscriptionUpdateModal;
