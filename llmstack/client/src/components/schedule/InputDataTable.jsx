import { useState, useRef, useEffect } from "react";
import { Box, Button } from "@mui/material";
import {
  GridRowModes,
  DataGrid,
  GridToolbarContainer,
  GridActionsCellItem,
  GridRowEditStopReasons,
  GridToolbarExport,
} from "@mui/x-data-grid";
import { randomId } from "@mui/x-data-grid-generator";
import { usePapaParse } from "react-papaparse";

import {
  UploadFile,
  AddOutlined,
  EditOutlined,
  DeleteOutlined,
  SaveOutlined,
  CancelOutlined,
} from "@mui/icons-material";

import { enqueueSnackbar } from "notistack";

export default function InputDataTable({ columnData, rowData, onChange }) {
  const { readString } = usePapaParse();

  const [rowModesModel, setRowModesModel] = useState({});
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);

  useEffect(() => {
    if (file) {
      const reader = new FileReader();

      reader.onload = (event) => {
        const fileContent = event.target.result;
        readString(fileContent, {
          header: true,
          worker: true,
          complete: (results) => {
            if (results.data.length === 0) {
              enqueueSnackbar("No data found in file", {
                variant: "warning",
              });
              return;
            }
            const headers = Object.keys(results.data[0]);

            if (headers.length !== columnData.length) {
              enqueueSnackbar("Headers do not match expected headers", {
                variant: "error",
              });
              return;
            }
            headers.forEach((header) => {
              if (!columnData.find((column) => column.headerName === header)) {
                enqueueSnackbar("Headers do not match expected headers", {
                  variant: "error",
                });
                return;
              }
            });
            const newRows = [];
            for (let i = 0; i < results.data.length; i++) {
              const row = results.data[i];
              if (Object.keys(row).length !== headers.length) {
                continue;
              }
              const newRow = { id: i, isNew: true };
              columnData.forEach((column) => {
                newRow[column.field] = row[column.headerName];
              });
              newRows.push(newRow);
            }
            onChange(newRows);
          },
        });
      };

      reader.readAsText(file);
    }
  }, [file]);

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
    onChange(rowData.filter((row) => row.id !== id));
  };

  const handleCancelClick = (id) => () => {
    setRowModesModel({
      ...rowModesModel,
      [id]: { mode: GridRowModes.View, ignoreModifications: true },
    });

    const editedRow = rowData.find((row) => row.id === id);

    if (editedRow.isNew) {
      onChange(rowData.filter((row) => row.id !== id));
    }
  };

  const handleFileUpload = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (event) => {
    const uploadedFile = event.target.files[0];
    setFile(uploadedFile);
  };

  const processRowUpdate = (newRow) => {
    const updatedRow = { ...newRow, isNew: false };

    onChange(rowData.map((row) => (row.id === newRow.id ? updatedRow : row)));

    return updatedRow;
  };

  const handleRowModesModelChange = (newRowModesModel) => {
    setRowModesModel(newRowModesModel);
  };

  function EditToolbar(props) {
    const { setRowModesModel } = props;

    const handleClick = () => {
      const id = randomId();
      const emptyRow = { id, isNew: true };
      columnData.forEach((column) => {
        emptyRow[column.field] = " ";
      });

      onChange((oldRows) => [...oldRows, emptyRow]);
      setRowModesModel((oldModel) => ({
        ...oldModel,
        [id]: {
          mode: GridRowModes.Edit,
          fieldToFocus: columnData[0]["field"],
        },
      }));
    };

    return (
      <GridToolbarContainer>
        <Button
          color="primary"
          startIcon={<UploadFile />}
          type="file"
          variant="contained"
          onClick={handleFileUpload}
        >
          Upload CSV
        </Button>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          ref={fileInputRef}
          style={{ display: "none" }} // Hide the input element
        />
        <Button
          color="secondary"
          startIcon={<AddOutlined />}
          onClick={handleClick}
          variant="contained"
        >
          Add record
        </Button>
        <GridToolbarExport
          csvOptions={{
            includeColumnGroupsHeaders: false,
            fileName: "input_data",
          }}
          printOptions={{ disableToolbarButton: true }}
        />
      </GridToolbarContainer>
    );
  }

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
        rows={rowData}
        columns={[
          ...columnData,
          {
            field: "actions",
            type: "actions",
            headerName: "Actions",
            width: 100,
            cellClassName: "actions",
            getActions: ({ id }) => {
              const isInEditMode =
                rowModesModel[id]?.mode === GridRowModes.Edit;

              if (isInEditMode) {
                return [
                  <GridActionsCellItem
                    icon={<SaveOutlined />}
                    label="Save"
                    sx={{
                      color: "primary.main",
                    }}
                    onClick={handleSaveClick(id)}
                  />,
                  <GridActionsCellItem
                    icon={<CancelOutlined />}
                    label="Cancel"
                    className="textPrimary"
                    onClick={handleCancelClick(id)}
                    color="inherit"
                  />,
                ];
              }

              return [
                <GridActionsCellItem
                  icon={<EditOutlined />}
                  label="Edit"
                  className="textPrimary"
                  onClick={handleEditClick(id)}
                  color="inherit"
                />,
                <GridActionsCellItem
                  icon={<DeleteOutlined />}
                  label="Delete"
                  onClick={handleDeleteClick(id)}
                  color="inherit"
                />,
              ];
            },
          },
        ]}
        editMode="row"
        rowModesModel={rowModesModel}
        onRowModesModelChange={handleRowModesModelChange}
        onRowEditStop={handleRowEditStop}
        processRowUpdate={processRowUpdate}
        pageSizeOptions={[5, 10]}
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 5,
            },
          },
        }}
        slots={{
          toolbar: EditToolbar,
        }}
        slotProps={{
          toolbar: { setRowModesModel },
        }}
      />
    </Box>
  );
}
