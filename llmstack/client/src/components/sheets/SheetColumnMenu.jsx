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
} from "@mui/material";
import { DeleteOutlined } from "@mui/icons-material";
import validator from "@rjsf/validator-ajv8";
import { GridCellKind } from "@glideapps/glide-data-grid";
import { useRecoilValue } from "recoil";
import { AddOutlined } from "@mui/icons-material";
import { getJSONSchemaFromInputFields } from "../../data/utils";
import { storeAppsBriefState, storeAppState } from "../../data/atoms";
import ThemedJsonForm from "../ThemedJsonForm";
import TextFieldWithVars from "../apps/TextFieldWithVars";
import "@glideapps/glide-data-grid/dist/index.css";

const numberToLetters = (num) => {
  let letters = "";
  while (num >= 0) {
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[num % 26] + letters;
    num = Math.floor(num / 26) - 1;
  }
  return letters;
};

// Allow the user to pick an app, and then show the form for that app input
const AppRunForm = ({ columns, data, setData }) => {
  const [selectedAppSlug, setSelectedAppSlug] = useState(data?.app_slug || "");
  const storeApps = useRecoilValue(storeAppsBriefState);
  const app = useRecoilValue(storeAppState(selectedAppSlug || "super-agent"));
  const [appInputSchema, setAppInputSchema] = useState({});
  const [appInputUiSchema, setAppInputUiSchema] = useState({});
  const formDataRef = useRef(data?.input || {});

  const TextWidget = (props) => {
    return (
      <TextFieldWithVars
        {...props}
        introText={"Available columns"}
        schemas={columns.map((c, index) => ({
          id: `${numberToLetters(index)}`,
          pillPrefix: `${numberToLetters(index)}:${c.title}`,
          label: `${numberToLetters(index)}: ${c.title}`,
        }))}
      />
    );
  };

  useEffect(() => {
    if (data) {
      setSelectedAppSlug(data.app_slug);
      formDataRef.current = data.input || {};
    }
  }, [data]);

  useEffect(() => {
    if (app) {
      const { schema, uiSchema } = getJSONSchemaFromInputFields(
        app.data?.input_fields || [],
      );
      setAppInputSchema(schema);
      setAppInputUiSchema(uiSchema);
      setData({
        app_slug: app.slug,
        input: {},
      });
    }
  }, [app, setData]);

  return (
    <Box>
      <Select
        value={selectedAppSlug}
        id="app-select"
        helperText="Select the app to run"
        onChange={(e) => setSelectedAppSlug(e.target.value)}
        onClick={(e) => e.stopPropagation()}
      >
        {storeApps.map((app) => (
          <MenuItem value={app.slug} key={app.uuid}>
            {app.name}
          </MenuItem>
        ))}
      </Select>
      {app && (
        <ThemedJsonForm
          disableAdvanced={true}
          schema={appInputSchema}
          uiSchema={{
            ...appInputUiSchema,
            "ui:submitButtonOptions": {
              norender: true,
            },
          }}
          submitBtn={null}
          validator={validator}
          formData={formDataRef.current}
          onChange={(e) => {
            setData({
              app_slug: app.slug,
              input: e.formData,
            });
            formDataRef.current = e.formData;
          }}
          fields={{
            multi: TextWidget,
          }}
          widgets={{
            text: TextWidget,
            textarea: TextWidget,
            file: TextWidget,
          }}
        />
      )}
    </Box>
  );
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
  const columnAppRunData = useRef(column?.data || {});

  useEffect(() => {
    setColumnType(column?.kind || GridCellKind.Text);
    setColumnName(column?.title || "");
    columnAppRunData.current = column?.data || {};
  }, [column]);

  const handleAddOrEditColumn = () => {
    const newColumn = {
      col: column ? column.col : numberToLetters(columns.length),
      title: columnName || "New Column",
      kind: columnType,
      data:
        columnType === "app_run" && columnAppRunData.current
          ? columnAppRunData.current
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
      sx={{ width: "450px" }}
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
              </Select>
              {columnType === "app_run" && (
                <AppRunForm
                  setData={(data) => {
                    columnAppRunData.current = data;
                  }}
                  data={columnAppRunData.current}
                  columns={columns}
                />
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
