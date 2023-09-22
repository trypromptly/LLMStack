import { useEffect } from "react";

import {
  Grid,
  Select,
  MenuItem,
  Box,
  FormControl,
  InputLabel,
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
        apibackends.find(
          (backend) => backend.api_endpoint === "chat/completions",
        )?.api_provider.name,
      );
      setApiBackendSelected(
        apibackends.find(
          (backend) => backend.api_endpoint === "chat/completions",
        ),
      );
    } else if (
      !apiBackendSelected &&
      apiProviderSelected &&
      apiProviderSelected === "Open AI"
    ) {
      setApiBackendSelected(
        apibackends.find(
          (backend) => backend.api_endpoint === "chat/completions",
        ),
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
      <Grid container direction="row">
        <Box sx={{ minWidth: 150 }}>
          <FormControl fullWidth>
            <InputLabel id="select-api-provider-label">API Provider</InputLabel>
            <Select
              style={{ width: "auto" }}
              onChange={(e) => {
                setApiProviderSelected(e.target.value);
                setApiBackendSelected(null);
                setendpointConfigValueState({});
                resetInputValueState();
              }}
              value={apiProviderSelected ? apiProviderSelected : ""}
              label="Select API Provider"
            >
              {apiprovidersDropdown.map((option, index) => (
                <MenuItem key={index} value={option.value}>
                  {option.label}
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
                style={{ width: 150 }}
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
                label="Select API Backend"
              >
                {apibackendsDropdown
                  .filter((x) => x.provider === apiProviderSelected)
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
