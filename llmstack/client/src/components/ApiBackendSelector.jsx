import LightbulbIcon from "@mui/icons-material/Lightbulb";
import {
  Box,
  FormControl,
  Grid,
  InputLabel,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Select,
  Typography,
} from "@mui/material";
import { useEffect } from "react";
import {
  useRecoilState,
  useRecoilValue,
  useResetRecoilState,
  useSetRecoilState,
} from "recoil";
import {
  apiBackendDropdownListState,
  apiBackendSelectedState,
  apiBackendsState,
  apiProviderDropdownListState,
  apiProviderSelectedState,
  endpointConfigValueState,
  endpointSelectedState,
  inputValueState,
  isMobileState,
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
  const isMobile = useRecoilValue(isMobileState);

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
      <Grid container direction="row" gap={2} alignItems={"center"}>
        <Box
          sx={{
            minWidth: 150,
            "& .MuiSelect-outlined": {
              display: "flex",
            },
            width: isMobile ? "48%" : "auto",
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
          <Box sx={{ minWidth: 150, width: isMobile ? "48%" : "auto" }}>
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
        <Box>
          <Typography
            variant="body1"
            sx={{
              display: "flex",
              border: "solid 1px #ccc",
              borderRadius: 2,
              padding: "3px",
              maxWidth: isMobile ? "100%" : "350px",
              color: "#666",
              alignItems: "center",
              textAlign: "left",
              gap: 1,
              backgroundColor: "#f0f7ff",
            }}
          >
            <a
              href={`https://docs.trypromptly.com/processors/${apiBackendSelected?.api_provider?.slug}`}
              target="_blank"
              aria-label="Learn more about this API Backend"
              rel="noreferrer"
            >
              <LightbulbIcon color="info" />
            </a>
            {apiBackendSelected?.description || "Select an API Backend "}
          </Typography>
        </Box>
      </Grid>
    </Grid>
  );
}
