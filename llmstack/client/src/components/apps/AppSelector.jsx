import { Select, MenuItem, FormControl, InputLabel } from "@mui/material";

export function AppSelector(props) {
  return (
    <div>
      <FormControl fullWidth>
        <InputLabel id="app-select-label">Select an application</InputLabel>
        <Select
          labelId="app-select-label"
          id="app-select"
          value={props.value}
          label="Select an application"
          onChange={(event) => props.onChange(event.target.value)}
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
