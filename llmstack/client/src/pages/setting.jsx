import {
  Box,
  TextField,
  Button,
  CircularProgress,
  Grid,
  Tooltip,
  Divider,
  IconButton,
  Typography,
  InputLabel,
  Paper,
  Stack,
} from "@mui/material";

import { LoadingButton } from "@mui/lab";

import { styled } from "@mui/material/styles";
import FileUpload from "@mui/icons-material/FileUpload";
import ContentCopy from "@mui/icons-material/ContentCopy";
import { useEffect, useState } from "react";
import { enqueueSnackbar } from "notistack";
import Connections from "../components/Connections";
import SecretTextField from "../components/form/SecretTextField";
import SubscriptionUpdateModal from "../components/SubscriptionUpdateModal";
import { fetchData, patchData } from "./dataUtil";
import { organizationState, profileFlagsState } from "../data/atoms";
import { useRecoilValue } from "recoil";
import { axios } from "../data/axios";
import "../index.css";
import ThemedJsonForm from "../components/ThemedJsonForm";
import validator from "@rjsf/validator-ajv8";

import { createRef } from "react";

const VisuallyHiddenInput = styled("input")({
  clip: "rect(0 0 0 0)",
  clipPath: "inset(50%)",
  height: 1,
  overflow: "hidden",
  position: "absolute",
  bottom: 0,
  left: 0,
  whiteSpace: "nowrap",
  width: 1,
});

const settingsSchema = {
  type: "object",
  properties: {
    openai_key: {
      type: "string",
      title: "OpenAI API Key",
    },
    stabilityai_key: {
      type: "string",
      title: "StabilityAI API Key",
    },
    cohere_key: {
      type: "string",
      title: "Cohere API Key",
    },
    elevenlabs_key: {
      type: "string",
      title: "Elevenlabs API Key",
    },
    google_service_account_json_key: {
      type: "string",
      title: "Google Credentials",
    },
    azure_openai_api_key: {
      type: "string",
      title: "Azure OpenAI API Key",
    },
    anthropic_api_key: {
      type: "string",
      title: "Anthropic API Key",
    },
    localai_base_url: {
      type: "string",
      title: "LocalAI Base URL",
    },
    localai_api_key: {
      type: "string",
      title: "LocalAI API Key",
    },
  },
};

const settingsUiSchema = {
  openai_key: {
    "ui:widget": "password",
    "ui:default": "",
  },
  stabilityai_key: {
    "ui:widget": "password",
    "ui:default": "",
  },
  cohere_key: {
    "ui:widget": "password",
    "ui:default": "",
  },
  elevenlabs_key: {
    "ui:widget": "password",
    "ui:default": "",
  },
  google_service_account_json_key: {
    "ui:widget": "password",
    "ui:help":
      "Add your Google Service Account JSON file content as base64 encoded string or paste the API key.",
    "ui:default": "",
  },
  azure_openai_api_key: {
    "ui:widget": "password",
    "ui:default": "",
  },
  localai_base_url: {
    "ui:widget": "text",
    "ui:help": "LocalAI base URL here if you want to use a self-hosted LocalAI",
    "ui:default": "",
  },
  localai_api_key: {
    "ui:widget": "password",
    "ui:help": "LocalAI API key if your instance needs authentication",
    "ui:default": "",
  },
  anthropic_api_key: {
    "ui:widget": "password",
    "ui:default": "",
  },
};

