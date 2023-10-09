import { useEffect, useState } from "react";
import { axios } from "../data/axios";
import { useNavigate, useParams } from "react-router-dom";
import { AppNameEditor } from "../components/apps/AppNameEditor";
import {
  EditSharingModal,
  PublishModal,
  UnpublishModal,
} from "../components/apps/AppPublisher";
import PublishedWithChangesIcon from "@mui/icons-material/PublishedWithChanges";
import { enqueueSnackbar } from "notistack";
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
import ChangeHistoryIcon from "@mui/icons-material/ChangeHistory";
import EditIcon from "@mui/icons-material/Edit";
import PreviewIcon from "@mui/icons-material/Preview";
import TimelineIcon from "@mui/icons-material/Timeline";
import UnpublishedIcon from "@mui/icons-material/Unpublished";
import { useRecoilValue } from "recoil";
import { profileState, profileFlagsState } from "../data/atoms";
import AppVisibilityIcon from "../components/apps/AppVisibilityIcon";
import AppEditorMenu from "../components/apps/AppEditorMenu";
import { AppEditor } from "../components/apps/AppEditor";
import { AppPreview } from "../components/apps/AppPreview";
import { AppRunHistory } from "../components/apps/AppRunHistory";
import { AppWebConfigEditor } from "../components/apps/AppWebConfigEditor";
import { AppSlackConfigEditor } from "../components/apps/AppSlackConfigEditor";
import { AppDiscordConfigEditor } from "../components/apps/AppDiscordConfigEditor";
import { AppTwilioConfigEditor } from "../components/apps/AppTwilioConfigEditor";
import { ReactComponent as CodeIcon } from "../assets/images/icons/code.svg";
import { ReactComponent as DiscordIcon } from "../assets/images/icons/discord.svg";
import { ReactComponent as IntegrationsIcon } from "../assets/images/icons/integrations.svg";
import { ReactComponent as SlackIcon } from "../assets/images/icons/slack.svg";
import { ReactComponent as TwilioIcon } from "../assets/images/icons/twilio.svg";
import { ReactComponent as TemplateIcon } from "../assets/images/icons/template.svg";
import { ReactComponent as TestsIcon } from "../assets/images/icons/tests.svg";
import { ReactComponent as WebIcon } from "../assets/images/icons/web.svg";
import { AppApiExamples } from "../components/apps/AppApiExamples";
import { AppTemplate } from "../components/apps/AppTemplate";
import { AppTests } from "../components/apps/AppTests";
import { AppVersions } from "../components/apps/AppVersions";
import { apiBackendsState } from "../data/atoms";

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
    name: "Tests",
    value: "tests",
    icon: <SvgIcon component={TestsIcon} />,
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

export default function AppEditPage(props) {
  const { appId } = useParams();
  const { page } = props;
  const apiBackends = useRecoilValue(apiBackendsState);
  const [appInputFields, setAppInputFields] = useState([]);
  const [app, setApp] = useState(null);
  const [isPublished, setIsPublished] = useState(false);
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [showSharingModal, setShowSharingModal] = useState(false);
  const [showUnpublishModal, setShowUnpublishModal] = useState(false);
  const [processors, setProcessors] = useState([]);
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [appTemplate, setAppTemplate] = useState(null);
  const [appOutputTemplate, setAppOutputTemplate] = useState({});
  const [missingKeys, setMissingKeys] = useState([]);
  const [appVisibility, setAppVisibility] = useState(3);
  const [selectedMenuItem, setSelectedMenuItem] = useState(page || "editor");
  const profile = useRecoilValue(profileState);
  const profileFlags = useRecoilValue(profileFlagsState);

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
        input_fields:
          app?.type?.slug === "agent"
            ? [
                {
                  name: "task",
                  title: "Task",
                  description: "What do you want the agent to perform?",
                  type: "string",
                  required: true,
                },
              ]
            : appInputFields,
        output_template:
          app?.type?.slug === "agent"
            ? { markdown: "{{agent}}" }
            : appOutputTemplate,
        web_config: app?.web_config || {},
        slack_config: app?.slack_config || {},
        discord_config: app?.discord_config || {},
        twilio_config: app?.twilio_config || {},
        processors: processors.map((processor, index) => ({
          id: `_inputs${index + 1}`,
          name: processor.name || processor.api_backend?.name,
          description:
            processor.description || processor.api_backend?.description,
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
    <div id="app-edit-page" style={{ margin: 10 }}>
      <AppBar
        position="sticky"
        sx={{ backgroundColor: "inherit", zIndex: 100 }}
      >
        {app?.type && (
          <Paper elevation={1} sx={{ padding: "10px 15px", boxShadow: "none" }}>
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
                  <Tooltip
                    arrow={true}
                    title={
                      app?.has_live_version
                        ? isPublished
                          ? "Unpublish App"
                          : "Publish App"
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
                          !app?.has_live_version
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
                )}
              </Stack>
            </Stack>
          </Paper>
        )}
      </AppBar>
      <Stack>
        &nbsp;
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
        sx={{ maxWidth: "1200px !important", margin: "auto" }}
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
        <Grid item md={9} xs={12}>
          <Box sx={{ alignSelf: "flex-start" }}>
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
                appConfig={app?.data?.config || {}}
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
            {selectedMenuItem === "tests" && <AppTests app={app} />}
            {selectedMenuItem === "versions" && <AppVersions app={app} />}
            {selectedMenuItem === "integrations/website" && (
              <AppWebConfigEditor
                app={app}
                webConfig={app?.web_config || {}}
                setWebConfig={(webConfig) => {
                  setApp((app) => ({ ...app, web_config: webConfig }));
                }}
                saveApp={saveApp}
              />
            )}
            {selectedMenuItem === "integrations/slack" && (
              <AppSlackConfigEditor
                app={app}
                slackConfig={app?.slack_config || {}}
                setSlackConfig={(slackConfig) => {
                  setApp((app) => ({ ...app, slack_config: slackConfig }));
                }}
                saveApp={saveApp}
              />
            )}
            {selectedMenuItem === "integrations/discord" && (
              <AppDiscordConfigEditor
                app={app}
                discordConfig={app?.discord_config || {}}
                setDiscordConfig={(discordConfig) => {
                  setApp((app) => ({ ...app, discord_config: discordConfig }));
                }}
                saveApp={saveApp}
              />
            )}
            {selectedMenuItem === "integrations/api" && (
              <AppApiExamples app={app} />
            )}
            {selectedMenuItem === "integrations/twilio" && (
              <AppTwilioConfigEditor
                app={app}
                twilioConfig={app?.twilio_config || {}}
                setTwilioConfig={(twilioConfig) => {
                  setApp((app) => ({ ...app, twilio_config: twilioConfig }));
                }}
                saveApp={saveApp}
              />
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
    </div>
  );
}
