import { useRecoilValue } from "recoil";
import { connectionsState } from "../../data/atoms";
import { Autocomplete, TextField } from "@mui/material";
import FormControl from "@mui/material/FormControl";

function ConnectionSelector(props) {
  const connections = useRecoilValue(connectionsState);

  return (
    <FormControl fullWidth>
      <Autocomplete
        id="connection-selector"
        options={connections}
        getOptionLabel={(option) => {
          const connection = connections.find(
            (connection) => connection.id === option,
          );

          return connection
            ? connection.name
            : option.name
            ? option.name
            : option;
        }}
        isOptionEqualToValue={(option, value) => {
          return (
            option && value && (option.id === value.id || option.id === value)
          );
        }}
        value={props.value}
        renderInput={(params) => (
          <TextField
            {...params}
            variant="outlined"
            label="Connections"
            placeholder="Connections"
          />
        )}
        onChange={(event, value) => {
          props.onChange(value?.id);
        }}
      />
    </FormControl>
  );
}

export default ConnectionSelector;
