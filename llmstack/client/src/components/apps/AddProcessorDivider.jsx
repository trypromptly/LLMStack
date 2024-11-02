import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import {
  Button,
  FormControl,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { styled } from "@mui/system";
import { useEffect, useState } from "react";
import { useRecoilValue } from "recoil";
import {
  processorsState,
  providersState,
  organizationState,
  profileFlagsSelector,
} from "../../data/atoms";
import { ProviderIcon } from "./ProviderIcon";

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

const HorizontalRule = styled("div")`
  width: 100%;
  height: 1px;
  background-color: #ccc;
  margin-top: 24px;
`;

export function AddProcessorDivider({
  showProcessorSelector,
  isTool,
  setProcessorBackend,
}) {
  const organization = useRecoilValue(organizationState);
  const profileFlags = useRecoilValue(profileFlagsSelector);
  const processors = useRecoilValue(processorsState);
  const providers = useRecoilValue(providersState);

  const defaultProvider =
    profileFlags.IS_ORGANIZATION_MEMBER && organization?.default_api_backend
      ? processors?.find(
          (backend) => backend.id === organization?.default_api_backend,
        )?.api_provider.name
      : "Promptly";
  const defaultProcessor =
    profileFlags.IS_ORGANIZATION_MEMBER && organization?.default_api_backend
      ? organization?.default_api_backend
      : processors?.find((backend) => backend.id === "promptly/llm")?.id;

  const [provider, setProvider] = useState("");
  const [processor, setProcessor] = useState("");

  useEffect(() => {
    setProvider(providers.length > 0 && defaultProvider ? defaultProvider : "");
    setProcessor(
      processors.length > 0 && defaultProcessor ? defaultProcessor : "",
    );
  }, [defaultProvider, defaultProcessor, providers, processors]);

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
                value={provider}
                onChange={(e) => {
                  setProvider(e.target.value);
                  setProcessor("");
                }}
                id="provider-select"
                size="small"
                displayEmpty
                renderValue={(value) => (
                  <MenuItem sx={{ padding: 0 }}>
                    <ListItemIcon sx={{ minWidth: "26px !important" }}>
                      <ProviderIcon
                        providerSlug={value}
                        style={{ width: "20px" }}
                      />
                    </ListItemIcon>
                    <Typography>{value}</Typography>
                  </MenuItem>
                )}
              >
                <MenuItem value="">
                  <ListItemText>
                    <Typography variant="caption">Provider</Typography>
                  </ListItemText>
                </MenuItem>
                {providers.map((provider) => (
                  <MenuItem value={provider.name} key={provider.name}>
                    <ListItemIcon>
                      <ProviderIcon
                        providerSlug={provider?.slug}
                        style={{ width: "20px", height: "20px" }}
                      />
                    </ListItemIcon>
                    <ListItemText>{provider.name}</ListItemText>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {provider && (
              <FormControl>
                <Select
                  value={processor}
                  onChange={(e) => setProcessor(e.target.value)}
                  id="processor-select"
                  placeholder="Processor"
                  style={{ width: 120 }}
                  size="small"
                  displayEmpty
                >
                  <MenuItem value="">
                    <Typography variant="caption">Processor</Typography>
                  </MenuItem>
                  {processors
                    .filter((processor) => processor.provider.name === provider)
                    .filter(
                      (processor) =>
                        (organization?.disabled_api_backends || []).indexOf(
                          processor.id,
                        ) === -1,
                    )
                    .map((processor) => (
                      <MenuItem value={processor.id} key={processor.id}>
                        {processor.name}
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
            )}
            <Button
              startIcon={<AddCircleOutlineIcon fontSize="small" />}
              style={{ textTransform: "none" }}
              variant="contained"
              disabled={processor === ""}
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
                setProcessorBackend(processors.find((p) => p.id === processor));
                setProvider(defaultProvider);
                setProcessor("");
              }}
            >
              {isTool ? "Tool" : "Processor"}
            </Button>
          </Stack>
          {isTool ? <HorizontalRule /> : <VerticalLine />}
        </>
      )}
    </Separator>
  );
}
