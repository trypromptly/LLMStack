import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import validator from "@rjsf/validator-ajv8";
import { enqueueSnackbar } from "notistack";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRecoilValue } from "recoil";
import { providerSchemasSelector, profileSelector } from "../../data/atoms";
import { axios } from "../../data/axios";
import { ProviderIcon } from "../apps/ProviderIcon";
import ThemedJsonForm from "../ThemedJsonForm";

export function ProviderConfigModal({
  open,
  handleCancelCb,
  configUpdatedCb,
  modalTitle = "Add Provider Configuration",
  providerConfigKey = null,
  toDelete = false,
}) {
  const [formData, setFormData] = useState({});
  const providerSchemas = useRecoilValue(providerSchemasSelector);
  const profileData = useRecoilValue(profileSelector);
  const providerConfigs = useMemo(
    () => profileData?.provider_configs || {},
    [profileData],
  );
  const [selectedProvider, setSelectedProvider] = useState("");

  const handleProviderConfigChange = useCallback(
    async (providerSlug, providerConfigs, config) => {
      // Verify that the provider slug is valid
      if (
        !providerSlug ||
        !providerSchemas.find((schema) => schema.slug === providerSlug)
      ) {
        enqueueSnackbar("Please select a valid provider", { variant: "error" });
        return;
      }

      // Build the provider configuration object
      const providerConfig = toDelete
        ? {}
        : {
            [`${providerSlug}/${config["processor_slug"]}/${config["model_slug"]}/${config["deployment_key"]}`]:
              {
                ...config,
                provider_slug: providerSlug,
              },
          };

      let updatedProviderConfigs = {};

      if (toDelete && providerConfigKey) {
        updatedProviderConfigs = { ...providerConfigs };
        delete updatedProviderConfigs[providerConfigKey];
      } else {
        updatedProviderConfigs = {
          ...providerConfigs,
          ...providerConfig,
        };
      }

      try {
        await axios().patch("/api/profiles/me", {
          provider_configs: updatedProviderConfigs,
        });

        if (providerConfigKey) {
          enqueueSnackbar("Provider configuration updated", {
            variant: "success",
          });
        } else {
          enqueueSnackbar("Provider configuration added", {
            variant: "success",
          });
        }

        configUpdatedCb();
      } catch (error) {
        if (providerConfigKey) {
          enqueueSnackbar("Failed to update provider configuration", {
            variant: "error",
          });
        } else {
          enqueueSnackbar("Failed to add provider configuration", {
            variant: "error",
          });
        }
      }
    },
    [providerConfigKey, toDelete, configUpdatedCb, providerSchemas],
  );

  useEffect(() => {
    const providerConfig = providerConfigs[providerConfigKey];
    if (providerConfig) {
      setSelectedProvider(providerConfig["provider_slug"]);
      setFormData(providerConfig);
    } else {
      setFormData({});
    }
  }, [providerConfigKey, providerConfigs]);

  return (
    <Dialog open={open} onClose={handleCancelCb} sx={{ zIndex: 900 }} fullWidth>
      <DialogTitle>{modalTitle}</DialogTitle>
      <DialogContent>
        {providerConfigKey && toDelete && (
          <Typography>
            Are you sure want to delete the provider configuration{" "}
            <strong>{providerConfigKey}</strong>?
          </Typography>
        )}
        {!toDelete && (
          <Stack spacing={2}>
            <FormControl
              sx={{
                marginTop: "8px !important",
              }}
            >
              <InputLabel id="select-provider-label">Provider</InputLabel>
              <Select
                onChange={(e) => {
                  setSelectedProvider(e.target.value);
                }}
                value={selectedProvider}
                label="Provider"
                sx={{
                  "& .MuiSelect-outlined": {
                    display: "flex",
                    height: "32px !important",
                  },
                }}
              >
                {providerSchemas.map((option, index) => (
                  <MenuItem key={index} value={option.slug}>
                    <ListItemIcon
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        minWidth: "32px !important",
                      }}
                    >
                      <ProviderIcon
                        providerSlug={option?.slug}
                        style={{ width: "20px", height: "20px" }}
                      />
                    </ListItemIcon>
                    <ListItemText sx={{ maxWidth: "calc(100% - 40px)" }}>
                      {option.name}
                    </ListItemText>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {selectedProvider && (
              <ThemedJsonForm
                schema={
                  providerSchemas.find(
                    (schema) => schema.slug === selectedProvider,
                  )?.config_schema
                }
                validator={validator}
                uiSchema={
                  providerSchemas.find(
                    (schema) => schema.slug === selectedProvider,
                  )?.config_ui_schema || {}
                }
                formData={formData}
                onChange={({ formData }) => {
                  setFormData(formData);
                }}
              />
            )}
          </Stack>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancelCb}>Cancel</Button>
        <Button
          variant="contained"
          onClick={() => {
            handleProviderConfigChange(
              selectedProvider,
              providerConfigs,
              formData,
            );
          }}
        >
          {toDelete ? "Delete" : providerConfigKey ? "Update" : "Submit"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
