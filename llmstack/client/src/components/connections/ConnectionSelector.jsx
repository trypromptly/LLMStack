import { useState } from "react";
import { Autocomplete, Button, TextField } from "@mui/material";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import FormControl from "@mui/material/FormControl";
import { useRecoilValue } from "recoil";
import { connectionsState } from "../../data/atoms";
import AddConnectionModal from "./AddConnectionModal";

/**
 * Check if the connection matches the given `filterString`.
 *
 * `filterString` is a combination of the connection attributes 'base_connection_type', 'provider_slug', and 'connection_type_slug', separated by '/'.
 * We may skip provider_slug or connection_type_slug if they are not present in the filter string.
 *
 * If the filter string is empty, the connection matches.
 * If the filter string has one part, the connection matches if the base_connection_type matches.
 * If the filter string has two parts, the connection matches if the base_connection_type and provider_slug or connection_type_slug match.
 * If the filter string has three parts, the connection matches if all three parts match.
 *
 * @param {*} connection The connection object to check.
 * @param {*} filterString The filter string to match against.
 * @returns {boolean} True if the connection matches the filter string, false otherwise.
 */
function hasMatchingConnectionFilter(connection, filterString) {
  if (!filterString) {
    // If the filter string is empty, return true.
    return true;
  }

  // Split the filter string by '/' to get each part.
  const parts = filterString.split("/");

  // Check the number of parts to determine which pattern we're matching against.
  // Then compare each part with the corresponding object attribute.
  const isMatch = parts.every((part, index) => {
    switch (index) {
      case 0:
        return part === connection.base_connection_type;
      case 1:
        return (
          part === connection.provider_slug ||
          part === connection.connection_type_slug
        );
      case 2:
        return part === connection.connection_type_slug;
      default:
        return false;
    }
  });

  return isMatch;
}

function ConnectionSelector(props) {
  const connectionFilters = props.schema?.filters || [];
  const connectionsFromState = useRecoilValue(connectionsState);

  const connections = connectionsFromState.filter((connection) =>
    connectionFilters.some((filter) =>
      hasMatchingConnectionFilter(connection, filter),
    ),
  );

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
