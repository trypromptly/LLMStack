import {
  AddOutlined,
  CancelOutlined,
  DeleteOutlined,
  EditOutlined,
  SaveOutlined,
  UploadFile,
} from "@mui/icons-material";
import { Box, Button } from "@mui/material";
import {
  DataGrid,
  GridActionsCellItem,
  GridRowEditStopReasons,
  GridRowModes,
  GridToolbarContainer,
  GridToolbarExport,
} from "@mui/x-data-grid";
import { randomId } from "@mui/x-data-grid-generator";
import { enqueueSnackbar } from "notistack";
import { useEffect, useRef, useState } from "react";
import { usePapaParse } from "react-papaparse";

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
              setFile(null);
              return;
            }
            const headers = Object.keys(results.data[0]);

            if (headers.length !== columnData.length) {
              enqueueSnackbar("Headers do not match expected headers", {
                variant: "error",
              });
              setFile(null);
              return;
            }
            headers.forEach((header) => {
              if (!columnData.find((column) => column.headerName === header)) {
                enqueueSnackbar("Headers do not match expected headers", {
                  variant: "error",
                });
                setFile(null);
                return;
              }
            });
            const newRows = [];
            for (let i = 0; i < results.data.length; i++) {
              const row = results.data[i];
              if (Object.keys(row).length !== headers.length) {
                continue;
              }
              const newRow = { _id: i, _isNew: true };
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
  }, [file, columnData, onChange, readString]);

  const handleRowEditStop = (params, event) => {
    if (params.reason === GridRowEditStopReasons.rowFocusOut) {
      event.defaultMuiPrevented = true;
      handleSaveClick(params.id)();
    }
  };

  const handleEditClick = (_id) => () => {
    setRowModesModel({ ...rowModesModel, [_id]: { mode: GridRowModes.Edit } });
  };

  const handleSaveClick = (_id) => () => {
    setRowModesModel({ ...rowModesModel, [_id]: { mode: GridRowModes.View } });
  };

  const handleDeleteClick = (_id) => () => {
    onChange(rowData.filter((row) => row._id !== _id));
  };

  const handleCancelClick = (_id) => () => {
    setRowModesModel({
      ...rowModesModel,
      [_id]: { mode: GridRowModes.View, ignoreModifications: true },
    });

    const editedRow = rowData.find((row) => row._id === _id);

    if (editedRow._isNew) {
      onChange(rowData.filter((row) => row._id !== _id));
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
    const updatedRow = { ...newRow, _isNew: false };

    onChange(rowData.map((row) => (row._id === newRow._id ? updatedRow : row)));

    return updatedRow;
  };

  const handleRowModesModelChange = (newRowModesModel) => {
    setRowModesModel(newRowModesModel);
  };

  function EditToolbar(props) {
    const { setRowModesModel } = props;

    const handleClick = () => {
      const _id = randomId();
      const emptyRow = { _id, _isNew: true };
      columnData.forEach((column) => {
        emptyRow[column.field] = " ";
      });

      onChange((oldRows) => [...oldRows, emptyRow]);
      setRowModesModel((oldModel) => ({
        ...oldModel,
        [_id]: {
          mode: GridRowModes.Edit,
          fieldToFocus: columnData[0]["field"],
        },
      }));
    };

    return (
      <GridToolbarContainer sx={{ alignSelf: "flex-end" }}>
        <Button
          color="primary"
          startIcon={<UploadFile />}
          type="file"
          variant="contained"
          onClick={handleFileUpload}
          size="small"
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
          size="small"
        >
          Add Record
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
        width: "100%",
        "& .actions": {
          color: "text.secondary",
        },
        "& .textPrimary": {
          color: "text.primary",
        },
        "& .MuiDataGrid-columnHeaderTitle": {
          fontWeight: "bold",
        },
      }}
    >
      <DataGrid
        rows={rowData}
        getRowId={(row) => row._id}
        columns={[
          ...columnData,
          {
            field: "actions",
            type: "actions",
            headerName: "Actions",
            width: 100,
            cellClassName: "actions",
            flex: 1,
            maxWidth: 100,
            getActions: (actionProps) => {
              const { id: _id } = actionProps;
              const isInEditMode =
                rowModesModel[_id]?.mode === GridRowModes.Edit;

              if (isInEditMode) {
                return [
                  <GridActionsCellItem
                    icon={<SaveOutlined />}
                    label="Save"
                    sx={{
                      color: "primary.main",
                    }}
                    onClick={handleSaveClick(_id)}
                  />,
                  <GridActionsCellItem
                    icon={<CancelOutlined />}
                    label="Cancel"
                    className="textPrimary"
                    onClick={handleCancelClick(_id)}
                    color="inherit"
                  />,
                ];
              }

              return [
                <GridActionsCellItem
                  icon={<EditOutlined />}
                  label="Edit"
                  className="textPrimary"
                  onClick={handleEditClick(_id)}
                  color="inherit"
                />,
                <GridActionsCellItem
                  icon={<DeleteOutlined />}
                  label="Delete"
                  onClick={handleDeleteClick(_id)}
                  color="inherit"
                />,
              ];
            },
          },
        ]}
        editMode="row"
        autoHeight={true}
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
