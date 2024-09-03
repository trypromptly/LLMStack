import { useEffect, useState } from "react";
import {
  Backdrop,
  Box,
  CircularProgress,
  IconButton,
  InputBase,
  Paper,
  Tooltip,
  Typography,
  TextField,
} from "@mui/material";
import AutoFixHighIcon from "@mui/icons-material/AutoFixHigh";
import { enqueueSnackbar } from "notistack";
import { axios } from "../../data/axios";

export default function DataTransformerGeneratorWidget(props) {
  const { onChange, disableGenerator, helpText } = props;
  const [value, setValue] = useState(props.value);
  const [generatorPrompt, setGeneratorPrompt] = useState(
    "Generate a Liquid.js template for data transformation",
  );
  const [generating, setGenerating] = useState(false);
  const [showGeneratorInput, setShowGeneratorInput] = useState(false);

  useEffect(() => {
    setValue(props.value);
  }, [props.value]);

  const generateTemplate = (prompt) => {
    if (!prompt) {
      enqueueSnackbar("Please provide instructions for the template", {
        variant: "warning",
      });
      return;
    }

    setGenerating(true);

    axios()
      .post(`/api/sheets/data_transformation/generate`, {
        prompt,
      })
      .then((response) => {
        setValue(response.data?.template || "");
        onChange(response.data?.template || "");
      })
      .catch((error) => {
        console.error(
          `Error Occurred: ${error?.response?.data?.message || error}`,
        );
      })
      .finally(() => {
        setGenerating(false);
      });
  };

  const handleTextFieldFocus = () => {
    setShowGeneratorInput(false);
  };

  return (
    <Box sx={{ position: "relative" }}>
      <Backdrop
        sx={{
          color: "#fff",
          position: "absolute",
        }}
        open={generating}
      >
        <CircularProgress color="inherit" />
      </Backdrop>
      <Box sx={{ position: "relative" }}>
        <TextField
          multiline
          fullWidth
          rows={4}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            onChange(e.target.value);
          }}
          onFocus={handleTextFieldFocus}
          placeholder="Enter your Liquid.js template here or use the generator to create one."
          variant="outlined"
          sx={{
            "& .MuiOutlinedInput-root": {
              "& fieldset": {
                borderColor: "#d0d0d0",
              },
              "&:hover fieldset": {
                borderColor: "#666",
              },
            },
          }}
        />
        {!disableGenerator && (
          <Box
            sx={{
              position: "absolute",
              bottom: 8,
              right: 8,
              left: 8,
              zIndex: 1,
            }}
          >
            {!showGeneratorInput ? (
              <Tooltip title="Auto-generate Liquid.js template for data transformation">
                <IconButton
                  type="button"
                  sx={{
                    float: "right",
                  }}
                  aria-label="generate"
                  onClick={() => setShowGeneratorInput(true)}
                >
                  <AutoFixHighIcon />
                </IconButton>
              </Tooltip>
            ) : (
              <Paper
                sx={{
                  p: "2px 4px",
                  display: "flex",
                  alignItems: "center",
                  width: "100%",
                  backgroundColor: "rgba(255, 255, 255, 0.9)",
                }}
              >
                <InputBase
                  sx={{ ml: 1, flex: 1 }}
                  placeholder="Instructions to generate the Liquid.js template"
                  inputProps={{
                    "aria-label":
                      "Instructions to generate the Liquid.js template",
                  }}
                  value={generatorPrompt}
                  onChange={(e) => {
                    setGeneratorPrompt(e.target.value);
                  }}
                  onFocus={(e) => {
                    setGeneratorPrompt("");
                  }}
                  disabled={generating}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      generateTemplate(generatorPrompt);
                    }
                  }}
                />
                <IconButton
                  type="button"
                  sx={{ p: "10px" }}
                  aria-label="generate"
                  onClick={() => generateTemplate(generatorPrompt)}
                >
                  {generating ? (
                    <CircularProgress size={24} color="inherit" />
                  ) : (
                    <AutoFixHighIcon />
                  )}
                </IconButton>
              </Paper>
            )}
          </Box>
        )}
      </Box>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ mt: 1, display: "block" }}
      >
        {helpText}
      </Typography>
    </Box>
  );
}
