import { useEffect, useState } from "react";
import {
  Backdrop,
  Box,
  CircularProgress,
  IconButton,
  InputBase,
  Paper,
  TextField,
  Tooltip,
} from "@mui/material";
import AutoFixHighIcon from "@mui/icons-material/AutoFixHigh";
import { axios } from "../../data/axios";
import { enqueueSnackbar } from "notistack";

export default function DescriptionGeneratorWidget(props) {
  const { schema, onChange } = props;
  const [value, setValue] = useState(props.value);
  const [showGenerator, setShowGenerator] = useState(false);
  const [generatorPrompt, setGeneratorPrompt] = useState(
    "Generate a description from the given app version",
  );
  const [generating, setGenerating] = useState(false);
  const appPublishedUuid = schema?.appPublishedUuid;

  useEffect(() => {
    props.onChange(value);
  }, [value, props]);

  const generateDescription = (prompt) => {
    if (!prompt) {
      enqueueSnackbar("Please provide a prompt to generate a description", {
        variant: "warning",
      });
      return;
    }

    setGenerating(true);

    axios()
      .post(`/api/store/generate/description`, {
        published_uuid: appPublishedUuid,
        prompt,
        app_version: schema?.appVersion,
        categories: schema?.appCategories,
      })
      .then((response) => {
        setValue(response.data.description);
        onChange(response.data.description);
      })
      .catch((error) => {
        enqueueSnackbar(
          `Error Occurred: ${error?.response?.data?.message || error}`,
          {
            variant: "error",
          },
        );
      })
      .finally(() => {
        setShowGenerator(false);
        setGenerating(false);
      });
  };

  return (
    <Box>
      <Backdrop
        sx={{
          color: "#fff",
          position: "absolute",
        }}
        open={generating}
      >
        <CircularProgress color="inherit" />
      </Backdrop>
      <TextField
        fullWidth
        multiline
        rows={4}
        value={value}
        onFocus={() => {
          setShowGenerator(false);
        }}
        onChange={(event) => {
          setValue(event.target.value);
          event.preventDefault();
        }}
        disabled={generating}
        label={props.label || "Description"}
      />
      {!showGenerator && (
        <Tooltip title="Auto-generate description from the given app version">
          <IconButton
            type="button"
            sx={{
              p: "2px 4px",
              display: "flex",
              position: "relative",
              top: "-2.2em",
              margin: "12px",
              float: "right",
            }}
            aria-label="search"
            onClick={() => setShowGenerator(true)}
          >
            <AutoFixHighIcon />
          </IconButton>
        </Tooltip>
      )}
      {showGenerator && (
        <Paper
          sx={{
            p: "2px 4px",
            display: "flex",
            alignItems: "center",
            position: "relative",
            top: "-3.5em",
            margin: "4px",
          }}
        >
          <InputBase
            sx={{ ml: 1, flex: 1 }}
            placeholder="Instructions to generate a description"
            inputProps={{
              "aria-label": "Instructions to generate a description.",
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
                generateDescription(generatorPrompt);
              }
            }}
          />
          <IconButton
            type="button"
            sx={{ p: "10px" }}
            aria-label="search"
            onClick={() => generateDescription(generatorPrompt)}
          >
            {generating && <CircularProgress color="inherit" />}
            {!generating && <AutoFixHighIcon />}
          </IconButton>
        </Paper>
      )}
    </Box>
  );
}
