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
import { useEffect, useState } from "react";
import { useRecoilValue } from "recoil";
import { processorsState, providersState, isMobileState } from "../data/atoms";
import { ProviderIcon } from "./apps/ProviderIcon";

export default function ProcessorSelector({
  onProcessorChange,
  hideDescription = false,
  defaultProviderSlug = "promptly",
  defaultProcessorSlug = "llm",
}) {
  const providers = useRecoilValue(providersState);
  const processors = useRecoilValue(processorsState);
  const isMobile = useRecoilValue(isMobileState);

  const [selectedProvider, setSelectedProvider] = useState(null);
  const [selectedProcessor, setSelectedProcessor] = useState(null);

  useEffect(() => {
    if (!selectedProvider && providers.length > 0) {
      setSelectedProvider(
        providers.find((p) => p.slug === defaultProviderSlug),
      );

      if (!selectedProcessor && processors.length > 0) {
        const processor = processors.find(
          (p) =>
            p.provider.slug === defaultProviderSlug &&
            p.slug === defaultProcessorSlug,
        );

        setSelectedProcessor(processor);

        if (onProcessorChange) {
          onProcessorChange(processor);
        }
      }
    }
  }, [
    providers,
    defaultProviderSlug,
    selectedProvider,
    processors,
    defaultProcessorSlug,
    selectedProcessor,
    onProcessorChange,
  ]);

  return (
    <Grid item id="processorselector">
      <Grid container direction="row" gap={2} alignItems={"center"}>
        <Box
          sx={{
            minWidth: 100,
            "& .MuiSelect-outlined": {
              display: "flex",
            },
            width: isMobile ? "48%" : "auto",
          }}
        >
          <FormControl fullWidth>
            <InputLabel id="select-provider-label">Provider</InputLabel>
            <Select
              onChange={(e) => {
                setSelectedProvider(
                  providers.find((p) => p.slug === e.target.value),
                );
                setSelectedProcessor(null);
              }}
              value={
                selectedProvider ? selectedProvider.slug : defaultProviderSlug
              }
              label="Provider"
              sx={{
                "& .MuiSelect-outlined": {
                  textAlign: "center",
                  padding: "6px",
                  marginLeft: "8px",
                },
              }}
            >
              {providers
                .filter((x) => x.has_processors)
                .map((option, index) => (
                  <MenuItem key={index} value={option.slug}>
                    <ListItemIcon
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        minWidth: "24px !important",
                      }}
                    >
                      <ProviderIcon
                        providerSlug={option?.slug}
                        style={{ width: "16px", height: "16px" }}
                      />
                    </ListItemIcon>
                    <ListItemText>{option.name}</ListItemText>
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
        </Box>

        {selectedProvider && (
          <Box sx={{ minWidth: 150, width: isMobile ? "48%" : "auto" }}>
            <FormControl fullWidth>
              <InputLabel id="select-processor-label">Processor</InputLabel>
              <Select
                sx={{
                  lineHeight: "32px",
                  "& .MuiSelect-outlined": {
                    textAlign: "center",
                    padding: "6px",
                    marginLeft: "8px",
                    fontSize: "0.9rem",
                  },
                }}
                onChange={(e) => {
                  const processor = processors.find(
                    (processor) =>
                      processor.provider.slug === selectedProvider.slug &&
                      processor.slug === e.target.value,
                  );

                  if (processor) {
                    setSelectedProcessor(processor);

                    if (onProcessorChange) {
                      onProcessorChange(processor);
                    }
                  }
                }}
                value={selectedProcessor ? selectedProcessor.slug : ""}
                label="Processor"
              >
                {processors
                  .filter(
                    (x) =>
                      x.provider.slug === selectedProvider.slug &&
                      x.name !== "Promptly App",
                  )
                  .map((option, index) => (
                    <MenuItem key={index} value={option.slug}>
                      {option.name}
                    </MenuItem>
                  ))}
              </Select>
            </FormControl>
          </Box>
        )}
        {!hideDescription && (
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
                href={`https://docs.trypromptly.com/processors/${selectedProcessor?.provider?.slug}`}
                target="_blank"
                aria-label="Learn more about this Processor"
                rel="noreferrer"
              >
                <LightbulbIcon color="info" />
              </a>
              {selectedProcessor?.description ||
                "Select a processor from this provider"}
            </Typography>
          </Box>
        )}
      </Grid>
    </Grid>
  );
}
