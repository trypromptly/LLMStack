import { useState } from "react";
import { Button, Stack } from "@mui/material";
import { ProviderConfigModal } from "./ProviderConfigModal";
import { ProviderConfigList } from "./ProviderConfigList";

function ProviderConfigs({ configs, handleProviderConfigChange }) {
  const [showAddProviderConfigModal, setShowAddProviderConfigModal] =
    useState(false);

  return (
    <Stack>
      <Button
        variant="contained"
        sx={{
          textTransform: "none",
          margin: "10px",
          marginLeft: "auto",
          marginRight: 0,
        }}
        onClick={() => {
          setShowAddProviderConfigModal(true);
        }}
      >
        Add Provider
      </Button>
      <ProviderConfigList
        providerConfigs={configs}
        handleProviderConfigChange={handleProviderConfigChange}
      />
      <ProviderConfigModal
        open={showAddProviderConfigModal}
        handleCancelCb={() => setShowAddProviderConfigModal(false)}
        configUpdatedCb={() => window.location.reload()}
        providerConfigs={configs}
        handleProviderConfigChange={handleProviderConfigChange}
      />
    </Stack>
  );
}

export default ProviderConfigs;
