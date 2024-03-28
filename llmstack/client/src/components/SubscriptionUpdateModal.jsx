import { LoadingButton } from "@mui/lab";
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  Radio,
  RadioGroup,
  Stack,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";
import { enqueueSnackbar } from "notistack";
import { useEffect, useState } from "react";
import { axios } from "../data/axios";

const SubscriptionUpdateModal = ({ open, handleCloseCb }) => {
  const [subscriptionPrices, setSubscriptionPrices] = useState([]);
  const [subscription, setSubscription] = useState("");
  const [tabValue, setTabValue] = useState(0);
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

  const getPriceCards = (isSubscription) =>
    subscriptionPrices
      .filter(
        (price) =>
          (isSubscription && price.recurring_interval) ||
          (!isSubscription && !price.recurring_interval),
      )
      .map((subscriptionPrice) => (
        <Card
          component="label"
          key={subscriptionPrice.id}
          sx={{ width: "150px", height: "150px" }}
        >
          <CardHeader
            title={subscriptionPrice.product_name}
            subheader={<Divider />}
            sx={{ padding: 0, "& span": { textAlign: "center" } }}
          />
          <CardContent>
            <Stack>
              {subscriptionPrice.recurring_interval && (
                <Typography variant="h5" sx={{ textAlign: "center" }}>
                  ${subscriptionPrice.unit_amount}
                  {isSubscription ? " / " : null}
                  {subscriptionPrice.recurring_interval}
                </Typography>
              )}
              {!subscriptionPrice.recurring_interval && (
                <Typography variant="body2" sx={{ textAlign: "center" }}>
                  {subscriptionPrice.description} at $
                  <b>{subscriptionPrice.unit_amount} </b>
                </Typography>
              )}
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
      ));

  return (
    <Dialog open={open} onClose={handleCloseCb} fullWidth>
      <DialogTitle>Manage Subscription</DialogTitle>
      <DialogContent>
        <Typography variant="body1">
          Please pick an option that suits you best. For more details, please
          visit our{" "}
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
        <Box sx={{ display: "flex" }}>
          <FormControl sx={{ width: "100%", flexDirection: "column" }}>
            <RadioGroup
              overlay
              name="subscriptions"
              defaultValue=""
              row
              sx={{ gap: 4 }}
            >
              <Stack spacing={2}>
                <Tabs
                  value={tabValue}
                  onChange={(e, newValue) => setTabValue(newValue)}
                >
                  <Tab
                    label="Buy credits"
                    id="credits-tab"
                    aria-controls="credits-tabpanel"
                  />
                  <Tab
                    label="Subscription"
                    id="subscription-tab"
                    aria-controls="subscription-tabpanel"
                  />
                </Tabs>

                {tabValue === 0 && (
                  <Box
                    id="credits-tabpanel"
                    aria-labelledby="credits-tab"
                    hidden={tabValue !== 0}
                    sx={{ display: "flex", gap: 2 }}
                  >
                    {getPriceCards(false)}
                  </Box>
                )}
                {tabValue === 1 && (
                  <Box
                    id="subscription-tabpanel"
                    aria-labelledby="subscription-tab"
                    hidden={tabValue !== 1}
                    sx={{ display: "flex", gap: 2 }}
                  >
                    {getPriceCards(true)}
                  </Box>
                )}
              </Stack>
            </RadioGroup>
          </FormControl>
        </Box>
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
