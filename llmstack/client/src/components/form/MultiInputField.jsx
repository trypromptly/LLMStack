import { useEffect, useRef, useState, useCallback } from "react";
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
  Keyboard,
  Mic,
  AudioFile,
  PlayCircle,
  StopCircle,
  VideoFile,
} from "@mui/icons-material";
import { useRecoilValue } from "recoil";
import { getObjStreamWs } from "../apps/renderer/utils";
import { appRunDataState } from "../../data/atoms";
import { WavRecorder } from "../../vendor/wavtools/wav_recorder.js";
import { WavRenderer } from "../../vendor/wavtools/utils.ts";
import styled from "styled-components";

const Canvas = styled.canvas`
  width: 100%;
  height: 80px;
  margin: 4px;
  background-color: #edeff77d;
  border-radius: 8px 0px 0px 8px;
`;

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
  const stream = props.schema?.stream || false;
  const inputTextAssetStream = useRef(null);
  const inputAudioAssetStream = useRef(null);
  const [inputType, setInputType] = useState(props.schema?.inputType || "text"); // "text" or "audio"
  const [isRecording, setIsRecording] = useState(false);
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const wavRecorder = useRef(null);

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

    if (!stream && (!value || !value.text?.trim() || appRunData?.isRunning))
      return;

    // Make sure changes are propagated before triggering the submit
    setTimeout(() => {
      props.formRef?.current?.submit();
    }, 0);

    // Clear the input field
    setValue({});
  };

  const handleRun = () => {
    if (stream) {
      props.onChange({
        text: value.text,
      });
      setTimeout(() => {
        props.formRef?.current?.submit();
      }, 0);
    }
  };

  const handleCancel = () => {
    props.onChange({});

    if (stream && inputTextAssetStream.current) {
      inputTextAssetStream.current.send(
        new Blob(["write\n", ""], { type: "text/plain" }),
      );
    }

    if (isRecording) {
      stopRecording();
    }

    props.onCancel();
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();

      if (stream) {
        if (appRunData?.isRunning && inputTextAssetStream.current) {
          inputTextAssetStream.current.send(
            new Blob(["write\n", value.text], { type: "text/plain" }),
          );
          props.onChange({
            text: "",
          });
        }
      } else {
        handleSubmit();
      }
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
    if (stream && appRunData?.agentInputTextStreamId) {
      inputTextAssetStream.current = getObjStreamWs(
        appRunData?.agentInputTextStreamId,
      );
    }
  }, [stream, appRunData?.agentInputTextStreamId]);

  useEffect(() => {
    if (stream && appRunData?.agentInputAudioStreamId) {
      inputAudioAssetStream.current = getObjStreamWs(
        appRunData?.agentInputAudioStreamId,
      );
    }
  }, [stream, appRunData?.agentInputAudioStreamId]);

  useEffect(() => {
    if (processedFiles.length > 0) {
      setValue((oldValue) => ({
        ...oldValue,
        files: processedFiles,
      }));
    }
  }, [processedFiles]);

  const drawVisualizer = useCallback(() => {
    if (!wavRecorder.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const canvasCtx = canvas.getContext("2d");

    const result = wavRecorder.current.recording
      ? wavRecorder.current.getFrequencies("voice")
      : { values: new Float32Array([0]) };

    // Clear the canvas before drawing
    canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

    WavRenderer.drawBars(
      canvas,
      canvasCtx,
      result.values,
      "#0099ff",
      1000,
      0,
      4,
      true,
    );

    animationRef.current = requestAnimationFrame(drawVisualizer);
  }, []);

  const startRecording = async () => {
    wavRecorder.current = new WavRecorder({ sampleRate: 24000 });
    await wavRecorder.current.begin();

    await wavRecorder.current.record((data) => {
      if (inputAudioAssetStream.current) {
        inputAudioAssetStream.current.send(
          new Blob(["write\n", data.mono], { type: "text/plain" }),
        );
      }
    });

    setIsRecording(true);

    drawVisualizer();
  };

  const stopRecording = () => {
    wavRecorder.current.end().then((result) => {
      console.log("Terminated recording");
    });
    setIsRecording(false);
  };

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
        disabled={stream !== appRunData?.isRunning}
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
        component={
          stream && inputType === "audio"
            ? () => (
                <Box
                  display="flex"
                  alignItems="center"
                  sx={{
                    boxShadow: "#ddd 1px 1px 8px",
                    borderRadius: "8px",
                    mb: 2,
                    width: "100%",
                  }}
                >
                  <Canvas ref={canvasRef} />
                  <Box m={2}>
                    <IconButton
                      onClick={isRecording ? handleCancel : startRecording}
                      color={isRecording ? "secondary" : "primary"}
                    >
                      {isRecording ? <StopCircle /> : <Mic />}
                    </IconButton>
                  </Box>
                </Box>
              )
            : "form"
        }
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
              <Box>
                {appRunData?.isRunning ? (
                  <IconButton
                    aria-label="keyboard"
                    onClick={() => {
                      if (inputType === "audio" && isRecording) {
                        stopRecording();
                      } else if (inputType === "text" && !isRecording) {
                        startRecording();
                      }

                      setInputType(inputType === "text" ? "audio" : "text");
                    }}
                  >
                    {inputType === "text" ? <Mic /> : <Keyboard />}
                  </IconButton>
                ) : null}
                <IconButton
                  aria-label="send"
                  onClick={
                    appRunData?.isRunning
                      ? handleCancel
                      : stream
                        ? handleRun
                        : handleSubmit
                  }
                >
                  {appRunData?.isRunning ? (
                    <StopCircle />
                  ) : stream ? (
                    <PlayCircle />
                  ) : (
                    <Send />
                  )}
                </IconButton>
              </Box>
            </InputAdornment>
          ),
        }}
      />
    </Box>
  );
};

export default MultiInputField;
