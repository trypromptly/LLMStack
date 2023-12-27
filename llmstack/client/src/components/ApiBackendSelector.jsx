import { useEffect } from "react";

import {
  Grid,
  Select,
  MenuItem,
  Box,
  FormControl,
  InputLabel,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import {
  useRecoilValue,
  useRecoilState,
  useSetRecoilState,
  useResetRecoilState,
} from "recoil";

import {
  apiProviderDropdownListState,
  apiBackendDropdownListState,
  apiBackendSelectedState,
  apiBackendsState,
  apiProviderSelectedState,
  endpointSelectedState,
  endpointConfigValueState,
  inputValueState,
} from "../data/atoms";
import { ProviderIcon } from "./apps/ProviderIcon";

export default function ApiBackendSelector() {
  const apiprovidersDropdown = useRecoilValue(apiProviderDropdownListState);
  const apibackendsDropdown = useRecoilValue(apiBackendDropdownListState);
  const apibackends = useRecoilValue(apiBackendsState);
  const resetEndpointSelected = useResetRecoilState(endpointSelectedState);
  const setendpointConfigValueState = useSetRecoilState(
    endpointConfigValueState,
  );
  const resetInputValueState = useResetRecoilState(inputValueState);
  const resetEndpointConfigValueState = useResetRecoilState(
    endpointConfigValueState,
  );

  const [apiProviderSelected, setApiProviderSelected] = useRecoilState(
    apiProviderSelectedState,
  );
  const [apiBackendSelected, setApiBackendSelected] = useRecoilState(
    apiBackendSelectedState,
  );

  useEffect(() => {
    if (apiBackendSelected) {
      resetEndpointSelected();
    }
  }, [apiBackendSelected, resetEndpointSelected]);

  useEffect(() => {
    if (!apiProviderSelected && apibackends && apibackends.length > 0) {
      setApiProviderSelected(
        apibackends.find((backend) => backend.id === "openai/chatgpt")
          ?.api_provider.name,
      );
      setApiBackendSelected(
        apibackends.find((backend) => backend.id === "openai/chatgpt"),
      );
    } else if (
      !apiBackendSelected &&
      apiProviderSelected &&
      apiProviderSelected === "Open AI"
    ) {
      setApiBackendSelected(
        apibackends.find((backend) => backend.id === "opennai/chatgpt"),
      );
    }
  }, [
    apibackends,
    apiBackendSelected,
    apiProviderSelected,
    setApiBackendSelected,
    setApiProviderSelected,
  ]);

  return (
    <Grid item id="apibackendselector">
      <Grid container direction="row" gap={2}>
        <Box
          sx={{
            minWidth: 150,
            "& .MuiSelect-outlined": {
              display: "flex",
            },
          }}
        >
          <FormControl fullWidth>
            <InputLabel id="select-api-provider-label">API Provider</InputLabel>
            <Select
              onChange={(e) => {
                setApiProviderSelected(e.target.value);
                setApiBackendSelected(null);
                setendpointConfigValueState({});
                resetInputValueState();
              }}
              value={apiProviderSelected ? apiProviderSelected : ""}
              label="API Provider"
            >
              {apiprovidersDropdown.map((option, index) => (
                <MenuItem key={index} value={option.value}>
                  <ListItemIcon
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      minWidth: "32px !important",
                    }}
                  >
                    <ProviderIcon
                      providerSlug={option?.value}
                      style={{ width: "20px", height: "20px" }}
                    />
                  </ListItemIcon>
                  <ListItemText>{option.label}</ListItemText>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        {apiProviderSelected && (
          <Box sx={{ minWidth: 150 }}>
            <FormControl fullWidth>
              <InputLabel id="select-api-backend-label">API Backend</InputLabel>
              <Select
                sx={{
                  lineHeight: "32px",
                  "& .MuiSelect-outlined": {
                    textAlign: "center",
                  },
                }}
                onChange={(e) => {
                  setApiBackendSelected(
                    apibackends.find(
                      (backend) => backend.id === e.target.value,
                    ),
                  );
                  setendpointConfigValueState({});
                  resetEndpointConfigValueState();
                  resetInputValueState();
                }}
                value={apiBackendSelected ? apiBackendSelected.id : ""}
                label="API Backend"
              >
                {/* TODO: Find a better way to render Promptly App processor in playground */}
                {apibackendsDropdown
                  .filter(
                    (x) =>
                      x.provider === apiProviderSelected &&
                      x.label !== "Promptly App",
                  )
                  .map((option, index) => (
                    <MenuItem key={index} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
              </Select>
            </FormControl>
          </Box>
        )}
      </Grid>
    </Grid>
  );
}
