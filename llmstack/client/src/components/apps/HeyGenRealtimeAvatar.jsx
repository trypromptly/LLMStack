import React, { useEffect, useRef } from "react";
import { Box } from "@mui/material";

const newSession = async (processor, runProcessor) => {
  // await new Promise((resolve) => setTimeout(resolve, 2000));

  const response = await runProcessor(processor, {
    task_type: "create_session",
  });

  if (response) {
    return response?.task_response_json?.data;
  }
  return null;
};

// submit the ICE candidate
const handleICE = async (session_id, candidate, processor, runProcessor) => {
  const respose = await runProcessor(processor, {
    task_type: "submit_ice_candidate",
    task_input_json: {
      session_id,
      candidate,
    },
  });

  return respose?.task_response_json?.data;
};

const startSession = async (session_id, sdp, processor, runProcessor) => {
  const response = await runProcessor(processor, {
    task_type: "start_session",
    task_input_json: {
      session_id,
      sdp,
    },
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
  const sessionInfo = await newSession(processor, runProcessor);

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
      createNewSession(videoRef, sessionRef, processor, runProcessor);
    }

    return () => {
      closeSession(processor, runProcessor);
    };
  }, [processor, runProcessor]);

  return (
    <Box>
      <video ref={videoRef} autoPlay style={videoStyle} />
    </Box>
  );
};
