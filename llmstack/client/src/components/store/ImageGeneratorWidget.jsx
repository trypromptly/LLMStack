import { useEffect, useMemo, useState } from "react";
import {
  Backdrop,
  Box,
  CircularProgress,
  IconButton,
  InputBase,
  Paper,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import AutoFixHighIcon from "@mui/icons-material/AutoFixHigh";
import { useDropzone } from "react-dropzone";
import { enqueueSnackbar } from "notistack";
import { axios } from "../../data/axios";

const baseStyle = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  padding: "20px",
  borderWidth: 2,
  borderRadius: 2,
  borderColor: "#eeeeee",
  borderStyle: "dashed",
  backgroundColor: "#fafafa",
  color: "#bdbdbd",
  outline: "none",
  transition: "border .24s ease-in-out",
};

const focusedStyle = {
  borderColor: "#2196f3",
};

const acceptStyle = {
  borderColor: "#00e676",
};

const rejectStyle = {
  borderColor: "#ff1744",
};

export default function ImageGeneratorWidget(props) {
  const { schema, onChange, disableGenerator } = props;
  const [value, setValue] = useState(props.value);
  const [showGenerator, setShowGenerator] = useState(false);
  const [generatorPrompt, setGeneratorPrompt] = useState(
    "Generate an image from the given app version",
  );
  const [generating, setGenerating] = useState(false);
  const { getRootProps, getInputProps, isFocused, isDragAccept, isDragReject } =
    useDropzone({
      accept: {
        "image/*": [".png", ".jpg", ".jpeg"],
      },
      onDrop: (acceptedFiles) => {
        const file = acceptedFiles[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (e) => {
            if (typeof e.target?.result !== "string") {
              return;
            }

            // Add name to the dataURL
            const dataURL = e.target.result.replace(
              ";base64",
              `;name=${encodeURIComponent(file.name)};base64`,
            );
            setValue(dataURL);
            onChange(dataURL);
          };
          reader.readAsDataURL(file);
        }
      },
      maxSize: 2000000,
      maxFiles: 1,
    });

  const appPublishedUuid = schema?.appPublishedUuid;

  const style = useMemo(
    () => ({
      ...baseStyle,
      ...(isFocused ? focusedStyle : {}),
      ...(isDragAccept ? acceptStyle : {}),
      ...(isDragReject ? rejectStyle : {}),
    }),
    [isFocused, isDragAccept, isDragReject],
  );

  useEffect(() => {
    setValue(props.value);
  }, [props.value]);

  const generateImage = (prompt) => {
    if (!prompt) {
      enqueueSnackbar("Please provide a instructions for the image", {
        variant: "warning",
      });
      return;
    }

    setGenerating(true);

    axios()
      .post(`/api/store/generate/image`, {
        published_uuid: appPublishedUuid,
        prompt,
        app_version: schema?.appVersion,
        categories: schema?.appCategories,
        description: schema?.appDescription,
      })
      .then((response) => {
        setValue(response.data.image);
        onChange(response.data.image);
      })
      .catch((error) => {
        alert(`Error Occurred: ${error?.response?.data?.message || error}`);
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
      <Stack
        direction={"row"}
        sx={{
          cursor: "pointer",
          border: "1px solid #d0d0d0",
          "&:hover": {
            boxShadow: "0 0 0 1px #666",
          },
          borderRadius: 1,
        }}
        width={1}
      >
        {value && (
          <img
            src={value}
            alt="Icon"
            style={{
              width: "100px",
              height: "100px",
              margin: "1em 0.5em",
              borderRadius: 1,
            }}
          />
        )}
        <Box {...getRootProps({ style })}>
          <input {...getInputProps()} multiple={false} />
          <Box
            sx={{
              display: "flex",
              height: "100%",
              alignItems: "center",
            }}
          >
            <Typography>
              Drag 'n' drop your image here. Maximum file size allowed is 2MB.
            </Typography>
          </Box>
        </Box>
      </Stack>
      {!disableGenerator && !showGenerator && (
        <Tooltip title="Auto-generate app image from the given app and description">
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
            placeholder="Instructions to generate the image"
            inputProps={{
              "aria-label": "Instructions to generate the image.",
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
                generateImage(generatorPrompt);
              }
            }}
          />
          <IconButton
            type="button"
            sx={{ p: "10px" }}
            aria-label="search"
            onClick={() => generateImage(generatorPrompt)}
          >
            {generating && <CircularProgress color="inherit" />}
            {!generating && <AutoFixHighIcon />}
          </IconButton>
        </Paper>
      )}
    </Box>
  );
}
