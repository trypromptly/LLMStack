import React, { useState, useMemo, useEffect } from "react";
import {
  Box,
  Select,
  MenuItem,
  Chip,
  FormControl,
  InputLabel,
  OutlinedInput,
  Typography,
  Switch,
  FormControlLabel,
} from "@mui/material";
import SimpleTextFieldWithVars from "../SimpleTextFieldWithVars";
import { SHEET_CELL_TYPE_OBJECT, SHEET_CELL_TYPE_TAGS } from "./Sheet";

const TOOLS = {
  "Web Search": {
    id: "web_search",
    name: "web_search",
    input: {},
    config: { k: 10 },
    provider_slug: "promptly",
    processor_slug: "web_search",
    description: "Search the web for information",
    llm_instructions: "",
    output_template: {
      markdown:
        "{% for result in results %}\n" +
        "{{result.text}}\n" +
        "{{result.source}}\n" +
        "{% endfor %}",
      jsonpath: "$.results[*]",
    },
  },
};

// Multiline system message field for agent
const SYSTEM_MESSAGE =
  "You are Promptly Sheets Agent a large language model. You perform tasks based on user instruction. Always follow the following Guidelines\n1.Never wrap your response in ```json <CODE_TEXT>```.\n2.Never ask user any follow up question.\n";

const AgentRunForm = ({
  setData,
  agentInstructions,
  selectedTools,
  columns,
  columnIndex,
  cellType,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [tools, setTools] = useState(selectedTools || []);

  useEffect(() => {
    if (cellType === SHEET_CELL_TYPE_OBJECT) {
      setData({
        agent_system_message:
          SYSTEM_MESSAGE + "Always respond to the user with valid JSON Object",
      });
    } else if (cellType === SHEET_CELL_TYPE_TAGS) {
      setData({
        agent_system_message:
          SYSTEM_MESSAGE +
          "Always respond to the user with comma separated string of text",
      });
    }
    setData({ agent_system_message: SYSTEM_MESSAGE });
  }, [cellType, setData]);

  const handleInstructionsChange = (newValue) => {
    setData({
      agent_instructions: newValue,
      input: { task: newValue },
    });
  };

  const handleToolsChange = (event) => {
    const selectedTools = event.target.value;
    setTools(selectedTools);
    setData({
      selected_tools: selectedTools,
      processors: selectedTools.map((tool) => TOOLS[tool]),
    });
  };

  const handleAdvancedToggle = (event) => {
    setShowAdvanced(event.target.checked);
  };

  const availableTools = Object.keys(TOOLS);

  const variables = useMemo(() => {
    return columns.slice(0, columnIndex).reduce((acc, column) => {
      acc[column.col_letter] = column.title || `{{${column.col_letter}}}`;
      return acc;
    }, {});
  }, [columns, columnIndex]);

  return (
    <Box sx={{ width: "100%" }}>
      <SimpleTextFieldWithVars
        value={agentInstructions}
        onChange={handleInstructionsChange}
        variables={variables}
        label="Agent Instructions"
        placeholder="Provide instructions to the LLM agent"
      />
      <FormControl fullWidth sx={{ mt: 2, mb: 2 }}>
        <InputLabel
          id="tools-select-label"
          sx={{ lineHeight: "14px", minHeight: "14px" }}
        >
          Tools
        </InputLabel>
        <Select
          labelId="tools-select-label"
          multiple
          value={tools}
          onChange={handleToolsChange}
          input={<OutlinedInput label="Tools" />}
          renderValue={(selected) => (
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
              {selected.map((value) => (
                <Chip key={value} label={value} />
              ))}
            </Box>
          )}
          sx={{
            "& .MuiInputBase-root": {
              "& fieldset": {
                border: "solid 1px #ccc",
                borderRadius: "8px",
                boxShadow:
                  "0px 1px 2px 0px #1018280F, 0px 1px 3px 0px #1018281A",
              },
            },
            "& .MuiSelect-select": {
              padding: "0px",
              paddingTop: "1px",
              minHeight: "36px",
            },
            "& .MuiOutlinedInput-root": {
              boxShadow: "none",
              borderRadius: "8px",
              fontSize: "12px",
              fontWeight: "600",
              color: "text.secondary",
            },
            "& .MuiOutlinedInput-notchedOutline": {
              borderRadius: "8px !important",
              boxShadow: "0px 0px 4px #e8ebee",
            },
          }}
        >
          {availableTools.map((tool) => (
            <MenuItem key={tool} value={tool}>
              <Typography variant="body1" color="text.secondary">
                {tool}
              </Typography>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <FormControlLabel
        sx={{
          ml: 0,
          mt: 2,
          "& .MuiFormControlLabel-label": {
            fontSize: "0.9rem",
            color: "text.secondary",
          },
        }}
        control={
          <Switch
            checked={showAdvanced}
            onChange={handleAdvancedToggle}
            size="small"
          />
        }
        label="Show Advanced Options"
      />
      {showAdvanced && <Box sx={{ mt: 2 }}></Box>}
    </Box>
  );
};

export default AgentRunForm;
