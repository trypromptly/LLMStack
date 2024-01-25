import { useParams } from "react-router-dom";
import ReactGA from "react-ga4";
import { useEffect, useState } from "react";

import {
  AppBar,
  Box,
  Button,
  Container,
  Stack,
  SvgIcon,
  Toolbar,
  Typography,
  Card,
  CardHeader,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from "@mui/material";
import { LoadingButton } from "@mui/lab";

import validator from "@rjsf/validator-ajv8";
import {
  embedDatasourceState,
  embedDatasourceEntriesState,
} from "../data/atoms";
import { useRecoilValue, useSetRecoilState } from "recoil";

import { ReactComponent as GithubIcon } from "../assets/images/icons/github.svg";
import { DataSourceEntries } from "./data";
import ThemedJsonForm from "../components/ThemedJsonForm";
import { axios } from "../data/axios";

const SITE_NAME = process.env.REACT_APP_SITE_NAME || "LLMStack";

function getFileSize(value) {
  let size = value;
  const units = ["", "K", "M", "G", "T", "P", "E", "Z", "Y"];
  let unit = 0;
  while (size >= 1024) {
    size /= 1024;
    unit += 1;
  }

  return size > 0
    ? size.toFixed(2) + " " + units[unit]
    : size + " " + units[unit];
}

function useReloadDataSourceEntries(datasourceId) {
  const setDataSourceEntries = useSetRecoilState(
    embedDatasourceEntriesState(datasourceId),
  );
  return () => {
    axios()
      .get(`/api/datasources/${datasourceId}/entries`)
      .then((res) => {
        setDataSourceEntries(res.data);
      })
      .catch((err) => {
        console.log(err);
      });
  };
}
function useReloadDataSource(datasourceId) {
  const setDataSource = useSetRecoilState(embedDatasourceState(datasourceId));
  return () => {
    axios()
      .get(`/api/datasources/${datasourceId}`)
      .then((res) => {
        setDataSource(res.data);
      })
      .catch((err) => {
        console.log(err);
      });
  };
}

function DatasourceRenderPage({ headless = false }) {
  const { datasourceId, embed } = useParams();
  const [addDataModal, setAddDataModal] = useState(false);
  const datasource = useRecoilValue(embedDatasourceState(datasourceId));
  const reloadDataSourceEntries = useReloadDataSourceEntries(datasourceId);
  const reloadDataSource = useReloadDataSource(datasourceId);
  const datasourceEntries = useRecoilValue(
    embedDatasourceEntriesState(datasourceId),
  );
  const [formData, setFormData] = useState({});
  const [submitButtonLoading, setSubmitButtonLoading] = useState(false);

  useEffect(() => {
    ReactGA.initialize(
      process.env.REACT_APP_GA_MEASUREMENT_ID || "G-WV60HC9CHD",
      {
        gaOptions: {
          cookieFlags: "SameSite=None;Secure",
        },
      },
    );
    ReactGA.send({
      hitType: "pageview",
      page: window.location.href,
      title: document.title,
    });
  });

  return (
    <Stack container spacing={2}>
      {!embed && (
        <AppBar
          position="static"
          sx={{
            backgroundColor: "#fff",
            color: "#000",
          }}
        >
          <Container maxWidth="xl">
            <Toolbar
              disableGutters
              sx={{
                width: "100%",
                margin: "0 auto",
              }}
            >
              <Box sx={{ flexGrow: 1 }} />
              {SITE_NAME === "LLMStack" && (
                <SvgIcon
                  component={GithubIcon}
                  sx={{ width: "54px", height: "54px" }}
                  viewBox="-10 -4 28 26"
                  onClick={() => {
                    window.location.href =
                      "https://github.com/trypromptly/llmstack";
                  }}
                />
              )}
            </Toolbar>
          </Container>
        </AppBar>
      )}
      <Box sx={{ justifyContent: "center" }}>{headless && <p></p>}</Box>
      <Box>
        <Card
          sx={{
            width: "90%",
            margin: 10,
            textAlign: "left",
            cursor: "default",
            boxShadow: "0 0 10px #449",
          }}
          elevation={2}
        >
          <CardHeader
            title={
              <Stack direction="row" spacing={2}>
                <Typography
                  style={{
                    fontSize: "16px",
                    fontWeight: 600,
                    fontFamily: "Lato, sans-serif",
                    marginTop: "8px",
                  }}
                >
                  {`Datasource Name: ${datasource.name}`}
                </Typography>
                <Button
                  variant="contained"
                  onClick={(e) => {
                    setAddDataModal(true);
                  }}
                >
                  Add Data
                </Button>
              </Stack>
            }
            subheader={
              <Stack direction="row" spacing={4}>
                <Typography
                  style={{
                    fontSize: "16px",
                    fontWeight: 600,
                    fontFamily: "Lato, sans-serif",
                    marginTop: "8px",
                  }}
                >
                  {`Datasource Type: ${datasource?.type?.name}`}
                </Typography>
                <Typography
                  style={{
                    fontSize: "16px",
                    fontWeight: 600,
                    fontFamily: "Lato, sans-serif",
                    marginTop: "8px",
                  }}
                >{`Size: ${getFileSize(datasource.size)}`}</Typography>
              </Stack>
            }
          ></CardHeader>
          <DataSourceEntries
            dataSourceEntryData={datasourceEntries}
            onDatasourceEntryDelete={() => {
              reloadDataSourceEntries();
              reloadDataSource();
            }}
          />
        </Card>
      </Box>
      <Box
        sx={{
          justifyContent: "center",
          textAlign: "center",
          bottom: "0px",
          margin: "0 auto",
          paddingTop: "10px",
        }}
      >
        {headless && !process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT && (
          <Typography sx={{ textAlign: "center" }} variant="caption">
            Powered by{" "}
            <a href="https://trypromptly.com" target="_blank" rel="noreferrer">
              Promptly
            </a>
          </Typography>
        )}
      </Box>

      {addDataModal && (
        <Dialog open={addDataModal} onClose={() => {}} sx={{ zIndex: 900 }}>
          <DialogTitle>Add Data</DialogTitle>
          <DialogContent>
            <Stack spacing={2}>
              <TextField
                label="Data Source Name"
                disabled={true}
                defaultValue={datasource?.name || "Untitled"}
                size="small"
                style={{ width: "100%", marginTop: "6px" }}
              />
              <ThemedJsonForm
                schema={datasource?.type?.entry_config_schema || {}}
                validator={validator}
                uiSchema={{
                  ...(datasource?.type?.entry_config_ui_schema || {}),
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
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => {
                setAddDataModal(false);
              }}
            >
              Cancel
            </Button>
            ,
            <LoadingButton
              loading={submitButtonLoading}
              disabled={submitButtonLoading}
              variant="contained"
              onClick={() => {
                if (datasource) {
                  setSubmitButtonLoading(true);
                  axios()
                    .post(
                      `/api/datasources/${datasource.uuid}/add_entry_async`,
                      {
                        entry_data: formData,
                      },
                    )
                    .then((res) => {
                      setTimeout(() => {
                        reloadDataSourceEntries();
                        reloadDataSource();
                        setAddDataModal(false);
                      }, 2000);
                    })
                    .catch((err) => {});
                }
              }}
            >
              Submit
            </LoadingButton>
          </DialogActions>
        </Dialog>
      )}
    </Stack>
  );
}

export default DatasourceRenderPage;
