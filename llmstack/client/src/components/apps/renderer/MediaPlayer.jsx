import { forwardRef, useEffect, useRef, useState } from "react";
import { getObjStreamWs } from "./utils";

const StreamingAudioPlayer = forwardRef(({ src, autoPlay }, ref) => {
  return (
    <audio
      controls
      style={{ display: "block" }}
      src={src}
      ref={ref}
      autoPlay={autoPlay}
    >
      {" "}
    </audio>
  );
});

const StreamingVideoPlayer = forwardRef(({ src, autoPlay }, ref) => {
  return (
    <video
      controls
      style={{
        display: "block",
        maxWidth: "100%",
        boxShadow: "0px 0px 10px 1px #7d7d7d",
      }}
      src={src}
      ref={ref}
      autoPlay={autoPlay}
    >
      Unable to load video
    </video>
  );
});

function getMediaSource() {
  if (window.MediaSource) {
    return new MediaSource();
  }

  if (window.ManagedMediaSource) {
    return new window.ManagedMediaSource();
  }

  console.error("MediaSource API is not supported in this browser.");

  return null;
}

function MediaPlayer(props) {
  const { src, mimeType, streaming, autoPlay } = props;
  const mediaRef = useRef(null);
  const mediaSource = useRef(new getMediaSource());
  const sourceBufferRef = useRef(null);
  const bufferQueue = useRef([]);
  const [isSourceBufferReady, setIsSourceBufferReady] = useState(false);

  const appendBufferFromQueue = () => {
    if (bufferQueue.current.length === 0) return;

    const arrayBuffer = bufferQueue.current.shift();

    if (arrayBuffer) {
      if (sourceBufferRef.current.updating) {
        bufferQueue.current.unshift(arrayBuffer);
        return;
      }

      if (arrayBuffer.byteLength === 0) {
        // End of stream. Close the media source
        mediaSource.current.endOfStream();
      } else {
        sourceBufferRef.current.appendBuffer(arrayBuffer);
      }
    }
  };

  useEffect(() => {
    // Initialization logic
    const media = mediaRef.current;

    if (streaming) {
      media.src = URL.createObjectURL(mediaSource.current);
    } else if (src && !src.startsWith("objref://")) {
      media.src = src;
    }

    media.addEventListener("error", (e) => {
      console.error("Media error:", media.error);
    });

    mediaSource.current.addEventListener("sourceopen", () => {
      if (!sourceBufferRef.current) {
        sourceBufferRef.current = mediaSource.current.addSourceBuffer(mimeType);
        sourceBufferRef.current.addEventListener("error", (e) => {
          console.error("SourceBuffer error:", e);
        });
        sourceBufferRef.current.addEventListener("updateend", (e) => {
          console.debug("SourceBuffer Update end", e);
          appendBufferFromQueue();
        });
        sourceBufferRef.current.addEventListener("updatestart", (e) => {
          console.debug("SourceBuffer Update start", e);
        });
        sourceBufferRef.current.addEventListener("abort", (e) => {
          console.debug("SourceBuffer aborted", e);
        });
        sourceBufferRef.current.addEventListener("update", (e) => {
          console.debug("SourceBuffer Updated", e);
        });
        setIsSourceBufferReady(true);
      }
    });
  }, [mimeType, src, streaming]);

  useEffect(() => {
    if (
      src &&
      src.startsWith("objref://") &&
      streaming &&
      isSourceBufferReady
    ) {
      const srcStream = getObjStreamWs(src);

      if (!srcStream) {
        return;
      }

      srcStream.setOnMessage(async (message) => {
        // Get the blob data from the message and append to the media source buffer
        const blob = message.data;
        try {
          const arrayBuffer = await blob.arrayBuffer();
          bufferQueue.current.push(arrayBuffer);
          appendBufferFromQueue();
        } catch (e) {
          console.error("Error appending blob to source buffer", e);
        }
      });

      // Send a binary blob "read" to the server to start streaming
      srcStream.send(new Blob(["read"], { type: "text/plain" }));
    }
  }, [streaming, src, mimeType, isSourceBufferReady]);

  if (mimeType.startsWith("audio")) {
    return <StreamingAudioPlayer ref={mediaRef} autoPlay={autoPlay} />;
  }

  if (mimeType.startsWith("video")) {
    return <StreamingVideoPlayer ref={mediaRef} autoPlay={autoPlay} />;
  }

  return null;
}

export default MediaPlayer;
