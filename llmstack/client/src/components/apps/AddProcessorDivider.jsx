import { useEffect, useState } from "react";
import {
  Button,
  FormControl,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { styled } from "@mui/system";
import { useRecoilValue } from "recoil";
import {
  apiBackendsState,
  apiProvidersState,
  organizationState,
  profileFlagsState,
} from "../../data/atoms";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";

const Separator = styled("div")`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
`;

const VerticalLine = styled("div")`
  width: 1px;
  height: 20px;
  background-color: black;
  margin: 4px 0;
`;

export function AddProcessorDivider({
  showProcessorSelector,
  setProcessorBackend,
}) {
  const organization = useRecoilValue(organizationState);
  const profileFlags = useRecoilValue(profileFlagsState);
  const apiBackends = useRecoilValue(apiBackendsState);
  const apiProviders = useRecoilValue(apiProvidersState);

  const defaultApiProvider =
    profileFlags.IS_ORGANIZATION_MEMBER && organization?.default_api_backend
      ? apiBackends?.find(
          (backend) => backend.id === organization?.default_api_backend,
        )?.api_provider.name
      : "Open AI";
  const defaultApiBackend =
    profileFlags.IS_ORGANIZATION_MEMBER && organization?.default_api_backend
      ? organization?.default_api_backend
      : apiBackends?.find((backend) => backend.name === "ChatGPT")?.id;

  const [apiProvider, setApiProvider] = useState("");
  const [apiBackend, setApiBackend] = useState("");

  useEffect(() => {
    setApiProvider(
      apiProviders.length > 0 && defaultApiProvider ? defaultApiProvider : "",
    );
    setApiBackend(
      apiBackends.length > 0 && defaultApiBackend ? defaultApiBackend : "",
    );
  }, [defaultApiProvider, defaultApiBackend, apiProviders, apiBackends]);

  return (
    <Separator>
      <VerticalLine />
      {showProcessorSelector && (
        <>
          <Stack
            direction="row"
            spacing={1}
            border="solid 1px #ccc"
            padding="5px"
            sx={{
              boxShadow: "0 0 10px #ccc",
            }}
          >
            <FormControl>
              <Select
                value={apiProvider}
                onChange={(e) => {
                  setApiProvider(e.target.value);
                  setApiBackend("");
                }}
                id="provider-select"
                style={{ width: 120 }}
                size="small"
                displayEmpty
              >
                <MenuItem value="">
                  <Typography variant="caption">Provider</Typography>
                </MenuItem>
                {apiProviders.map((provider) => (
                  <MenuItem value={provider.name} key={provider.name}>
                    {provider.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {apiProvider && (
              <FormControl>
                <Select
                  value={apiBackend}
                  onChange={(e) => setApiBackend(e.target.value)}
                  id="backend-select"
                  placeholder="Backend"
                  style={{ width: 120 }}
                  size="small"
                  displayEmpty
                >
                  <MenuItem value="">
                    <Typography variant="caption">Backend</Typography>
                  </MenuItem>
                  {apiBackends
                    .filter(
                      (backend) => backend.api_provider.name === apiProvider,
                    )
                    .filter(
                      (backend) =>
                        (organization?.disabled_api_backends || []).indexOf(
                          backend.id,
                        ) === -1,
                    )
                    .map((backend) => (
                      <MenuItem value={backend.id} key={backend.id}>
                        {backend.name}
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
            )}
            <Button
              startIcon={<AddCircleOutlineIcon fontSize="small" />}
              style={{ textTransform: "none" }}
              variant="contained"
              disabled={apiBackend === ""}
              sx={{
                "&.Mui-disabled": {
                  backgroundColor: "#8ac48f !important",
                  color: "#444 !important",
                },
                "&.MuiButton-contained": {
                  color: "#fff",
                  backgroundColor: "#146226",
                },
              }}
              onClick={() => {
                setProcessorBackend(
                  apiBackends.find((b) => b.id === apiBackend),
                );
                setApiProvider(defaultApiProvider);
                setApiBackend("");
              }}
            >
              Processor
            </Button>
          </Stack>
          <VerticalLine />
        </>
      )}
    </Separator>
  );
}
