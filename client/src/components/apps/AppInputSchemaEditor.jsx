import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Button,
  Container,
  IconButton,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { Delete, ArrowUpward, ArrowDownward } from "@mui/icons-material";

const dataTypes = [
  "string",
  "text",
  "number",
  "boolean",
  "file",
  "select",
  "voice",
];

export function AppInputSchemaEditor({
  schema,
  setSchema,
  uiSchema,
  setUiSchema,
  initSchema = {},
  readOnly = false,
}) {
  const defaultFields = useMemo(() => [initSchema], [initSchema]);
  const [fields, setFields] = useState(defaultFields);

  useEffect(() => {
    const order = uiSchema["ui:order"] || [];
    const unorderedProperties = Object.entries(schema.properties || {});
    const orderedProperties = order
      .map((key) => unorderedProperties.find(([name]) => name === key))
      .filter((item) => item);

    const remainingProperties = unorderedProperties.filter(
      ([name]) => !order.includes(name),
    );

    const properties = [...orderedProperties, ...remainingProperties];

    const schemaFields = properties.map(([name, property]) => {
      let type =
        property.type === "string" &&
        uiSchema[name]?.["ui:widget"] === "textarea"
          ? "text"
          : property.type;

      if (property.format === "data-url") {
        type = uiSchema[name]?.["ui:widget"] === "voice" ? "voice" : "file";
      }

      if (property.type === "string" && property.enum) {
        type = "select";
      }

      const options =
        type === "select"
          ? property.enum.map((value, index) => ({
              label: property.enumNames[index],
              value,
            }))
          : undefined;

      const optionsString =
        type === "select" && options.length > 0
          ? options
              .map((option) =>
                option.value !== undefined
                  ? `${option.label}:${option.value}`
                  : option.label,
              )
              .join(",")
          : "";

      return {
        name: property.title || property.name,
        description: property.description,
        type,
        options,
        optionsString,
        required: (schema.required || []).includes(name),
      };
    });
    setFields(schemaFields);
  }, [schema, uiSchema]);

  const generateSchemas = useCallback(
    (newFields) => {
      const fieldsWithLabels = newFields.map((field) => ({
        ...field,
        // Sanitize field names so they can be used as valid keys in json
        name: field.name.replace(/[^a-zA-Z0-9]/g, "_").toLowerCase(),
        label: field.name,
      }));

      const generatedSchema = {
        type: "object",
        properties: fieldsWithLabels.reduce((props, field) => {
          const type =
            field.type === "text" ||
            field.type === "file" ||
            field.type === "voice" ||
            field.type === "select"
              ? "string"
              : field.type;
          props[field.name] = {
            type,
            description: field.description,
            title: field.label,
          };
          if (field.type === "file") {
            props[field.name].format = "data-url";
            props[field.name].default = "";
            props[field.name].pattern = "data:(.*);name=(.*);base64,(.*)";
          }
          if (field.type === "voice") {
            props[field.name].format = "data-url";
            props[field.name].default = "";
            props[field.name].pattern = "data:(.*);name=(.*);base64,(.*)";
          }
          if (field.type === "select") {
            const field_options = field?.options || [];
            props[field.name].enum = field_options.map(
              (option) => option.value,
            );
            props[field.name].enumNames = field_options.map(
              (option) => option.label,
            );
          }
          return props;
        }, {}),
        required: fieldsWithLabels
          .filter((field) => field.required)
          .map((field) => field.name),
      };

      const generatedUiSchema = {
        ...fieldsWithLabels.reduce((ui, field) => {
          if (field.type === "text") {
            ui[field.name] = { "ui:widget": "textarea" };
          }
          if (field.type === "file") {
            ui[field.name] = { "ui:widget": "file" };
          }
          if (field.type === "voice") {
            ui[field.name] = { "ui:widget": "voice" };
          }
          return ui;
        }, {}),
        "ui:order": fieldsWithLabels.map((field) => field.name),
      };

      setSchema(generatedSchema);
      setUiSchema(generatedUiSchema);
    },
    [setSchema, setUiSchema],
  );

  useEffect(() => {
    if (fields.length === 0) {
      setFields(defaultFields);
      generateSchemas(defaultFields);
    }
  }, [fields, defaultFields, generateSchemas]);

  const addField = () => {
    setFields([
      ...fields,
      { name: "", description: "", type: "string", required: false },
    ]);
  };

  const updateField = (index, field) => {
    // Check if field name is duplicate
    const duplicate =
      fields.find((f, i) => i !== index && f.name === field.name) !== undefined;

    const newFields = fields.map((f, i) => (i === index ? field : f));
    setFields(newFields);
    // We hit updateField when the user is typing in the field name, so we don't want to generate schemas if there are duplicates
    if (!duplicate) {
      generateSchemas(newFields);
    }
  };

  const removeField = (index) => {
    const newFields = fields.filter((_, i) => i !== index);
    setFields(newFields);
    generateSchemas(newFields);
  };

  const moveField = (index, direction) => {
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= fields.length) return;
    const newFields = [...fields];
    const temp = newFields[index];
    newFields[index] = newFields[newIndex];
    newFields[newIndex] = temp;
    setFields(newFields);
    generateSchemas(newFields);
  };

  return (
    <Container>
      <Typography mb={3} style={{ margin: 10 }}>
        Define the input fields you want this app to accept. These will be
        rendered as a form for users to fill out. If using the app via the API,
        the input fields will form the JSON schema for the input data.
      </Typography>
      <Table
        sx={{
          "& .MuiTableCell-root": { padding: "10px 5px" },
          "& .MuiInputBase-input": { padding: "10px" },
        }}
      >
        <TableHead>
          <TableRow
            sx={{
              "& .MuiTableCell-root": { fontWeight: "bold" },
            }}
          >
            <TableCell>Name</TableCell>
            <TableCell>Description</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Options</TableCell>
            <TableCell>Required</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {fields.map((field, index) => (
            <TableRow
              key={index}
              style={readOnly ? { opacity: 0.5, pointerEvents: "none" } : {}}
            >
              <TableCell>
                <TextField
                  value={field.name}
                  onChange={(e) => {
                    updateField(index, { ...field, name: e.target.value });
                  }}
                />
              </TableCell>
              <TableCell>
                <TextField
                  value={field.description}
                  onChange={(e) =>
                    updateField(index, {
                      ...field,
                      description: e.target.value,
                    })
                  }
                />
              </TableCell>
              <TableCell>
                <Select
                  value={field.type}
                  onChange={(e) =>
                    updateField(index, { ...field, type: e.target.value })
                  }
                >
                  {dataTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type}
                    </MenuItem>
                  ))}
                </Select>
              </TableCell>
              <TableCell>
                {field.type === "select" ? (
                  <TextField
                    value={field.optionsString || ""}
                    onChange={(e) =>
                      updateField(index, {
                        ...field,
                        optionsString: e.target.value,
                        options: e.target.value.split(",").map((item) => {
                          const [label, value] = item.split(":");
                          return {
                            label: label,
                            value: value ? value.trim() : value,
                          };
                        }),
                      })
                    }
                    placeholder="Label1:Value1, Label2:Value2"
                  />
                ) : (
                  ""
                )}
              </TableCell>
              <TableCell>
                <Select
                  value={field.required}
                  onChange={(e) =>
                    updateField(index, { ...field, required: e.target.value })
                  }
                >
                  <MenuItem value={true}>Yes</MenuItem>
                  <MenuItem value={false}>No</MenuItem>
                </Select>
              </TableCell>
              <TableCell>
                <IconButton onClick={() => moveField(index, -1)} size="small">
                  <ArrowUpward />
                </IconButton>
                <IconButton onClick={() => moveField(index, 1)} size="small">
                  <ArrowDownward />
                </IconButton>
                <IconButton onClick={() => removeField(index)} size="small">
                  <Delete />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <Button
        variant="contained"
        onClick={addField}
        disabled={readOnly}
        sx={{
          mt: 2,
          textTransform: "none",
          float: "right",
          marginBottom: 2,
          backgroundColor: "#6287ac",
          color: "#fff",
        }}
      >
        Add Field
      </Button>
    </Container>
  );
}
