import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  FormControl,
  Grow,
  IconButton,
  MenuItem,
  InputLabel,
  Paper,
  Popper,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { DeleteOutlined, AddOutlined } from "@mui/icons-material";
import DataTransformerGeneratorWidget from "./DataTransformerGeneratorWidget";
import AppRunForm from "./AppRunForm";
import ProcessorRunForm from "./ProcessorRunForm";
import AgentRunForm from "./AgentRunForm";
import {
  sheetCellTypes,
  sheetFormulaTypes,
  SHEET_FORMULA_TYPE_DATA_TRANSFORMER,
  SHEET_FORMULA_TYPE_APP_RUN,
  SHEET_FORMULA_TYPE_PROCESSOR_RUN,
  SHEET_CELL_TYPE_TEXT,
  SHEET_FORMULA_TYPE_NONE,
  SHEET_FORMULA_TYPE_AI_AGENT,
} from "./Sheet";

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
    column?.formula?.type && column.formula.type !== SHEET_FORMULA_TYPE_NONE
      ? true
      : false,
  );
  const formulaDataRef = useRef(column?.formula?.data || {});

  useEffect(() => {
    setCellType(column?.cell_type || 0);
    setColumnName(column?.title || "");
    setFormulaType(column?.formula?.type || "");
    setFormulaData(column?.formula?.data || {});
    setShowFormulaTypeSelect(
      column?.formula?.type && column.formula.type !== SHEET_FORMULA_TYPE_NONE
        ? true
        : false,
    );
    formulaDataRef.current = column?.formula?.data || {};
  }, [column]);

  useEffect(() => {
    if (!open) {
      setColumnName("");
      setCellType(SHEET_CELL_TYPE_TEXT);
      setFormulaType("");
      setFormulaData({});
      formulaDataRef.current = {};
      setShowFormulaTypeSelect(false);
    } else {
      setShowFormulaTypeSelect(
        column?.formula?.type && column.formula.type !== SHEET_FORMULA_TYPE_NONE
          ? true
          : false,
      );
      setFormulaData(column?.formula?.data || {});
      setFormulaType(column?.formula?.type || "");
      formulaDataRef.current = column?.formula?.data || {};
    }
  }, [open, column]);

  const setDataHandler = useCallback(
    (data) => {
      formulaDataRef.current = {
        ...formulaDataRef.current,
        ...data,
      };
    },
    [formulaDataRef],
  );

  const memoizedProcessorRunForm = useMemo(
    () => (
      <ProcessorRunForm
        setData={setDataHandler}
        providerSlug={formulaData?.provider_slug}
        processorSlug={formulaData?.processor_slug}
        processorInput={formulaData?.input}
        processorConfig={formulaData?.config}
        processorOutputTemplate={formulaData?.output_template}
      />
    ),
    [formulaData, setDataHandler],
  );

  const memoizedAppRunForm = useMemo(
    () => (
      <AppRunForm
        setData={setDataHandler}
        appSlug={formulaData?.app_slug}
        appInput={formulaData?.input}
      />
    ),
    [formulaData, setDataHandler],
  );

  const memoizedAgentRunForm = useMemo(
    () => (
      <AgentRunForm
        setData={setDataHandler}
        agentInstructions={formulaData?.agent_instructions}
        selectedTools={formulaData?.selected_tools}
        columns={columns}
        columnIndex={
          column
            ? columns.findIndex((c) => c.col_letter === column.col_letter)
            : 0
        }
        cellType={cellType}
      />
    ),
    [formulaData, cellType, setDataHandler, columns, column],
  );

  const handleAddOrEditColumn = () => {
    const newColumn = {
      col_letter: column ? column.col_letter : numberToLetters(columns.length),
      title: columnName || "",
      cell_type: cellType,
      width: column?.width || 300,
      formula: showFormulaTypeSelect
        ? {
            type:
              typeof formulaType === "string"
                ? parseInt(formulaType)
                : formulaType,
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
    setCellType(SHEET_CELL_TYPE_TEXT);
    formulaDataRef.current = {};
    setFormulaType("");
    setFormulaData({});
    formulaDataRef.current = {};
  };

  const handleColumnDelete = () => {
    deleteColumn(column);
    setOpen(false);
    setColumnName("");
    setCellType(SHEET_CELL_TYPE_TEXT);
    setFormulaType("");
    setFormulaData({});
    formulaDataRef.current = {};
  };

  return (
    open && (
      <Popper
        open={open}
        anchorEl={anchorEl}
        role={undefined}
        placement="bottom-start"
        transition
        sx={{
          width: "450px",
          maxHeight: "80vh",
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
            <Paper
              sx={{
                borderRadius: "0 0 8px 8px",
                border: "1px solid #e8ebee",
                borderTop: "none",
              }}
            >
              <Stack gap={1} sx={{ padding: 2, paddingTop: 6 }}>
                <Stack direction="row" gap={2}>
                  <TextField
                    label="Column name"
                    value={columnName}
                    placeholder="Name of the column"
                    variant="outlined"
                    onChange={(e) => setColumnName(e.target.value)}
                    sx={{
                      width: "70%",
                      "& .MuiInputBase-root": {
                        "& fieldset": {
                          border: "solid 1px #ccc",
                          borderRadius: "8px",
                          boxShadow:
                            "0px 1px 2px 0px #1018280F, 0px 1px 3px 0px #1018281A",
                        },
                      },
                      "& .MuiOutlinedInput-root": {
                        boxShadow: "none",
                        borderRadius: "8px",
                        fontSize: "14px",
                        fontWeight: "600",
                        color: "text.secondary",
                        "& .MuiOutlinedInput-input": {
                          padding: "10px",
                        },
                      },
                      "& .MuiOutlinedInput-notchedOutline": {
                        borderRadius: "8px !important",
                        boxShadow: "0px 0px 4px #e8ebee",
                      },
                      "& .MuiInputLabel-root": {
                        fontSize: "14px",
                        fontWeight: "600",
                        color: "text.secondary",
                        marginTop: "0px",
                      },
                    }}
                  />
                  <FormControl sx={{ width: "30%" }}>
                    <InputLabel
                      id="column-type-select-label"
                      sx={{
                        backgroundColor: "white",
                        fontSize: "14px",
                        fontWeight: "600",
                        color: "text.secondary",
                        padding: "0 4px",
                      }}
                    >
                      Column Type
                    </InputLabel>
                    <Select
                      value={cellType}
                      id="column-type-select"
                      aria-label="Cell Type"
                      placeholder="Cell Type"
                      onChange={(e) => setCellType(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      renderValue={(value) => {
                        return sheetCellTypes[value].label;
                      }}
                      sx={{
                        fontWeight: "600",
                        fontSize: "14px",
                        color: "text.secondary",
                      }}
                    >
                      {Object.keys(sheetCellTypes).map((type) => (
                        <MenuItem key={type} value={type}>
                          <Stack spacing={0}>
                            <Typography
                              variant="body1"
                              sx={{ fontSize: "0.9rem" }}
                            >
                              {sheetCellTypes[type].label}
                            </Typography>
                            <Typography
                              variant="caption"
                              color="text.secondary"
                            >
                              {sheetCellTypes[type].description}
                            </Typography>
                          </Stack>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Stack>
                <Stack
                  gap={2}
                  sx={{
                    paddingTop: 2,
                    marginBottom: 4,
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                  direction="row"
                >
                  <Tooltip title="Use a formula to dynamically generate data for this column. You can access cell values in the current row using {{A}}, where A is the column letter.">
                    <Alert
                      icon={false}
                      severity="info"
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1,
                        padding: 2,
                        cursor: "pointer",
                        maxWidth: "70%",
                        borderRadius: "8px",
                        border: "1px solid #ccc",
                        backgroundColor: "#fbfbfb",
                        transition: "border-color 0.1s ease",
                        boxShadow:
                          "0px 1px 2px 0px #1018280F, 0px 1px 3px 0px #1018281A",
                        "&:hover": {
                          borderColor: "text.secondary",
                        },
                        "& .MuiPaper-root": {
                          borderRadius: "8px !important",
                          padding: 0,
                          margin: 0,
                        },
                        "& .MuiAlert-root": {
                          borderRadius: "8px",
                          padding: 0,
                          margin: 0,
                        },
                        "& .MuiAlert-message": {
                          width: "100%",
                          display: "flex",
                          alignItems: "center",
                          gap: 1,
                          padding: 0,
                          margin: 0,
                        },
                      }}
                      onClick={() =>
                        setShowFormulaTypeSelect(!showFormulaTypeSelect)
                      }
                    >
                      <Checkbox
                        checked={showFormulaTypeSelect}
                        onChange={(e) =>
                          setShowFormulaTypeSelect(e.target.checked)
                        }
                        inputProps={{ "aria-label": "Add dynamic data" }}
                        sx={{
                          marginLeft: 0,
                          paddingRight: 0,
                          "& .MuiCheckbox-root": {
                            padding: 0,
                          },
                        }}
                        size="small"
                      />
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          fontWeight: "600",
                          fontSize: "14px",
                        }}
                      >
                        Use formula
                      </Typography>
                    </Alert>
                  </Tooltip>
                  {showFormulaTypeSelect && (
                    <FormControl sx={{ minWidth: "30%", flex: 1 }}>
                      <InputLabel
                        id="formula-type-select-label"
                        sx={{
                          backgroundColor: "white",
                          fontSize: "14px",
                          fontWeight: "600",
                          color: "text.secondary",
                          padding: "0 4px",
                        }}
                      >
                        Formula Type
                      </InputLabel>
                      <Select
                        value={formulaType.toString() || "0"}
                        id="formula-type-select"
                        aria-label="Formula Type"
                        onChange={(e) => {
                          setFormulaType(parseInt(e.target.value));
                          formulaDataRef.current = {};
                        }}
                        onClick={(e) => e.stopPropagation()}
                        variant="outlined"
                        disabled={!showFormulaTypeSelect}
                        renderValue={(value) => {
                          return sheetFormulaTypes[value].label;
                        }}
                        sx={{
                          fontWeight: "600",
                          fontSize: "14px",
                          width: "100%",
                          minWidth: "100px",
                          color: "text.secondary",
                        }}
                      >
                        {Object.keys(sheetFormulaTypes)
                          .sort(
                            (a, b) =>
                              sheetFormulaTypes[a].order -
                              sheetFormulaTypes[b].order,
                          )
                          .map((type) => (
                            <MenuItem key={type} value={type.toString()}>
                              <Stack spacing={0}>
                                <Typography
                                  variant="body1"
                                  sx={{ fontSize: "0.9rem" }}
                                >
                                  {sheetFormulaTypes[type].label}
                                </Typography>
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                >
                                  {sheetFormulaTypes[type].description}
                                </Typography>
                              </Stack>
                            </MenuItem>
                          ))}
                      </Select>
                    </FormControl>
                  )}
                  {showFormulaTypeSelect && (
                    <TextField
                      type="number"
                      label="Parallel Runs"
                      value={formulaData.max_parallel_runs || 1}
                      onChange={(e) => {
                        const value = Math.max(
                          4,
                          parseInt(e.target.value, 10) || 4,
                        );
                        setFormulaData((prevData) => ({
                          ...prevData,
                          max_parallel_runs: value,
                        }));
                        formulaDataRef.current = {
                          ...formulaDataRef.current,
                          max_parallel_runs: value,
                        };
                      }}
                      InputProps={{ inputProps: { min: 1, max: 4 } }}
                      fullWidth
                      variant="outlined"
                      margin="normal"
                      sx={{
                        maxWidth: "100px",
                        margin: 0,
                        "& .MuiOutlinedInput-root": {
                          borderRadius: "8px",
                          boxShadow:
                            "0px 1px 2px 0px #1018280F, 0px 1px 3px 0px #1018281A",
                          "& fieldset": {
                            border: "solid 1px #ccc",
                            borderRadius: "8px",
                          },
                        },
                        "& .MuiInputLabel-root": {
                          fontSize: "14px",
                          fontWeight: "600",
                          color: "text.secondary",
                          marginTop: 0,
                        },
                      }}
                    />
                  )}
                </Stack>
                {showFormulaTypeSelect &&
                  formulaType !== SHEET_FORMULA_TYPE_NONE && (
                    <Alert
                      icon={false}
                      severity="info"
                      sx={{
                        borderRadius: "8px",
                        marginBottom: 4,
                        padding: "4px 8px",
                      }}
                    >
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ marginBottom: 4 }}
                      >
                        Access cell values in the current row using{" "}
                        <code>{"{{A}}"}</code>, where A is the column letter.
                      </Typography>
                    </Alert>
                  )}
                {showFormulaTypeSelect &&
                  formulaType === SHEET_FORMULA_TYPE_DATA_TRANSFORMER && (
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
                {showFormulaTypeSelect &&
                  formulaType === SHEET_FORMULA_TYPE_APP_RUN &&
                  memoizedAppRunForm}
                {showFormulaTypeSelect &&
                  formulaType === SHEET_FORMULA_TYPE_PROCESSOR_RUN &&
                  memoizedProcessorRunForm}
                {showFormulaTypeSelect &&
                  formulaType === SHEET_FORMULA_TYPE_AI_AGENT &&
                  memoizedAgentRunForm}
                <Stack
                  direction="row"
                  spacing={2}
                  sx={{
                    width: "100%",
                    justifyContent: "space-between",
                    mt: 4,
                  }}
                >
                  <Box sx={{ flex: 1 }}>
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
                  </Box>
                  <Box
                    sx={{ display: "flex", justifyContent: "center", flex: 2 }}
                  >
                    <Button
                      sx={{ textTransform: "none", mr: 2 }}
                      variant="standard"
                      onClick={() => {
                        setOpen(false);
                      }}
                    >
                      Cancel
                    </Button>
                    <Button variant="contained" onClick={handleAddOrEditColumn}>
                      {column ? "Update" : "Add"}
                    </Button>
                  </Box>
                  <Box sx={{ flex: 1 }} />
                </Stack>
              </Stack>
            </Paper>
          </Grow>
        )}
      </Popper>
    )
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
