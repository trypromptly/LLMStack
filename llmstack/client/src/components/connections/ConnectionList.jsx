import { DeleteForever, EditOutlined } from "@mui/icons-material";
import {
  Alert,
  AlertTitle,
  Box,
  Chip,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import { useRecoilValue } from "recoil";
import { connectionsState } from "../../data/atoms";

const statusChipStyle = {
  width: "10px",
  height: "10px",
};

function ConnectionItem({
  connection,
  setConnection,
  setOpenConnectionModal,
  setDeleteConnectionModal,
}) {
  return (
    <TableRow>
      <TableCell>
        <Typography variant="h7">{connection.name}</Typography>
        <Typography variant="caption" sx={{ display: "block", color: "#999" }}>
          {connection.description}
        </Typography>
      </TableCell>
      <TableCell sx={{ textAlign: "center", width: "20px" }}>
        <Tooltip title={connection.status}>
          <Box>
            {connection.status === "Created" && (
              <Chip
                sx={{ ...statusChipStyle, ...{ backgroundColor: "#ccc" } }}
              />
            )}
            {connection.status === "Connecting" && (
              <Chip color="warning" sx={statusChipStyle} />
            )}
            {connection.status === "Active" && (
              <Chip color="success" sx={statusChipStyle} />
            )}
            {connection.status === "Failed" && (
              <Chip color="error" sx={statusChipStyle} />
            )}
          </Box>
        </Tooltip>
      </TableCell>
      <TableCell sx={{ width: "20px" }}>
        <IconButton
          size="small"
          onClick={() => {
            setConnection(connection);
            setOpenConnectionModal(true);
          }}
        >
          <EditOutlined />
        </IconButton>
      </TableCell>
      <TableCell sx={{ width: "20px" }}>
        <IconButton
          size="small"
          onClick={() => {
            setConnection(connection);
            setDeleteConnectionModal(true);
          }}
        >
          <DeleteForever
            sx={(theme) => ({
              color: theme.palette.error.main,
            })}
          />
        </IconButton>
      </TableCell>
    </TableRow>
  );
}

function ConnectionList({
  setConnection,
  setOpenConnectionModal,
  setDeleteConnectionModal,
}) {
  const connections = useRecoilValue(connectionsState);

  return (
    <Paper sx={{ width: "100%" }}>
      {!connections ||
        (connections.length === 0 && (
          <Alert severity="info" sx={{ textAlign: "left" }}>
            <AlertTitle>No connections found</AlertTitle>
            Add a connection using the <strong>+ Connection</strong> button
          </Alert>
        ))}
      {connections && connections.length > 0 && (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>
                  <strong>Name</strong>
                </TableCell>
                <TableCell>
                  <strong>Status</strong>
                </TableCell>
                <TableCell>
                  <strong>Edit</strong>
                </TableCell>
                <TableCell>
                  <strong>Delete</strong>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {connections.map((connection) => {
                return (
                  <ConnectionItem
                    key={connection.id}
                    connection={connection}
                    setConnection={setConnection}
                    setOpenConnectionModal={setOpenConnectionModal}
                    setDeleteConnectionModal={setDeleteConnectionModal}
                  />
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
}

export default ConnectionList;
