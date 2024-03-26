import { useState } from "react";
import { Autocomplete, Button, TextField } from "@mui/material";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import FormControl from "@mui/material/FormControl";
import { useRecoilValue } from "recoil";
import { connectionsState } from "../../data/atoms";
import AddConnectionModal from "./AddConnectionModal";

function ConnectionSelector(props) {
  const connectionFilters = props.schema?.filters || {};
  const connectionsFromState = useRecoilValue(connectionsState);
  const connections = connectionsFromState.filter((connection) => {
    let include = true;
    for (const [key, value] of Object.entries(connectionFilters)) {
      if (connection[key] !== value) {
        include = false;
        break;
      }
    }
    return include;
  });

  const [showAddConnectionModal, setShowAddConnectionModal] = useState(false);

  return (
    <FormControl fullWidth sx={{ display: "flex", flexFlow: "nowrap" }}>
      <Autocomplete
        id="connection-selector"
        sx={{ width: "100%" }}
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
      <Button
        onClick={() => setShowAddConnectionModal(true)}
        variant="contained"
        sx={{
          marginLeft: "5px",
          height: "40px",
          margin: "auto",
        }}
      >
        <AddCircleOutlineIcon />
      </Button>
      <AddConnectionModal
        open={showAddConnectionModal}
        connection={null}
        onCancelCb={() => {
          setShowAddConnectionModal(false);
        }}
      />
    </FormControl>
  );
}

export default ConnectionSelector;
