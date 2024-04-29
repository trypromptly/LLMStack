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
  Link,
  Paper,
  Stack,
  SvgIcon,
  Tooltip,
} from "@mui/material";
import { enqueueSnackbar } from "notistack";
import { useEffect, useState } from "react";
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
import { AppNameEditor } from "../components/apps/AppNameEditor";
import { AppPreview } from "../components/apps/AppPreview";
import {
  EditSharingModal,
  PublishModal,
  UnpublishModal,
} from "../components/apps/AppPublisher";
import { AppRunHistory } from "../components/apps/AppRunHistory";
import { AppSlackConfigEditor } from "../components/apps/AppSlackConfigEditor";
import { AppTemplate } from "../components/apps/AppTemplate";
import { AppTwilioConfigEditor } from "../components/apps/AppTwilioConfigEditor";
import { AppVersions } from "../components/apps/AppVersions";
import AppVisibilityIcon from "../components/apps/AppVisibilityIcon";
import { AppWebConfigEditor } from "../components/apps/AppWebConfigEditor";
import { useValidationErrorsForAppConsole } from "../data/appValidation";
import {
  apiBackendsState,
  profileFlagsSelector,
  profileSelector,
} from "../data/atoms";
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
  const apiBackends = useRecoilValue(apiBackendsState);
  const [appInputFields, setAppInputFields] = useState([]);
  const [app, setApp] = useState(null);
  const [isPublished, setIsPublished] = useState(false);
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [showSharingModal, setShowSharingModal] = useState(false);
  const [showUnpublishModal, setShowUnpublishModal] = useState(false);
  const [showStoreListingModal, setShowStoreListingModal] = useState(false);
  const [processors, setProcessors] = useState([]);
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [appTemplate, setAppTemplate] = useState(null);
  const [appOutputTemplate, setAppOutputTemplate] = useState({});
  const [missingKeys, setMissingKeys] = useState([]);
  const [appVisibility, setAppVisibility] = useState(3);
  const [selectedMenuItem, setSelectedMenuItem] = useState(page || "editor");
  const profile = useRecoilValue(profileSelector);
  const profileFlags = useRecoilValue(profileFlagsSelector);
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
          setAppVisibility(app.visibility);

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
    let missingKeys = new Set();
    app?.processors
      ?.map((processor) => {
        return [
          processor.apiBackend?.api_provider?.slug,
          processor.apiBackend?.api_provider?.name,
        ];
      })
      .forEach(([slug, name]) => {
        if (slug === "promptly") {
          if (!profile.openai_key) {
            missingKeys = missingKeys.add("Open AI");
          }
        } else {
          if (!profile[`${slug}_key`]) missingKeys = missingKeys.add(name);
        }
      });

    setMissingKeys(Array.from(missingKeys));
  }, [app?.processors, profile]);

  useEffect(() => {
    // If processors are coming from app.data, replace provider_slug and processor_slug with api_backend
    if (app?.data?.processors) {
      setProcessors(
        app.data.processors.map((processor) => ({
          ...processor,
          api_backend: apiBackends.find(
            (apiBackend) =>
              apiBackend.slug === processor.processor_slug &&
              apiBackend.api_provider.slug === processor.provider_slug,
          ),
        })),
      );
    }
  }, [app?.data?.processors, apiBackends]);

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
        description: "",
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
          id: processor.id || `${processor.api_backend.slug}${index + 1}`,
          name: processor.name || processor.api_backend?.name,
          description:
            app?.data?.processors[index]?.description ||
            processor.description ||
            processor.api_backend?.description,
          provider_slug:
            processor.api_backend?.api_provider?.slug ||
            processor.provider_slug,
          processor_slug:
            processor.api_backend?.slug || processor.processor_slug,
          config: processor.config,
          input: processor.input,
          output_template: processor.output_template || {},
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
              padding: "10px 15px",
              boxShadow: "none",
              backgroundColor: "#edeff755",
            }}
          >
            <Stack direction="row" spacing={1}>
              <Stack direction="column">
                <Stack direction="row" spacing={1.2}>
                  <AppNameEditor
                    appName={app.name}
                    setAppName={(newAppName) =>
                      setApp((app) => ({
                        ...app,
                        name: newAppName,
                      }))
                    }
                  />
                  {app.owner_email !== profile.user_email && (
                    <span style={{ color: "gray", lineHeight: "40px" }}>
                      shared by <b>{app.owner_email}</b>
                    </span>
                  )}
                  {app.owner_email === profile.user_email &&
                    app.visibility === 0 &&
                    app.last_modified_by_email && (
                      <span style={{ color: "gray", lineHeight: "40px" }}>
                        Last modified by{" "}
                        <b>
                          {app.last_modified_by_email === profile.user_email
                            ? "You"
                            : app.last_modified_by_email}
                        </b>
                      </span>
                    )}
                </Stack>
                {isPublished && (
                  <Stack
                    direction="row"
                    spacing={0.2}
                    sx={{ justifyContent: "left" }}
                  >
                    <Link
                      href={`${window.location.origin}/app/${app.published_uuid}`}
                      target="_blank"
                      rel="noreferrer"
                      variant="body2"
                    >
                      {`${window.location.origin}/app/${app.published_uuid}`}
                    </Link>
                    <AppVisibilityIcon
                      visibility={appVisibility}
                      published={isPublished}
                      setShowSharingModal={setShowSharingModal}
                      disabled={app.owner_email !== profile.user_email}
                    />
                  </Stack>
                )}
              </Stack>
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
                <EditSharingModal
                  show={showSharingModal}
                  setShow={setShowSharingModal}
                  app={app}
                  setIsPublished={setIsPublished}
                  setAppVisibility={setAppVisibility}
                />
                <PublishModal
                  show={showPublishModal}
                  setShow={setShowPublishModal}
                  app={app}
                  setIsPublished={setIsPublished}
                  setAppVisibility={setAppVisibility}
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
      <Stack>
        {false &&
          missingKeys.length > 0 &&
          !profileFlags.IS_ORGANIZATION_MEMBER && (
            <Alert
              severity="error"
              style={{ width: "100%", margin: "10px 0", textAlign: "left" }}
            >
              <AlertTitle>Missing API Keys</AlertTitle>
              <p>
                You are missing API keys for the following providers:{" "}
                <strong>{missingKeys.join(", ")}</strong>. Please add them in
                your <Link href="/settings">profile</Link> to use these
                processors in your app successfully. If you don't have an API
                key for a provider, you can get one from their websites. For
                example by visiting{" "}
                <Link
                  href="https://platform.openai.com/account/api-keys"
                  target="_blank"
                  rel="noreferrer"
                >
                  Open AI
                </Link>
                ,{" "}
                <Link
                  href="https://beta.dreamstudio.ai/membership?tab=apiKeys"
                  target="_blank"
                  rel="noreferrer"
                >
                  Dream Studio
                </Link>{" "}
                etc.
              </p>
            </Alert>
          )}
      </Stack>
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
                setProcessors={(newProcessors) => {
                  setApp((app) => ({
                    ...app,
                    processors: newProcessors,
                    data: { ...app.data, processors: newProcessors },
                  }));
                  setProcessors(newProcessors);
                }}
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
