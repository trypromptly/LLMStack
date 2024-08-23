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
import validator from "@rjsf/validator-ajv8";
import { GridCellKind } from "@glideapps/glide-data-grid";
import { useRecoilValue } from "recoil";
import { AddOutlined } from "@mui/icons-material";
import { getJSONSchemaFromInputFields } from "../../data/utils";
import { storeAppsBriefState, storeAppState } from "../../data/atoms";
import ThemedJsonForm from "../ThemedJsonForm";
import TextFieldWithVars from "../apps/TextFieldWithVars";
import "@glideapps/glide-data-grid/dist/index.css";

export const columnTypeToDatagridMapping = {
  text: {
    kind: GridCellKind.Text,
  },
  number: {
    kind: GridCellKind.Number,
  },
  image: {
    kind: GridCellKind.Image,
  },
  file: {
    kind: GridCellKind.Image,
  },
  app_run: {
    kind: GridCellKind.Custom,
  },
};

// Allow the user to pick an app, and then show the form for that app input
const AppRunForm = ({ columns, data, setData }) => {
  const [selectedAppSlug, setSelectedAppSlug] = useState(data?.app_slug || "");
  const storeApps = useRecoilValue(storeAppsBriefState);
  const app = useRecoilValue(storeAppState(selectedAppSlug));
  const [appInputSchema, setAppInputSchema] = useState({});
  const [appInputUiSchema, setAppInputUiSchema] = useState({});
  const formDataRef = useRef(data?.input || {});

  const TextWidget = (props) => {
    return (
      <TextFieldWithVars
        {...props}
        introText={"Available columns"}
        schemas={columns.map((c, index) => ({
          id: `${index}`,
          pillPrefix: `${index}:${c.title}`,
          label: `${index}: ${c.title}`,
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
            setTimeout(() => {
              setData({
                app_slug: app.slug,
                input: e.formData,
              });
            }, 10);
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
    if (column?.kind === GridCellKind.Custom) {
      setColumnType(column?.data?.kind || GridCellKind.Text);
    } else {
      setColumnType(column?.kind || GridCellKind.Text);
    }

    setColumnName(column?.title || "");
    columnAppRunData.current = column?.data || {};
  }, [column]);

  const handleAddOrEditColumn = () => {
    const newColumn = {
      col: columns.length,
      title: columnName || "New Column",
      kind: columnTypeToDatagridMapping[columnType].kind,
      data:
        columnType === "app_run" && columnAppRunData.current
          ? { ...columnAppRunData.current, kind: columnType }
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
                {column && (
                  <Button variant="contained" onClick={handleColumnDelete}>
                    Delete
                  </Button>
                )}
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
