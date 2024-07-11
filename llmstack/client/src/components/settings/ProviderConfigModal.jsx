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
import { useEffect, useState } from "react";
import { useRecoilValue } from "recoil";
import { providerSchemasSelector } from "../../data/atoms";
import { ProviderIcon } from "../apps/ProviderIcon";
import ThemedJsonForm from "../ThemedJsonForm";

export function ProviderConfigModal({
  open,
  handleCancelCb,
  handleProviderConfigChange,
  providerConfigs,
  modalTitle = "Add Provider Configuration",
  providerConfigKey = null,
  toDelete = false,
}) {
  const [formData, setFormData] = useState({});
  const providerSchemas = useRecoilValue(providerSchemasSelector);
  const [selectedProvider, setSelectedProvider] = useState("");

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
              providerConfigKey,
              selectedProvider,
              providerConfigs,
              formData,
              toDelete,
            );
          }}
        >
          {toDelete ? "Delete" : providerConfigKey ? "Update" : "Submit"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
