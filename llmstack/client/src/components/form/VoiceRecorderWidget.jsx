import { useState } from "react";

import { IconButton, Stack, Typography, Box } from "@mui/material";
import StopCircleIcon from "@mui/icons-material/StopCircle";
import MicIcon from "@mui/icons-material/Mic";
import DeleteIcon from "@mui/icons-material/Delete";

const VoiceRecorderWidget = (props) => {
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [recordedBlob, setRecordedBlob] = useState(null);

  const handleStartRecording = async () => {
    if (recordedBlob) {
      setRecordedBlob(null);
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, {
        mimeType: "audio/webm",
      });

      recorder.addEventListener("dataavailable", (event) => {
        const audioBlob = event.data;
        setRecordedBlob(audioBlob);
        const reader = new window.FileReader();
        const name = "audio_recording.webm";
        reader.onload = (event) => {
          if (typeof event.target?.result === "string") {
            const split_data = event.target.result.split(";");
            const dataURL = `${split_data[0]};name=${name};${split_data[2]}`;
            props.onChange(dataURL);
          } else {
            props.onChange(null);
          }
        };
        reader.readAsDataURL(audioBlob);
      });

      recorder.start();
      setIsRecording(true);
      setMediaRecorder(recorder);
    } catch (error) {
      console.error("Error starting recording:", error);
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const handleClearRecording = () => {
    setRecordedBlob(null);
    props.onChange(null);
  };

  const RecordIcon = (props) => {
    return (
      <Stack direction={"column"}>
        <IconButton
          onClick={handleStartRecording}
          color="primary"
          size="small"
          variant="outlined"
        >
          <MicIcon />
        </IconButton>
        <Typography style={{ fontSize: "8px", textAlign: "center" }}>
          Start
        </Typography>
        <Typography style={{ fontSize: "8px", textAlign: "center" }}>
          Recording
        </Typography>
      </Stack>
    );
  };

  const StopIcon = (props) => {
    return (
      <Stack direction={"column"}>
        <IconButton
          onClick={handleStopRecording}
          size="small"
          aria-label="Stop recording"
          variant="outlined"
        >
          <StopCircleIcon />
        </IconButton>
        <Typography
          style={{ fontSize: "8px", textAlign: "center", color: "red" }}
        >
          Recording
        </Typography>
      </Stack>
    );
  };

  const ClearRecordingIcon = (props) => {
    return (
      <Stack direction={"column"} ml={1} mr={1}>
        <IconButton
          onClick={handleClearRecording}
          size="small"
          aria-label="Clear Recording"
          variant="outlined"
        >
          <DeleteIcon />
        </IconButton>
        <Typography style={{ fontSize: "8px", textAlign: "center" }}>
          Clear
        </Typography>
        <Typography style={{ fontSize: "8px", textAlign: "center" }}>
          Recording
        </Typography>
      </Stack>
    );
  };

  return (
    <div>
      <label>{props.label}</label>
      <div>
        {recordedBlob ? (
          <Stack direction={"row"}>
            <audio src={URL.createObjectURL(recordedBlob)} controls />
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
              }}
            >
              <ClearRecordingIcon />
              <RecordIcon />
            </Box>
          </Stack>
        ) : isRecording ? (
          <StopIcon />
        ) : (
          <RecordIcon />
        )}
      </div>
    </div>
  );
};

export default VoiceRecorderWidget;
