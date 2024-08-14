import { useEffect, useState } from "react";
import {
  Grid,
  Button,
  Box,
  Stack,
  Tab,
  IconButton,
  Menu,
  ListItemText,
  TextField,
  MenuItem,
  MenuList,
  ListItemIcon,
} from "@mui/material";
import { useRecoilValue } from "recoil";
import { TabList, TabContext, TabPanel } from "@mui/lab";
import { sheetsState } from "../data/atoms";
import { axios } from "../data/axios";
import AddIcon from "@mui/icons-material/Add";
import { SaveOutlined } from "@mui/icons-material";
import { ArrowDropDown } from "@mui/icons-material";
import { DeleteOutlineOutlined } from "@mui/icons-material";
import {
  DataGrid,
  GridToolbarContainer,
  GridToolbarColumnsButton,
  GridToolbarFilterButton,
  GridPagination,
  useGridApiRef,
  GridColumnMenu,
  useGridApiContext,
} from "@mui/x-data-grid";

const COLUMN_TYPES = {
  string: {
    type: "string",
    editable: true,
    sortable: false,
    flex: 1,
  },
};

function gridDataToApiData(columns, rows, apiRef) {
  const cells = [];
  const headerCells = columns.map((column) => ({
    value: column.headerName,
    value_type: "string",
    extra_data: { is_header: true },
  }));
  cells.push(headerCells);
  const columnIndices = columns.reduce(
    (acc, column, index) => ({ ...acc, [column.field]: index }),
    {},
  );
  rows.forEach((row) => {
    const rowCells = new Array(columns.length).fill({ value: "" });
    Object.keys(row)
      .filter((key) => key !== "id")
      .forEach((key) => {
        const columnIndex = columnIndices[key];
        rowCells[columnIndex] = {
          value: row[key],
          value_type: apiRef.current.getColumn(key).type,
        };
      });
    cells.push(rowCells);
  });

  return cells;
}

const RowUpdateButton = () => {
  const apiRef = useGridApiContext();
  const selectedRows = apiRef.current.getSelectedRows();
  const rows = apiRef.current.getRowModels();

  return selectedRows.size ? (
    <Button
      variant="contained"
      color="primary"
      size="small"
      onClick={() => {
        selectedRows.forEach((row) => {
          apiRef.current.updateRows([{ id: row.id, _action: "delete" }]);
        });
      }}
    >
      {`Delete ${selectedRows.size} record(s)`}
    </Button>
  ) : (
    <Button
      color="primary"
      startIcon={<AddIcon />}
      onClick={() => {
        const newRow = {
          id: rows.size,
          ...Object.fromEntries(
            apiRef.current
              .getAllColumns()
              .filter((entry) => entry.field !== "__check__")
              .map((col) => [col.field, ""]),
          ),
        };
        apiRef.current.updateRows([newRow]);
      }}
    >
      Add record
    </Button>
  );
};

const AddColumnButton = ({ options, onSelect }) => {
  const [anchorEl, setAnchorEl] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredOptions, setFilteredOptions] = useState(options);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleSearch = (event) => {
    const search = event.target.value.toLowerCase();
    setSearchTerm(search);
    setFilteredOptions(
      options.filter((option) => option.name.toLowerCase().includes(search)),
    );
  };

  const handleSelect = (option) => {
    onSelect(option);
    handleClose();
  };

  return (
    <div>
      <Button
        variant="contained"
        endIcon={<ArrowDropDown />}
        onClick={handleClick}
      >
        Add Column
      </Button>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        sx={{ maxHeight: "300px" }}
      >
        <div style={{ padding: "8px 16px" }}>
          <TextField
            variant="outlined"
            fullWidth
            placeholder="Search..."
            value={searchTerm}
            onChange={handleSearch}
          />
        </div>
        <MenuList>
          {filteredOptions.map((option, index) => (
            <MenuItem key={index} onClick={() => handleSelect(option)}>
              {option.name}
            </MenuItem>
          ))}
        </MenuList>
      </Menu>
    </div>
  );
};

const CustomColumnItem = ({ columnProps, setColumns }) => {
  return (
    <MenuItem
      onClick={(data) => {
        setColumns((prevColumns) =>
          prevColumns.filter((col) => col.field !== columnProps?.colDef?.field),
        );
      }}
    >
      <ListItemIcon>
        <DeleteOutlineOutlined fontSize="small" />
      </ListItemIcon>
      <ListItemText primary="Delete Column" />
    </MenuItem>
  );
};

function SheetFooter() {
  return (
    <Stack direction={"row"} justifyContent={"space-between"}>
      <RowUpdateButton />
      <GridPagination />
    </Stack>
  );
}

