import React, { useEffect, useRef, useState } from "react";
import { Alert, Box } from "@mui/material";

const newSession = async (processor, runProcessor) => {
  try {
    const response = await runProcessor(processor, {
      task_type: "create_session",
    });

    if (response?.task_response_json?.data?.session_id) {
      return response?.task_response_json?.data;
    }

    throw new Error("Failed to create new session");
  } catch (error) {
    // Handle or log the error as needed
    console.error(error);
    throw error; // Rethrow the error to be caught by the retry logic
  }
};

const retryWithBackoff = async (fn, maxRetries, delay) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn(); // Attempt to run the function
    } catch (error) {
      const nextDelay = delay * Math.pow(2, i); // Calculate the next delay
      console.log(`Retry ${i + 1}: waiting for ${nextDelay}ms`);
      await new Promise((resolve) => setTimeout(resolve, nextDelay)); // Wait for the delay before next retry
    }
  }
  throw new Error("Max retries reached");
};

// submit the ICE candidate
const handleICE = async (session_id, candidate, processor, runProcessor) => {
  const respose = await runProcessor(processor, {
    task_type: "submit_ice_candidate",
    task_input_json: {
      candidate,
    },
    session_id,
  });

  return respose?.task_response_json?.data;
};

const startSession = async (session_id, sdp, processor, runProcessor) => {
  const response = await runProcessor(processor, {
    task_type: "start_session",
    task_input_json: {
      sdp,
    },
    session_id,
  });

  return response?.task_response_json;
};

const closeSession = async (processor, runProcessor) => {
  await runProcessor(processor, {
    task_type: "close_session",
    task_input_json: {},
  });
};

const createNewSession = async (
  videoRef,
  sessionRef,
  processor,
  runProcessor,
) => {
  // call the new interface to get the server's offer SDP and ICE server to create a new RTCPeerConnection
  const maxRetries = 5; // Maximum number of retries
  const initialDelay = 4000; // Initial delay in milliseconds

  const sessionInfo = await retryWithBackoff(
    () => newSession(processor, runProcessor),
    maxRetries,
    initialDelay,
  );

  if (!sessionInfo) {
    console.error("Failed to create new session");
    return;
  }

  sessionRef.current = sessionInfo;
  const { sdp: serverSdp, ice_servers2: iceServers } = sessionInfo;

  // Create a new RTCPeerConnection
  const peerConnection = new RTCPeerConnection({ iceServers: iceServers });

  // When ICE candidate is available, send to the server
  peerConnection.onicecandidate = ({ candidate }) => {
    if (candidate) {
      handleICE(
        sessionInfo.session_id,
        candidate.toJSON(),
        processor,
        runProcessor,
      );
    }
  };

  // When ICE connection state changes, display the new state
  peerConnection.oniceconnectionstatechange = (event) => {
    console.log("ICE connection state changed", event);
  };

  // When audio and video streams are received, display them in the video element
  const mediaElement = videoRef.current;
  peerConnection.ontrack = (event) => {
    if (event.track.kind === "audio" || event.track.kind === "video") {
      try {
        mediaElement.srcObject = event.streams[0];
      } catch (e) {
        console.error(e);
      }
    }
  };

  // When receiving a message, display it in the status element
  peerConnection.ondatachannel = (event) => {
    const dataChannel = event.channel;
    dataChannel.onmessage = (event) => {
      mediaElement.muted = false;
      console.log("Data channel message received", event);
    };
  };

  // Set server's SDP as remote description
  const remoteDescription = new RTCSessionDescription(serverSdp);

  try {
    await peerConnection.setRemoteDescription(remoteDescription);
  } catch (e) {
    console.error(e);
  }

  // Create and set local SDP description
  const localDescription = await peerConnection.createAnswer();
  try {
    await peerConnection.setLocalDescription(localDescription);
  } catch (e) {
    console.error(e);
  }

  await new Promise((resolve) => setTimeout(resolve, 1500));

  // Start session
  await startSession(
    sessionInfo.session_id,
    localDescription,
    processor,
    runProcessor,
  );
};

const videoStyle = {
  width: "100%",
  height: "100%",
  objectFit: "cover",
};

export const HeyGenRealtimeAvatar = (props) => {
  const { processor, runProcessor } = props;
  const [error, setError] = useState(null);
  const videoRef = useRef(null);
  const sessionRef = useRef(null);
  const createSessionRef = useRef(null);

  useEffect(() => {
    if (
      processor &&
      runProcessor &&
      !sessionRef.current &&
      videoRef.current &&
      !createSessionRef.current
    ) {
      createSessionRef.current = true;

      createNewSession(videoRef, sessionRef, processor, runProcessor).catch(
        (e) => {
          setError(e);
          console.error(e);
        },
      );
    }

    return () => {
      closeSession(processor, runProcessor);
    };
  }, [processor, runProcessor]);

  return (
    <Box>
      {error && (
        <Alert severity="error">{`${error.message}. Please refresh the app.`}</Alert>
      )}
      <video ref={videoRef} autoPlay muted style={videoStyle} />
    </Box>
  );
};
