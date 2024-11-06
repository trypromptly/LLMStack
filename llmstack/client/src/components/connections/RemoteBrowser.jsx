import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";
import RFB from "@novnc/novnc/core/rfb";
import React from "react";
import { isMobileState } from "../../data/atoms";
import { useRecoilValue } from "recoil";
import { useCallback, useEffect, useRef, useState } from "react";

export function RemoteBrowser({ wsUrl, timeout, onClose }) {
  const screenRef = useRef(null);
  const rfbRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [open, setOpen] = useState(false);
  const [timeLeft, setTimeLeft] = useState(timeout);

  const setupRFB = useCallback(() => {
    if (screenRef.current && !rfbRef.current) {
      const credentials = wsUrl.split("@")[0].split("://")[1];

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
      <DialogTitle>
        Remote Browser - {timeLeft}s left
        <br />
        <Typography variant="caption">
          Login to your account and press DONE when you are finished.
        </Typography>
      </DialogTitle>
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

export function RemoteBrowserEmbed({ wsUrl }) {
  const screenRef = useRef(null);
  const boxRef = useRef(null);
  const rfbRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [closedConnection, setClosedConnection] = useState(false);
  const isMobile = useRecoilValue(isMobileState);

  const setupRFB = useCallback(() => {
    if (screenRef.current && !rfbRef.current) {
      const credentials = wsUrl.split("@")[0].split("://")[1];

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
        setClosedConnection(true);
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
  }, [wsUrl]);

  useEffect(() => {
    if (!wsUrl || rfbRef.current) {
      return;
    }

    // Try to setup RFB every second until it works with a timeout of 10 seconds
    let tries = 0;
    const interval = setInterval(() => {
      if (!rfbRef.current) {
        setupRFB();
        tries++;
      }

      if (tries >= 10 || rfbRef.current) {
        if (rfbRef.current && screenRef.current) {
          rfbRef.current.viewOnly = true;

          // Get width of screenRef parent and set it to the screenRef
          const width =
            isMobile || screenRef.current.clientWidth > 400
              ? screenRef.current.clientWidth
              : 400;
          screenRef.current.style.width = `${width}px`;
          screenRef.current.style.height = `${(width * 720) / 1024}px`;

          rfbRef.current.scaleViewport = true;
          rfbRef.current.showDotCursor = true;
        }
        clearInterval(interval);
      }
    }, 1000);
  }, [wsUrl, setupRFB, isMobile]);

  useEffect(() => {
    if (closedConnection && rfbRef.current) {
      screenRef.current.innerHTML = "Video stream ended";
      screenRef.current.style.height = "30px";
    }
  }, [closedConnection]);

  return (
    <Box ref={boxRef} sx={{ width: "100%" }}>
      <div ref={screenRef}></div>
      {!connected &&
        !closedConnection &&
        "Loading video stream. Make sure you have stream video option set."}
    </Box>
  );
}
