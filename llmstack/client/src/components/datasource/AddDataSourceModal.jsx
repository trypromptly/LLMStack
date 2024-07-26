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
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

import validator from "@rjsf/validator-ajv8";
import { enqueueSnackbar } from "notistack";
import { useState } from "react";
import { useRecoilState, useRecoilValue } from "recoil";
import { dataSourcesState, dataSourceTypesState } from "../../data/atoms";
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

export function AddDataSourceModal({
  open,
  handleCancelCb,
  dataSourceAddedCb,
  modalTitle = "Add New Data Source",
  datasource = null,
}) {
  const dataSourceTypes = useRecoilValue(dataSourceTypesState);
  const [dataSourceName, setDataSourceName] = useState(
    datasource?.name ? datasource.name : "",
  );
  const [dataSourceNameError, setDataSourceNameError] = useState(false);

  const [dataSources, setDataSources] = useRecoilState(dataSourcesState);
  const [dataSourceType, setDataSourceType] = useState(
    datasource?.type ? datasource.type : dataSourceTypes?.[0],
  );
  const [formData, setFormData] = useState({});
  const [destinationFormData, setDestinationFormData] = useState({});
  const [transformationsData, setTransformationsData] = useState([]);
  const [refreshData, setRefreshData] = useState({});
  const reloadDataSourceEntries = useReloadDataSourceEntries();

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
          <span>Data Source Type</span>
          <ButtonGroup
            variant="outlined"
            size="small"
            style={{ display: "inline-block" }}
            disabled={datasource ? true : false}
          >
            {dataSourceTypes.map((dst) => (
              <Button
                key={dst.slug}
                variant={
                  dataSourceType?.slug === dst.slug ? "contained" : "outlined"
                }
                onClick={(e) => {
                  setDataSourceType(dst);
                  setTransformationsData(
                    dst?.pipeline?.transformations?.map(
                      (transformation) => transformation.data || {},
                    ) || [],
                  );
                }}
              >
                {dst.name}
              </Button>
            ))}
          </ButtonGroup>
          <ThemedJsonForm
            schema={dataSourceType?.pipeline?.source?.schema || {}}
            validator={validator}
            uiSchema={{
              ...(dataSourceType?.pipeline?.source?.ui_schema || {}),
              ...{
                "ui:submitButtonOptions": {
                  norender: true,
                },
                "ui:DescriptionFieldTemplate": () => null,
                "ui:TitleFieldTemplate": () => null,
              },
            }}
            formData={formData}
            onChange={({ formData }) => {
              setFormData(formData);
            }}
            disableAdvanced={true}
          />
          {datasource === null && dataSourceType?.pipeline?.transformations && (
            <Accordion defaultExpanded={false}>
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                aria-controls="transformations-content"
                id="transformations-header"
              >
                <Typography>Transformations (Advanced)</Typography>
              </AccordionSummary>
              <AccordionDetails>
                {dataSourceType?.pipeline?.transformations?.map(
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
            dataSourceType?.pipeline?.destination &&
            dataSourceType?.pipeline?.destination?.provider_slug !==
              "weaviate" && (
              <ThemedJsonForm
                schema={dataSourceType?.pipeline?.destination?.schema || {}}
                validator={validator}
                uiSchema={{
                  ...(dataSourceType?.pipeline?.destination?.ui_schema || {}),
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
          {datasource === null && dataSourceType?.pipeline?.source && (
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
                  entry_data: formData,
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
                  type: dataSourceType.id,
                  type_slug: dataSourceType.slug,
                  config: dataSourceType.is_external_datasource ? formData : {},
                  destination_data: destinationFormData,
                  transformations_data: transformationsData,
                  refresh_config: refreshData,
                })
                .then((response) => {
                  // External data sources do not support adding entries
                  if (!dataSourceType.is_external_datasource) {
                    const dataSource = response.data;
                    setDataSources([...dataSources, dataSource]);
                    axios()
                      .post(
                        `/api/datasources/${dataSource.uuid}/add_entry_async`,
                        {
                          entry_data: formData,
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
