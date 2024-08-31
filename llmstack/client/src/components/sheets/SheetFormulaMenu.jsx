import React, { useState, useMemo, useEffect, useCallback } from "react";
import {
  Popper,
  Paper,
  Grow,
  Stack,
  TextField,
  Select,
  MenuItem,
  Button,
  Typography,
  InputLabel,
} from "@mui/material";
import AppRunForm from "./AppRunForm";
import ProcessorRunForm from "./ProcessorRunForm";

const formulaTypes = {
  data_transformer: {
    value: "data_transformer",
    label: "Data Transformer",
    description: "Transform data using a LiquidJS template",
  },
  app_run: {
    value: "app_run",
    label: "App Run",
    description: "Run an app to generate formula output",
  },
  processor_run: {
    value: "processor_run",
    label: "Processor Run",
    description: "Run a processor to generate formula output",
  },
};

const SheetFormulaMenu = ({
  anchorEl,
  open,
  onClose,
  cellId,
  formulaCells,
  setFormulaCell,
  columns,
}) => {
  const [formulaType, setFormulaType] = useState(
    formulaCells[cellId]?.formula?.type || "",
  );
  const [transformationTemplate, setTransformationTemplate] = useState(
    formulaCells[cellId]?.formula?.data?.transformation_template || "",
  );
  const [formulaData, setFormulaData] = useState(
    formulaCells[cellId]?.formula?.data || {},
  );
  const formulaDataRef = React.useRef(
    formulaCells[cellId]?.formula?.data || {},
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
    formulaDataRef.current = formulaCells[cellId]?.formula?.data || {};
    setFormulaType(formulaCells[cellId]?.formula?.type || "");
    setTransformationTemplate(
      formulaCells[cellId]?.formula?.data?.transformation_template || "",
    );
    setFormulaData(formulaCells[cellId]?.formula?.data || {});
  }, [cellId, formulaCells, setFormulaData, setFormulaType]);

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

  const handleApplyFormula = () => {
    const newFormula = {
      type: formulaType,
      data: {
        ...formulaDataRef.current,
        transformation_template: transformationTemplate,
      },
    };
    setFormulaCell(cellId, newFormula);
    formulaDataRef.current = null;
    setTransformationTemplate("");
    setFormulaType("data_transformer");
    onClose();
  };

  const handleClearFormula = () => {
    setFormulaCell(cellId, null);
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
          <Paper>
            <Stack gap={2} sx={{ padding: 2 }}>
              <InputLabel>Formula: {cellId}</InputLabel>
              <Typography variant="caption" color="text.secondary">
                Select the type of formula you want to apply
              </Typography>
              <Select
                value={formulaType}
                onChange={(e) => setFormulaType(e.target.value)}
              >
                {Object.keys(formulaTypes).map((type) => (
                  <MenuItem key={type} value={type}>
                    <Stack spacing={0}>
                      <Typography variant="body1">
                        {formulaTypes[type].label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formulaTypes[type].description}
                      </Typography>
                    </Stack>
                  </MenuItem>
                ))}
              </Select>

              {formulaType === "data_transformer" && (
                <TextField
                  label="Transformation Template"
                  value={transformationTemplate}
                  onChange={(e) => setTransformationTemplate(e.target.value)}
                  multiline
                  rows={4}
                  placeholder="Enter LiquidJS template"
                />
              )}

              {formulaType === "app_run" && (
                <AppRunForm
                  setData={(data) => {
                    formulaDataRef.current = {
                      ...formulaDataRef.current,
                      ...data,
                    };
                  }}
                  appSlug={formulaDataRef.current?.app_slug}
                  appInput={formulaDataRef.current?.input}
                />
              )}

              {formulaType === "processor_run" && memoizedProcessorRunForm}

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
