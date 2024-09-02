import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import {
  Box,
  Button,
  Grow,
  IconButton,
  MenuItem,
  Paper,
  Popper,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { DeleteOutlined, AddOutlined } from "@mui/icons-material";
import { GridCellKind, GridColumnIcon } from "@glideapps/glide-data-grid";
import AppRunForm from "./AppRunForm";
import ProcessorRunForm from "./ProcessorRunForm";
import { getProviderIconImage } from "../apps/ProviderIcon";
import "@glideapps/glide-data-grid/dist/index.css";

const numberToLetters = (num) => {
  let letters = "";
  while (num >= 0) {
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[num % 26] + letters;
    num = Math.floor(num / 26) - 1;
  }
  return letters;
};

export const sheetColumnTypes = {
  text: {
    value: "text",
    label: "Text",
    description: "Plain text content",
    icon: GridColumnIcon.HeaderString,
    kind: GridCellKind.Text,
    getCellDataFromValue: (value) => value?.data || value || "",
    getCellData: (cell) => cell?.data?.output || cell?.data || "",
    getCellDisplayData: (cell) =>
      typeof cell?.data === "object" ? cell?.data?.output : cell?.data || "",
  },
  number: {
    value: "number",
    label: "Number",
    description: "Numeric values",
    icon: GridColumnIcon.HeaderNumber,
    kind: GridCellKind.Number,
    getCellDataFromValue: (value) => value?.data || value || "",
    getCellData: (cell) => cell?.data?.output || cell?.data || 0,
    getCellDisplayData: (cell) => cell?.data?.toLocaleString() || "",
  },
  uri: {
    value: "uri",
    label: "URI",
    description: "Uniform Resource Identifier",
    icon: GridColumnIcon.HeaderUri,
    kind: GridCellKind.Uri,
    getCellDataFromValue: (value) => value?.data || "",
    getCellData: (cell) => cell?.data?.output || cell?.data || "",
    getCellDisplayData: (cell) => cell?.data?.output || cell?.data || "",
  },
  app_run: {
    value: "app_run",
    label: "App Run",
    description: "Results from running an app",
    icon: "app_run",
    kind: GridCellKind.Text,
    getCellDataFromValue: (value) => {
      return {
        output: value?.data,
      };
    },
    getCellData: (cell) => cell?.data?.output || cell?.display_data || "",
    getCellDisplayData: (cell) =>
      cell?.data?.output || cell?.display_data || "",
    getIconImage: (columnData) => {
      return getProviderIconImage("promptly", false);
    },
  },
  processor_run: {
    value: "processor_run",
    label: "Processor Run",
    description: "Results from running a processor",
    icon: "processor_run",
    getIconImage: (columnData) => {
      return getProviderIconImage(columnData?.provider_slug, false);
    },
    kind: GridCellKind.Text,
    getCellDataFromValue: (value) => {
      return {
        output: value?.data,
      };
    },
    getCellData: (cell) => cell?.data?.output || cell?.display_data || "",
    getCellDisplayData: (cell) =>
      cell?.data?.output || cell?.display_data || "",
  },
  data_transformer: {
    value: "data_transformer",
    label: "Data Transformer",
    description: "Create new columns from existing columns",
    icon: "data_transformer",
    kind: GridCellKind.Text,
    getCellDataFromValue: (value) => {
      return {
        output: value?.data,
      };
    },
    getCellData: (cell) => cell?.data?.output || cell?.display_data || "",
    getCellDisplayData: (cell) =>
      cell?.data?.output || cell?.display_data || "",
    getIconImage: (columnData) => {
      return getProviderIconImage("promptly", false);
    },
  },
};

export function SheetColumnMenu({
  anchorEl,
  column,
  columns,
  addColumn,
  updateColumn,
  deleteColumn,
  open,
  setOpen,
}) {
  const [columnName, setColumnName] = useState(column?.title || "");
  const [columnType, setColumnType] = useState(GridCellKind.Text);
  const columnRunData = useRef(column?.data || {});
  const [transformData, setTransformData] = useState(false);
  const [transformationTemplate, setTransformationTemplate] = useState("");

  useEffect(() => {
    setColumnType(column?.type || GridCellKind.Text);
    setColumnName(column?.title || "");
    columnRunData.current = column?.data || {};
    setTransformData(!!column?.data?.transformation_template);
    setTransformationTemplate(column?.data?.transformation_template || "");
  }, [column]);

  const setDataHandler = useCallback(
    (data) => {
      columnRunData.current = {
        ...columnRunData.current,
        ...data,
      };
    },
    [columnRunData],
  );

  const memoizedProcessorRunForm = useMemo(
    () => (
      <ProcessorRunForm
        setData={setDataHandler}
        providerSlug={columnRunData.current?.provider_slug}
        processorSlug={columnRunData.current?.processor_slug}
        processorInput={columnRunData.current?.input}
        processorConfig={columnRunData.current?.config}
        processorOutputTemplate={columnRunData.current?.output_template}
      />
    ),
    [setDataHandler],
  );

  const handleAddOrEditColumn = () => {
    const newColumn = {
      col: column ? column.col : numberToLetters(columns.length),
      title: columnName || "New Column",
      type: columnType,
      kind: sheetColumnTypes[columnType]?.kind,
      icon: sheetColumnTypes[columnType]?.icon,
      hasMenu: column?.hasMenu || true,
      width: column?.width || 300,
      data:
        (columnType === "app_run" ||
          columnType === "processor_run" ||
          columnType === "data_transformer") &&
        columnRunData.current
          ? {
              ...columnRunData.current,
              transformation_template:
                transformData || columnType === "data_transformer"
                  ? transformationTemplate
                  : undefined,
              kind: columnType,
            }
          : {},
    };

    if (column) {
      updateColumn(newColumn);
    } else {
      addColumn(newColumn);
    }
    setOpen(false);
    setColumnName("");
    setColumnType(GridCellKind.Text);
    columnRunData.current = {};
    setTransformData(false);
    setTransformationTemplate("");
  };

  const handleColumnDelete = () => {
    deleteColumn(column);
    setOpen(false);
    setColumnName("");
    setColumnType(GridCellKind.Text);
  };

  return (
    <Popper
      open={open}
      anchorEl={anchorEl}
      role={undefined}
      placement="bottom-start"
      transition
      sx={{
        width: "450px",
        maxHeight: "90vh",
        overflowY: "auto",
        padding: "0px 2px 8px 2px",
      }}
    >
      {({ TransitionProps, placement }) => (
        <Grow
          {...TransitionProps}
          style={{
            transformOrigin:
              placement === "bottom-start" ? "left top" : "left bottom",
          }}
        >
          <Paper>
            <Stack gap={2} sx={{ padding: 2 }}>
              <Stack
                direction="row"
                gap={2}
                sx={{ justifyContent: "flex-end" }}
              >
                {column && (
                  <IconButton
                    variant="outlined"
                    onClick={handleColumnDelete}
                    sx={{
                      color: "text.secondary",
                      minWidth: "30px",
                      padding: 0,
                    }}
                  >
                    <DeleteOutlined />
                  </IconButton>
                )}
              </Stack>
              <TextField
                label="Name"
                value={columnName}
                placeholder="Column Name"
                variant="outlined"
                onChange={(e) => setColumnName(e.target.value)}
              />
              <Select
                value={columnType}
                id="column-type-select"
                aria-label="Column Type"
                placeholder="Column Type"
                helperText="Select the type of data this column will contain"
                onChange={(e) => setColumnType(e.target.value)}
                onClick={(e) => e.stopPropagation()}
              >
                {Object.keys(sheetColumnTypes).map((type) => (
                  <MenuItem key={type} value={type}>
                    <Stack spacing={0}>
                      <Typography variant="body1">
                        {sheetColumnTypes[type].label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {sheetColumnTypes[type].description}
                      </Typography>
                    </Stack>
                  </MenuItem>
                ))}
              </Select>
              {columnType === "app_run" && (
                <AppRunForm
                  setData={(data) => {
                    columnRunData.current = {
                      ...columnRunData.current,
                      ...data,
                    };
                  }}
                  appSlug={columnRunData.current?.app_slug}
                  appInput={columnRunData.current?.input}
                />
              )}
              {columnType === "processor_run" && memoizedProcessorRunForm}
              {columnType === "data_transformer" && (
                <>
                  <TextField
                    label="Transformation Template"
                    value={transformationTemplate}
                    onChange={(e) => setTransformationTemplate(e.target.value)}
                    multiline
                    rows={4}
                    placeholder="Enter LiquidJS template"
                  />
                  <Typography variant="caption" color="text.secondary">
                    Use LiquidJS syntax to transform the input. Example:
                    <code>{`{{ input | upcase }}`}</code>. The 'input' variable
                    contains the original cell value.
                  </Typography>
                </>
              )}
              <Stack
                direction="row"
                spacing={2}
                sx={{ width: "100%", justifyContent: "center", mt: 2 }}
              >
                <Button
                  sx={{ textTransform: "none" }}
                  variant="standard"
                  onClick={() => setOpen(false)}
                >
                  Cancel
                </Button>
                <Button variant="contained" onClick={handleAddOrEditColumn}>
                  {column ? "Update" : "Add"}
                </Button>
              </Stack>
            </Stack>
          </Paper>
        </Grow>
      )}
    </Popper>
  );
}

export function SheetColumnMenuButton({ columns, addColumn }) {
  const anchorRef = useRef(null);
  const [open, setOpen] = useState(false);

  return (
    <Box>
      <IconButton
        aria-label="add-column"
        ref={anchorRef}
        aria-controls={open ? "composition-menu" : undefined}
        aria-expanded={open ? "true" : undefined}
        aria-haspopup="true"
        onClick={() => setOpen(!open)}
      >
        <AddOutlined />
      </IconButton>
      <SheetColumnMenu
        columns={columns}
        addColumn={addColumn}
        open={open}
        setOpen={setOpen}
        anchorEl={anchorRef.current}
      />
    </Box>
  );
}
