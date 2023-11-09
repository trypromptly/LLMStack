import React, { useRef, useEffect, useState } from "react";
import { useRecoilValue } from "recoil";
import { get } from "lodash";
import { streamChunksState } from "../../data/atoms";

function StreamingVideoPlayer({ streamKey, messageId }) {
  const videoRef = useRef(null);
  const sourceBufferRef = useRef(null);
  const mediaSource = useRef(new MediaSource());
  const [isSourceBufferReady, setIsSourceBufferReady] = useState(false);
  const isVideoSrcSet = useRef(false); // New ref to track if video's src is set
  const streamChunks = useRecoilValue(streamChunksState);
  const chunks = get(
    streamChunks,
    messageId ? `${messageId}.${streamKey}` : streamKey,
    [],
  );
  const [chunksProcessed, setChunksProcessed] = useState(0);

  useEffect(() => {
    // Initialization logic
    const video = videoRef.current;

    if (!isVideoSrcSet.current) {
      video.src = URL.createObjectURL(mediaSource.current);
      isVideoSrcSet.current = true;
    }

    videoRef.current.addEventListener("error", (e) => {
      console.error("Video error:", videoRef.current.error);
    });

    function sourceOpen() {
      if (!sourceBufferRef.current) {
        sourceBufferRef.current = mediaSource.current.addSourceBuffer(
          "video/mp4; codecs=avc1.64001e",
        );
        sourceBufferRef.current.addEventListener("error", (e) => {
          console.error("SourceBuffer error:", e);
        });
        sourceBufferRef.current.addEventListener("updateend", (e) => {
          console.debug("SourceBuffer Update end", e);
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
    }

    mediaSource.current.addEventListener("sourceopen", sourceOpen);
  }, [chunksProcessed]);

  useEffect(() => {
    if (!isSourceBufferReady || !sourceBufferRef.current || chunks.length === 0)
      return;

    let currentChunkIndex = chunksProcessed;

    function updateSourceBuffer() {
      if (sourceBufferRef.current.updating) return;
      if (currentChunkIndex >= chunks.length) return;

      const base64String = chunks[currentChunkIndex];
      const uint8Array = base64ToArrayBuffer(base64String);
      try {
        sourceBufferRef.current.appendBuffer(uint8Array);
        currentChunkIndex += 1;
        setChunksProcessed(currentChunkIndex);
      } catch (e) {
        console.error(e);
      }

      console.debug(
        "Current chunk index",
        currentChunkIndex,
        uint8Array,
        sourceBufferRef.current,
        mediaSource.current.readyState,
        sourceBufferRef.current.buffered,
      );
    }

    sourceBufferRef.current.addEventListener("updateend", updateSourceBuffer);
    updateSourceBuffer();

    return () => {
      sourceBufferRef.current.removeEventListener(
        "updateend",
        updateSourceBuffer,
      );
    };
  }, [chunks, isSourceBufferReady, chunksProcessed]);

  function base64ToArrayBuffer(base64) {
    const binaryString = atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  }

  return chunks ? (
    <video ref={videoRef} autoPlay width={"100%"} controls />
  ) : null;
}

export default StreamingVideoPlayer;
