import React, { useState, useEffect, useRef } from "react";
import { Box, TextField, Button, Typography, Paper } from "@mui/material";
import { Ws } from "../../data/ws";

function SheetBuilder({ sheetId, open }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const wsUrlPrefix = `${
    window.location.protocol === "https:" ? "wss" : "ws"
  }://${
    process.env.NODE_ENV === "development"
      ? process.env.REACT_APP_API_SERVER || "localhost:9000"
      : window.location.host
  }/ws`;

  useEffect(() => {
    if (open && !wsRef.current) {
      wsRef.current = new Ws(`${wsUrlPrefix}/sheets/${sheetId}/builder`);
      wsRef.current.setOnMessage((event) => {
        const data = JSON.parse(event.data);
        if (data.type === "message") {
          setMessages((prevMessages) => [
            ...prevMessages,
            { role: "assistant", content: data.message },
          ]);
        }
      });

      wsRef.current.setOnClose(() => {
        console.log("WebSocket connection closed");
        wsRef.current = null;
      });

      wsRef.current.send(
        JSON.stringify({
          type: "connect",
          sheet_id: sheetId,
        }),
      );
    }

    if (!open) {
      wsRef.current.close();
    }
  }, [sheetId, wsUrlPrefix, open]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = () => {
    if (input.trim() && wsRef.current) {
      const message = {
        type: "message",
        message: input,
        sheet_id: sheetId,
      };
      wsRef.current.send(JSON.stringify(message));
      setMessages((prevMessages) => [
        ...prevMessages,
        { role: "user", content: input },
      ]);
      setInput("");
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "90vh",
        maxHeight: "100vh",
      }}
    >
      <Box
        sx={{
          flexGrow: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            flexGrow: 1,
            overflowY: "auto",
            p: 2,
          }}
        >
          {messages.map((message, index) => (
            <Paper
              key={index}
              sx={{
                p: 1,
                mb: 1,
                textAlign: message.role === "user" ? "right" : "left",
                bgcolor: message.role === "user" ? "#e3f2fd" : "#f5f5f5",
              }}
            >
              <Typography variant="body1">{message.content}</Typography>
            </Paper>
          ))}
          <div ref={messagesEndRef} />
        </Box>
      </Box>
      <Box sx={{ p: 2, borderTop: "1px solid #e0e0e0" }}>
        <TextField
          fullWidth
          variant="outlined"
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            if (e.key === "Enter") {
              sendMessage();
            }
          }}
          placeholder="Type your message..."
        />
        <Button variant="contained" onClick={sendMessage} sx={{ mt: 1 }}>
          Send
        </Button>
      </Box>
    </Box>
  );
}

export default SheetBuilder;
