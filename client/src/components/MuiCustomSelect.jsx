import { Autocomplete, TextField } from "@mui/material";
import { useEffect, useState } from "react";

export default function MuiCustomSelect(props) {
  const [inputValue, setInputValue] = useState(
    props.value || props?.schema?.default || "",
  );
  const [options, setOptions] = useState(
    (props?.options?.enumOptions || []).map((o) => o.value),
  );

  useEffect(() => {
    setInputValue(props.value);
  }, [props.value]);

  return (
    <Autocomplete
      options={options}
      noOptionsText="Enter to create a new option"
      getOptionLabel={(option) => {
        return option;
      }}
      defaultValue={props.value || props?.schema?.default || options[0] || ""}
      onInputChange={(e, newValue) => {
        setInputValue(newValue);
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          label="Select"
          variant="standard"
          onKeyDown={(e) => {
            if (
              e.key === "Enter" &&
              options.findIndex((o) => o === inputValue) === -1
            ) {
              setOptions((o) => o.concat(inputValue));
            }
          }}
        />
      )}
      onChange={(e, newValue) => {
        props.onChange(newValue);
      }}
    />
  );
}
