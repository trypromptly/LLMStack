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
const AppRunForm = ({ columns, setData }) => {
  const [selectedAppSlug, setSelectedAppSlug] = useState("");
  const storeApps = useRecoilValue(storeAppsBriefState);
  const app = useRecoilValue(storeAppState(selectedAppSlug));
  const [appInputSchema, setAppInputSchema] = useState({});
  const [appInputUiSchema, setAppInputUiSchema] = useState({});
  const formDataRef = useRef(null);

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

function SheetColumnMenu({ columns, addColumn }) {
  const [open, setOpen] = useState(false);
  const [columnName, setColumnName] = useState("");
  const [columnType, setColumnType] = useState(GridCellKind.Text);
  const anchorRef = useRef(null);
  const columnAppRunData = useRef(null);

  const handleClose = (event) => {
    if (anchorRef.current && anchorRef.current.contains(event.target)) {
      return;
    }

    setOpen(false);
  };

  const handleAddColumn = () => {
    addColumn({
      col: columns.length,
      title: columnName || "New Column",
      kind: columnTypeToDatagridMapping[columnType].kind,
      data:
        columnType === "app_run" && columnAppRunData.current
          ? { ...columnAppRunData.current, kind: columnType }
          : {},
    });
    setOpen(false);
    setColumnName("");
    setColumnType(GridCellKind.Text);
  };

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
      <Popper
        open={open}
        anchorEl={anchorRef.current}
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
                    columns={columns}
                  />
                )}
                <Stack
                  direction="row"
                  spacing={2}
                  sx={{ width: "100%", justifyContent: "center", mt: 2 }}
                >
                  <Button variant="standard" onClick={handleClose}>
                    Cancel
                  </Button>
                  <Button variant="contained" onClick={handleAddColumn}>
                    Add
                  </Button>
                </Stack>
              </Stack>
            </Paper>
          </Grow>
        )}
      </Popper>
    </Box>
  );
}

export default SheetColumnMenu;
