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
import { useState, useMemo, useEffect } from "react";
import { useRecoilState, useRecoilValue } from "recoil";
import {
  dataSourcesState,
  pipelineTemplatesState,
  sourceTypesState,
  transformationTypesState,
  destinationTypesState,
  embeddingTypesState,
} from "../../data/atoms";
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
      default: "None",
      enum: ["None"],
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

function AdvancedForm({
  datasource,
  source,
  setSource,
  sourceData,
  setSourceData,
  transformations,
  setTransformations,
  transformationsData,
  setTransformationsData,
  embedding,
  setEmbedding,
  embeddingData,
  setEmbeddingData,
  destination,
  setDestination,
  destinationFormData,
  setDestinationData,
}) {
  const sourceTypes = useRecoilValue(sourceTypesState);
  const transformationTypes = useRecoilValue(transformationTypesState);
  const destinationTypes = useRecoilValue(destinationTypesState);
  const embeddingTypes = useRecoilValue(embeddingTypesState);

  return (
    <Stack>
      <Accordion defaultExpanded={true}>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="source-content"
          id="source-header"
        >
          <Typography>Source</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <ButtonGroup
            variant="outlined"
            size="small"
            style={{ display: "inline-block" }}
          >
            {sourceTypes.map((sourceType) => (
              <Button
                key={sourceType.slug}
                variant={
                  source?.slug === sourceType.slug &&
                  source?.provider_slug === sourceType.provider_slug
                    ? "contained"
                    : "outlined"
                }
                onClick={(e) => {
                  setSource(sourceType);
                }}
              >
                {sourceType.slug}
              </Button>
            ))}
          </ButtonGroup>
          <ThemedJsonForm
            schema={source?.schema || {}}
            validator={validator}
            uiSchema={{
              ...(source?.ui_schema || {}),
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
        </AccordionDetails>
      </Accordion>
      <Accordion defaultExpanded={false}>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="transformations-content"
          id="transformations-header"
        >
          <Typography>Transformations</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <ButtonGroup
            variant="outlined"
            size="small"
            style={{ display: "inline-block" }}
          >
            {transformationTypes.map((transformationType) => (
              <Button
                key={transformationType.slug}
                variant={
                  transformationType.slug === transformations[0]?.slug &&
                  transformationType.provider_slug ===
                    transformations[0]?.provider_slug
                    ? "contained"
                    : "outlined"
                }
                onClick={(e) => {
                  setTransformations([transformationType]);
                }}
              >
                {transformationType.slug}
              </Button>
            ))}
            {datasource === null && (
              <ThemedJsonForm
                schema={transformations[0]?.schema || {}}
                validator={validator}
                uiSchema={{
                  ...(transformations[0]?.ui_schema || {}),
                  ...{
                    "ui:submitButtonOptions": {
                      norender: true,
                    },
                    "ui:DescriptionFieldTemplate": () => null,
                    "ui:TitleFieldTemplate": () => null,
                  },
                }}
                formData={transformationsData[0]}
                onChange={({ formData }) => {
                  setTransformationsData([formData]);
                }}
                disableAdvanced={true}
              />
            )}
          </ButtonGroup>
          <ButtonGroup
            variant="outlined"
            size="small"
            style={{ display: "inline-block" }}
          >
            {embeddingTypes.map((embeddingType) => (
              <Button
                key={embeddingType.slug}
                variant={
                  embedding?.slug === embeddingType.slug &&
                  embedding.provider_slug === embeddingType.provider_slug
                    ? "contained"
                    : "outlined"
                }
                onClick={(e) => {
                  setEmbedding(embeddingType);
                }}
              >
                {embeddingType.slug}
              </Button>
            ))}
          </ButtonGroup>
          {datasource === null && (
            <ThemedJsonForm
              schema={embedding?.schema || {}}
              validator={validator}
              uiSchema={{
                ...(embedding?.ui_schema || {}),
                ...{
                  "ui:submitButtonOptions": {
                    norender: true,
                  },
                  "ui:DescriptionFieldTemplate": () => null,
                  "ui:TitleFieldTemplate": () => null,
                },
              }}
              formData={embeddingData}
              onChange={({ formData }) => {
                setEmbeddingData(formData);
              }}
              disableAdvanced={true}
            />
          )}
        </AccordionDetails>
      </Accordion>
      <Accordion defaultExpanded={false}>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="destination-content"
          id="destination-header"
        >
          <Typography>Destination</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <ButtonGroup
            variant="outlined"
            size="small"
            style={{ display: "inline-block" }}
          >
            {destinationTypes.map((destinationType) => (
              <Button
                key={destinationType.slug}
                variant={
                  destination?.slug === destinationType.slug &&
                  destination.provider_slug === destinationType.provider_slug
                    ? "contained"
                    : "outlined"
                }
                onClick={(e) => {
                  setDestination(destinationType);
                }}
              >
                {destinationType.slug}
              </Button>
            ))}
          </ButtonGroup>
          {datasource === null && (
            <ThemedJsonForm
              schema={destination?.schema || {}}
              validator={validator}
              uiSchema={{
                ...(destination?.ui_schema || {}),
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
                setDestinationData(formData);
              }}
              disableAdvanced={true}
            />
          )}
        </AccordionDetails>
      </Accordion>
    </Stack>
  );
}

function TemplateForm({
  datasource,
  sourceData,
  setSourceData,
  transformationsData,
  setTransformationsData,
  destinationFormData,
  setDestinationData,
  setPipelineSlug,
  setPipeline,
}) {
  const templates = useRecoilValue(pipelineTemplatesState);
  const [selectedTemplate, setSelectedTemplate] = useState(
    useMemo(() => {
      return datasource?.type?.slug &&
        templates.find((t) => t.slug === datasource.type?.slug)
        ? templates.find((t) => t.slug === datasource.type?.slug)
        : templates[0];
    }, [datasource, templates]),
  );

  useEffect(() => {
    if (selectedTemplate) {
      setPipelineSlug(selectedTemplate.slug);
      setPipeline({
        source: selectedTemplate?.pipeline?.source || {},
        transformations: selectedTemplate?.pipeline?.transformations || [],
        destination: selectedTemplate?.pipeline?.destination || {},
      });
      setTransformationsData(
        selectedTemplate?.pipeline?.transformations?.map(
          (transformation) => transformation.data || {},
        ) || [],
      );
    }
  }, [selectedTemplate]);
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
          "promptly" && (
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
              setDestinationData(formData);
            }}
            disableAdvanced={true}
          />
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

  const [embedding, setEmbedding] = useState({});
  const [embeddingData, setEmbeddingData] = useState({});

  const [destination, setDestination] = useState({});
  const [destinationFormData, setDestinationData] = useState({});

  const [formTab, setFormTab] = useState(
    datasource
      ? datasource.type.slug !== "custom"
        ? "template"
        : "advanced"
      : "template",
  );
  const [refreshData, setRefreshData] = useState({});
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
                <Tab
                  label="Templates"
                  value="template"
                  disabled={datasource && formTab !== "template"}
                />
                <Tab
                  label="Advanced"
                  value="advanced"
                  disabled={datasource && formTab !== "advanced"}
                />
              </TabList>
            </Box>
            <TabPanel value="template">
              <TemplateForm
                datasource={datasource}
                sourceData={sourceData}
                setSourceData={setSourceData}
                transformationsData={transformationsData}
                setTransformationsData={setTransformationsData}
                destinationFormData={destinationFormData}
                setDestinationData={setDestinationData}
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
            <TabPanel value="advanced">
              <AdvancedForm
                datasource={datasource}
                source={source}
                setSource={setSource}
                sourceData={sourceData}
                setSourceData={setSourceData}
                transformations={transformations}
                setTransformations={setTransformations}
                transformationsData={transformationsData}
                setTransformationsData={setTransformationsData}
                embedding={embedding}
                setEmbedding={setEmbedding}
                embeddingData={embeddingData}
                setEmbeddingData={setEmbeddingData}
                destination={destination}
                setDestination={setDestination}
                destinationFormData={destinationFormData}
                setDestinationData={setDestinationData}
              />
            </TabPanel>
          </TabContext>
          {datasource === null && source && (
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
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancelCb}>Cancel</Button>,
        <Button
          variant="contained"
          onClick={() => {
            if (datasource) {
              axios()
                .post(`/api/datasources/${datasource.uuid}/add_entry_async`, {
                  source_data: sourceData,
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
                          data: {},
                        }
                      : {},
                    transformations: transformations.map(
                      (transformation, index) => ({
                        slug: transformation.slug,
                        provider_slug: transformation.provider_slug,
                        data: transformationsData[index],
                      }),
                    ),
                    embedding: embedding
                      ? {
                          slug: embedding.slug,
                          provider_slug: embedding.provider_slug,
                          data: embeddingData,
                        }
                      : {},
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
