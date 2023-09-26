import {
  Box,
  TextField,
  Button,
  CircularProgress,
  FormGroup,
  Tooltip,
  Divider,
  IconButton,
  Typography,
  InputLabel,
  Paper,
  Stack,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import FileUpload from "@mui/icons-material/FileUpload";
import ContentCopy from "@mui/icons-material/ContentCopy";
import { useEffect, useState } from "react";
import { enqueueSnackbar } from "notistack";
import SecretTextField from "../components/form/SecretTextField";
import { fetchData, patchData } from "./dataUtil";
import { organizationState, profileFlagsState } from "../data/atoms";
import { useRecoilValue } from "recoil";

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

  return (
    <div id="setting-page">
      {loading ? (
        <CircularProgress />
      ) : (
        <FormGroup>
          <Stack
            spacing={2}
            sx={{
              maxWidth: 900,
              width: "100%",
              padding: "20px 10px",
              textAlign: "left",
            }}
          >
            <Paper sx={{ marginBottom: "30px" }}>
              <TextField
                label="Promptly Token"
                value={formData.token}
                fullWidth
                variant="outlined"
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
            </Paper>
            <SecretTextField
              label="OpenAI API Token"
              type="password"
              fullWidth
              variant="outlined"
              size="small"
              disabled={!profileFlags.CAN_ADD_KEYS}
              value={formData.openai_key || ""}
              onChange={(e) => {
                setFormData({ ...formData, openai_key: e.target.value });
                setUpdateKeys(updateKeys.add("openai_key"));
              }}
            />
            <SecretTextField
              label="StabilityAI API Token"
              type="password"
              fullWidth
              variant="outlined"
              size="small"
              disabled={!profileFlags.CAN_ADD_KEYS}
              value={formData.stabilityai_key || ""}
              onChange={(e) => {
                setFormData({
                  ...formData,
                  stabilityai_key: e.target.value,
                });
                setUpdateKeys(updateKeys.add("stabilityai_key"));
              }}
            />
            <SecretTextField
              label="Cohere API Token"
              type="password"
              fullWidth
              variant="outlined"
              size="small"
              disabled={!profileFlags.CAN_ADD_KEYS}
              value={formData.cohere_key || ""}
              onChange={(e) => {
                setFormData({ ...formData, cohere_key: e.target.value });
                setUpdateKeys(updateKeys.add("cohere_key"));
              }}
            />
            <SecretTextField
              label="Elevenlabs API Token"
              type="password"
              fullWidth
              variant="outlined"
              size="small"
              disabled={!profileFlags.CAN_ADD_KEYS}
              value={formData.elevenlabs_key || ""}
              onChange={(e) => {
                setFormData({
                  ...formData,
                  elevenlabs_key: e.target.value,
                });
                setUpdateKeys(updateKeys.add("elevenlabs_key"));
              }}
            />
            <SecretTextField
              label="Azure OpenAI API Key"
              type="password"
              fullWidth
              variant="outlined"
              size="small"
              disabled={!profileFlags.CAN_ADD_KEYS}
              value={formData.azure_openai_api_key || ""}
              onChange={(e) => {
                setFormData({
                  ...formData,
                  azure_openai_api_key: e.target.value,
                });
                setUpdateKeys(updateKeys.add("azure_openai_api_key"));
              }}
            />
            <SecretTextField
              label="Google Service Account JSON Key"
              type="password"
              fullWidth
              variant="outlined"
              size="small"
              disabled={!profileFlags.CAN_ADD_KEYS}
              value={formData.google_service_account_json_key || ""}
              onChange={(e) => {
                setFormData({
                  ...formData,
                  google_service_account_json_key: e.target.value,
                });
                setUpdateKeys(
                  updateKeys.add("google_service_account_json_key"),
                );
              }}
            />
            <SecretTextField
              label="Anthropic API Key"
              type="password"
              fullWidth
              variant="outlined"
              size="small"
              disabled={!profileFlags.CAN_ADD_KEYS}
              value={formData.anthropic_api_key || ""}
              onChange={(e) => {
                setFormData({
                  ...formData,
                  anthropic_api_key: e.target.value,
                });
                setUpdateKeys(updateKeys.add("anthropic_api_key"));
              }}
            />
            <Paper>
              <Typography variant="h7">&nbsp;LocalAI</Typography>
            </Paper>
            <TextField
              label="LocalAI Base URL"
              fullWidth
              variant="outlined"
              size="small"
              disabled={!profileFlags.CAN_ADD_KEYS}
              value={formData.localai_base_url || ""}
              onChange={(e) => {
                setFormData({
                  ...formData,
                  localai_base_url: e.target.value,
                });
                setUpdateKeys(updateKeys.add("localai_base_url"));
              }}
            />
            <SecretTextField
              label="LocalAI API Key"
              type="password"
              fullWidth
              variant="outlined"
              size="small"
              disabled={!profileFlags.CAN_ADD_KEYS}
              value={formData.localai_api_key || ""}
              onChange={(e) => {
                setFormData({
                  ...formData,
                  localai_api_key: e.target.value,
                });
                setUpdateKeys(updateKeys.add("localai_api_key"));
              }}
            />
            <Box sx={{ my: 2 }}>
              <InputLabel>Custom Logo</InputLabel>
              {formData.logo && (
                <img
                  src={formData.logo}
                  alt="Logo"
                  style={{ height: 50, margin: 10, display: "block" }}
                />
              )}
              <Button
                component="label"
                variant="outlined"
                startIcon={<FileUpload />}
              >
                Upload
                <VisuallyHiddenInput
                  type="file"
                  accept="image/*"
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
            </Box>
            <Divider />
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
                  Logged in as&nbsp;<strong>{formData.user_email}</strong>. You
                  are currently subscribed to&nbsp;
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
            <Stack spacing={2} direction={"row"} flexDirection={"row-reverse"}>
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
                  }?prefilled_email=${encodeURIComponent(formData.user_email)}`}
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
        </FormGroup>
      )}
    </div>
  );
};

export default SettingPage;
