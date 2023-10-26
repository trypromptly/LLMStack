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
          value={frequency?.type || ""}
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
            value={frequency?.start_date}
            type="date"
            onChange={(event) =>
              handleChange({
                ...frequency,
                type: "run_once",
                start_date: event.target.value,
              })
            }
            variant="outlined"
          />

          <TextField
            type="time"
            value={frequency?.start_time}
            onChange={(event) =>
              handleChange({
                ...frequency,
                type: "run_once",
                start_time: event.target.value,
              })
            }
          />
        </div>
      )}
      {frequency?.type === "repeat" && (
        <div>
          <TextField
            type="date"
            value={frequency?.start_date}
            onChange={(event) =>
              handleChange({
                ...frequency,
                type: "repeat",
                start_date: event.target.value,
              })
            }
          />
          <TextField
            type="time"
            value={frequency?.start_time}
            onChange={(event) =>
              handleChange({
                ...frequency,
                start_time: event.target.value,
              })
            }
          />
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
