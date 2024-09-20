import React, { useState, useRef, useEffect } from "react";
import {
  FormControl,
  InputLabel,
  OutlinedInput,
  Chip,
  Popper,
  Paper,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";

const SimpleTextFieldWithVars = ({
  value,
  onChange,
  variables,
  label,
  placeholder,
}) => {
  const [inputValue, setInputValue] = useState(value || "");
  const [cursorPosition, setCursorPosition] = useState(0);
  const [showVarList, setShowVarList] = useState(false);
  const inputRef = useRef(null);
  const displayRef = useRef(null);
  const popperAnchorEl = useRef(null);

  const handleInputChange = (event) => {
    const newValue = event.target.value;
    setInputValue(newValue);
    setCursorPosition(event.target.selectionStart);
    onChange(newValue);

    if (newValue[event.target.selectionStart - 1] === "@") {
      const inputRect = event.target.getBoundingClientRect();
      const atIndex = event.target.selectionStart - 1;
      const textBeforeAt = newValue.slice(0, atIndex);
      const dummySpan = document.createElement("span");
      dummySpan.style.font = window.getComputedStyle(event.target).font;
      dummySpan.style.visibility = "hidden";
      dummySpan.textContent = textBeforeAt;
      document.body.appendChild(dummySpan);

      const atOffset = dummySpan.offsetWidth;
      document.body.removeChild(dummySpan);

      // Calculate line height
      const lineHeight = parseInt(
        window.getComputedStyle(event.target).lineHeight,
      );

      popperAnchorEl.current = {
        clientWidth: 0,
        clientHeight: 0,
        getBoundingClientRect() {
          return {
            top: inputRect.top + lineHeight,
            left: inputRect.left + (atOffset % inputRect.width),
            right: inputRect.left + (atOffset % inputRect.width),
            bottom:
              inputRect.top +
              Math.floor(atOffset / inputRect.width) * lineHeight,
            width: 0,
            height: 0,
          };
        },
      };
      setShowVarList(true);
    } else {
      setShowVarList(false);
    }
  };

  // Add this new function to handle cursor position updates
  const handleSelectionChange = () => {
    if (inputRef.current) {
      setCursorPosition(inputRef.current.selectionStart);
    }
  };

  useEffect(() => {
    const inputElement = inputRef.current;
    if (inputElement) {
      inputElement.addEventListener("select", handleSelectionChange);
      inputElement.addEventListener("click", handleSelectionChange);
      inputElement.addEventListener("keyup", handleSelectionChange);
    }
    return () => {
      if (inputElement) {
        inputElement.removeEventListener("select", handleSelectionChange);
        inputElement.removeEventListener("click", handleSelectionChange);
        inputElement.removeEventListener("keyup", handleSelectionChange);
      }
    };
  }, []);

  const handleVarSelect = (varName) => {
    const before = inputValue.slice(0, cursorPosition - 1);
    const after = inputValue.slice(cursorPosition);
    const newValue = `${before}{{${varName}}}${after}`;
    setInputValue(newValue);
    setShowVarList(false);
    onChange(newValue);
  };

  useEffect(() => {
    if (inputRef.current && displayRef.current) {
      displayRef.current.scrollTop = inputRef.current.scrollTop;
    }
  }, [inputValue]);

  const renderDisplayValue = () => {
    const parts = inputValue.split(/(\{\{.*?\}\}|\n)/);
    let currentIndex = 0;
    return parts.map((part, index) => {
      if (part === "\n") {
        currentIndex += 1;
        return <br key={`br-${index}`} />;
      }
      if (part.startsWith("{{") && part.endsWith("}}")) {
        const varName = part.slice(2, -2);
        currentIndex += part.length;
        return (
          <Chip
            key={index}
            label={variables[varName]}
            size="small"
            sx={{ mx: 0.5, my: 0.25, height: "24px" }}
          />
        );
      }
      const beforeCursor = part.slice(
        0,
        Math.max(0, cursorPosition - currentIndex),
      );
      const afterCursor = part.slice(
        Math.max(0, cursorPosition - currentIndex),
      );
      currentIndex += part.length;
      return (
        <React.Fragment key={index}>
          {beforeCursor}
          {cursorPosition >= currentIndex - part.length &&
            cursorPosition <= currentIndex && (
              <span
                style={{
                  borderLeft: "1px solid black",
                  marginLeft: "-1px",
                  animation: "blink 1s step-end infinite",
                }}
              />
            )}
          {afterCursor}
        </React.Fragment>
      );
    });
  };

  return (
    <FormControl fullWidth>
      <InputLabel
        shrink
        htmlFor="rich-text-input"
        sx={{ backgroundColor: "white", px: 1, zIndex: 1000 }}
      >
        {label}
      </InputLabel>
      <div style={{ position: "relative" }}>
        <OutlinedInput
          id="rich-text-input"
          multiline
          rows={4}
          value={inputValue}
          onChange={handleInputChange}
          inputRef={inputRef}
          placeholder={placeholder}
          sx={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            opacity: 0,
            zIndex: 2,
          }}
        />
        <div
          ref={displayRef}
          style={{
            padding: "12px",
            minHeight: "96px",
            border: "1px solid #ccc",
            boxShadow: "0px 1px 2px 0px #1018280F, 0px 1px 3px 0px #1018281A",
            borderRadius: "8px",
            overflowY: "auto",
            position: "relative",
            zIndex: 1,
            pointerEvents: "none",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            "&::after": {
              content: '""',
              position: "absolute",
              left: 0,
              top: 0,
              right: 0,
              bottom: 0,
              pointerEvents: "none",
            },
          }}
        >
          {renderDisplayValue()}
        </div>
      </div>
      <Popper
        open={showVarList}
        anchorEl={popperAnchorEl.current}
        placement="bottom-start"
        modifiers={[
          {
            name: "offset",
            options: {
              offset: [0, 4],
            },
          },
        ]}
      >
        <Paper>
          <List>
            {Object.keys(variables).map((varName) => (
              <ListItem
                key={varName}
                onClick={() => handleVarSelect(varName)}
                sx={{
                  cursor: "pointer",
                  padding: "2px 12px",
                  fontSize: "10px",
                  color: "text.secondary",
                }}
              >
                <ListItemText primary={variables[varName]} />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Popper>
    </FormControl>
  );
};

export default SimpleTextFieldWithVars;
