import { useEffect } from "react";
import { Button } from "@mui/material";
import Grid from "@mui/material/Unstable_Grid2";
import { useSetRecoilState } from "recoil";
import {
  AgentMessage,
  AppMessage,
  UserMessage,
} from "../apps/renderer/Messages";
import { appRunDataState } from "../../data/atoms";
import StoreAppHeader from "./StoreAppHeader";
import LayoutRenderer from "../apps/renderer/LayoutRenderer";

const SessionRenderer = ({ sessionData }) => {
  const storeApp = sessionData?.store_app;
  const appTypeSlug = storeApp?.data?.type_slug || "agent";
  const setAppRunData = useSetRecoilState(appRunDataState);

  useEffect(() => {
    let messages = [];
    for (const runEntry of sessionData?.run_entry_requests || []) {
      let input = runEntry.request_body;
      try {
        input = JSON.parse(
          runEntry.request_body.replace(/'/g, '"').replace(/True/g, "true"),
        ).input;
      } catch (e) {
        console.error(e);
      }

      messages.push(new UserMessage(null, runEntry.request_uuid, input));
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

    setAppRunData({
      messages,
      assistantImage: storeApp.data?.config?.assistant_image || "",
      inputFields: storeApp.data?.input_fields || [],
    });
  }, [
    sessionData,
    appTypeSlug,
    setAppRunData,
    storeApp.data?.config?.assistant_image,
    storeApp.data?.input_fields,
  ]);

  return (
    <Grid container spacing={1} direction={"column"} sx={{ height: "100%" }}>
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
      <Grid
        sx={{
          flex: 1,
          padding: 4,
          paddingBottom: 0,
          height: 0,
          overflow: "auto",
        }}
      >
        <LayoutRenderer noInput>
          {storeApp?.data?.config?.layout || ""}
        </LayoutRenderer>
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
