import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Pagination,
  Table,
  TableBody,
  TableHead,
  Typography,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from "@mui/material";

import { AppSelector } from "../components/apps/AppSelector";
import InputDataTable from "../components/schedule/InputDataTable";
import { useRecoilValue } from "recoil";
import { appsState } from "../data/atoms";
import { axios } from "../data/axios";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

function AddAppRunScheduleModal({
  open,
  handleCancelCb,
  scheduleAddedCb,
  modalTitle = "Add New Schedule",
}) {
  const [selectedApp, setSelectedApp] = useState(null);
  const apps = (useRecoilValue(appsState) || []).filter(
    (app) => app.published_uuid,
  );
  const [columns, setColumns] = useState(null);

  useEffect(() => {
    if (selectedApp) {
      const appDetail = apps.find((app) => app.published_uuid === selectedApp);
      const columnFields = appDetail.data.input_fields.map((entry) => {
        return {
          field: entry.name,
          headerName: entry.title,
          width: entry.type === "text" ? 300 : 200,
          disableColumnMenu: true,
          sortable: false,
          editable: true,
        };
      });

      setColumns(columnFields);
    }
  }, [selectedApp]);

  return (
    <Dialog open={open} onClose={handleCancelCb} fullScreen>
      <DialogTitle>{modalTitle}</DialogTitle>
      <DialogContent>
        <Accordion defaultExpanded>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="panel1a-content"
            id="panel1a-header"
          >
            <Typography>Select Application</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box>
              <AppSelector
                apps={apps}
                value={selectedApp}
                onChange={(appId) => {
                  setSelectedApp(appId);
                }}
              />
            </Box>
          </AccordionDetails>
        </Accordion>
        <Accordion defaultExpanded>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="panel1a-content"
            id="panel1a-header"
          >
            <Typography>Input</Typography>
          </AccordionSummary>
          <AccordionDetails>
            {selectedApp ? (
              <InputDataTable columnData={columns || []} rowData={[]} />
            ) : (
              <div>Please Select And App</div>
            )}
          </AccordionDetails>
        </Accordion>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancelCb}>Cancel</Button>
        <Button
          onClick={() => {
            scheduleAddedCb(selectedApp);
          }}
        >
          Submit
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function Modal({
  scheduleType,
  open,
  handleCancelCb,
  scheduleAddedCb,
  modalTitle,
}) {
  switch (scheduleType) {
    case "app":
      return (
        <AddAppRunScheduleModal
          open={open}
          handleCancelCb={handleCancelCb}
          scheduleAddedCb={scheduleAddedCb}
          modalTitle=""
        />
      );
  }
}

export default function Schedule() {
  const entriesPerPage = 10;
  const [pageNumber, setPageNumber] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [scheduleJobType, setScheduleJobType] = useState(null);

  return (
    <div id="schedule-page" style={{ marginBottom: "120px" }}>
      <Grid span={24} style={{ padding: "10px" }}>
        <Grid item style={{ width: "100%", padding: "15px 0px" }}>
          <Button
            onClick={() => {
              setScheduleJobType("app");
              setModalOpen(true);
            }}
            type="primary"
            variant="contained"
            sx={{ float: "left", marginBottom: "10px", textTransform: "none" }}
          >
            Schedule App Run
          </Button>
        </Grid>
        <Grid item style={{ width: "100%" }}>
          <Table stickyHeader aria-label="sticky table">
            <TableHead></TableHead>
            <TableBody></TableBody>
          </Table>
          <Pagination
            variant="outlined"
            shape="rounded"
            page={pageNumber}
            onChange={(event, value) => {
              setPageNumber(value);
            }}
            sx={{ marginTop: 2, float: "right" }}
          />
        </Grid>
      </Grid>
      {modalOpen && (
        <Modal
          open={modalOpen}
          scheduleType={scheduleJobType}
          handleCancelCb={() => setModalOpen(false)}
          scheduleAddedCb={(appId) => {
            axios()
              .post("/api/jobs/app_run", {
                app_id: "1",
              })
              .then((res) => {
                console.log(res);
              })
              .catch((err) => {
                console.log(err);
              });
            setModalOpen(false);
          }}
        />
      )}
    </div>
  );
}
