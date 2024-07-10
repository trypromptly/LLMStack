import { useState } from "react";
import { Button, Stack } from "@mui/material";
import { useRecoilValue } from "recoil";
import { ProviderConfigModal } from "./ProviderConfigModal";
import { ProviderConfigList } from "./ProviderConfigList";
import { profileSelector } from "../../data/atoms";

function ProviderConfigs() {
  const [showAddProviderConfigModal, setShowAddProviderConfigModal] =
    useState(false);
  const profileData = useRecoilValue(profileSelector);

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
        providerConfigs={profileData?.provider_configs || {}}
      />
      <ProviderConfigModal
        open={showAddProviderConfigModal}
        handleCancelCb={() => setShowAddProviderConfigModal(false)}
        configUpdatedCb={() => window.location.reload()}
      />
    </Stack>
  );
}

export default ProviderConfigs;
