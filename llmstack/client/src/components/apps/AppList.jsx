import { useState } from "react";
import {
  Alert,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Paper,
  TablePagination,
} from "@mui/material";
import { axios } from "../../data/axios";
import { useNavigate } from "react-router-dom";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import AppVisibilityIcon from "./AppVisibilityIcon";
import { useRecoilValue } from "recoil";
import { appsBriefState } from "../../data/atoms";

const DeleteUnpublishedAppModal = ({ open, setOpen, appId }) => {
  const [deleteValue, setDeleteValue] = useState("");

  const handleClose = () => {
    setOpen(false);
  };

  const deleteApp = () => {
    axios()
      .delete(`/api/apps/${appId}`)
      .then((response) => {
        setOpen(false);
        window.location.reload();
      });
  };

  return (
    <div>
      <Dialog
        open={open}
        onClose={handleClose}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">{"Delete App"}</DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            <Alert severity="warning">
              Are you sure you want to delete this app? This action cannot be
              undone.
            </Alert>
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            id="name"
            label="DELETE"
            placeholder="Type DELETE to confirm"
            type="text"
            fullWidth
            variant="standard"
            value={deleteValue}
            required={true}
            onChange={(e) => setDeleteValue(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button
            onClick={handleClose}
            variant="outlined"
            style={{ textTransform: "none" }}
          >
            Cancel
          </Button>
          <Button
            onClick={deleteApp}
            variant="contained"
            style={{ textTransform: "none" }}
            disabled={deleteValue !== "DELETE"}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

const DeletePublishedAppAlert = ({ open, setOpen }) => {
  const handleClose = () => {
    setOpen(false);
  };

  return (
    <div>
      <Dialog
        open={open}
        onClose={handleClose}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">
          {"Failed to Delete App"}
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            <Alert severity="error">
              You cannot delete a published app. Please unpublish the app first.
            </Alert>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={handleClose}
            variant="contained"
            style={{ textTransform: "none" }}
          >
            Okay
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export function AppList() {
  const [page, setPage] = useState(0);
  const apps = useRecoilValue(appsBriefState);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [openDeletePublishedAppAlert, setOpenDeletePublishedAppAlert] =
    useState(false);
  const [openDeleteUnpublishedAppModal, setOpenDeleteUnpublishedAppModal] =
    useState(false);
  const [appIdToDelete, setAppIdToDelete] = useState("");

  const navigate = useNavigate();

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Paper sx={{ width: "100%" }}>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: "#f0f7ff" }}>
              <TableCell sx={{ padding: "3px 16px" }}>App Name</TableCell>
              <TableCell sx={{ padding: "3px 16px", textAlign: "center" }}>
                App Type
              </TableCell>
              <TableCell sx={{ padding: "3px 16px", textAlign: "center" }}>
                Visibility
              </TableCell>
              <TableCell sx={{ padding: "3px 16px" }}>Processors</TableCell>
              <TableCell sx={{ padding: "3px 16px" }}>Delete</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {apps
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((row) => (
                <TableRow
                  key={row.uuid}
                  hover
                  onClick={() => navigate(`/apps/${row.uuid}`)}
                  sx={{
                    cursor: "pointer",
                  }}
                >
                  <TableCell>{row.name}</TableCell>
                  <TableCell sx={{ textAlign: "center" }}>
                    {row.app_type_name}
                  </TableCell>
                  <TableCell sx={{ textAlign: "center" }}>
                    <AppVisibilityIcon
                      visibility={row.visibility}
                      published={row.is_published}
                    />
                  </TableCell>
                  <TableCell style={{ maxWidth: "100px" }}>
                    {row.unique_processors?.map((x) => (
                      <Chip key={x} label={x} size="small" />
                    ))}
                  </TableCell>
                  <TableCell>
                    <DeleteForeverIcon
                      sx={(theme) => ({
                        color: row.is_published
                          ? "#ccc"
                          : theme.palette.error.main,
                      })}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (row.is_published) {
                          setOpenDeletePublishedAppAlert(true);
                        } else {
                          setAppIdToDelete(row.uuid);
                          setOpenDeleteUnpublishedAppModal(true);
                        }
                      }}
                    />
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[10, 25, 50]}
        component="div"
        count={apps.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
      <DeletePublishedAppAlert
        open={openDeletePublishedAppAlert}
        setOpen={setOpenDeletePublishedAppAlert}
      />
      <DeleteUnpublishedAppModal
        open={openDeleteUnpublishedAppModal}
        setOpen={setOpenDeleteUnpublishedAppModal}
        appId={appIdToDelete}
      />
    </Paper>
  );
}
