import { useEffect, useState } from "react";
import {
  Button,
  Grid,
  Divider,
  Pagination,
  Table,
  TableBody,
  TableHead,
  Typography,
} from "@mui/material";

function Modal({ scheduleType, open, handleCancelCb, handleSubmitCb }) {
  switch (scheduleType) {
    case "app":
      return null;
    default:
      return null;
  }
}

export default function Schedule() {
  const [pageNumber, setPageNumber] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState(null);

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
            <TableHead></TableHead>
            <TableBody></TableBody>
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
