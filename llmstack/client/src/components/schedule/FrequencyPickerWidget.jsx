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

import { DateTimePicker, DatePicker } from "@mui/x-date-pickers";

export default function FrequencyPickerWidget(props) {
  const { onChange, id, value, minStartTime, maxStartTime } = props;

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
          <DateTimePicker
            minDateTime={minStartTime}
            maxDateTime={maxStartTime}
            timeSteps={{ minutes: 15 }}
            disablePast
            value={moment(
              `${frequency?.start_date} ${frequency?.start_time}`,
              "YYYY-MM-DD HH:mm:ss",
            )}
            onChange={(value) => {
              handleChange({
                ...frequency,
                type: "run_once",
                start_date: value.format("YYYY-MM-DD"),
                start_time: value.format("HH:mm:ss"),
              });
            }}
            label="Schedule Time"
          />
        </LocalizationProvider>
      )}
      {frequency?.type === "repeat" && (
        <div>
          <LocalizationProvider dateAdapter={AdapterMoment}>
            <DateTimePicker
              minDateTime={minStartTime}
              maxDateTime={maxStartTime}
              timeSteps={{ minutes: 15 }}
              disablePast
              value={moment(
                `${frequency?.start_date} ${frequency?.start_time}`,
                "YYYY-MM-DD HH:mm:ss",
              )}
              onChange={(value) => {
                handleChange({
                  ...frequency,
                  type: "repeat",
                  start_date: value.format("YYYY-MM-DD"),
                  start_time: value.format("HH:mm:ss"),
                });
              }}
              label="Schedule Start Time"
            />
            <TextField
              label="Repeat Interval (in days)"
              value={frequency?.interval}
              type="number"
              onChange={(event) =>
                handleChange({ ...frequency, interval: event.target.value })
              }
            />
            <DatePicker
              disablePast
              value={moment(frequency?.end_date, "YYYY-MM-DD")}
              onChange={(value) => {
                handleChange({
                  ...frequency,
                  type: "run_once",
                  end_date: value.format("YYYY-MM-DD"),
                });
              }}
              label="Schedule End Date"
            />
          </LocalizationProvider>
        </div>
      )}
      {frequency?.type === "cron" && (
        <LocalizationProvider dateAdapter={AdapterMoment}>
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
          <DatePicker
            disablePast
            value={moment(frequency?.end_date, "YYYY-MM-DD")}
            onChange={(value) => {
              handleChange({
                ...frequency,
                type: "run_once",
                end_date: value.format("YYYY-MM-DD"),
              });
            }}
            label="Schedule End Date"
          />
        </LocalizationProvider>
      )}
    </Box>
  );
}

// Rest of the code remains the same
