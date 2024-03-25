import ContentCopy from "@mui/icons-material/ContentCopy";
import FileUpload from "@mui/icons-material/FileUpload";
import {
  Box,
  Button,
  CircularProgress,
  Divider,
  Grid,
  IconButton,
  InputLabel,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import validator from "@rjsf/validator-ajv8";
import { enqueueSnackbar } from "notistack";
import { createRef, useEffect, useState } from "react";
import { useRecoilValue, useRecoilState } from "recoil";
import Connections from "../components/Connections";
import Subscription from "../components/Subscription";
import ThemedJsonForm from "../components/ThemedJsonForm";
import { profileFlagsState, profileState } from "../data/atoms";
import { axios } from "../data/axios";
import "../index.css";

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
    username: {
      type: "string",
      title: "Username",
    },
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
  username: {
    "ui:default": null,
  },
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
    username: "",
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
  const [loading, setLoading] = useState(false);
  const [updateKeys, setUpdateKeys] = useState(new Set());
  const profileFlags = useRecoilValue(profileFlagsState);
  const [profileData, setProfileData] = useRecoilState(profileState);
  const formRef = createRef();

  useEffect(() => {
    setFormData(profileData);
  }, [profileData, setFormData]);

  const handleUpdate = (update_keys) => {
    setLoading(true);
    let data = {};
    update_keys.forEach((update_key) => {
      data[update_key] = formData[update_key];
    });

    axios()
      .patch("api/profiles/me", data)
      .then((response) => {
        setProfileData(response.data);
        enqueueSnackbar("Profile updated successfully", {
          variant: "success",
        });
      })
      .catch((error) => {
        enqueueSnackbar(
          `Failed to update profile. ${error?.response?.data?.error}`,
          {
            variant: "error",
          },
        );
      })
      .finally(() => {
        setUpdateKeys(new Set());
        setLoading(false);
      });
  };

  function settingsValidate(formData, errors, uiSchema) {
    return errors;
  }

  return (
    <div id="setting-page">
      {loading ? (
        <CircularProgress />
      ) : (
        <Grid container sx={{ m: 1 }}>
          <Grid item xs={12} md={6}>
            <Stack spacing={2} sx={{ textAlign: "left" }}>
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
              <Button
                variant="contained"
                sx={{ alignSelf: "end", width: "fit-content" }}
                onClick={() => {
                  handleUpdate(updateKeys);
                }}
              >
                Update
              </Button>
            </Stack>
          </Grid>

          <Grid item xs={12} md={6} sx={{ p: 0 }}>
            <Stack sx={{ margin: "0 10px", marginBottom: "60px" }} spacing={4}>
              <Connections />
              {process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT ===
                "true" && <Subscription user_email={formData.user_email} />}
            </Stack>
          </Grid>
        </Grid>
      )}
    </div>
  );
};

export default SettingPage;
