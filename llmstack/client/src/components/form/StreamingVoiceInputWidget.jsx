import DeleteIcon from "@mui/icons-material/Delete";
import MicIcon from "@mui/icons-material/Mic";
import StopIcon from "@mui/icons-material/Stop";
import { IconButton, Box, Typography } from "@mui/material";
import { useEffect, useState, useRef, useCallback } from "react";
import { useRecoilValue } from "recoil";
import { appRunDataState } from "../../data/atoms";
import { getObjStreamWs } from "../apps/renderer/utils";
import styled from "styled-components";

const Canvas = styled.canvas`
  width: 100%;
  height: 80px;
  margin: 4px;
  background-color: #edeff77d;
  border-radius: 8px 0px 0px 8px;
`;

const Timer = styled.div`
  font-size: 14px;
  color: #183a58;
  text-align: center;
  margin-top: 10px;
`;

const StreamingVoiceInputWidget = (props) => {
  const { createAsset, formRef, onChange } = props;
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const appRunData = useRecoilValue(appRunDataState);
  const [assetId, setAssetId] = useState(null);
  const [asset, setAsset] = useState(null);
  const assetStream = useRef(null);
  const dataFetcher = useRef(null);
  const bufferQueue = useRef([]);
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const audioContext = useRef(null);
  const audioAnalyserNode = useRef(null);
  const audioSource = useRef(null);
  const [timer, setTimer] = useState(0);
  const timerRef = useRef(null);

  const startTimer = () => {
    timerRef.current = setInterval(() => {
      setTimer((prev) => prev + 1);
    }, 1000);
  };

  const stopTimer = () => {
    clearInterval(timerRef.current);
    timerRef.current = null;
    setTimer(0);
  };

  const processBufferQueue = async () => {
    if (assetStream.current && bufferQueue.current.length > 0) {
      const chunk = bufferQueue.current.shift();
      assetStream.current.send(
        new Blob(["write\n", chunk], { type: "text/plain" }),
      );
    }
  };

  const drawVisualizer = useCallback(() => {
    if (!audioAnalyserNode.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const canvasCtx = canvas.getContext("2d");
    const bufferLength = audioAnalyserNode.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    audioAnalyserNode.current.getByteTimeDomainData(dataArray);

    canvasCtx.fillStyle = "#edeff77d";
    canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

    canvasCtx.lineWidth = 2;
    canvasCtx.strokeStyle = "#183a5833";

    canvasCtx.beginPath();

    const sliceWidth = (canvas.width * 1.0) / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * canvas.height) / 4;

      if (i === 0) {
        canvasCtx.moveTo(x, y);
      } else {
        canvasCtx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    canvasCtx.lineTo(canvas.width, canvas.height / 2);
    canvasCtx.stroke();

    animationRef.current = requestAnimationFrame(drawVisualizer);
  }, []);

  useEffect(() => {
    if (isRecording && !assetId && createAsset) {
      const id = Math.random().toString(36).substring(7);
      setAssetId(id);

      // Create a streaming asset
      createAsset(id, `${id}.webm`, "audio/webm", true);
    }

    if (
      assetId &&
      appRunData &&
      appRunData?.assets &&
      appRunData?.assets[assetId]
    ) {
      setAsset(appRunData?.assets[assetId]);

      // Connect to the asset to stream data
      if (!assetStream.current) {
        assetStream.current = getObjStreamWs(appRunData?.assets[assetId]);

        onChange(appRunData?.assets[assetId]);

        // Submit the form if the form ref is available
        if (formRef.current) {
          setTimeout(() => {
            formRef.current.submit();
          }, 0);
        }
      }
    }

    if (canvasRef.current) {
      const canvas = canvasRef.current;
      const canvasCtx = canvas.getContext("2d");

      // Adjust for high-DPI displays
      const dpr = window.devicePixelRatio || 1;
      canvas.width = canvas.offsetWidth * dpr;
      canvas.height = canvas.offsetHeight * dpr;
      canvasCtx.scale(dpr, dpr);

      canvasCtx.font = "16px Lato";
      canvasCtx.fillStyle = "#bbb";
      canvasCtx.textAlign = "center";
      canvasCtx.textBaseline = "middle";
      canvasCtx.fillText(
        "Please click on the microphone to start recording.",
        canvas.offsetWidth / 2,
        canvas.offsetHeight / 2,
      );
    }
  }, [assetId, appRunData, createAsset, formRef, isRecording, onChange]);

  useEffect(() => {
    if (asset && mediaRecorder) {
      // Request data from the media recorder every 1 second. Terminate the interval when the media recorder stops.
      if (!dataFetcher.current) {
        dataFetcher.current = setInterval(async () => {
          try {
            await mediaRecorder.requestData();
          } catch (error) {
            console.error("Error requesting data from media recorder:", error);
          }
        }, 1000);
      }

      if (!isRecording) {
        clearInterval(dataFetcher.current);
      }

      return () => {
        clearInterval(dataFetcher.current);
      };
    }
  }, [asset, mediaRecorder, isRecording]);

  const handleStartRecording = async () => {
    if (recordedBlob) {
      setRecordedBlob(null);
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!audioContext.current) {
        audioContext.current = new (window.AudioContext ||
          window.webkitAudioContext)();
        audioAnalyserNode.current = audioContext.current.createAnalyser();
        audioAnalyserNode.current.fftSize = 2048;
        drawVisualizer();
      }

      audioSource.current =
        audioContext.current.createMediaStreamSource(stream);
      audioSource.current.connect(audioAnalyserNode.current);

      const recorder = new MediaRecorder(stream, {
        mimeType: "audio/webm",
      });

      // Read data as it becomes available
      recorder.addEventListener("dataavailable", (event) => {
        event.data.arrayBuffer().then((buffer) => {
          bufferQueue.current.push(buffer);
          processBufferQueue();
        });
      });

      recorder.addEventListener("stop", () => {
        stream.getTracks().forEach((track) => track.stop());
        cancelAnimationFrame(animationRef.current);
      });

      recorder.start();
      setIsRecording(true);
      setMediaRecorder(recorder);
      startTimer();
    } catch (error) {
      console.error("Error starting recording:", error);
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      setIsRecording(false);
      stopTimer();

      if (assetStream.current) {
        assetStream.current.send(
          new Blob(["write\n", ""], { type: "text/plain" }),
        );
      }
      cancelAnimationFrame(animationRef.current);
    }
  };

  const handleClearRecording = () => {
    setRecordedBlob(null);
    props.onChange(null);
  };

  return (
    <Box>
      <Box
        display="flex"
        alignItems="center"
        sx={{ boxShadow: "#ddd 1px 1px 8px", borderRadius: "8px" }}
      >
        <Canvas ref={canvasRef} />
        <Box m={2}>
          {isRecording ? (
            <IconButton onClick={handleStopRecording} color="secondary">
              <StopIcon />
            </IconButton>
          ) : (
            <IconButton onClick={handleStartRecording} color="primary">
              <MicIcon />
            </IconButton>
          )}
          <Timer>{`${String(Math.floor(timer / 60)).padStart(2, "0")}:${String(
            timer % 60,
          ).padStart(2, "0")}`}</Timer>
        </Box>
      </Box>
      {recordedBlob && (
        <Box display="flex" alignItems="center" justifyContent="center" mt={2}>
          <audio src={URL.createObjectURL(recordedBlob)} controls />
          <ClearRecordingIcon onClearRecording={handleClearRecording} />
        </Box>
      )}
    </Box>
  );
};

const ClearRecordingIcon = ({ onClearRecording }) => {
  return (
    <Box
      ml={1}
      mr={1}
      display="flex"
      flexDirection="column"
      alignItems="center"
    >
      <IconButton
        onClick={onClearRecording}
        size="small"
        aria-label="Clear Recording"
        variant="outlined"
      >
        <DeleteIcon />
      </IconButton>
      <Typography style={{ fontSize: "8px", textAlign: "center" }}>
        Clear Recording
      </Typography>
    </Box>
  );
};

export default StreamingVoiceInputWidget;
