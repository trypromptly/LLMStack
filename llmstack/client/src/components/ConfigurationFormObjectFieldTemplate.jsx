import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Grid,
} from "@mui/material";
import { canExpand } from "@rjsf/utils";

function ObjectFieldGrid(props) {
  const {
    properties,
    disabled,
    readonly,
    uiSchema,
    schema,
    formData,
    onAddClick,
    registry,
  } = props;

  const { AddButton } = registry.templates;

  return (
    <Grid container={true} sx={{ mt: 2 }} gap={1}>
      {properties.map((element, index) =>
        // Remove the <Grid> if the inner element is hidden as the <Grid>
        // itself would otherwise still take up space.
        element.hidden ? (
          element.content
        ) : (
          <Grid item={true} xs={12} key={index}>
            {element.content}
          </Grid>
        ),
      )}
      {canExpand(schema, uiSchema, formData) && (
        <Grid container justifyContent="flex-end">
          <Grid item={true}>
            <AddButton
              className="object-property-expand"
              onClick={onAddClick(schema)}
              disabled={disabled || readonly}
              uiSchema={uiSchema}
              registry={registry}
            />
          </Grid>
        </Grid>
      )}
    </Grid>
  );
}

function RootObjectFieldTemplate(props) {
  const { properties, uiSchema, disableAdvanced } = props;

  let requiredProperties = [];
  let optionalProperties = [];
  properties.forEach((prop) => {
    if (
      disableAdvanced ||
      (uiSchema[prop.name] &&
        "ui:advanced" in uiSchema[prop.name] &&
        !uiSchema[prop.name]["ui:advanced"])
    ) {
      requiredProperties.push(prop);
    } else {
      optionalProperties.push(prop);
    }
  });

  return (
    <>
      <ObjectFieldGrid {...{ ...props, properties: requiredProperties }} />
      {optionalProperties.length > 0 && (
        <Accordion sx={{ marginTop: "16px" }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <strong>Advanced</strong>
          </AccordionSummary>
          <AccordionDetails>
            <ObjectFieldGrid
              {...{ ...props, properties: optionalProperties }}
            />
          </AccordionDetails>
        </Accordion>
      )}
    </>
  );
}

export default function CustomObjectFieldTemplate(props) {
  const { idSchema } = props;

  if (idSchema?.$id === "root") {
    return <RootObjectFieldTemplate {...props} />;
  } else {
    return <ObjectFieldGrid {...props} />;
  }
}
