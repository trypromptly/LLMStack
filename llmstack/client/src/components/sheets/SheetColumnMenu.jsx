import { useEffect, useRef, useState } from "react";
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
  Checkbox,
  FormControlLabel,
  Typography,
} from "@mui/material";
import { DeleteOutlined, AddOutlined } from "@mui/icons-material";
import { GridCellKind } from "@glideapps/glide-data-grid";
import AppRunForm from "./AppRunForm";
import ProcessorRunForm from "./ProcessorRunForm"; // Added this import
import "@glideapps/glide-data-grid/dist/index.css";

const numberToLetters = (num) => {
  let letters = "";
  while (num >= 0) {
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[num % 26] + letters;
    num = Math.floor(num / 26) - 1;
  }
  return letters;
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
    setColumnType(column?.kind || GridCellKind.Text);
    setColumnName(column?.title || "");
    columnRunData.current = column?.data || {};
    setTransformData(!!column?.data?.transformation_template);
    setTransformationTemplate(column?.data?.transformation_template || "");
  }, [column]);

  const handleAddOrEditColumn = () => {
    const newColumn = {
      col: column ? column.col : numberToLetters(columns.length),
      title: columnName || "New Column",
      kind: columnType,
      data:
        (columnType === "app_run" || columnType === "processor_run") &&
        columnRunData.current
          ? {
              ...columnRunData.current,
              transformation_template: transformData
                ? transformationTemplate
                : undefined,
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
                <MenuItem value={"text"}>Text</MenuItem>
                <MenuItem value={"number"}>Number</MenuItem>
                <MenuItem value={"image"}>Image</MenuItem>
                <MenuItem value={"app_run"}>App Run</MenuItem>
                <MenuItem value={"processor_run"}>Processor Run</MenuItem>
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
                  columns={columns}
                />
              )}
              {columnType === "processor_run" && (
                <ProcessorRunForm
                  setData={(data) => {
                    columnRunData.current = {
                      ...columnRunData.current,
                      ...data,
                    };
                  }}
                  providerSlug={columnRunData.current?.provider_slug}
                  processorSlug={columnRunData.current?.processor_slug}
                  processorInput={columnRunData.current?.input}
                  processorConfig={columnRunData.current?.config}
                  processorOutputTemplate={
                    columnRunData.current?.output_template
                  }
                  columns={columns}
                />
              )}
              {(columnType === "app_run" || columnType === "processor_run") && (
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={transformData}
                      onChange={(e) => setTransformData(e.target.checked)}
                    />
                  }
                  label="Transform output data"
                />
              )}
              {transformData && (
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
                    Use LiquidJS syntax to transform the output. Example:
                    <code>{`{{ output | split: ' ' | first }}`}</code>. The
                    'output' variable contains the original result.
                  </Typography>
                </>
              )}
              <Stack
                direction="row"
                spacing={2}
                sx={{ width: "100%", justifyContent: "center", mt: 2 }}
              >
                <Button variant="standard" onClick={() => setOpen(false)}>
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
