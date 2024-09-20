import React, { useState, useEffect, useRef } from "react";
import { Ws } from "../../data/ws";
import { PaperAirplaneIcon } from "@heroicons/react/24/outline";

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
      wsRef.current?.close();
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

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-[90vh] max-h-screen bg-gray-100">
      <div className="flex-grow flex flex-col overflow-hidden">
        <div className="flex-grow overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[70%] rounded-lg p-3 ${
                  message.role === "user"
                    ? "bg-blue-900 text-white"
                    : "bg-white text-gray-800"
                }`}
              >
                <pre className="text-sm whitespace-pre-wrap font-sans">
                  {message.content}
                </pre>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>
      <div className="relative flex items-center justify-center m-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          className="w-full px-4 py-3 pr-12 border border-blue-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-800 resize-none overflow-hidden"
          placeholder="Type your message..."
          rows={1}
          style={{ minHeight: "44px", maxHeight: "120px" }}
        />
        <button
          onClick={sendMessage}
          className="absolute right-3 bottom-1/2 transform translate-y-1/2 text-blue-500 hover:text-blue-600 transition duration-200 ease-in-out"
        >
          <PaperAirplaneIcon className="h-6 w-6" />
        </button>
      </div>
    </div>
  );
}

export default SheetBuilder;
