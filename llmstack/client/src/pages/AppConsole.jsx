import ChangeHistoryIcon from "@mui/icons-material/ChangeHistory";
import EditIcon from "@mui/icons-material/Edit";
import PreviewIcon from "@mui/icons-material/Preview";
import PublishedWithChangesIcon from "@mui/icons-material/PublishedWithChanges";
import TimelineIcon from "@mui/icons-material/Timeline";
import UnpublishedIcon from "@mui/icons-material/Unpublished";
import StorefrontIcon from "@mui/icons-material/Storefront";
import {
  Alert,
  AlertTitle,
  AppBar,
  Box,
  Button,
  CircularProgress,
  Grid,
  Paper,
  Stack,
  SvgIcon,
  Tooltip,
} from "@mui/material";
import { enqueueSnackbar } from "notistack";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useRecoilValue } from "recoil";
import { ReactComponent as CodeIcon } from "../assets/images/icons/code.svg";
import { ReactComponent as DiscordIcon } from "../assets/images/icons/discord.svg";
import { ReactComponent as IntegrationsIcon } from "../assets/images/icons/integrations.svg";
import { ReactComponent as SlackIcon } from "../assets/images/icons/slack.svg";
import { ReactComponent as TemplateIcon } from "../assets/images/icons/template.svg";
import { ReactComponent as TwilioIcon } from "../assets/images/icons/twilio.svg";
import { ReactComponent as WebIcon } from "../assets/images/icons/web.svg";
import { AppApiExamples } from "../components/apps/AppApiExamples";
import { AppDiscordConfigEditor } from "../components/apps/AppDiscordConfigEditor";
import { AppEditor } from "../components/apps/AppEditor";
import AppEditorMenu from "../components/apps/AppEditorMenu";
import { AppPreview } from "../components/apps/AppPreview";
import { PublishModal, UnpublishModal } from "../components/apps/AppPublisher";
import { AppRunHistory } from "../components/apps/AppRunHistory";
import { AppSlackConfigEditor } from "../components/apps/AppSlackConfigEditor";
import { AppTemplate } from "../components/apps/AppTemplate";
import { AppTwilioConfigEditor } from "../components/apps/AppTwilioConfigEditor";
import { AppVersions } from "../components/apps/AppVersions";
import { AppDetailsEditor } from "../components/apps/AppDetailsEditor";
import { AppWebConfigEditor } from "../components/apps/AppWebConfigEditor";
import { useValidationErrorsForAppConsole } from "../data/appValidation";
import { profileSelector } from "../data/atoms";
import { axios } from "../data/axios";
import StoreListingModal from "../components/store/StoreListingModal";
import {
  defaultChatLayout,
  defaultWorkflowLayout,
} from "../components/apps/renderer/AppRenderer";

const menuItems = [
  {
    name: "Editor",
    value: "editor",
    icon: <EditIcon />,
  },
  {
    name: "Preview",
    value: "preview",
    icon: <PreviewIcon />,
  },
  {
    name: "History",
    value: "history",
    icon: <TimelineIcon />,
  },
  {
    name: "Versions",
    value: "versions",
    icon: <SvgIcon component={ChangeHistoryIcon} />,
  },
  {
    name: "Integrations",
    icon: <SvgIcon component={IntegrationsIcon} />,
    children: [
      {
        name: "Website",
        value: "integrations/website",
        icon: <SvgIcon component={WebIcon} />,
      },
      {
        name: "API",
        value: "integrations/api",
        icon: <SvgIcon component={CodeIcon} />,
      },
      {
        name: "Discord",
        value: "integrations/discord",
        icon: <SvgIcon component={DiscordIcon} />,
      },
      {
        name: "Slack",
        value: "integrations/slack",
        icon: <SvgIcon component={SlackIcon} />,
      },
      {
        name: "Twilio",
        value: "integrations/twilio",
        icon: <SvgIcon component={TwilioIcon} />,
      },
    ],
  },
];

function ErrorList({ errors }) {
  return (
    <ol>
      {errors.map((error, index) => (
        <li key={index}>
          {" "}
          {error.name}
          <ul>
            {error.errors.map((err, index) => (
              <li key={`${error.id}_${index}`}>{err.message}</li>
            ))}
          </ul>
        </li>
      ))}
    </ol>
  );
}

