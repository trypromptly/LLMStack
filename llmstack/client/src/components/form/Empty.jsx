import { Alert, Box } from "@mui/material";

export function Empty({ emptyImage, emptyMessage, ...props }) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      height="100%"
      color="#838383"
    >
      {emptyImage ? emptyImage : null}
      <Alert severity="info" style={{ marginTop: "10px" }}>
        {emptyMessage ? emptyMessage : "No data available"}
      </Alert>
    </Box>
  );
}
