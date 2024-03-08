import { useEffect, useState } from "react";
import {
  Box,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
} from "@mui/material";
import { useRecoilValue } from "recoil";
import { appVersionsState } from "../../data/atoms";

export default function AppVersionSelector(props) {
  const { schema, onChange } = props;
  const [value, setValue] = useState(props.value);
  const appUuid = schema?.appUuid;
  const appVersions = useRecoilValue(appVersionsState(appUuid));

  useEffect(() => {
    setValue(props.value);
  }, [props.value]);

  return (
    <Box>
      <FormControl fullWidth>
        <InputLabel id="app-version-select-label">
          Select an app version
        </InputLabel>
        <Select
          labelId="app-version-select-label"
          id="app-version-select"
          value={value === undefined ? "" : value}
          label="Select an app version"
          onChange={(event) => onChange(event.target.value)}
          variant="filled"
          sx={{ lineHeight: "0.5em" }}
        >
          {appVersions
            .filter((a) => !a?.is_draft)
            .sort((a, b) => a?.version > b?.version)
            .map((appVersion) => (
              <MenuItem key={appVersion.version} value={appVersion.version}>
                <Stack direction={"row"}>{appVersion.version}</Stack>
              </MenuItem>
            ))}
        </Select>
      </FormControl>
    </Box>
  );
}
