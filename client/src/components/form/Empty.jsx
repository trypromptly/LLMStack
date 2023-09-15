import { Box, Typography } from "@mui/material";

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
      <Typography variant="h6">
        {emptyMessage ? emptyMessage : "No data available"}
      </Typography>
    </Box>
  );
}
