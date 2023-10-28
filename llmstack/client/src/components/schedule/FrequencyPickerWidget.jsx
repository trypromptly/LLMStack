import React from "react";
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
} from "@mui/material";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterMoment } from "@mui/x-date-pickers/AdapterMoment";
import moment from "moment";

import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { TimePicker } from "@mui/x-date-pickers/TimePicker";

export default function FrequencyPickerWidget(props) {
  const { onChange, id, value } = props;

  const frequency = value ? JSON.parse(value) : null;

  const handleChange = (newValue) => {
    onChange(JSON.stringify(newValue));
  };

  return (
    <Box sx={{ display: "flex" }}>
      <FormControl sx={{ width: "120px" }}>
        <InputLabel id={`${id}-label`}>Frequency</InputLabel>
        <Select
          labelId={`${id}-label`}
          id={id}
          label="Frequency"
          value={frequency?.type || ""}
          onChange={(event) => handleChange({ type: event.target.value })}
          placeholder="Select a frequency"
        >
          <MenuItem value="run_once">Run Once</MenuItem>
          <MenuItem value="repeat">Repeat</MenuItem>
          <MenuItem value="cron">Cron Job</MenuItem>
        </Select>
      </FormControl>
      {frequency?.type === "run_once" && (
        <LocalizationProvider dateAdapter={AdapterMoment}>
          <DatePicker
            disablePast
            value={moment(frequency?.start_date, "YYYY-MM-DD")}
            onChange={(value) => {
              handleChange({
                ...frequency,
                type: "run_once",
                start_date: value.format("YYYY-MM-DD"),
              });
            }}
          />
          <TimePicker
            value={moment(frequency?.start_time, "HH:mm:ss")}
            onChange={(value) => {
              handleChange({
                ...frequency,
                type: "run_once",
                start_time: value.format("HH:mm:ss"),
              });
            }}
          />
        </LocalizationProvider>
      )}
      {frequency?.type === "repeat" && (
        <div>
          <LocalizationProvider dateAdapter={AdapterMoment}>
            <DatePicker
              disablePast
              value={moment(frequency?.start_date, "YYYY-MM-DD")}
              onChange={(value) => {
                handleChange({
                  ...frequency,
                  type: "repeat",
                  start_date: value.format("YYYY-MM-DD"),
                });
              }}
            />
            <TimePicker
              value={moment(frequency?.start_time, "HH:mm:ss")}
              onChange={(value) => {
                handleChange({
                  ...frequency,
                  type: "repeat",
                  start_time: value.format("HH:mm:ss"),
                });
              }}
            />
          </LocalizationProvider>
          <TextField
            label="Repeat Interval (in days)"
            value={frequency?.interval}
            type="number"
            onChange={(event) =>
              handleChange({ ...frequency, interval: event.target.value })
            }
          />
        </div>
      )}
      {frequency?.type === "cron" && (
        <TextField
          label="Cron Job Expression"
          value={frequency?.cron_expression}
          onChange={(event) =>
            handleChange({
              ...frequency,
              type: "cron",
              cron_expression: event.target.value,
            })
          }
        />
      )}
    </Box>
  );
}

// Rest of the code remains the same
