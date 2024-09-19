import React, { useState, useMemo, useEffect, useCallback } from "react";
import {
  Popper,
  Paper,
  Grow,
  Stack,
  Select,
  MenuItem,
  Button,
  Typography,
  InputLabel,
  Checkbox,
  FormControlLabel,
} from "@mui/material";
import DataTransformerGeneratorWidget from "./DataTransformerGeneratorWidget";
import AppRunForm from "./AppRunForm";
import ProcessorRunForm from "./ProcessorRunForm";
import {
  sheetFormulaTypes,
  SHEET_FORMULA_TYPE_DATA_TRANSFORMER,
  SHEET_FORMULA_TYPE_APP_RUN,
  SHEET_FORMULA_TYPE_PROCESSOR_RUN,
} from "./Sheet";

const SheetFormulaMenu = ({
  anchorEl,
  open,
  onClose,
  cellId,
  selectedCell,
  setFormula,
}) => {
  const [formulaType, setFormulaType] = useState(
    selectedCell?.formula?.type || "",
  );
  const [transformationTemplate, setTransformationTemplate] = useState(
    selectedCell?.formula?.data?.transformation_template || "",
  );
  const [formulaData, setFormulaData] = useState(
    selectedCell?.formula?.data || {},
  );
  const formulaDataRef = React.useRef(selectedCell?.formula?.data || {});
  const [spreadOutput, setSpreadOutput] = useState(
    selectedCell?.spread_output || false,
  );

  const setDataHandler = useCallback(
    (data) => {
      formulaDataRef.current = {
        ...formulaDataRef.current,
        ...data,
      };
    },
    [formulaDataRef],
  );

  useEffect(() => {
    formulaDataRef.current = selectedCell?.formula?.data || {};
    setFormulaType(selectedCell?.formula?.type || "");
    setTransformationTemplate(
      selectedCell?.formula?.data?.transformation_template || "",
    );
    setFormulaData(selectedCell?.formula?.data || {});
    setSpreadOutput(selectedCell?.spread_output || false);
  }, [selectedCell]);

  useEffect(() => {
    if (!open) {
      setFormulaType("");
      setFormulaData({});
      formulaDataRef.current = {};
    }
  }, [open]);

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
    [setDataHandler, formulaData],
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

  const handleApplyFormula = () => {
    const newFormula = {
      type: formulaType,
      data: {
        ...formulaDataRef.current,
        transformation_template: transformationTemplate,
      },
    };
    setFormula(cellId, newFormula, spreadOutput);
    formulaDataRef.current = null;
    setTransformationTemplate("");
    setFormulaType("");
    setFormulaData({});
    onClose();
  };

  const handleClearFormula = () => {
    setFormula(cellId, null, false);
    onClose();
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
          <Paper
            sx={{
              border: "solid 2px #e0e0e0",
              borderTop: "none",
              marginLeft: "-2px",
            }}
          >
            <Stack gap={2} sx={{ padding: 2 }}>
              <InputLabel>Formula: {cellId}</InputLabel>
              <Typography variant="caption" color="text.secondary">
                Select the type of formula you want to apply
              </Typography>
              <Select
                value={formulaType}
                onChange={(e) => {
                  setFormulaType(parseInt(e.target.value));
                  setFormulaData({});
                  formulaDataRef.current = {};
                }}
              >
                {Object.keys(sheetFormulaTypes)
                  .sort(
                    (a, b) =>
                      sheetFormulaTypes[a].order - sheetFormulaTypes[b].order,
                  )
                  .map((type) => (
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
              {(formulaType === SHEET_FORMULA_TYPE_DATA_TRANSFORMER ||
                formulaType === SHEET_FORMULA_TYPE_APP_RUN ||
                formulaType === SHEET_FORMULA_TYPE_PROCESSOR_RUN) && (
                <Typography variant="caption" color="text.secondary">
                  You can access the output from previous cell or a range of
                  cells using the cell ids. For example, <code>{"{{A1}}"}</code>{" "}
                  refers to the value in the cell with column A and row 1.{" "}
                  <code>{"{{A1-B10}}"}</code> returns a list of values from
                  cells A1 to B10. To access all the values in a column as a
                  list, use <code>{"{{A}}"}</code>, where A is the column
                  letter.
                  <br />
                  &nbsp;
                </Typography>
              )}
              {formulaType === SHEET_FORMULA_TYPE_DATA_TRANSFORMER && (
                <>
                  <DataTransformerGeneratorWidget
                    label="Transformation Template"
                    value={transformationTemplate}
                    onChange={(value) => setTransformationTemplate(value)}
                    multiline
                    rows={4}
                    placeholder="Enter LiquidJS template"
                    helpText={
                      "Use LiquidJS syntax to transform data from other cells. Example: {{ A1 | upcase }}. The 'A1' variable contains the A1 cell's value."
                    }
                  />
                </>
              )}
              {formulaType === SHEET_FORMULA_TYPE_APP_RUN && memoizedAppRunForm}
              {formulaType === SHEET_FORMULA_TYPE_PROCESSOR_RUN &&
                memoizedProcessorRunForm}
              {formulaType && (
                <>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={spreadOutput}
                        onChange={(e) => setSpreadOutput(e.target.checked)}
                      />
                    }
                    label="Spread output into cells"
                  />
                  <Typography variant="caption" color="text.secondary">
                    If the output is a list, it will fill the column. If the
                    output is a list of lists, it will populate the cells in
                    rows and columns starting from the top-left cell.
                  </Typography>
                </>
              )}
              <Stack direction="row" spacing={2} justifyContent="flex-end">
                <Button sx={{ textTransform: "none" }} onClick={onClose}>
                  Cancel
                </Button>
                <Button
                  sx={{ textTransform: "none" }}
                  variant="outlined"
                  onClick={handleClearFormula}
                >
                  Clear
                </Button>
                <Button variant="contained" onClick={handleApplyFormula}>
                  Apply
                </Button>
              </Stack>
            </Stack>
          </Paper>
        </Grow>
      )}
    </Popper>
  );
};

export default SheetFormulaMenu;
