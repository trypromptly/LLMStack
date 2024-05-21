import { useEffect, useMemo } from "react";
import { Button } from "@mui/material";
import Grid from "@mui/material/Unstable_Grid2";
import { useSetRecoilState } from "recoil";
import { Liquid } from "liquidjs";
import {
  AgentMessage,
  AppMessage,
  AgentStepMessage,
  UserMessage,
} from "../apps/renderer/Messages";
import { appRunDataState } from "../../data/atoms";
import StoreAppHeader from "./StoreAppHeader";
import LayoutRenderer from "../apps/renderer/LayoutRenderer";
import { useCallback } from "react";
import {
  defaultChatLayout,
  defaultWorkflowLayout,
  webPageRenderLayout,
} from "../apps/renderer/AppRenderer";

const SessionRenderer = ({
  sessionData,
  noHeader = false,
  skipSteps = false,
}) => {
  const storeApp = sessionData?.store_app;
  const renderAsWebPage = sessionData?.metadata?.render_as_web_page || false;
  const appTypeSlug = storeApp?.data?.type_slug || "agent";
  const setAppRunData = useSetRecoilState(appRunDataState);
  const templateEngine = useMemo(() => new Liquid(), []);

  const renderAgentStepOutput = useCallback(
    (output, processorId) => {
      const template = storeApp?.data?.processors?.find(
        (processor) => processor.id === processorId,
      )?.output_template;

      if (!template) {
        return JSON.stringify(output);
      }

      return templateEngine.renderSync(
        templateEngine.parse(template.markdown),
        output,
      );
    },
    [storeApp?.data?.processors, templateEngine],
  );

  useEffect(() => {
    let messages = [];
    for (const runEntry of sessionData?.run_entry_requests || []) {
      messages.push(
        new UserMessage(
          null,
          runEntry.request_uuid,
          runEntry.request_body?.input || {},
        ),
      );

      if (appTypeSlug === "agent" && !skipSteps) {
        for (const processorRun of runEntry.processor_runs) {
          messages.push(
            new AgentStepMessage(
              null,
              null,
              {
                name: processorRun.processor_id || "",
                arguments: JSON.stringify(processorRun.input),
                output: renderAgentStepOutput(
                  processorRun.output,
                  processorRun.processor_id,
                ),
              },
              null,
              false,
            ),
          );
        }
      }

      messages.push(
        appTypeSlug === "agent"
          ? new AgentMessage(
              null,
              runEntry.request_uuid,
              runEntry.response_body,
            )
          : new AppMessage(null, runEntry.request_uuid, runEntry.response_body),
      );
    }

    if (storeApp) {
      setAppRunData({
        messages,
        assistantImage: storeApp.data?.config?.assistant_image || "",
        inputFields: storeApp.data?.input_fields || [],
        processors: storeApp.data?.processors || [],
      });
    }
  }, [
    sessionData,
    appTypeSlug,
    setAppRunData,
    renderAgentStepOutput,
    skipSteps,
    storeApp,
    storeApp?.data?.config?.assistant_image,
    storeApp?.data?.input_fields,
    storeApp?.data?.processors,
  ]);

  const memoizedLayoutRenderer = useMemo(
    () => (
      <LayoutRenderer noInput>
        {renderAsWebPage
          ? webPageRenderLayout
          : storeApp?.data?.config?.layout ||
            (appTypeSlug === "web" ? defaultWorkflowLayout : defaultChatLayout)}
      </LayoutRenderer>
    ),
    [storeApp, appTypeSlug, renderAsWebPage],
  );

  if (!storeApp) {
    return null;
  }

  return (
    <Grid container spacing={1} direction={"column"} sx={{ height: "100%" }}>
      {!noHeader && (
        <Grid>
          <StoreAppHeader
            name={storeApp.name}
            icon={storeApp.icon128}
            username={storeApp.username}
            description={storeApp.description}
            categories={storeApp.categories}
            appTypeSlug={storeApp?.data?.type_slug || "agent"}
            appStoreUuid={storeApp.uuid}
            shareHeader
          />
        </Grid>
      )}
      <Grid
        sx={{
          flex: 1,
          padding: 4,
          paddingBottom: 0,
          height: 0,
          overflow: "auto",
        }}
      >
        {memoizedLayoutRenderer}
      </Grid>
      <Button
        variant="contained"
        component="a"
        sx={{ margin: 2 }}
        href={`/a/${storeApp.slug}`}
      >
        Try it out now!
      </Button>
    </Grid>
  );
};

export default SessionRenderer;
