import React, { useRef, useCallback, useEffect, useState } from "react";
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from "@mui/material";
import RFB from "@novnc/novnc/core/rfb";

function RemoteBrowser({ wsUrl, timeout, onClose }) {
  const screenRef = useRef(null);
  const rfbRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [open, setOpen] = useState(false);
  const [timeLeft, setTimeLeft] = useState(timeout);

  const setupRFB = useCallback(() => {
    if (screenRef.current && !rfbRef.current) {
      const credentials = wsUrl.split("@")[0].split("://")[1];
      console.log(credentials);

      rfbRef.current = new RFB(screenRef.current, wsUrl, {
        credentials: {
          username: credentials.split(":")[0],
          password: credentials.split(":")[1],
        },
        scaleViewport: true,
      });

      rfbRef.current.addEventListener("connect", () => {
        console.log("Connected");
        setConnected(true);
      });

      rfbRef.current.addEventListener("disconnect", () => {
        setConnected(false);
        setOpen(false);
        onClose();
      });

      rfbRef.current.addEventListener("credentialsrequired", () => {
        console.log("Credentials required");
      });

      rfbRef.current.addEventListener("securityfailure", () => {
        console.log("Security failure");
      });

      rfbRef.current.addEventListener("capabilities", () => {
        console.log("Capabilities");
      });

      rfbRef.current.addEventListener("clipboard", (e) => {
        if (e.detail.text) {
          navigator.clipboard.writeText(e.detail.text);
        }
      });

      rfbRef.current.addEventListener("bell", () => {
        console.log("Bell");
      });

      rfbRef.current.addEventListener("desktopname", () => {
        console.log("Desktop name");
      });

      rfbRef.current.addEventListener("resize", () => {
        console.log("Resize");
      });

      rfbRef.current.addEventListener("focus", () => {
        console.log("Focus");
      });

      rfbRef.current.addEventListener("blur", () => {
        console.log("Blur");
      });
    }
  }, [wsUrl, onClose]);

  useEffect(() => {
    if (!wsUrl || !timeout || rfbRef.current) {
      return;
    }

    setOpen(true);

    // Try to setup RFB every second until it works with a timeout of 10 seconds
    let tries = 0;
    const interval = setInterval(() => {
      if (!rfbRef.current) {
        setupRFB();
        tries++;
      }

      if (tries >= 10 || rfbRef.current) {
        clearInterval(interval);
      }
    }, 1000);
  }, [wsUrl, timeout, setupRFB]);

  useEffect(() => {
    if (timeout && onClose && connected) {
      setTimeout(() => {
        setOpen(false);
        onClose();
      }, timeout * 1000);
    }
  }, [timeout, onClose, connected]);

  useEffect(() => {
    if (timeout && timeLeft > 0) {
      setTimeout(() => {
        if (rfbRef.current) {
          setTimeLeft(timeLeft - 1);
        }
      }, 1000);
    }
  }, [timeout, timeLeft]);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullWidth
      PaperProps={{
        style: {
          minWidth: "1070px",
          overflow: "scroll",
        },
      }}
    >
      <DialogTitle>Remote Browser - {timeLeft}s left</DialogTitle>
      <DialogContent>
        <div ref={screenRef}></div>
        {!connected && "Connecting..."}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => onClose()} variant="contained">
          Done
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default RemoteBrowser;
