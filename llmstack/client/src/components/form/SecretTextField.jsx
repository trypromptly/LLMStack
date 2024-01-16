// A wrapper over TextField component to show secret field
import { Visibility, VisibilityOff } from "@mui/icons-material";
import { IconButton, InputAdornment, TextField } from "@mui/material";
import { useState } from "react";

const SecretTextField = (props) => {
  const [showSecret, setShowSecret] = useState(false);

  return (
    <TextField
      {...props}
      type={showSecret ? "text" : "password"}
      onChange={(e) => props.onChange(e.target.value)}
      InputProps={{
        endAdornment: (
          <InputAdornment position="end">
            <IconButton
              onClick={() => setShowSecret(!showSecret)}
              aria-label="toggle secret visibility"
            >
              {showSecret ? (
                <Visibility fontSize="small" />
              ) : (
                <VisibilityOff fontSize="small" />
              )}
            </IconButton>
          </InputAdornment>
        ),
      }}
    />
  );
};

export default SecretTextField;