function SheetToolbar({ setColumns, columns, sheet_id, addColumnOptions }) {
  const apiRef = useGridApiContext();

  return (
    <GridToolbarContainer>
      <GridToolbarColumnsButton />
      <GridToolbarFilterButton />
      <RowUpdateButton />

      <IconButton
        color="primary"
        onClick={() => {
          const updatedCellsData = gridDataToApiData(
            columns,
            apiRef.current.getRowModels(),
            apiRef,
          );
          axios()
            .patch(`/api/sheets/${sheet_id}`, {
              cells: updatedCellsData,
            })
            .then((res) => {
              window.location.reload();
            });
        }}
      >
        <SaveOutlined />
      </IconButton>
      <AddColumnButton
        options={addColumnOptions}
        onSelect={(option) => {
          let newColumn = {
            field: `0~${columns.length}`,
            headerName: `New Column ${columns.length + 1}`,
            ...COLUMN_TYPES[option.type],
          };

          setColumns((prevColumns) => [...prevColumns, newColumn]);
        }}
      />
    </GridToolbarContainer>
  );
}

function SheetColumnMenu(props) {
  const { apiRef, columns, setColumns } = props;
  return (
    <GridColumnMenu
      {...props}
      slots={{ columnMenuSortItem: null, columnMenuUserItem: CustomColumnItem }}
      slotProps={{
        columnMenuUserItem: {
          displayOrder: 1,
          columnProps: props,
          apiRef,
          columns,
          setColumns,
        },
      }}
    />
  );
}

function SheetGrid(props) {
  const addColumnOptions = [{ type: "string", name: "String" }];

  const apiRef = useGridApiRef();
  const { id } = props;

  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);

  useEffect(() => {
    axios()
      .get(`/api/sheets/${id}?include_cells=true`)
      .then((res) => {
        if (res.data.cells) {
          const headerCells = res.data.cells[0];
          const columns = headerCells.map((cell, index) => ({
            field: cell.cell_id,
            headerName: cell.value,
            ...COLUMN_TYPES[cell.value_type],
          }));
          const rows = res.data.cells.slice(1).map((row, rowIndex) =>
            row.reduce(
              (acc, cell, cellIndex) => ({
                ...acc,
                [headerCells[cellIndex].cell_id]: cell.value,
              }),
              { id: rowIndex },
            ),
          );
          setColumns(columns);
          setRows(rows);
        }
      });
  }, [setColumns, setRows]);

  useEffect(() => {
    if (rows.length) {
      const columnFields = columns.map((column) => column.field);
      // From row remove keys that are not in columnFields except id
      const newRows = Array.from(apiRef.current.getRowModels().values()).map(
        (row) =>
          Object.keys(row).reduce(
            (acc, key) =>
              key === "id" || columnFields.includes(key)
                ? { ...acc, [key]: row[key] }
                : acc,
            {},
          ),
      );
      setRows(newRows);
    }
  }, [columns]);

  return (
    <Box sx={{ width: "100%" }}>
      <DataGrid
        apiRef={apiRef}
        editMode="row"
        columns={columns}
        rows={rows}
        slots={{
          toolbar: SheetToolbar,
          footer: SheetFooter,
          columnMenu: SheetColumnMenu,
        }}
        slotProps={{
          toolbar: {
            setRows,
            setColumns,
            columns,
            sheet_id: id,
            addColumnOptions,
          },
          columnMenu: { apiRef, columns, setColumns },
        }}
        checkboxSelection
        disableRowSelectionOnClick
      />
    </Box>
  );
}
export default function SheetsPage() {
  const sheets = useRecoilValue(sheetsState);
  const [selectedSheet, setSelectedSheet] = useState(sheets[0].uuid || "");

  const createSheet = () => {
    axios()
      .post("/api/sheets", { name: `New sheet ${sheets.length + 1}` })
      .then((res) => {
        window.location.reload();
      });
  };

  return (
    <Box padding={4} sx={{ height: "100%" }}>
      <Grid container spacing={2} sx={{ height: "100%" }}>
        <Grid xs={12} sx={{ height: "10%" }}>
          <Grid container>
            <Grid xs={8}>
              <h1>Sheets</h1>
            </Grid>
            <Grid xs={4}></Grid>
          </Grid>
        </Grid>
        <Grid xs={12} sx={{ height: "80%" }}>
          <Box sx={{ width: "100%", height: "50%" }}>
            <TabContext value={selectedSheet}>
              <Stack
                sx={{ borderBottom: 1, borderColor: "divider" }}
                direction={"row"}
                justifyContent={"space-between"}
              >
                <TabList onChange={(e, value) => setSelectedSheet(value)}>
                  {sheets.map((sheet) => {
                    return <Tab label={sheet.name} value={sheet.uuid} />;
                  })}
                </TabList>
                <Button variant="contained" onClick={createSheet}>
                  New Sheet
                </Button>
              </Stack>
              {sheets.map((sheet) => {
                return (
                  <TabPanel key={sheet.uuid} value={sheet.uuid}>
                    <SheetGrid id={sheet.uuid} />
                  </TabPanel>
                );
              })}
            </TabContext>
          </Box>
        </Grid>
        <Grid xs={12} sx={{ height: "5%" }}></Grid>
      </Grid>
    </Box>
  );
}
