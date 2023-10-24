import { useEffect, useState } from "react";
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  Container,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Pagination,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
  Stack,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from "@mui/material";

import {
  GridRowModes,
  DataGrid,
  GridToolbarContainer,
  GridActionsCellItem,
  GridRowEditStopReasons,
} from "@mui/x-data-grid";
import AddIcon from "@mui/icons-material/Add";

import {
  randomCreatedDate,
  randomTraderName,
  randomId,
  randomArrayItem,
} from "@mui/x-data-grid-generator";
import { AppSelector } from "../components/apps/AppSelector";
import { useRecoilValue } from "recoil";
import { appsState } from "../data/atoms";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

function EditToolbar(props) {
  const { setRows, setRowModesModel } = props;

  const handleClick = () => {
    const id = randomId();
    setRows((oldRows) => [...oldRows, { id, name: "", age: "", isNew: true }]);
    setRowModesModel((oldModel) => ({
      ...oldModel,
      [id]: { mode: GridRowModes.Edit, fieldToFocus: "name" },
    }));
  };

  return (
    <GridToolbarContainer>
      <Button color="primary" startIcon={<AddIcon />} onClick={handleClick}>
        Add record
      </Button>
    </GridToolbarContainer>
  );
}

function InputTable({ columnData, rowData }) {
  console.log(columnData);
  const [rows, setRows] = useState(rowData);
  const [columns, setColumns] = useState(columnData);
  const [rowModesModel, setRowModesModel] = useState({});

  const handleRowEditStop = (params, event) => {
    if (params.reason === GridRowEditStopReasons.rowFocusOut) {
      event.defaultMuiPrevented = true;
    }
  };

  const handleEditClick = (id) => () => {
    setRowModesModel({ ...rowModesModel, [id]: { mode: GridRowModes.Edit } });
  };

  const handleSaveClick = (id) => () => {
    setRowModesModel({ ...rowModesModel, [id]: { mode: GridRowModes.View } });
  };

  const handleDeleteClick = (id) => () => {
    setRows(rows.filter((row) => row.id !== id));
  };

  const handleCancelClick = (id) => () => {
    setRowModesModel({
      ...rowModesModel,
      [id]: { mode: GridRowModes.View, ignoreModifications: true },
    });

    const editedRow = rows.find((row) => row.id === id);
    if (editedRow.isNew) {
      setRows(rows.filter((row) => row.id !== id));
    }
  };

  const processRowUpdate = (newRow) => {
    const updatedRow = { ...newRow, isNew: false };
    setRows(rows.map((row) => (row.id === newRow.id ? updatedRow : row)));
    return updatedRow;
  };

  const handleRowModesModelChange = (newRowModesModel) => {
    setRowModesModel(newRowModesModel);
  };

  return (
    <Box
      sx={{
        height: 500,
        width: "100%",
        "& .actions": {
          color: "text.secondary",
        },
        "& .textPrimary": {
          color: "text.primary",
        },
      }}
    >
      <DataGrid
        rows={rows}
        columns={columns}
        editMode="row"
        rowModesModel={rowModesModel}
        onRowModesModelChange={handleRowModesModelChange}
        onRowEditStop={handleRowEditStop}
        processRowUpdate={processRowUpdate}
        slots={{
          toolbar: EditToolbar,
        }}
        slotProps={{
          toolbar: { setRows, setRowModesModel },
        }}
      />
    </Box>
  );
}

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
    if (selectedApp && columns === null) {
      const appDetail = apps.find((app) => app.published_uuid === selectedApp);

      setColumns(
        appDetail.data.input_fields.map((entry) => {
          return {
            field: entry.title,
            headerName: entry.name,
            width: entry.type === "text" ? 300 : 200,
            editable: true,
            sortable: false,
            resizable: true,
          };
        }),
      );
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
              <InputTable columnData={columns || []} rowData={[]} />
            ) : (
              <div>Please Select And App</div>
            )}
          </AccordionDetails>
        </Accordion>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancelCb}>Cancel</Button>
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
        />
      )}
    </div>
  );
}
