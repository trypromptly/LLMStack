import { TextField, MenuItem } from "@mui/material";

export function AppSelector(props) {
  return (
    <div style={{ width: "100%", display: "flex" }}>
      <TextField
        select
        style={{
          width: "auto",
          textAlign: "left",
          borderColor: "#000",
        }}
        value={props.value}
        label="Select a promptly app"
        onChange={(event) => props.onChange(event.target.value)}
        variant="outlined"
      >
        {props.apps.map((app) => (
          <MenuItem key={app.published_uuid} value={app.published_uuid}>
            {app.name}
          </MenuItem>
        ))}
      </TextField>
    </div>
  );
}
