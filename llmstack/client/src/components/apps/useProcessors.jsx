import { useCallback, useState } from "react";
import { axios } from "../../data/axios";

// In the context of an app, this can be used to run a single processor from the chain and get the output.
export function useProcessors(appId) {
  const [processorSessionId, setProcessorSessionId] = useState(null);

  const runProcessor = useCallback(
    async (processorId, input, disable_history = true) => {
      // Do not allow running a processor if there is no session
      if (!processorSessionId) {
        console.error("No session ID set");
        return;
      }

      const response = await axios().post(
        `/api/apps/${appId}/processors/${processorId}/run`,
        {
          input,
          session_id: processorSessionId,
          preview: window.location.pathname.endsWith("/preview"),
          disable_history,
        },
      );

      // Check if output is a string and parse it as JSON
      let output = response?.data?.output;
      if (output && typeof output === "string") {
        try {
          output = JSON.parse(output);
        } catch (e) {
          console.error(e);
        }
      }

      return output;
    },
    [processorSessionId, appId],
  );

  return [runProcessor, processorSessionId, setProcessorSessionId];
}
