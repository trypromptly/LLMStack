import { useEffect, useRef, useState } from "react";
import {
  Box,
  IconButton,
  InputAdornment,
  TextField,
  Chip,
  Stack,
} from "@mui/material";
import {
  Image,
  Send,
  AttachFile,
  PictureAsPdf,
  ViewList,
  AudioFile,
  StopCircle,
  VideoFile,
} from "@mui/icons-material";
import { useRecoilValue } from "recoil";
import { appRunDataState } from "../../data/atoms";

const getFileIcon = (mimeType) => {
  if (mimeType.startsWith("image/")) {
    return <Image />;
  } else if (mimeType.startsWith("audio/")) {
    return <AudioFile />;
  } else if (mimeType.startsWith("video/")) {
    return <VideoFile />;
  } else if (mimeType === "application/pdf") {
    return <PictureAsPdf />;
  } else if (mimeType === "text/csv") {
    return <ViewList />;
  }

  return <AttachFile />;
};

const addNameToDataURL = (dataURL, name) => {
  if (dataURL === null) {
    return null;
  }
  return dataURL.replace(";base64", `;name=${encodeURIComponent(name)};base64`);
};

const processFile = (file) => {
  const { name, size, type } = file;
  return new Promise((resolve, reject) => {
    const reader = new window.FileReader();
    reader.onerror = reject;
    reader.onload = (event) => {
      if (typeof event.target?.result === "string") {
        resolve({
          data: addNameToDataURL(event.target.result, name),
          name,
          size,
          type,
        });
      } else {
        resolve({
          data: null,
          name,
          size,
          type,
        });
      }
    };
    reader.readAsDataURL(file);
  });
};

const processFiles = (files) => {
  return Promise.all(Array.from(files).map(processFile));
};

const MultiInputField = (props) => {
  const fileInputRef = useRef(null);
  const [value, setValue] = useState({});
  const [multiline, setMultiline] = useState(true);
  const [processedFiles, setProcessedFiles] = useState([]);
  const appRunData = useRecoilValue(appRunDataState);

  const handleFileSelect = (e) => {
    processFiles(e.target.files).then((files) => {
      setProcessedFiles((prevFiles) => [...prevFiles, ...files]);
    });
  };

  const handleClick = () => {
    fileInputRef.current.click();
  };

  const handleSubmit = () => {
    props.onChange(value);

    setMultiline(false);

    if (!value || !value.text?.trim() || appRunData?.isRunning) return;

    // Make sure changes are propagated before triggering the submit
    setTimeout(() => {
      props.formRef?.current?.submit();
    }, 0);

    // Clear the input field
    setValue({});
  };

  const handleCancel = () => {
    props.onChange({});
    props.onCancel();
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    } else if (event.key === "Enter" && event.shiftKey) {
      event.preventDefault();
      setMultiline(true);
      setValue((oldValue) => ({
        ...oldValue,
        text: (oldValue?.text || "") + "\n",
      }));
    }
  };

  const handleDeleteFile = (fileIndex) => {
    setProcessedFiles((prevFiles) =>
      prevFiles.filter((_, index) => index !== fileIndex),
    );
  };

  useEffect(() => {
    if (processedFiles.length > 0) {
      setValue((oldValue) => ({
        ...oldValue,
        files: processedFiles,
      }));
    }
  }, [processedFiles]);

  return (
    <Box sx={{ width: "100%" }}>
      {processedFiles.length > 0 && (
        <Stack direction="row" mb={2} sx={{ display: "block" }}>
          {processedFiles.map((file, index) => (
            <Chip
              key={index}
              icon={getFileIcon(file.type)}
              label={file.name}
              onDelete={() => handleDeleteFile(index)}
              variant="Filled"
            />
          ))}
        </Stack>
      )}
      <TextField
        value={value?.text || ""}
        label={
          props.schema?.placeholder
            ? null
            : props.schema?.label || props.schema?.title
        }
        placeholder={props.schema?.placeholder}
        helperText={props.schema?.description}
        multiline={multiline}
        maxRows={10}
        onKeyDown={handleKeyDown}
        disabled={appRunData?.isRunning}
        onChange={(e) =>
          setValue((oldValue) => ({ ...oldValue, text: e.target.value }))
        }
        sx={{
          "& .MuiInputBase-root": {
            padding: 2,
          },
          "& .MuiInputBase-input": {
            resize: "none",
          },
        }}
        fullWidth
        InputProps={{
          startAdornment: props.schema.allowFiles ? (
            <InputAdornment
              position="start"
              sx={{
                marginRight: 0,
                paddingRight: 0,
                marginBottom: 5,
                alignSelf: "flex-end",
              }}
            >
              <IconButton aria-label="files" onClick={handleClick}>
                <AttachFile />
              </IconButton>
              <input
                ref={fileInputRef}
                id="file-input"
                type="file"
                style={{ display: "none" }}
                onChange={handleFileSelect}
                accept={props.schema.filesAccept}
                multiple={props.schema.filesMultiple}
              />
            </InputAdornment>
          ) : null,
          endAdornment: (
            <InputAdornment
              position="end"
              sx={{ marginBottom: 5, alignSelf: "flex-end" }}
            >
              <IconButton
                aria-label="send"
                onClick={appRunData?.isRunning ? handleCancel : handleSubmit}
              >
                {appRunData?.isRunning ? <StopCircle /> : <Send />}
              </IconButton>
            </InputAdornment>
          ),
        }}
      />
    </Box>
  );
};

export default MultiInputField;
