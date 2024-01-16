import { Box, Button, Grid, Stack } from "@mui/material";
import { useEffect, useState } from "react";
import { useRecoilState, useRecoilValue } from "recoil";
import ApiBackendSelector from "../components/ApiBackendSelector";
import ConfigForm from "../components/ConfigForm";
import InputForm from "../components/InputForm";
import Output from "../components/Output";
import {
  apiBackendSelectedState,
  endpointConfigValueState,
  endpointSelectedState,
  inputValueState,
  isLoggedInState,
  templateValueState,
} from "../data/atoms";
import { axios } from "../data/axios";

export default function PlaygroundPage() {
  const isLoggedIn = useRecoilValue(isLoggedInState);
  const [input] = useRecoilState(inputValueState);

  const [apiBackendSelected, setApiBackendSelected] = useRecoilState(
    apiBackendSelectedState,
  );
  const [endpointSelected, setEndpointSelected] = useRecoilState(
    endpointSelectedState,
  );
  const [paramValues, setParamValues] = useRecoilState(
    endpointConfigValueState,
  );
  const [promptValues, setPromptValues] = useRecoilState(templateValueState);
  const [output, setOutput] = useState("");
  const [runError, setRunError] = useState("");
  const [outputLoading, setOutputLoading] = useState(false);
  const [tokenCount, setTokenCount] = useState(null);
  const [processorResult, setProcessorResult] = useState(null);

  const run = () => {
    setRunError("");
    setOutputLoading(true);
    axios()
      .post(`/api/playground/run`, {
        input: input,
        config: paramValues,
        bypass_cache: true,
        api_backend_slug: apiBackendSelected.slug,
        api_provider_slug: apiBackendSelected.api_provider.slug,
      })
      .then((response) => {
        if (response?.data?.errors) {
          setOutput("");
          setRunError(JSON.stringify(response?.data?.errors));
        }

        setProcessorResult(response?.data?.output);
        if (response?.data?.output?.generations) {
          setOutput(response?.data?.output?.generations);
        } else if (response?.data?.output?.chat_completions) {
          setOutput(response?.data?.output?.chat_completions);
        } else {
          setOutput([response?.data?.output]);
        }

        setOutputLoading(false);

        // Update token count
        if (
          response?.data?.output?._response?.api_response?.usage !== undefined
        ) {
          if (
            response?.data?.output?._response?.api_response?.usage
              .prompt_tokens !== undefined &&
            response?.data?.output?._response?.api_response?.usage
              .completion_tokens !== undefined
          ) {
            setTokenCount(
              `${response?.data?.output?._response?.api_response?.usage.total_tokens} (P${response?.data?.output?._response?.api_response?.usage.prompt_tokens} + C${response?.data?.output?._response?.api_response?.usage.completion_tokens})`,
            );
          } else if (
            response?.data?.output?._response?.api_response?.usage
              .total_tokens !== undefined
          ) {
            setTokenCount(
              response?.data?.output?._response?.api_response?.usage
                .total_tokens,
            );
          }
        }
      })
      .catch((error) => {
        console.error(error);
        setRunError(error?.response?.data || "Failed to run given prompt");
        setOutputLoading(false);
      });
  };
  const Run = () => {
    return (
      <Button
        type="primary"
        onClick={(e) => {
          if (isLoggedIn) {
            return run();
          }
        }}
        variant="contained"
      >
        {"Run"}
      </Button>
    );
  };

  // Reset endpointSelected, apiBackendSelected, promptValues, paramValues and output on load
  useEffect(() => {
    setTokenCount(null);
    setOutput("");
  }, [
    setApiBackendSelected,
    setEndpointSelected,
    setParamValues,
    setPromptValues,
  ]);

  useEffect(() => {}, [paramValues, promptValues]);

  return (
    <Box sx={{ margin: "10px 2px" }}>
      <Stack>
        <ApiBackendSelector />
        <Grid container spacing={2}>
          <Grid item xs={12} md={4} sx={{ height: "100%" }}>
            <Stack spacing={2}>
              <div style={{ height: "10%" }}>
                <InputForm
                  schema={
                    apiBackendSelected ? apiBackendSelected.input_schema : {}
                  }
                  uiSchema={
                    apiBackendSelected ? apiBackendSelected.input_ui_schema : {}
                  }
                  emptyMessage="Select your API Backend to see the parameters"
                />
              </div>
              <div>{apiBackendSelected && <Run />}</div>
            </Stack>
          </Grid>
          <Grid item xs={12} md={4}>
            <ConfigForm
              schema={
                apiBackendSelected ? apiBackendSelected.config_schema : {}
              }
              uiSchema={
                apiBackendSelected ? apiBackendSelected.config_ui_schema : {}
              }
              formData={paramValues}
              atomState={endpointConfigValueState}
              emptyMessage="Select your API Backend to see the parameters"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Output
              result={output}
              endpoint={endpointSelected}
              loading={outputLoading}
              loadingTip={"Running the input..."}
              runError={runError}
              tokenCount={tokenCount}
              schema={apiBackendSelected?.output_schema || {}}
              uiSchema={apiBackendSelected?.output_ui_schema || {}}
              formData={processorResult || {}}
            />
          </Grid>
        </Grid>
      </Stack>
    </Box>
  );
}
