// Helper function to optionally stitch base64 string together
function stitchStringsTogether(string1, string2) {
  return string1 + string2;
}

// Helper function to stitch two objects together. If the key doesn't exist in the first object,
// it will be added. If it does exist, the value will be appended to the existing value in case
// of strings. In case of arrays, entries will be recursively stitched together. We keep the original
// order of the array. If the incoming array has more entries than the existing array, the extra
// entries will be appended to the end of the existing array.
export function stitchObjects(obj1, obj2) {
  if (!obj1) return obj2;
  if (!obj2) return obj1;

  let newObj = { ...obj1 };

  for (const [key, value] of Object.entries(obj2)) {
    // If the key doesn't exist in the first object, add it
    if (!newObj[key]) {
      newObj[key] = value;
      continue;
    }

    // If the key exists in the first object, stitch the values together
    if (Array.isArray(value)) {
      if (Array.isArray(newObj[key])) {
        // If both the values are arrays, stitch the arrays together
        for (let i = 0; i < value.length; i++) {
          if (i < newObj[key].length) {
            if (typeof value[i] === "string") {
              // If newObj[key][i] is a valid base64 string and the incoming value is also a valid base64 string,
              // append binary data together and save it as a base64 string
              newObj[key][i] = stitchStringsTogether(newObj[key][i], value[i]);
              continue;
            }
            if (typeof value[i] === "number") {
              newObj[key][i] = value[i];
              continue;
            }
            // If the index exists in the existing array, stitch the objects together
            newObj[key][i] = stitchObjects(newObj[key][i], value[i]);
          } else {
            // If the index doesn't exist in the existing array, append the object to the end of the array
            newObj[key].push(value[i]);
          }
        }
      } else {
        newObj[key] = newObj[key] + value;
      }
    } else if (typeof value === "object") {
      newObj[key] = stitchObjects(newObj[key], value);
    } else if (typeof value === "string") {
      newObj[key] = stitchStringsTogether(newObj[key], value);
    } else if (typeof value === "number") {
      newObj[key] = value;
    } else {
      newObj[key] = newObj[key] + value;
    }
  }
  return newObj;
}

/**
 *
 * @param {*} inputFields - array of input fields with name, title, description, type, required etc.,
 * @returns {object} schema
 */
export function getJSONSchemaFromInputFields(inputFields) {
  let schema = {
    type: "object",
    properties: {},
  };

  let uiSchema = {};
  let order = [];
  let required = [];

  inputFields &&
    inputFields.forEach((field) => {
      order.push(field.name);

      if (field.required) {
        required.push(field.name);
      }

      schema.properties[field.name] = {
        type:
          field.type === "text" ||
          field.type === "voice" ||
          field.type === "file" ||
          field.type === "select"
            ? "string"
            : field.type,
        title: field.title,
        description: field.description,
      };

      if (field.default) {
        schema.properties[field.name].default = field.default;
      }

      if (field.type === "text") {
        uiSchema[field.name] = {
          "ui:widget": "textarea",
        };
      }

      if (field.type === "boolean") {
        uiSchema[field.name] = {
          "ui:widget": "radio",
        };
      }

      if (field.type === "file") {
        uiSchema[field.name] = {
          "ui:widget": "file",
        };
        schema.properties[field.name].format = "data-url";
        schema.properties[field.name].pattern =
          "data:(.*);name=(.*);base64,(.*)";
      }

      if (field.type === "voice") {
        uiSchema[field.name] = {
          "ui:widget": "voice",
        };
        schema.properties[field.name].format = "data-url";
        schema.properties[field.name].pattern =
          "data:(.*);name=(.*);base64,(.*)";
      }

      if (field.type === "select") {
        uiSchema[field.name] = {
          "ui:widget": "select",
        };
        schema.properties[field.name].enum = field.options?.map(
          (option) => option.value,
        );
        schema.properties[field.name].enumNames = field.options?.map(
          (option) => option.label,
        );

        if (field["ui:options"] && uiSchema[field.name]) {
          uiSchema[field.name]["ui:options"] = field["ui:options"];
        }
      }
    });

  uiSchema["ui:order"] = order;
  uiSchema["ui:required"] = required;

  return { schema, uiSchema };
}
