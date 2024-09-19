import {
  Autocomplete,
  Box,
  FormControl,
  Grid,
  InputLabel,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Select,
  TextField,
  Typography,
  Stack,
  Tooltip,
} from "@mui/material";
import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { useRecoilValue } from "recoil";
import { processorsState, providersState, isMobileState } from "../data/atoms";
import { ProviderIcon } from "./apps/ProviderIcon";

export default function ProcessorSelector({
  onProcessorChange,
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
                  padding: "4px",
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
          <Box
            sx={{
              width: isMobile ? "48%" : "auto",
              flexGrow: 1,
            }}
          >
            <FormControl fullWidth>
              <Autocomplete
                clearIcon={false}
                id="processor-autocomplete"
                options={processors.filter(
                  (x) =>
                    x.provider.slug === selectedProvider.slug &&
                    x.name !== "Promptly App",
                )}
                getOptionLabel={(option) => option.description}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Processor"
                    sx={{
                      "& .MuiInputBase-root": {
                        textAlign: "center",
                        padding: "8px 10px !important",
                        marginLeft: "8px",
                        fontSize: "0.7rem",
                        color: "text.secondary",
                      },
                      "& .MuiInputBase-root.MuiOutlinedInput-root": {
                        border: "solid 1px #ccc",
                      },
                    }}
                    InputProps={{
                      ...params.InputProps,
                      startAdornment: selectedProcessor && (
                        <Box
                          component="span"
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            ml: 1,
                          }}
                        >
                          <Link
                            to={`https://docs.trypromptly.com/processors/${selectedProcessor?.provider?.slug}#${selectedProcessor?.slug}`}
                            target="_blank"
                            aria-label="Learn more about this Processor"
                            rel="noreferrer"
                          >
                            <Typography variant="body1" color="text.primary">
                              {selectedProcessor.name}
                            </Typography>
                          </Link>
                        </Box>
                      ),
                    }}
                  />
                )}
                onChange={(event, newValue) => {
                  if (newValue) {
                    setSelectedProcessor(newValue);
                    if (onProcessorChange) {
                      onProcessorChange(newValue);
                    }
                  }
                }}
                value={selectedProcessor}
                renderOption={(props, option) => (
                  <li {...props}>
                    <Stack spacing={0}>
                      <Typography
                        variant="body1"
                        sx={{ fontWeight: "bold", fontSize: "0.9rem" }}
                      >
                        {option.name}
                      </Typography>
                      <Tooltip
                        title={option.description}
                        disableHoverListener={option.description.length <= 50}
                      >
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{
                            textOverflow: "ellipsis",
                            overflow: "hidden",
                            whiteSpace: "nowrap",
                            maxWidth: "250px",
                          }}
                        >
                          {option.description}
                        </Typography>
                      </Tooltip>
                    </Stack>
                  </li>
                )}
                filterOptions={(options, { inputValue }) => {
                  return options.filter(
                    (option) =>
                      option.name
                        .toLowerCase()
                        .includes(inputValue.toLowerCase()) ||
                      option.description
                        .toLowerCase()
                        .includes(inputValue.toLowerCase()),
                  );
                }}
                sx={{
                  "& .MuiSelect-outlined": {
                    textAlign: "center",
                    padding: "6px",
                    marginLeft: "8px",
                    fontSize: "0.9rem",
                  },
                  "& .MuiInputBase-root": {
                    paddingRight: "30px !important",
                    paddingLeft: "12px !important",
                    fontSize: "0.9rem",
                    borderRadius: "8px",
                    marginLeft: "0px !important",
                    width: "100%",
                  },
                  "& .MuiFormLabel-root": {
                    marginLeft: "-5px",
                    backgroundColor: "white",
                    padding: "0px 8px",
                  },
                  "& .MuiOutlinedInput-notchedOutline": {
                    border: "none !important",
                  },
                }}
              />
            </FormControl>
          </Box>
        )}
      </Grid>
    </Grid>
  );
}
