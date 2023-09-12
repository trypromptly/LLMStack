import { useEffect, useRef, useState } from "react";

import { Stack, Grid, Divider, Button as MuiButton } from "@mui/material";

import ApiBackendSelector from "../components/ApiBackendSelector";
import { useRecoilState, useRecoilValue } from "recoil";
import {
  apiBackendSelectedState,
  endpointSelectedState,
  endpointConfigValueState,
  templateValueState,
  isLoggedInState,
  inputValueState,
} from "../data/atoms";
import { axios } from "../data/axios";
import Output from "../components/Output";

import InputForm from "../components/InputForm";
import ConfigForm from "../components/ConfigForm";
import HomeTour from "../components/home/HomeTour";

const homeCardStyle = {
  backgroundColor: "#fff",
  borderRadius: "8px",
  boxShadow: "0px 2px 8px rgba(0, 0, 0, 0.2)",
  height: "100%",
};

export default function HomePage() {
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

  const tourRef1 = useRef(null);
  const tourRef2 = useRef(null);
  const tourRef3 = useRef(null);
  const tourRef4 = useRef(null);
  const tourRef5 = useRef(null);
  const tourRef6 = useRef(null);

  const runEndpoint = (endpoint) => {
    if (!endpoint) {
      setRunError(
        "No endpoint selected. Please select API Backend or an existing endpoint.",
      );
      return;
    }

    setRunError("");
    setTokenCount(null);
    setOutputLoading(true);

    axios()
      .post(
        `/api/endpoints/invoke_api/${endpoint.parent_uuid}/${endpoint.version}`,
        {
          input: input,
          template_values: promptValues || {},
          config: paramValues || {},
          bypass_cache: true,
        },
      )
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

  const testPrompt = () => {
    // If we do not have an endpoint available, create a temporary one
    let endpoint = endpointSelected;
    if (!endpointSelected && apiBackendSelected) {
      axios()
        .post(`/api/endpoints`, {
          name: `Playground - ${new Date().toLocaleString()}`,
          api_backend: apiBackendSelected.id,
          draft: true,
          input: input,
          param_values: paramValues,
          config: paramValues,
          prompt_values: promptValues,
          post_processor: "",
        })
        .then((response) => {
          endpoint = response.data;
          setEndpointSelected(response.data);
        })
        .catch((error) => {
          console.error(error);
        })
        .then(() => {
          runEndpoint(endpoint);
        });
    } else {
      runEndpoint(endpoint);
    }
  };

  const TestPrompt = () => {
    return (
      <MuiButton
        type="primary"
        onClick={(e) => {
          if (isLoggedIn) {
            return testPrompt();
          }
        }}
        ref={tourRef6}
        variant="contained"
      >
        {"Submit"}
      </MuiButton>
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
    <div
      id="home-page"
      style={{ height: "100%", overflow: "scroll", padding: "2px" }}
    >
      <HomeTour
        tourRef1={tourRef1}
        tourRef2={tourRef2}
        tourRef3={tourRef3}
        tourRef4={tourRef4}
        tourRef5={tourRef5}
        tourRef6={tourRef6}
      />
      <Stack
        spacing={2}
        divider={<Divider orientation="horizontal" flexItem />}
        sx={{ width: "100%", height: "100%", paddingTop: "5px" }}
      >
        <ApiBackendSelector innerRef={tourRef2} />
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
              <div>{apiBackendSelected && <TestPrompt />}</div>
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
    </div>
  );
}
