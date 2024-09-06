import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import {
  Box,
  Button,
  Checkbox,
  FormControl,
  Grow,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Popper,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { DeleteOutlined, AddOutlined } from "@mui/icons-material";
import DataTransformerGeneratorWidget from "./DataTransformerGeneratorWidget";
import AppRunForm from "./AppRunForm";
import ProcessorRunForm from "./ProcessorRunForm";
import { sheetCellTypes, sheetFormulaTypes } from "./Sheet";
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
  const [cellType, setCellType] = useState(0);
  const [formulaType, setFormulaType] = useState(column?.formula?.type || "");
  const [formulaData, setFormulaData] = useState(column?.formula?.data || {});
  const [showFormulaTypeSelect, setShowFormulaTypeSelect] = useState(
    column?.formula?.type ? true : false,
  );
  const formulaDataRef = useRef(column?.formula?.data || {});

  useEffect(() => {
    setCellType(column?.cell_type || 0);
    setColumnName(column?.title || "");
    setFormulaType(column?.formula?.type || "");
    setFormulaData(column?.formula?.data || {});
  }, [column]);

  const setDataHandler = useCallback(
    (data) => {
      formulaDataRef.current = {
        ...data,
      };
    },
    [formulaDataRef],
  );

  const memoizedProcessorRunForm = useMemo(
    () => (
      <ProcessorRunForm
        setData={setDataHandler}
        providerSlug={formulaDataRef.current?.provider_slug}
        processorSlug={formulaDataRef.current?.processor_slug}
        processorInput={formulaDataRef.current?.input}
        processorConfig={formulaDataRef.current?.config}
        processorOutputTemplate={formulaDataRef.current?.output_template}
      />
    ),
    [formulaDataRef, setDataHandler],
  );

  const handleAddOrEditColumn = () => {
    const newColumn = {
      col_letter: column ? column.col_letter : numberToLetters(columns.length),
      title: columnName || "New Column",
      cell_type: cellType,
      width: column?.width || 300,
      formula: showFormulaTypeSelect
        ? {
            type: formulaType,
            data: formulaDataRef.current,
          }
        : null,
    };

    if (column) {
      updateColumn(newColumn);
    } else {
      addColumn(newColumn);
    }
    setOpen(false);
    setColumnName("");
    setCellType(0);
    formulaDataRef.current = {};
    setFormulaType("");
    setFormulaData({});
    formulaDataRef.current = {};
  };

  const handleColumnDelete = () => {
    deleteColumn(column);
    setOpen(false);
    setColumnName("");
    setCellType(0);
    setFormulaType("");
    setFormulaData({});
    formulaDataRef.current = {};
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
                value={cellType}
                id="column-type-select"
                aria-label="Cell Type"
                placeholder="Cell Type"
                onChange={(e) => setCellType(e.target.value)}
                onClick={(e) => e.stopPropagation()}
              >
                {Object.keys(sheetCellTypes).map((type) => (
                  <MenuItem key={type} value={type}>
                    <Stack spacing={0}>
                      <Typography variant="body1">
                        {sheetCellTypes[type].label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {sheetCellTypes[type].description}
                      </Typography>
                    </Stack>
                  </MenuItem>
                ))}
              </Select>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  paddingTop: 2,
                  paddingBottom: 2,
                  cursor: "pointer",
                }}
                onClick={() => setShowFormulaTypeSelect(!showFormulaTypeSelect)}
              >
                <Checkbox
                  checked={showFormulaTypeSelect}
                  onChange={(e) => setShowFormulaTypeSelect(e.target.checked)}
                  inputProps={{ "aria-label": "Add dynamic data" }}
                  sx={{
                    paddingLeft: 0,
                    marginLeft: 0,
                  }}
                />
                <Typography variant="body2">
                  Populate column with a formula
                </Typography>
              </Box>
              {showFormulaTypeSelect && (
                <FormControl>
                  <InputLabel id="formula-type-select-label">
                    Formula Type
                  </InputLabel>
                  <Select
                    value={formulaType}
                    id="formula-type-select"
                    aria-label="Formula Type"
                    onChange={(e) => {
                      setFormulaType(parseInt(e.target.value));
                      formulaDataRef.current = {};
                    }}
                    onClick={(e) => e.stopPropagation()}
                    variant="filled"
                    label="Formula Type"
                  >
                    {Object.keys(sheetFormulaTypes).map((type) => (
                      <MenuItem key={type} value={type.toString()}>
                        <Stack spacing={0}>
                          <Typography variant="body1">
                            {sheetFormulaTypes[type].label}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {sheetFormulaTypes[type].description}
                          </Typography>
                        </Stack>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
              {formulaType && (
                <Typography variant="caption" color="text.secondary">
                  You can access the value of a cell in the current row using{" "}
                  <code>{"{{A}}"}</code>, where A is the column letter.
                  <br />
                  &nbsp;
                </Typography>
              )}
              {formulaType === 1 && (
                <DataTransformerGeneratorWidget
                  label="Transformation Template"
                  value={formulaData?.transformation_template}
                  onChange={(value) => {
                    setFormulaData({
                      transformation_template: value,
                    });
                    formulaDataRef.current = {
                      ...formulaDataRef.current,
                      transformation_template: value,
                    };
                  }}
                  multiline
                  rows={4}
                  placeholder="Enter LiquidJS template"
                  helpText={
                    "Use LiquidJS syntax to transform data from other columns in this row. Example: {{ A | upcase }}. The 'A' variable contains the value of the A column in this row."
                  }
                />
              )}
              {formulaType === 2 && (
                <AppRunForm
                  setData={(data) => {
                    setFormulaData({
                      ...data,
                    });
                    formulaDataRef.current = {
                      ...formulaDataRef.current,
                      ...data,
                    };
                  }}
                  appSlug={formulaData.current?.app_slug}
                  appInput={formulaData.current?.input}
                />
              )}
              {formulaType === 3 && memoizedProcessorRunForm}
              <Stack
                direction="row"
                spacing={2}
                sx={{ width: "100%", justifyContent: "center", mt: 2 }}
              >
                <Button
                  sx={{ textTransform: "none" }}
                  variant="standard"
                  onClick={() => {
                    setOpen(false);
                    setFormulaData({});
                    setFormulaType("");
                  }}
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
