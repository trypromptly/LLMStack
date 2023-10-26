import React from "react";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import TextField from "@mui/material/TextField";
import Stack from "@mui/material/Stack";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterMoment } from "@mui/x-date-pickers/AdapterMoment";
import moment from "moment";

import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { TimePicker } from "@mui/x-date-pickers/TimePicker";

export default function FrequencyPickerWidget(props) {
  const { onChange, id, value } = props;

  const frequency = value ? JSON.parse(value) : null;

  const handleChange = (newValue) => {
    onChange(newValue);
  };

  return (
    <div>
      <FormControl fullWidth>
        <InputLabel id={`${id}-label`}>Frequency</InputLabel>
        <Select
          labelId={`${id}-label`}
          id={id}
          label="Frequency"
          value={frequency?.type || ""}
          onChange={(event) => handleChange({ type: event.target.value })}
        >
          <MenuItem value="run_once">Run Once</MenuItem>
          <MenuItem value="repeat">Repeat</MenuItem>
          <MenuItem value="cron_job">Cron Job</MenuItem>
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
      {frequency?.type === "cron_job" && (
        <div>
          <TextField
            label="Cron Job Expression"
            value={frequency?.cron_job}
            onChange={(event) =>
              handleChange({
                ...frequency,
                type: "cron_job",
                cron_job: event.target.value,
              })
            }
          />
        </div>
      )}
    </div>
  );
}

// Rest of the code remains the same
