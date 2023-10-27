import { useEffect, useState } from "react";
import {
  Button,
  Grid,
  Divider,
  Pagination,
  IconButton,
  Table,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
  Typography,
  Box,
  Chip,
} from "@mui/material";
import { axios } from "../data/axios";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import PauseCircleOutlinedIcon from "@mui/icons-material/PauseCircleOutlined";
import { enqueueSnackbar } from "notistack";
function Modal({ scheduleType, open, handleCancelCb, handleSubmitCb }) {
  switch (scheduleType) {
    case "app":
      return null;
    default:
      return null;
  }
}

const AppRunJobsColumn = [
  {
    title: "Name",
    key: "name",
  },
  {
    title: "Type",
    key: "model",
    render: (record, row) => {
      switch (record) {
        case "ScheduledJob":
          return <Chip label="Scheduled Job" color="primary" />;
        case "RepeatableJob":
          return <Chip label="Repeatable Job" color="primary" />;
        case "CronJob":
          return <Chip label="Cron Job" color="primary" />;
        default:
          return null;
      }
    },
  },
  {
    title: "Input",
    key: "input",
    render: (record, row) => {
      return <Button>View</Button>;
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
    title: "Last Run",
    key: "last_run",
  },
  {
    title: "Action",
    key: "operation",
    render: (record, row) => {
      console.log(row);

      return (
        <Box>
          <IconButton
            onClick={() => {
              axios()
                .post(`/api/jobs/app_run/${row.uuid}/pause`)
                .then((res) => {
                  console.log(res);
                })
                .catch((err) => {
                  enqueueSnackbar(err.message, { variant: "error" });
                });
            }}
            color="primary"
          >
            <PauseCircleOutlinedIcon />
          </IconButton>
          <IconButton
            onClick={() => {
              axios()
                .delete(`/api/jobs/app_run/${row.uuid}`)
                .then((res) => {
                  console.log(res);
                })
                .catch((err) => {
                  enqueueSnackbar(err.message, { variant: "error" });
                });
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
export default function Schedule() {
  const [pageNumber, setPageNumber] = useState(1);
  const [scheduledAppRuns, setScheduledAppRuns] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState(null);

  useEffect(() => {
    axios()
      .get("/api/jobs/app_run")
      .then((res) => {
        setScheduledAppRuns(res.data);
      });
  }, []);
  return (
    <div id="schedule-page" style={{ marginBottom: "120px" }}>
      <Grid style={{ padding: "10px", width: "100%" }}>
        <Grid item style={{ width: "100%", padding: "15px 0px" }}>
          <Button
            onClick={() => {
              window.location.href = "/schedule/add_app_run";
            }}
            type="primary"
            variant="contained"
          >
            Schedule App Run
          </Button>
        </Grid>
        <Grid item>
          <Divider />
        </Grid>
        <Grid item style={{ width: "100%" }}>
          <Typography variant="h6">Scheduled App Runs</Typography>
          <Table stickyHeader aria-label="sticky table">
            <TableHead>
              <TableRow>
                {AppRunJobsColumn.map((column) => {
                  return <TableCell>{column.title}</TableCell>;
                })}
              </TableRow>
            </TableHead>
            <TableBody>
              {scheduledAppRuns.map((row) => {
                return (
                  <TableRow key={row.uuid} sx={{ cursor: "pointer" }}>
                    {AppRunJobsColumn.map((column) => {
                      const value = row[column.key];
                      return (
                        <TableCell key={column.key} align={column.align}>
                          {column.render ? column.render(value, row) : value}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
          {/* <Pagination
            variant="outlined"
            shape="rounded"
            page={pageNumber}
            onChange={(event, value) => {
              setPageNumber(value);
            }}
            sx={{ marginTop: 2, float: "right" }}
          /> */}
        </Grid>
      </Grid>
      {modalOpen && (
        <Modal
          open={modalOpen}
          scheduleType={modalType}
          handleCancelCb={() => setModalOpen(false)}
          handleSubmitCb={() => {
            setModalOpen(false);
          }}
        />
      )}
    </div>
  );
}
