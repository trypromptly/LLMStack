import React, { useEffect, useState } from "react";
import {
  Button,
  Collapse,
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
  Tooltip,
  Typography,
} from "@mui/material";
import moment from "moment";
import { axios } from "../data/axios";
import { useRecoilValue } from "recoil";
import { appsBriefState } from "../data/atoms";
import AddAppRunScheduleModal from "../components/schedule/AddAppRunScheduleModal";
import {
  KeyboardArrowDownOutlined,
  KeyboardArrowRightOutlined,
} from "@mui/icons-material";
import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import PauseCircleOutlinedIcon from "@mui/icons-material/PauseCircleOutlined";
import PlayCircleOutlinedIcon from "@mui/icons-material/PlayCircleOutlined";
import RefreshOutlinedIcon from "@mui/icons-material/RefreshOutlined";
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

  const runJob = () => {
    axios()
      .post(`/api/jobs/${jobId}/run`)
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
    case "run":
      return (
        <ConfirmationModal
          id="run-job"
          open={open}
          onOk={runJob}
          onCancel={onCancel}
          title="Run Job"
          text="Are you sure you want to run this job now?"
        />
      );
    default:
      return null;
  }
}

export default function Schedule() {
  const apps = useRecoilValue(appsBriefState);
  const [pageNumber, setPageNumber] = useState(1);
  const [jobs, setJobs] = useState([]);
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

  const handleExpandJob = (row) => {
    const newJobs = [...jobs];
    const index = newJobs.findIndex((job) => job.uuid === row.uuid);
    newJobs[index].expand = !newJobs[index].expand;
    setJobs(newJobs);

    if (newJobs[index].expand) {
      axios()
        .get(`/api/jobs/${row.uuid}/tasks`)
        .then((res) => {
          const newJobs = [...jobs];
          const index = newJobs.findIndex((job) => job.uuid === row.uuid);
          newJobs[index].tasks = res.data;
          setJobs(newJobs);
        });
    }
  };

  const getTaskStatusTooltip = (task) => {
    const successCount = task.result?.filter(
      (r) => r.status === "success",
    )?.length;
    const failedCount = task.result?.filter(
      (r) => r.status === "failed",
    )?.length;
    const startedCount = task.result?.filter(
      (r) => r.status === "started",
    )?.length;
    const notStartedCount = task.result?.filter(
      (r) => r.status === "not_started",
    ).length;
    const totalCount = task.result?.length;

    return (
      <div>
        <div>Total Rows: {totalCount}</div>
        {successCount && totalCount !== successCount ? (
          <div>
            <br />
            Success: {successCount}
          </div>
        ) : null}
        {failedCount ? <div>Failed: {failedCount}</div> : null}
        {startedCount ? <div>Started: {startedCount}</div> : null}
        {notStartedCount ? <div>Pending: {notStartedCount}</div> : null}
      </div>
    );
  };

  const columnData = [
    {
      title: "Name",
      key: "name",
      render: (record, row) => {
        return (
          <Typography
            sx={{
              display: "flex",
              fontSize: "0.9rem",
              fontWeight: row.expand ? "600" : "inherit",
              gap: 1,
            }}
          >
            {row.expand ? (
              <KeyboardArrowDownOutlined
                fontSize="10px"
                sx={{ color: "#999", margin: "auto 0" }}
              />
            ) : (
              <KeyboardArrowRightOutlined
                fontSize="10px"
                sx={{ color: "#999", margin: "auto 0" }}
              />
            )}
            {record}
          </Typography>
        );
      },
    },
    {
      title: "Type",
      key: "model",
      render: (record, row) => {
        const getJobTypeTitle = () => {
          switch (record) {
            case "ScheduledJob":
              return "Scheduled";
            case "RepeatableJob":
              return "Repeatable";
            case "CronJob":
              return "Cron";
            default:
              return null;
          }
        };
        const getJobCategoryTitle = () => {
          switch (row?.task_category) {
            case "app_run":
              return "App";
            case "datasource_refresh":
              return "Datasource";
            default:
              return null;
          }
        };
        return (
          <div>
            <Chip label={getJobTypeTitle()} color="secondary" size="small" />
            <Chip label={getJobCategoryTitle()} color="primary" size="small" />
          </div>
        );
      },
    },
    {
      title: "Source",
      key: "source_uuid",
      render: (record, row) => {
        return row?.task_category === "app_run" ? (
          <Button
            onClick={() => {
              window.location.href = `/apps/${record}`;
            }}
            sx={{
              textTransform: "none",
              fontWeight: "inherit",
              textAlign: "left",
            }}
          >
            {apps.find((app) => app.uuid === record)?.name}
          </Button>
        ) : null;
      },
    },
    {
      title: "Status",
      key: "enabled",
      render: (record, row) => {
        return row ? (
          <Chip label="Enabled" color="success" size="small" />
        ) : (
          <Chip label="Disabled" color="error" size="small" />
        );
      },
    },
    {
      title: "Created",
      key: "created_at",
      render: (record, row) => {
        return row?.created_at
          ? moment.utc(row?.created_at).local().format("D-MMM-YYYY h:mm:ss A")
          : null;
      },
    },
    {
      title: "Last Run",
      key: "last_run",
      render: (record, row) => {
        return row?.updated_at
          ? moment.utc(row?.updated_at).local().fromNow()
          : null;
      },
    },
    {
      title: "Action",
      key: "operation",
      render: (record, row) => {
        return (
          <Box>
            <IconButton
              onClick={() => {
                setJobId(row.uuid);
                setModalType("run");
                setModalOpen(true);
              }}
              color="primary"
            >
              <RefreshOutlinedIcon />
            </IconButton>
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
        // Create an array from scheduled_jobs, repeatable_jobs and cron_jobs properties and include the job type
        let jobs = [];

        const scheduledJobs = res.data.scheduled_jobs.map((job) => {
          return {
            ...job,
            model: "ScheduledJob",
            expand: false,
          };
        });

        const repeatableJobs = res.data.repeatable_jobs.map((job) => {
          return {
            ...job,
            model: "RepeatableJob",
            expand: false,
          };
        });

        const cronJobs = res.data.cron_jobs.map((job) => {
          return {
            ...job,
            model: "CronJob",
            expand: false,
          };
        });

        // Merge all jobs into one array and sort by created_at desc
        jobs = [...scheduledJobs, ...repeatableJobs, ...cronJobs].sort(
          (a, b) => {
            return (
              moment.utc(b.created_at).local() -
              moment.utc(a.created_at).local()
            );
          },
        );

        // Set the jobs state
        setJobs(jobs);
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
              {jobs.map((row) => {
                return [
                  <TableRow
                    key={row.uuid}
                    sx={{ cursor: "pointer", backgroundColor: "inherit" }}
                    onClick={() => {
                      if (row.task_category === "app_run") {
                        handleExpandJob(row);
                      }
                    }}
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
                  </TableRow>,
                  <TableRow key={`${row.uuid}_details`}>
                    <TableCell
                      style={{
                        paddingBottom: 0,
                        paddingTop: 0,
                        border: 0,
                      }}
                      colSpan={12}
                    >
                      <Collapse in={row.expand} timeout="auto" unmountOnExit>
                        <Box sx={{ margin: 1 }}>
                          <Table size="small" aria-label="tasks">
                            <TableHead>
                              <TableRow>
                                <TableCell>
                                  <strong>Created At</strong>
                                </TableCell>
                                <TableCell>
                                  <strong>Status</strong>
                                </TableCell>
                                <TableCell>
                                  <strong>Actions</strong>
                                </TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {row.tasks?.map((task) => {
                                return (
                                  <TableRow key={task.uuid}>
                                    <TableCell>
                                      {moment
                                        .utc(task.created_at)
                                        .local()
                                        .format("D-MMM-YYYY h:mm:ss A")}
                                    </TableCell>
                                    <TableCell>
                                      <Tooltip
                                        title={getTaskStatusTooltip(task)}
                                      >
                                        {task.status === "started" &&
                                        task.result?.filter(
                                          (r) => r.status === "success",
                                        )?.length === task.result?.length ? (
                                          <Chip
                                            label="Finished"
                                            color="success"
                                            size="small"
                                          />
                                        ) : task.status === "started" ? (
                                          <Chip
                                            label="Started"
                                            color="warning"
                                            size="small"
                                          />
                                        ) : (
                                          <Chip
                                            label="Failed"
                                            color="error"
                                            size="small"
                                          />
                                        )}
                                      </Tooltip>
                                    </TableCell>
                                    <TableCell>
                                      <Button
                                        variant="outlined"
                                        size="small"
                                        startIcon={<DownloadOutlinedIcon />}
                                        disabled={task.status === "failed"}
                                        onClick={() => {
                                          window.open(
                                            `/api/jobs/${row.uuid}/tasks/${task.uuid}/download`,
                                          );
                                        }}
                                        sx={{ textTransform: "none" }}
                                      >
                                        Download
                                      </Button>
                                    </TableCell>
                                  </TableRow>
                                );
                              })}
                            </TableBody>
                          </Table>
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>,
                ];
              })}
            </TableBody>
          </Table>
          {jobs.length > 0 && (
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
