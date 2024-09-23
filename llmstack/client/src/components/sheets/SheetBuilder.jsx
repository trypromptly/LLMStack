import React, { useCallback, useState, useEffect, useRef } from "react";
import { Ws } from "../../data/ws";
import { PaperAirplaneIcon } from "@heroicons/react/24/outline";

function SheetBuilder({ sheetId, open, addOrUpdateColumns, addOrUpdateCells }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const wsUrlPrefix = `${
    window.location.protocol === "https:" ? "wss" : "ws"
  }://${
    process.env.NODE_ENV === "development"
      ? process.env.REACT_APP_API_SERVER || "localhost:9000"
      : window.location.host
  }/ws`;
  const [suggestedMessages, setSuggestedMessages] = useState([]);

  const handleBuilderUpdates = useCallback(
    (updates) => {
      for (const update of updates) {
        if (update.name === "create_or_update_columns") {
          try {
            const args = JSON.parse(update.arguments);
            addOrUpdateColumns(args.columns);
          } catch (e) {
            console.error("Error adding or updating column", e, update);
          }
        } else if (update.name === "send_suggested_messages") {
          try {
            const args = JSON.parse(update.arguments);
            setSuggestedMessages(args.messages || []);
          } catch (e) {
            console.error("Error setting suggested messages", e, update);
          }
        } else if (update.name === "add_or_update_cells") {
          try {
            const args = JSON.parse(update.arguments);
            addOrUpdateCells(args.cells);
          } catch (e) {
            console.error("Error adding or updating cells", e, update);
          }
        }
      }
    },
    [addOrUpdateColumns, addOrUpdateCells],
  );

  const createWebSocketConnection = useCallback(() => {
    if (!wsRef.current) {
      wsRef.current = new Ws(`${wsUrlPrefix}/sheets/${sheetId}/builder`);
      wsRef.current.setOnMessage((event) => {
        const data = JSON.parse(event.data);
        if (data.type === "message") {
          setMessages((prevMessages) => [
            ...prevMessages,
            { role: "assistant", content: data.message },
          ]);
          setIsTyping(false);

          if (data.updates) {
            handleBuilderUpdates(data.updates);
          }
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
  }, [sheetId, wsUrlPrefix, handleBuilderUpdates]);

  useEffect(() => {
    return () => {
      // Close the connection when the component unmounts
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!open) {
      // Close the connection when open becomes false
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    }
  }, [open]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSuggestedMessageClick = (message) => {
    setSuggestedMessages([]);
    setInput(message);
    sendMessage(message);
  };

  const sendMessage = (messageToSend = input) => {
    if (messageToSend.trim()) {
      createWebSocketConnection(); // Create connection if it doesn't exist
      if (wsRef.current) {
        const message = {
          type: "message",
          message: messageToSend,
          sheet_id: sheetId,
        };
        wsRef.current.send(JSON.stringify(message));
        setMessages((prevMessages) => [
          ...prevMessages,
          { role: "user", content: messageToSend },
        ]);
        setInput("");
        setIsTyping(true);
      }
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
                <pre className="text-sm whitespace-pre-wrap font-sans text-left">
                  {message.content}
                </pre>
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex items-center justify-start">
              <div className="bg-gray-200 rounded-lg px-3 py-0">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
      <div className="relative flex flex-col items-center justify-center m-2">
        {suggestedMessages.length > 0 && (
          <div className="flex flex-wrap justify-center mb-2 space-x-2">
            {suggestedMessages.map((message, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedMessageClick(message)}
                className="px-3 py-2 mb-2 text-sm bg-blue-100 text-blue-800 rounded-md hover:bg-blue-200 transition duration-200 ease-in-out"
              >
                {message}
              </button>
            ))}
          </div>
        )}
        <div className="relative w-full">
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
            onClick={() => sendMessage()}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-blue-500 hover:text-blue-600 transition duration-200 ease-in-out"
          >
            <PaperAirplaneIcon className="h-6 w-6" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default SheetBuilder;