const SettingPage = () => {
  const [formData, setFormData] = useState({
    token: "",
    openai_key: "",
    stabilityai_key: "",
    cohere_key: "",
    forefrontai_key: "",
    elevenlabs_key: "",
    localai_api_key: "",
    localai_base_url: "",
    azure_openai_api_key: "",
    google_service_account_json_key: "",
    anthropic_api_key: "",
    logo: "",
  });
  const [loading, setLoading] = useState(true);
  const [updateKeys, setUpdateKeys] = useState(new Set());
  const profileFlags = useRecoilValue(profileFlagsState);
  const organization = useRecoilValue(organizationState);
  const formRef = createRef();

  useEffect(() => {
    fetchData(
      "api/profiles/me",
      () => {},
      (profile) => {
        setFormData({
          token: profile.token,
          openai_key: profile.openai_key,
          stabilityai_key: profile.stabilityai_key,
          cohere_key: profile.cohere_key,
          forefrontai_key: profile.forefrontai_key,
          elevenlabs_key: profile.elevenlabs_key,
          google_service_account_json_key:
            profile.google_service_account_json_key,
          azure_openai_api_key: profile.azure_openai_api_key,
          localai_api_key: profile.localai_api_key,
          localai_base_url: profile.localai_base_url,
          anthropic_api_key: profile.anthropic_api_key,
          logo: profile.logo,
          user_email: profile.user_email,
        });
        setLoading(false);
      },
    );

    const searchParams = new URLSearchParams(window.location.search);
    if (searchParams.get("showNotification")) {
      enqueueSnackbar(searchParams.get("notificationMessage") || "", {
        variant: searchParams.get("notificationType") || "info",
      });
    }
  }, []);

  const handleUpdate = (update_keys) => {
    setLoading(true);
    let data = {};
    update_keys.forEach((update_key) => {
      data[update_key] = formData[update_key];
    });

    patchData(
      "api/profiles/me",
      data,
      (loading_result) => {
        setLoading(loading_result);
      },
      (profile) => {
        setFormData({
          token: profile.token,
          openai_key: profile.openai_key,
          stabilityai_key: profile.stabilityai_key,
          cohere_key: profile.cohere_key,
          forefrontai_key: profile.forefrontai_key,
          elevenlabs_key: profile.elevenlabs_key,
          google_service_account_json_key:
            profile.google_service_account_json_key,
          azure_openai_api_key: profile.azure_openai_api_key,
          localai_api_key: profile.localai_api_key,
          localai_base_url: profile.localai_base_url,
          anthropic_api_key: profile.anthropic_api_key,
          logo: profile.logo,
        });
        setLoading(false);
        enqueueSnackbar("Profile updated successfully", {
          variant: "success",
        });
      },
      () => {},
    );
  };

  function settingsValidate(formData, errors, uiSchema) {
    return errors;
  }

  return (
    <div id="setting-page">
      {loading ? (
        <CircularProgress />
      ) : (
        <Grid container>
          <Grid item xs={12} md={6}>
            <Stack spacing={2} sx={{ textAlign: "left", margin: "10px" }}>
              <Typography variant="h6" className="section-header">
                Settings
              </Typography>
              <Box sx={{ padding: "15px 0" }}>
                <TextField
                  label="Promptly Token"
                  value={formData.token}
                  fullWidth
                  variant="outlined"
                  size="medium"
                  InputProps={{
                    readOnly: true,
                    endAdornment: (
                      <IconButton
                        onClick={(e) => {
                          navigator.clipboard.writeText(formData.token);
                          enqueueSnackbar("Token copied successfully", {
                            variant: "success",
                          });
                        }}
                      >
                        <Tooltip title="Copy Promptly API Token">
                          <ContentCopy fontSize="small" />
                        </Tooltip>
                      </IconButton>
                    ),
                  }}
                />
                <Typography variant="caption">
                  This is your API token. You can use this token to access
                  {process.env.REACT_APP_SITE_NAME} API directly. Please do not
                  share this token with anyone.
                </Typography>
              </Box>
              <Paper sx={{ width: "100%" }}>
                <Stack gap={2} padding={1} spacing={2}>
                  <ThemedJsonForm
                    schema={settingsSchema}
                    uiSchema={settingsUiSchema}
                    formData={formData}
                    validator={validator}
                    disableAdvanced={true}
                    onChange={(e) => {
                      const newFormData = { ...formData, ...e.formData };
                      setUpdateKeys(
                        new Set(
                          Object.keys(newFormData).filter((key) => {
                            return e.formData[key] !== formData[key];
                          }),
                        ),
                      );
                      setFormData(newFormData);
                    }}
                    formRef={formRef}
                    customValidate={settingsValidate}
                  />
                  <Divider />
                  <Box sx={{ my: 2 }}>
                    <InputLabel>Custom Logo</InputLabel>
                    {formData.logo && (
                      <img
                        src={formData.logo}
                        alt="Logo"
                        style={{ height: 50, margin: 10, display: "block" }}
                      />
                    )}
                    <Tooltip
                      title={
                        !profileFlags.CAN_UPLOAD_APP_LOGO
                          ? "You need to be a Pro subscriber to upload a custom logo"
                          : ""
                      }
                    >
                      <Button
                        component="label"
                        variant="outlined"
                        startIcon={<FileUpload />}
                        disabled={!profileFlags.CAN_UPLOAD_APP_LOGO}
                      >
                        Upload
                        <VisuallyHiddenInput
                          type="file"
                          accept="image/*"
                          disabled={!profileFlags.CAN_UPLOAD_APP_LOGO}
                          onChange={(e) => {
                            const files = e.target.files;
                            if (files && files.length > 0) {
                              const reader = new FileReader();
                              reader.readAsDataURL(files[0]);
                              reader.onload = (e) => {
                                setFormData({
                                  ...formData,
                                  logo: e.target?.result,
                                });
                                setUpdateKeys(updateKeys.add("logo"));
                              };
                            }
                          }}
                        />
                      </Button>
                    </Tooltip>
                  </Box>
                </Stack>
              </Paper>
              {process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT ===
                "true" && (
                <Stack>
                  <strong>Subscription</strong>
                  <p
                    style={{
                      display: profileFlags.IS_ORGANIZATION_MEMBER
                        ? "none"
                        : "block",
                    }}
                  >
                    Logged in as&nbsp;<strong>{formData.user_email}</strong>.
                    You are currently subscribed to&nbsp;
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
                      Note: You will be needed to login with a link that is sent
                      to your email.
                    </i>
                  </p>
                  <p
                    style={{
                      display: profileFlags.IS_ORGANIZATION_MEMBER
                        ? "block"
                        : "none",
                    }}
                  >
                    Logged in as <strong>{formData.user_email}</strong>. Your
                    account is managed by your organization,&nbsp;
                    <strong>{organization?.name}</strong>. Please contact your
                    admin to manage your subscription.
                  </p>
                </Stack>
              )}
              {process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT ===
                "true" && <Divider />}
              <Stack
                spacing={2}
                direction={"row"}
                flexDirection={"row-reverse"}
              >
                <Button
                  variant="contained"
                  onClick={() => {
                    handleUpdate(updateKeys);
                  }}
                >
                  Update
                </Button>
                {process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT ===
                  "true" && (
                  <Button
                    href={`${
                      process.env.REACT_APP_SUBSCRIPTION_MANAGEMENT_URL
                    }?prefilled_email=${encodeURIComponent(
                      formData.user_email,
                    )}`}
                    target="_blank"
                    variant="outlined"
                    style={{
                      marginRight: "10px",
                      display: profileFlags.IS_ORGANIZATION_MEMBER
                        ? "none"
                        : "inherit",
                    }}
                  >
                    Manage Subscription
                  </Button>
                )}
              </Stack>
            </Stack>
          </Grid>
          <Grid item xs={12} md={6}>
            <Connections />
          </Grid>
        </Grid>
      )}
      {subscriptionUpdateModalOpen && (
        <SubscriptionUpdateModal
          open={subscriptionUpdateModalOpen}
          handleCloseCb={() => {
            setSubscriptionUpdateModalOpen(false);
          }}
          userEmail={formData.user_email}
        />
      )}
    </div>
  );
};

export default SettingPage;
