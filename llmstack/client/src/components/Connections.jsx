import { useState } from "react";
import ReactGA from "react-ga4";
import { Button, Stack, Typography } from "@mui/material";
import { AddOutlined } from "@mui/icons-material";
import AddConnectionModal from "./connections/AddConnectionModal";
import ConnectionList from "./connections/ConnectionList";
import DeleteConnectionModal from "./connections/DeleteConnectionModal";
import { enqueueSnackbar } from "notistack";

import "../index.css";
import { axios } from "../data/axios";
import { connectionsState } from "../data/atoms";
import { useRecoilCallback } from "recoil";

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

  const saveConnection = (conn) => {
    return new Promise((resolve, reject) => {
      if (!conn || Object.keys(conn).length === 0) {
        enqueueSnackbar("Invalid connection information provided", {
          variant: "error",
        });
        reject(new Error("Invalid connection information provided"));
        return;
      }

      if (conn.id) {
        // Update existing connection
        axios()
          .patch(`/api/connections/${conn.id}`, conn)
          .then((res) => {
            enqueueSnackbar("Connection updated successfully", {
              variant: "success",
            });
            reloadConnections();
            resolve(res.data);
          })
          .catch((err) => {
            enqueueSnackbar("Error updating connection", {
              variant: "error",
            });
            reject(err);
          });
      } else {
        // Create new connection
        axios()
          .post("/api/connections", conn)
          .then((res) => {
            enqueueSnackbar("Connection created successfully", {
              variant: "success",
            });
            reloadConnections();
            resolve(res.data);
          })
          .catch((err) => {
            console.log(err);
            enqueueSnackbar("Error creating connection", {
              variant: "error",
            });
            reject(err);
          });

        ReactGA.event({
          category: "Connections",
          action: "Create Connection",
          label: conn.connection_type_slug,
          transport: "beacon",
        });
      }
    });
  };

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
        onSaveCb={(conn) => saveConnection(conn)}
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
