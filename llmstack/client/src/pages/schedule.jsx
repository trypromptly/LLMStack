import React, { useEffect, useState } from "react";
import {
  Button,
  Grid,
  Pagination,
  IconButton,
  Table,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
  Box,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from "@mui/material";

import { axios } from "../data/axios";
import AddAppRunScheduleModal from "../components/schedule/AddAppRunScheduleModal";
import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import PauseCircleOutlinedIcon from "@mui/icons-material/PauseCircleOutlined";
import PlayCircleOutlinedIcon from "@mui/icons-material/PlayCircleOutlined";
import { enqueueSnackbar } from "notistack";

import SplitButton from "../components/SplitButton";

function ConfirmationModal(props) {
  const { open, onOk, onCancel, title, text } = props;
  return (
    <Dialog
      title={title ? title : "Logged Out"}
      open={open}
      onCancel={onCancel}
    >
      <DialogTitle id="delete-modal-title">{title}</DialogTitle>
      <DialogContent>
        <DialogContentText>{text}</DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button key="cancel" onClick={onCancel}>
          Cancel
        </Button>
        ,
        <Button key="submit" variant="contained" type="primary" onClick={onOk}>
          Confirm
        </Button>
        ,
      </DialogActions>
    </Dialog>
  );
}

function ActionModal({ modalType, open, onCancel, onOk, jobId }) {
  function deleteAppRunJob() {
    axios()
      .delete(`/api/jobs/${jobId}`)
      .then((res) => {
        window.location.reload();
      })
      .catch((err) => {
        enqueueSnackbar(err.message, { variant: "error" });
      })
      .finally(() => {
        onOk();
      });
  }
  function pauseAppRunJob() {
    axios()
      .post(`/api/jobs/${jobId}/pause`)
      .then((res) => {
        window.location.reload();
      })
      .catch((err) => {
        enqueueSnackbar(err.message, { variant: "error" });
      })
      .finally(() => {
        onOk();
      });
  }

  const resumeAppRunJob = () => {
    axios()
      .post(`/api/jobs/${jobId}/resume`)
      .then((res) => {
        window.location.reload();
      })
      .catch((err) => {
        enqueueSnackbar(err.message, { variant: "error" });
      })
      .finally(() => {
        onOk();
      });
  };

  switch (modalType) {
    case "delete":
      // Show a delete confirmation modal
      return (
        <ConfirmationModal
          id="delete-job"
          open={open}
          onOk={deleteAppRunJob}
          onCancel={onCancel}
          title="Delete Job"
          text="Are you sure you want to delete this job?"
        />
      );
    case "pause":
      return (
        <ConfirmationModal
          id="pause-job"
          open={open}
          onOk={pauseAppRunJob}
          onCancel={onCancel}
          title="Pause Job"
          text="Are you sure you want to pause this job?"
        />
      );
    case "resume":
      return (
        <ConfirmationModal
          id="resume-job"
          open={open}
          onOk={resumeAppRunJob}
          onCancel={onCancel}
          title="Resume Job"
          text="Are you sure you want to resume this job?"
        />
      );
    default:
      return null;
  }
}

export default function Schedule() {
  const [pageNumber, setPageNumber] = useState(1);
  const [scheduledJobs, setScheduledJobs] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [openAddAppRunScheduleModal, setOpenAddAppRunScheduleModal] =
    useState(false);

  const modalCancelCb = () => {
    setModalType(null);
    setJobId(null);
    setModalOpen(false);
  };

  const columnData = [
    {
      title: "Name",
      key: "name",
    },
    {
      title: "Type",
      key: "model",
      render: (record, row) => {
        const getJobTypeTitle = () => {
          switch (record) {
            case "ScheduledJob":
              return "Scheduled Job";
            case "RepeatableJob":
              return "Repeatable Job";
            case "CronJob":
              return "Cron Job";
            default:
              return null;
          }
        };
        const getJobCategoryTitle = () => {
          switch (row?.task_category) {
            case "app_run":
              return "Application Run";
            case "datasource_refresh":
              return "Datasource Refresh";
            default:
              return null;
          }
        };
        return (
          <div>
            <Chip label={getJobCategoryTitle()} color="primary" />
            <Chip label={getJobTypeTitle()} color="secondary" />
          </div>
        );
      },
    },
    {
      title: "Status",
      key: "enabled",
      render: (record, row) => {
        return row ? (
          <Chip label="Enabled" color="success" />
        ) : (
          <Chip label="Disabled" color="error" />
        );
      },
    },
    {
      title: "Action",
      key: "operation",
      render: (record, row) => {
        return (
          <Box>
            {row?.model !== "ScheduledJob" ? (
              row?.enabled ? (
                <IconButton
                  onClick={() => {
                    setJobId(row.uuid);
                    setModalType("pause");
                    setModalOpen(true);
                  }}
                  color="primary"
                >
                  <PauseCircleOutlinedIcon />
                </IconButton>
              ) : (
                <IconButton
                  onClick={() => {
                    setJobId(row.uuid);
                    setModalType("resume");
                    setModalOpen(true);
                  }}
                  color="primary"
                >
                  <PlayCircleOutlinedIcon />
                </IconButton>
              )
            ) : null}
            <IconButton
              onClick={() => {
                setJobId(row.uuid);
                setModalType("delete");
                setModalOpen(true);
              }}
              color="primary"
            >
              <DeleteOutlineOutlinedIcon />
            </IconButton>
          </Box>
        );
      },
    },
  ];

  useEffect(() => {
    axios()
      .get("/api/jobs")
      .then((res) => {
        setScheduledJobs(res.data);
      });
  }, []);

  return (
    <div id="schedule-page" style={{ marginBottom: "120px" }}>
      <Grid span={24} style={{ padding: "10px" }}>
        <Grid item style={{ width: "100%", padding: "15px 0px" }}>
          <SplitButton
            options={[
              {
                key: 1,
                title: "App Run Job",
                startIcon: <AddOutlinedIcon />,
                onClick: () => {
                  setOpenAddAppRunScheduleModal(true);
                },
              },
            ]}
            sx={{ float: "left", marginBottom: "10px", textTransform: "none" }}
          />
        </Grid>
        <Grid item style={{ width: "100%" }}>
          <Table stickyHeader aria-label="sticky table">
            <TableHead>
              <TableRow>
                {columnData.map((column) => {
                  return (
                    <TableCell
                      key={column.key}
                      sx={{
                        paddingLeft: column.key === "name" ? "20px" : "inherit",
                        textAlign: column.key === "name" ? "left" : "center",
                      }}
                    >
                      <strong>{column.title}</strong>
                    </TableCell>
                  );
                })}
              </TableRow>
            </TableHead>
            <TableBody>
              {scheduledJobs.map((row) => {
                return (
                  <TableRow
                    key={row.uuid}
                    sx={{ cursor: "pointer", backgroundColor: "inherit" }}
                  >
                    {columnData.map((column) => {
                      const value = row[column.key];
                      return (
                        <TableCell
                          key={column.key}
                          align={column.align}
                          sx={{
                            fontWeight: "inherit",
                            textAlign:
                              column.key === "name" ? "left" : "center",
                          }}
                        >
                          {column.render ? column.render(value, row) : value}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
          {scheduledJobs.length > 0 && (
            <Pagination
              variant="outlined"
              shape="rounded"
              page={pageNumber}
              onChange={(event, value) => {
                setPageNumber(value);
              }}
              sx={{ marginTop: 2, float: "right" }}
            />
          )}
        </Grid>
      </Grid>
      {modalOpen && (
        <ActionModal
          open={modalOpen}
          modalType={modalType}
          onCancel={modalCancelCb}
          jobId={jobId}
          onOk={modalCancelCb}
        />
      )}
      {openAddAppRunScheduleModal && (
        <AddAppRunScheduleModal
          open={openAddAppRunScheduleModal}
          onClose={() => setOpenAddAppRunScheduleModal(false)}
        />
      )}
    </div>
  );
}
