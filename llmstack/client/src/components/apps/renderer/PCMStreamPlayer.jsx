import { forwardRef, useEffect, useRef, useCallback } from "react";
import { getObjStreamWs } from "./utils";
import { WavStreamPlayer } from "../../../vendor/wavtools/wav_stream_player";
import { WavRenderer } from "../../../vendor/wavtools/utils.ts";
import { appRunDataState } from "../../../data/atoms";
import { useRecoilValue } from "recoil";
import styled from "@emotion/styled";

const Canvas = styled.canvas`
  width: 100%;
  height: 100px;
  background: #000;
  border-radius: 4px;
`;

const PCMStreamPlayer = forwardRef(
  ({ src, sampleRate = 24000, channels = 1 }, ref) => {
    const canvasRef = useRef(null);
    const wavStreamPlayerRef = useRef(null);
    const appRunData = useRecoilValue(appRunDataState);
    const animationRef = useRef(null);

    const drawVisualizer = useCallback(() => {
      if (!wavStreamPlayerRef.current || !canvasRef.current) return;

      const canvas = canvasRef.current;
      const canvasCtx = canvas.getContext("2d");

      // Clear the canvas before drawing
      canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

      if (wavStreamPlayerRef.current?.context?.state === "running") {
        try {
          const result = wavStreamPlayerRef.current.getFrequencies("voice");
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
        } catch (e) {
          console.error("Error drawing visualizer:", e);
        }
      }

      animationRef.current = requestAnimationFrame(drawVisualizer);
    }, []);

    useEffect(() => {
      if (
        appRunData?.agentInputAudioStreamStartedAt &&
        wavStreamPlayerRef.current
      ) {
        const interrupt = async () => {
          await wavStreamPlayerRef.current.interrupt();
        };
        interrupt();
      }
    }, [appRunData?.agentInputAudioStreamStartedAt]);

    useEffect(() => {
      wavStreamPlayerRef.current = new WavStreamPlayer({
        sampleRate,
      });

      const connect = async () => {
        await wavStreamPlayerRef.current.connect();
        drawVisualizer();
      };
      connect();
    }, [sampleRate, drawVisualizer]);

    useEffect(() => {
      if (src && src.startsWith("objref://")) {
        const srcStream = getObjStreamWs(src);

        if (!srcStream) return;

        srcStream.setOnMessage(async (message) => {
          const blob = message.data;
          let arrayBuffer;

          try {
            arrayBuffer = await blob.arrayBuffer();

            // If the buffer is empty, skip processing
            if (arrayBuffer.byteLength === 0) {
              console.log("Received empty buffer, skipping");
              return;
            }

            // Handle odd-length buffers by truncating to nearest even number
            const usableLength =
              arrayBuffer.byteLength - (arrayBuffer.byteLength % 2);
            if (usableLength !== arrayBuffer.byteLength) {
              console.warn(
                `Truncating buffer from ${arrayBuffer.byteLength} to ${usableLength} bytes`,
              );
            }

            wavStreamPlayerRef.current.add16BitPCM(arrayBuffer);
          } catch (e) {
            console.error("Error processing PCM data:", e);
            console.error("Blob size:", blob.size);
            if (arrayBuffer) {
              console.error("ArrayBuffer length:", arrayBuffer.byteLength);
              // Log the first few bytes for debugging
              const firstBytes = new Uint8Array(
                arrayBuffer.slice(0, Math.min(20, arrayBuffer.byteLength)),
              );
              console.error("First bytes:", Array.from(firstBytes));
            }
          }
        });

        srcStream.send(new Blob(["read"], { type: "text/plain" }));

        return () => {
          srcStream.close();
        };
      }
    }, [src]);

    return <Canvas ref={canvasRef} width="600" height="100" />;
  },
);

export default PCMStreamPlayer;
