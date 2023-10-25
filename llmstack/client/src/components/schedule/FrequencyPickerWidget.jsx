import React from "react";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import TextField from "@mui/material/TextField";
import Stack from "@mui/material/Stack";

export default function FrequencyPickerWidget(props) {
  const { onChange, id, value } = props;

  const frequency = value ? JSON.parse(value) : null;

  console.log("frequency", frequency, value);
  const handleChange = (newValue) => {
    onChange(newValue);
  };

  return (
    <div>
      <FormControl>
        <InputLabel id={`${id}-label`}>Frequency</InputLabel>
        <Select
          labelId={`${id}-label`}
          id={id}
          value={frequency?.type || "run_once"}
          onChange={(event) => handleChange({ type: event.target.value })}
        >
          <MenuItem value="run_once">Run Once</MenuItem>
          <MenuItem value="repeat">Repeat</MenuItem>
          <MenuItem value="cron_job">Cron Job</MenuItem>
        </Select>
      </FormControl>
      {frequency?.type === "run_once" && (
        <div>
          <TextField
            type="date"
            onChange={(event) =>
              handleChange({
                type: "run_once",
                run_once: { start_date: event.target.value },
              })
            }
            variant="outlined"
          />

          <TextField
            type="time"
            onChange={(event) =>
              handleChange({ run_once: { start_time: event.target.value } })
            }
          />
        </div>
      )}
      {frequency?.type === "repeat" && (
        <div>
          <TextField
            type="date"
            onChange={(event) =>
              handleChange({
                type: "repeat",
                repeat: {
                  start_date: event.target.value,
                  repeat_interval: value.repeat.repeat_interval,
                },
              })
            }
          />
          <TextField
            type="time"
            onChange={(event) =>
              handleChange({
                type: "repeat",
                repeat: {
                  start_time: event.target.value,
                  repeat_interval: value.repeat.repeat_interval,
                },
              })
            }
          />
          <TextField
            label="Repeat Interval (in days)"
            type="number"
            onChange={(event) =>
              handleChange({
                type: "repeat",
                repeat: {
                  start_date: value.repeat.start_date,
                  start_time: value.repeat.start_time,
                  repeat_interval: event.target.value,
                },
              })
            }
          />
        </div>
      )}
      {frequency?.type === "cron_job" && (
        <div>
          <TextField
            label="Cron Job Expression"
            onChange={(event) =>
              handleChange({ type: "cron_job", cron_job: event.target.value })
            }
          />
        </div>
      )}
    </div>
  );
}

// Rest of the code remains the same
