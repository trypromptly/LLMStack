import {
  Button,
  ButtonGroup,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Typography,
  Box,
  Tab,
} from "@mui/material";
import { TabContext, TabList, TabPanel } from "@mui/lab";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

import validator from "@rjsf/validator-ajv8";
import { enqueueSnackbar } from "notistack";
import { useState, useMemo } from "react";
import { useRecoilState, useRecoilValue } from "recoil";
import { dataSourcesState, pipelineTemplatesState } from "../../data/atoms";
import { axios } from "../../data/axios";
import { useReloadDataSourceEntries } from "../../data/init";
import ThemedJsonForm from "../ThemedJsonForm";

const SOURCE_REFRESH_SCHEMA = {
  type: "object",
  properties: {
    refresh_interval: {
      type: "string",
      title: "Refresh Interval",
      description: "The interval at which the data source should be refreshed.",
      default: "Weekly",
      enum: ["Daily", "Weekly", "Monthly"],
    },
  },
};
const SOURCE_REFRESH_UI_SCHEMA = {
  refresh_interval: {
    "ui:widget": "radio",
    "ui:options": {
      inline: true,
    },
  },
};

function TemplateForm({
  datasource,
  sourceData,
  setSourceData,
  transformationsData,
  setTransformationsData,
  destinationFormData,
  setDestinationFormData,
  refreshData,
  setRefreshData,
  setPipelineSlug,
  setPipeline,
}) {
  const templates = useRecoilValue(pipelineTemplatesState);
  const [selectedTemplate, setSelectedTemplate] = useState(
    useMemo(() => {
      return datasource?.type_slug &&
        templates.find((t) => t.slug === datasource.type_slug)
        ? templates.find((t) => t.slug === datasource.type_slug)
        : templates[0];
    }, [datasource, templates]),
  );

  return (
    <Stack>
      <ButtonGroup
        variant="outlined"
        size="small"
        style={{ display: "inline-block" }}
        disabled={datasource ? true : false}
      >
        {templates.map((template) => (
          <Button
            key={template.slug}
            variant={
              selectedTemplate?.slug === template.slug
                ? "contained"
                : "outlined"
            }
            onClick={(e) => {
              setSelectedTemplate(template);
              setPipelineSlug(template.slug);
              setPipeline({
                source: template?.pipeline?.source || {},
                transformations: template?.pipeline?.transformations || [],
                destination: template?.pipeline?.destination || {},
              });
              setTransformationsData(
                template?.pipeline?.transformations?.map(
                  (transformation) => transformation.data || {},
                ) || [],
              );
            }}
          >
            {template.name}
          </Button>
        ))}
      </ButtonGroup>
      <ThemedJsonForm
        schema={selectedTemplate?.pipeline?.source?.schema || {}}
        validator={validator}
        uiSchema={{
          ...(selectedTemplate?.pipeline?.source?.ui_schema || {}),
          ...{
            "ui:submitButtonOptions": {
              norender: true,
            },
            "ui:DescriptionFieldTemplate": () => null,
            "ui:TitleFieldTemplate": () => null,
          },
        }}
        formData={sourceData}
        onChange={({ formData }) => {
          setSourceData(formData);
        }}
        disableAdvanced={true}
      />
      {datasource === null && selectedTemplate?.pipeline?.transformations && (
        <Accordion defaultExpanded={false}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="transformations-content"
            id="transformations-header"
          >
            <Typography>Transformations (Advanced)</Typography>
          </AccordionSummary>
          <AccordionDetails>
            {selectedTemplate?.pipeline?.transformations?.map(
              (transformation, index) => {
                return (
                  <ThemedJsonForm
                    key={index}
                    schema={transformation.schema}
                    validator={validator}
                    uiSchema={{
                      ...(transformation.ui_schema || {}),
                      ...{
                        "ui:submitButtonOptions": {
                          norender: true,
                        },
                        "ui:DescriptionFieldTemplate": () => null,
                        "ui:TitleFieldTemplate": () => null,
                      },
                    }}
                    formData={transformationsData[index] || {}}
                    onChange={({ formData }) => {
                      setTransformationsData((prev) => {
                        const newTransformationsData = [...prev];
                        newTransformationsData[index] = formData;
                        return newTransformationsData;
                      });
                    }}
                    disableAdvanced={true}
                  />
                );
              },
            )}
          </AccordionDetails>
        </Accordion>
      )}
      {datasource === null &&
        selectedTemplate?.pipeline?.destination &&
        selectedTemplate?.pipeline?.destination?.provider_slug !==
          "weaviate" && (
          <ThemedJsonForm
            schema={selectedTemplate?.pipeline?.destination?.schema || {}}
            validator={validator}
            uiSchema={{
              ...(selectedTemplate?.pipeline?.destination?.ui_schema || {}),
              ...{
                "ui:submitButtonOptions": {
                  norender: true,
                },
                "ui:DescriptionFieldTemplate": () => null,
                "ui:TitleFieldTemplate": () => null,
              },
            }}
            formData={destinationFormData}
            onChange={({ formData }) => {
              setDestinationFormData(formData);
            }}
            disableAdvanced={true}
          />
        )}
      {datasource === null && selectedTemplate?.pipeline?.source && (
        <Accordion defaultExpanded={false}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="refresh-content"
            id="refresh-header"
          >
            <Typography>Refresh Configuration</Typography>
          </AccordionSummary>
          <AccordionDetails>
            {
              <ThemedJsonForm
                schema={SOURCE_REFRESH_SCHEMA}
                validator={validator}
                uiSchema={{
                  ...(SOURCE_REFRESH_UI_SCHEMA || {}),
                  ...{
                    "ui:submitButtonOptions": {
                      norender: true,
                    },
                    "ui:DescriptionFieldTemplate": () => null,
                    "ui:TitleFieldTemplate": () => null,
                  },
                }}
                formData={refreshData || {}}
                onChange={({ formData }) => {
                  setRefreshData(formData);
                }}
                disableAdvanced={true}
              />
            }
          </AccordionDetails>
        </Accordion>
      )}
    </Stack>
  );
}