function AppIntegration({ integration, app, saveApp, setApp }) {
  switch (integration) {
    case "integrations/website":
      return (
        <AppWebConfigEditor
          app={app}
          webConfig={app?.web_config || {}}
          setWebConfig={(webConfig) => {
            setApp((app) => ({ ...app, web_config: webConfig }));
          }}
          saveApp={saveApp}
        />
      );
    case "integrations/slack":
      return (
        <AppSlackConfigEditor
          app={app}
          slackConfig={app?.slack_config || {}}
          setSlackConfig={(slackConfig) => {
            setApp((app) => ({ ...app, slack_config: slackConfig }));
          }}
          saveApp={saveApp}
        />
      );
    case "integrations/discord":
      return (
        <AppDiscordConfigEditor
          app={app}
          discordConfig={app?.discord_config || {}}
          setDiscordConfig={(discordConfig) => {
            setApp((app) => ({ ...app, discord_config: discordConfig }));
          }}
          saveApp={saveApp}
        />
      );
    case "integrations/twilio":
      return (
        <AppTwilioConfigEditor
          app={app}
          twilioConfig={app?.twilio_config || {}}
          setTwilioConfig={(twilioConfig) => {
            setApp((app) => ({ ...app, twilio_config: twilioConfig }));
          }}
          saveApp={saveApp}
        />
      );
    case "integrations/api":
      return <AppApiExamples app={app} />;
    default:
      return null;
  }
}
export default function AppConsolePage(props) {
  const { appId } = useParams();
  const { page } = props;
  const [appInputFields, setAppInputFields] = useState([]);
  const [app, setApp] = useState(null);
  const [isPublished, setIsPublished] = useState(false);
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [showUnpublishModal, setShowUnpublishModal] = useState(false);
  const [showStoreListingModal, setShowStoreListingModal] = useState(false);
  const [processors, setProcessors] = useState([]);
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [appTemplate, setAppTemplate] = useState(null);
  const [appOutputTemplate, setAppOutputTemplate] = useState({});
  const [selectedMenuItem, setSelectedMenuItem] = useState(page || "editor");
  const profile = useRecoilValue(profileSelector);
  const validationErrors = useValidationErrorsForAppConsole();

  useEffect(() => {
    if (appId) {
      axios()
        .get(`/api/apps/${appId}`)
        .then((response) => {
          const app = response.data;
          setIsLoading(false);
          setApp(app);

          setIsPublished(app.is_published);
          setAppInputFields(
            app?.data?.input_fields || [
              {
                name: "question",
                title: "Question",
                description: "Modify your fields here",
                type: "string",
                required: true,
              },
            ],
          );
          setProcessors(app?.data?.processors || app?.processors || []);
          setAppOutputTemplate(
            app?.data?.output_template || app?.output_template,
          );

          if (app?.template) {
            setSelectedMenuItem(page || "template");
            axios()
              .get(`/api/apps/templates/${response.data.template.slug}`)
              .then((response) => {
                setAppTemplate(response.data);
              });
          }
        })
        .catch((error) => {
          window.location.href = "/apps";
        });
    }
  }, [appId, page]);

  useEffect(() => {
    setApp((app) => ({
      ...app,
      data: { ...app?.data, input_fields: appInputFields },
    }));
  }, [appInputFields]);

  useEffect(() => {
    setApp((app) => ({ ...app, output_template: appOutputTemplate }));
  }, [appOutputTemplate]);

  const createApp = (app) => {
    return new Promise((resolve, reject) => {
      axios()
        .post("/api/apps", app)
        .then((response) => {
          enqueueSnackbar("App created successfully", {
            variant: "success",
            autoHideDuration: 500,
          });
          navigate(`/apps/${response.data.uuid}`);
          resolve(response);
        })
        .catch((error) => reject(error));
    });
  };

  const saveApp = (draft = true, comment = "") => {
    return new Promise((resolve, reject) => {
      const updatedApp = {
        name: app?.name,
        description: app?.description || "",
        icon: app?.icon || "",
        draft: draft,
        comment: comment,
        config: app?.data?.config,
        app_type: app?.type?.id,
        type_slug: app?.type?.slug,
        input_fields: appInputFields,
        output_template:
          app?.type?.slug === "agent"
            ? { markdown: "{{agent.content}}" }
            : appOutputTemplate,
        web_config: app?.web_config || {},
        slack_config: app?.slack_config || {},
        discord_config: app?.discord_config || {},
        twilio_config: app?.twilio_config || {},
        processors: processors.map((processor, index) => ({
          id: processor.id || `${processor.processor.slug}${index + 1}`,
          name: processor.name || processor.processor?.name,
          description:
            app?.data?.processors[index]?.description ||
            processor.description ||
            processor.processor?.description,
          provider_slug:
            processor.processor?.api_provider?.slug || processor.provider_slug,
          processor_slug: processor.processor?.slug || processor.processor_slug,
          config: processor.config,
          input: processor.input,
          input_fields: processor.input_fields,
          output_template: processor.output_template || {},
          dependencies: processor.dependencies || [],
        })),
      };

      if (appId) {
        axios()
          .patch(`/api/apps/${appId}`, updatedApp)
          .then((response) => {
            setApp(response.data);
            enqueueSnackbar("App updated successfully", { variant: "success" });
            resolve(response.data);
          })
          .catch((error) => {
            reject(error);
          });
      } else {
        createApp(updatedApp)
          .then((response) => resolve(response.data))
          .catch((error) => reject(error));
      }
    });
  };

  const setProcessorsCallback = useCallback(
    (newProcessors) => {
      setApp((app) => ({
        ...app,
        processors: newProcessors,
        data: { ...app.data, processors: newProcessors },
      }));
      setProcessors(newProcessors);
    },
    [setApp, setProcessors],
  );

  return isLoading ? (
    <CircularProgress />
  ) : (
    <Box
      id="app-edit-page"
      style={{
        padding: 5,
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <AppBar
        position="sticky"
        sx={{
          backgroundColor: "#fff",
          zIndex: 100,
          border: "1px solid #ddd",
          borderRadius: "4px",
        }}
        elevation={1}
      >
        {app?.type && (
          <Paper
            elevation={1}
            sx={{
              padding: "8px 12px",
              boxShadow: "none",
              backgroundColor: "#edeff755",
            }}
          >
            <Stack direction="row" spacing={1}>
              <AppDetailsEditor app={app} setApp={setApp} saveApp={saveApp} />
              <Stack
                direction="row"
                spacing={1}
                sx={{
                  justifyContent: "flex-end",
                  flexGrow: 1,
                  flexShrink: 1,
                  alignItems: "center",
                }}
              >
                <PublishModal
                  show={showPublishModal}
                  setShow={setShowPublishModal}
                  app={app}
                  setIsPublished={setIsPublished}
                  setAppVisibility={(visibility) =>
                    setApp({ ...app, visibility })
                  }
                  setReadAccessibleBy={(readAccessibleBy) =>
                    setApp((app) => ({
                      ...app,
                      read_accessible_by: readAccessibleBy,
                    }))
                  }
                  setWriteAccessibleBy={(writeAccessibleBy) => {
                    setApp((app) => ({
                      ...app,
                      write_accessible_by: writeAccessibleBy,
                    }));
                  }}
                />
                <UnpublishModal
                  show={showUnpublishModal}
                  setShow={setShowUnpublishModal}
                  app={app}
                  setIsPublished={setIsPublished}
                />

                {appId && app && (
                  <>
                    <Tooltip
                      arrow={true}
                      title={
                        app?.has_live_version
                          ? isPublished
                            ? "Unpublish App"
                            : "Publish App"
                          : app?.store_uuid
                            ? "Please unlist your app from the store before unpublishing"
                            : "Please save App before publishing"
                      }
                    >
                      <span>
                        <Button
                          variant="contained"
                          color="success"
                          style={{ textTransform: "none" }}
                          disabled={
                            app.owner_email !== profile.user_email ||
                            !app?.has_live_version ||
                            app?.store_uuid
                          }
                          startIcon={
                            isPublished ? (
                              <UnpublishedIcon />
                            ) : (
                              <PublishedWithChangesIcon />
                            )
                          }
                          onClick={() =>
                            isPublished
                              ? setShowUnpublishModal(true)
                              : setShowPublishModal(true)
                          }
                        >
                          {isPublished ? "Unpublish" : "Publish"}
                        </Button>
                      </span>
                    </Tooltip>
                    {process.env.REACT_APP_ENABLE_APP_STORE && (
                      <Tooltip
                        arrow={true}
                        title={
                          !isPublished
                            ? "Please publish the app before submitting to Promptly App Store"
                            : !profile.username
                              ? "Please set your username in settings to submit to Promptly App Store"
                              : !app?.store_uuid
                                ? "Submit to Promptly App Store to make it available to other users"
                                : "Edit Store Listing"
                        }
                      >
                        <span>
                          <Button
                            variant="contained"
                            color="primary"
                            style={{ textTransform: "none" }}
                            disabled={!isPublished || !profile.username}
                            startIcon={<StorefrontIcon />}
                            onClick={() =>
                              setShowStoreListingModal(!showStoreListingModal)
                            }
                          >
                            {app?.store_uuid
                              ? "Edit Store Listing"
                              : "List on App Store"}
                          </Button>
                        </span>
                      </Tooltip>
                    )}
                  </>
                )}
              </Stack>
            </Stack>
          </Paper>
        )}
      </AppBar>
      <Grid
        container
        sx={{ maxWidth: "1200px !important", margin: "auto", flex: "1 1 auto" }}
        rowSpacing={1}
        columnSpacing={{ xs: 0, sm: 1 }}
      >
        <Grid item md={3} xs={12}>
          <Box sx={{ width: "100%" }}>
            <AppEditorMenu
              menuItems={
                appTemplate
                  ? [
                      {
                        name: appTemplate.name,
                        value: "template",
                        icon: <SvgIcon component={TemplateIcon} />,
                      },
                      ...menuItems,
                    ]
                  : menuItems
              }
              selectedMenuItem={selectedMenuItem}
              setSelectedMenuItem={(value) => {
                setSelectedMenuItem(value);
                navigate(`/apps/${appId}/${value}`);
              }}
            />
          </Box>
        </Grid>
        <Grid item md={9} xs={12} mt={3}>
          {Object.values(validationErrors).flatMap((entry) => entry.errors)
            .length > 0 && (
            <Box sx={{ marginBottom: "8px" }}>
              <Alert
                onClose={() => {}}
                severity="warning"
                style={{ width: "100%", textAlign: "left" }}
              >
                <AlertTitle>
                  Your application has the following errors, please correct them
                  before saving your application
                </AlertTitle>
                <ErrorList errors={Object.values(validationErrors)} />
              </Alert>
            </Box>
          )}
          <Box sx={{ alignSelf: "flex-start", height: "100%" }}>
            {selectedMenuItem === "editor" && (
              <AppEditor
                processors={processors}
                setProcessors={setProcessorsCallback}
                appConfig={{
                  layout:
                    app?.data?.type_slug === "web"
                      ? defaultWorkflowLayout
                      : defaultChatLayout,
                  ...app?.data?.config,
                }}
                setAppConfig={(newConfig) =>
                  setApp((app) => ({
                    ...app,
                    config: newConfig,
                    data: {
                      ...app?.data,
                      config: newConfig,
                    },
                  }))
                }
                appInputFields={appInputFields}
                setAppInputFields={setAppInputFields}
                appOutputTemplate={appOutputTemplate}
                setAppOutputTemplate={(template) => {
                  setApp((app) => ({
                    ...app,
                    output_template: template,
                    data: {
                      ...app?.data,
                      output_template: template,
                    },
                  }));
                  setAppOutputTemplate(template);
                }}
                app={app}
                setApp={setApp}
                saveApp={saveApp}
              />
            )}
            {selectedMenuItem === "preview" && <AppPreview app={app} />}
            {selectedMenuItem === "history" && <AppRunHistory app={app} />}
            {selectedMenuItem === "versions" && <AppVersions app={app} />}
            {(selectedMenuItem === "integrations/website" ||
              selectedMenuItem === "integrations/slack" ||
              selectedMenuItem === "integrations/discord" ||
              selectedMenuItem === "integrations/api" ||
              selectedMenuItem === "integrations/twilio") && (
              <Box sx={{ position: "relative" }}>
                <AppIntegration
                  integration={selectedMenuItem}
                  app={app}
                  saveApp={saveApp}
                  setApp={setApp}
                />
                {!app.is_published && (
                  <Box
                    sx={{
                      position: "absolute",
                      top: 0,
                      width: "100%",
                      height: "100%",
                      zIndex: 10,
                      opacity: 0.9,
                      display: "flex",
                      backgroundColor: "grey",
                    }}
                  >
                    <Box sx={{ margin: "auto" }}>
                      <Alert severity="warning">
                        This app is not published yet. Please publish the app to
                        enable this integration.
                      </Alert>
                    </Box>
                  </Box>
                )}
              </Box>
            )}
            {selectedMenuItem === "template" && (
              <AppTemplate
                app={app}
                setApp={(newApp) =>
                  setApp((oldApp) => ({ ...oldApp, ...newApp }))
                }
                appTemplate={appTemplate}
                saveApp={saveApp}
              />
            )}
          </Box>
        </Grid>
      </Grid>
      {showStoreListingModal && (
        <StoreListingModal
          app={app}
          open={showStoreListingModal}
          handleCloseCb={() => setShowStoreListingModal(false)}
        />
      )}
    </Box>
  );
}
