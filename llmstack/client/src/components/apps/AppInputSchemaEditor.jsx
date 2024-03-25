import { ArrowDownward, ArrowUpward, Delete } from "@mui/icons-material";
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
import React from "react";

const dataTypes = [
  "string",
  "text",
  "number",
  "boolean",
  "file",
  "select",
  "voice",
  "multi",
];

export function AppInputSchemaEditor({
  fields,
  setFields,
  readOnly = false,
  ...props
}) {
  React.useEffect(() => {
    let newErrors = [];
    if (fields.length === 0) {
      newErrors.push({ message: "At least one field is required" });
    }
    for (let i = 0; i < fields.length; i++) {
      const field = fields[i];
      if (field.name.startsWith("_")) {
        newErrors.push({
          message: `App Input field ${
            i + 1
          } name cannot start with an underscore`,
        });
      }

      if (!field.title) {
        newErrors.push({
          message: `App Input field ${i + 1} must have a name`,
        });
      }
      if (!field.description) {
        newErrors.push({
          message: `App Input field ${i + 1} must have a description`,
        });
      }
      if (!field.type) {
        newErrors.push({
          message: `App Input field ${i + 1} must have a type`,
        });
      }
      if (field.type === "select" && !field.options) {
        newErrors.push({
          message: `App Input field ${i + 1} must have at least one option`,
        });
      }
      if (field.type === "select" && field.options) {
        for (let j = 0; j < field.options.length; j++) {
          const option = field.options[j];
          if (!option.label) {
            newErrors.push({
              message: `App Input field ${i + 1} option ${
                j + 1
              } must have a label`,
            });
          }
          if (!option.value) {
            newErrors.push({
              message: `App Input field ${i + 1} option ${
                j + 1
              } must have a value`,
            });
          }
        }
      }
    }
    props.setErrors(newErrors);
  }, [fields, props]);

  const addField = () => {
    setFields([
      ...fields,
      {
        name: `Field${fields.length + 1}`,
        title: `Field${fields.length + 1}`,
        description: `Description for Field${fields.length + 1}`,
        type: "string",
        required: true,
      },
    ]);
  };

  const updateField = (index, field) => {
    // Check if field name is duplicate
    field.name = field.title.replace(/[^a-zA-Z0-9]/g, "_").toLowerCase();
    const newFields = fields.map((f, i) => (i === index ? field : f));
    setFields(newFields);
  };

  const removeField = (index) => {
    const newFields = fields.filter((_, i) => i !== index);
    setFields(newFields);
  };

  const moveField = (index, direction) => {
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= fields.length) return;
    const newFields = [...fields];
    const temp = newFields[index];
    newFields[index] = newFields[newIndex];
    newFields[newIndex] = temp;
    setFields(newFields);
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
                  value={field.title}
                  onChange={(e) => {
                    updateField(index, { ...field, title: e.target.value });
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
                    value={
                      field.options?.length > 0
                        ? field.options
                            .map((option) => {
                              if (option.value !== undefined) {
                                return `${option.label}:${option.value}`;
                              } else {
                                return option.label;
                              }
                            })
                            .join(",")
                        : ""
                    }
                    onChange={(e) =>
                      updateField(index, {
                        ...field,
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
                  value={field.required ? true : false}
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