export function AddDataSourceModal({
  open,
  handleCancelCb,
  dataSourceAddedCb,
  modalTitle = "Add New Data Source",
  datasource = null,
}) {
  const [dataSourceName, setDataSourceName] = useState(
    datasource?.name ? datasource.name : "",
  );
  const [dataSourceNameError, setDataSourceNameError] = useState(false);

  const [dataSources, setDataSources] = useRecoilState(dataSourcesState);

  const reloadDataSourceEntries = useReloadDataSourceEntries();

  const [source, setSource] = useState({});
  const [sourceData, setSourceData] = useState({});
  const [transformations, setTransformations] = useState([]);
  const [transformationsData, setTransformationsData] = useState([]);
  const [destination, setDestination] = useState({});
  const [destinationFormData, setDestinationFormData] = useState({});
  const [formTab, setFormTab] = useState("template");

  const [pipelineSlug, setPipelineSlug] = useState("");

  return (
    <Dialog open={open} onClose={handleCancelCb} sx={{ zIndex: 900 }}>
      <DialogTitle>{modalTitle}</DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          <TextField
            label="Data Source Name"
            value={dataSourceName}
            onChange={(e) => setDataSourceName(e.target.value)}
            disabled={datasource ? true : false}
            required={true}
            defaultValue={datasource?.name || "Untitled"}
            size="small"
            style={{ width: "100%", marginTop: "6px" }}
            error={dataSourceNameError}
          />
          <TabContext value={formTab}>
            <Box style={{ height: "100%" }}>
              <TabList
                onChange={(event, newValue) => setFormTab(newValue)}
                aria-label="simple tabs example"
              >
                <Tab label="Templates" value="template" />
                <Tab label="Advanced" value="advanced" />
              </TabList>
            </Box>
            <TabPanel value="template">
              <TemplateForm
                datasource={datasource}
                sourceData={sourceData}
                setSourceData={setSourceData}
                setSource={setSource}
                transformationsData={transformationsData}
                setTransformationsData={setTransformationsData}
                setTransformations={setTransformations}
                destinationFormData={destinationFormData}
                setDestinationFormData={setDestinationFormData}
                setDestination={setDestination}
                refreshData={{}}
                setRefreshData={() => {}}
                setPipelineSlug={setPipelineSlug}
                setPipeline={({ source, transformations, destination }) => {
                  setSource(source);
                  setTransformations(transformations);
                  setDestination(destination);
                }}
              />
            </TabPanel>
          </TabContext>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancelCb}>Cancel</Button>,
        <Button
          variant="contained"
          onClick={() => {
            if (datasource) {
              axios()
                .post(`/api/datasources/${datasource.uuid}/add_entry_async`, {
                  entry_data: sourceData.data,
                })
                .then(() => {
                  reloadDataSourceEntries();
                  enqueueSnackbar(
                    "Processing Data, please refresh the page in a few minutes",
                    {
                      variant: "success",
                    },
                  );
                })
                .catch((error) => {
                  enqueueSnackbar(
                    `Failed to add entry. ${error?.response?.data}`,
                    {
                      variant: "error",
                    },
                  );
                })
                .finally(() => {
                  handleCancelCb();
                });
            } else {
              if (dataSourceName === "") {
                setDataSourceNameError(true);
                return;
              }

              axios()
                .post("/api/datasources", {
                  name: dataSourceName,
                  type_slug: pipelineSlug,
                  pipeline: {
                    source: source
                      ? {
                          slug: source.slug,
                          provider_slug: source.provider_slug,
                          data: sourceData,
                        }
                      : {},
                    transformations: transformations.map(
                      (transformation, index) => ({
                        slug: transformation.slug,
                        provider_slug: transformation.provider_slug,
                        data: transformationsData[index],
                      }),
                    ),
                    destination: destination
                      ? {
                          slug: destination.slug,
                          provider_slug: destination.provider_slug,
                          data: destinationFormData,
                        }
                      : {},
                  },
                })
                .then((response) => {
                  // External data sources do not support adding entries
                  if (sourceData) {
                    const dataSource = response.data;
                    setDataSources([...dataSources, dataSource]);
                    axios()
                      .post(
                        `/api/datasources/${dataSource.uuid}/add_entry_async`,
                        {
                          source_data: sourceData,
                        },
                      )
                      .then((response) => {
                        dataSourceAddedCb(dataSource);
                      });
                  }
                });
              handleCancelCb();
              enqueueSnackbar(
                "Processing Data, please refresh the page in a few minutes",
                {
                  variant: "success",
                },
              );
            }
          }}
        >
          Submit
        </Button>
      </DialogActions>
    </Dialog>
  );
}
