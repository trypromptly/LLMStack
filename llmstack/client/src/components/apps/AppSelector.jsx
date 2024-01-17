import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";

export function AppSelector(props) {
  return (
    <div>
      <FormControl fullWidth>
        <InputLabel id="app-select-label">Select an App</InputLabel>
        <Select
          labelId="app-select-label"
          id="app-select"
          value={props.value || ""}
          label="Select an application"
          onChange={(event) => props.onChange(event.target.value)}
          variant="filled"
          sx={{ lineHeight: "0.5em" }}
        >
          {props.apps.map((app) => (
            <MenuItem key={app.published_uuid} value={app.published_uuid}>
              {app.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </div>
  );
}
