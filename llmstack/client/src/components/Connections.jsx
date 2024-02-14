import { AddOutlined } from "@mui/icons-material";
import { Button, Stack, Typography } from "@mui/material";
import { enqueueSnackbar } from "notistack";
import { useState } from "react";
import { useRecoilCallback } from "recoil";
import { connectionsState } from "../data/atoms";
import { axios } from "../data/axios";
import "../index.css";
import AddConnectionModal from "./connections/AddConnectionModal";
import ConnectionList from "./connections/ConnectionList";
import DeleteConnectionModal from "./connections/DeleteConnectionModal";

function Connections() {
  const [openConnectionModal, setOpenConnectionModal] = useState(false);
  const [deleteConnectionModal, setDeleteConnectionModal] = useState(false);
  const [connection, setConnection] = useState(null);

  const reloadConnections = useRecoilCallback(({ set }) => () => {
    axios()
      .get("/api/connections")
      .then((res) => {
        set(connectionsState, res.data);
      })
      .catch((err) => {
        enqueueSnackbar("Error loading connections", {
          variant: "error",
        });
      });
  });

  const deleteConnection = (conn) => {
    return new Promise((resolve, reject) => {
      if (!conn || !conn.id) {
        enqueueSnackbar("Invalid connection information provided", {
          variant: "error",
        });
        reject(new Error("Invalid connection information provided"));
        return;
      }

      axios()
        .delete(`/api/connections/${conn.id}`)
        .then((res) => {
          enqueueSnackbar("Connection deleted successfully", {
            variant: "success",
          });
          reloadConnections();
          resolve(res.data);
        })
        .catch((err) => {
          console.log(err);
          enqueueSnackbar("Error deleting connection", {
            variant: "error",
          });
          reject(err);
        });
    });
  };

  return (
    <Stack>
      <Typography variant="h6" className="section-header">
        Connections
      </Typography>
      <Button
        startIcon={<AddOutlined />}
        variant="contained"
        sx={{
          textTransform: "none",
          margin: "10px",
          marginLeft: "auto",
          marginRight: 0,
        }}
        onClick={() => {
          setConnection(null);
          setOpenConnectionModal(true);
        }}
      >
        Connection
      </Button>
      <ConnectionList
        setConnection={setConnection}
        setOpenConnectionModal={setOpenConnectionModal}
        setDeleteConnectionModal={setDeleteConnectionModal}
      />
      <AddConnectionModal
        open={openConnectionModal}
        connection={connection}
        onCancelCb={() => {
          setOpenConnectionModal(false);
          setConnection(null);
        }}
      />
      <DeleteConnectionModal
        open={deleteConnectionModal}
        onCancelCb={() => setDeleteConnectionModal(false)}
        onDeleteCb={(conn) => deleteConnection(conn)}
        connection={connection}
      />
    </Stack>
  );
}

export default Connections;
