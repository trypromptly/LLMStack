import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Button,
  Card,
  Col,
  Divider,
  Radio,
  Row,
  Space,
  Tooltip,
  Input,
  Select,
  Modal,
  Collapse,
  Checkbox,
} from "antd";

import ApiBackendSelector from "../components/ApiBackendSelector";
import EndpointSelector from "../components/EndpointSelector";
import { LoggedOutModal } from "../components/LoggedOutModal";
import {
  useRecoilState,
  useRecoilValue,
  useSetRecoilState,
  useResetRecoilState,
} from "recoil";
import {
  apiBackendSelectedState,
  endpointSelectedState,
  endpointConfigValueState,
  templateValueState,
  isLoggedInState,
  inputValueState,
  saveEndpointModalVisibleState,
  shareEndpointModalVisibleState,
  saveEndpointVersionModalVisibleState,
  endpointShareCodeValueState,
} from "../data/atoms";
import { axios } from "../data/axios";
import {
  SaveEndpointModal,
  SaveVersionModal,
} from "../components/EndpointModal";
import Output from "../components/Output";

import InputForm from "../components/InputForm";
import ConfigForm from "../components/ConfigForm";
import HomeTour from "../components/home/HomeTour";
import ShareEndpointButton from "../components/home/ShareEndpointButton";
import ShareButtons from "../components/ShareButtons";
import { CopyOutlined } from "@ant-design/icons";

const { Panel } = Collapse;

const homeCardStyle = {
  backgroundColor: "#fff",
  borderRadius: "8px",
  boxShadow: "0px 2px 8px rgba(0, 0, 0, 0.2)",
  height: "100%",
};

export default function HomePage({ isSharedPageMode }) {
  const isLoggedIn = useRecoilValue(isLoggedInState);
  const [input, setInput] = useRecoilState(inputValueState);

  const setSaveEndpointModalVisibility = useSetRecoilState(
    saveEndpointModalVisibleState,
  );
  const [shareModalVisibility, setShareModalVisibility] = useRecoilState(
    shareEndpointModalVisibleState,
  );
  const setSaveVersionModalVisibility = useSetRecoilState(
    saveEndpointVersionModalVisibleState,
  );

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
  const [shareCode, setShareCode] = useRecoilState(endpointShareCodeValueState);
  const resetShareCode = useResetRecoilState(endpointShareCodeValueState);

  const [useExistingEndpoint, setUseExistingEndpoint] = useState(false);
  const [loggedOutModalVisibility, setLoggedOutModalVisibility] =
    useState(false);
  const [responseId, setResponseId] = useState(null);
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

  const { shareId } = useParams();

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

        // Update response id
        if (response?.data?.id) {
          setResponseId(response.data.id);
        } else if (response?.data?.errors?.id) {
          setResponseId(response.data.errors.id);
        }
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
        setResponseId(null);
        setOutputLoading(false);
      })
      .then(() => {
        resetShareCode();
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
      <Button
        type="primary"
        onClick={(e) => {
          if (isLoggedIn) {
            return testPrompt();
          } else {
            setLoggedOutModalVisibility(true);
          }
        }}
        style={{ backgroundColor: "#477c24" }}
        ref={tourRef6}
      >
        {"Submit"}
      </Button>
    );
  };

  function ShareModal() {
    const [promptName, setPromptName] = useState("");
    const [promptTags, setPromptTags] = useState([]);
    const [promptPrivate, setPromptPrivate] = useState(false);

    function handleCopy() {
      navigator.clipboard.writeText(`${window.location.origin}/s/${shareCode}`);
    }

    const handleUpdatePrompt = async () => {
      axios()
        .patch(`/api/share/code/${shareCode}`, {
          name: promptName,
          tags: promptTags,
          is_private: promptPrivate,
        })
        .then((response) => {})
        .catch((error) => {
          console.error(error);
        })
        .then(() => {});
    };

    const defaultPromptTags = ["codex", "diffusion", "davinci", "ada"];

    // antd modal that show a share link with click to copy functionality
    return (
      <Modal
        title="Share this Prompt"
        style={{ top: "10px" }}
        centered
        open={shareModalVisibility}
        onCancel={() => setShareModalVisibility(false)}
        footer={null}
      >
        <Col
          style={{ display: "flex", flexDirection: "column", rowGap: "10px" }}
        >
          <Row style={{ margin: "10px 0 5px" }}>
            Use below link to share this prompt and model parameters with
            others. Recipients can run this prompt by logging into their
            Promptly account and use their own API provider keys.
          </Row>
          <Row>
            <Input.Group compact>
              <Input
                size="large"
                style={{
                  width: "calc(100% - 220px)",
                  border: "solid 1px #02f",
                  marginBottom: "10px",
                }}
                defaultValue={`${window.location.origin}/s/${shareCode}`}
                readOnly
              />
              <Tooltip title="Copy URL">
                <Button
                  size="large"
                  icon={<CopyOutlined />}
                  onClick={handleCopy}
                  style={{ border: "solid 1px #02f" }}
                />
              </Tooltip>
            </Input.Group>
          </Row>
          <Row
            style={{ marginLeft: "-16px", marginTop: "-5px", width: "100%" }}
          >
            <Collapse ghost style={{ width: "100%" }}>
              <Panel header="Additional Settings" key="1">
                <Col span={12}>
                  <span>Prompt Name</span>{" "}
                  <Input
                    style={{ width: "100%", marginBottom: "10px" }}
                    onChange={(e) => setPromptName(e.target.value)}
                    placeholder="Identifier for this prompt"
                  />{" "}
                  <br />
                </Col>
                <Col span={12}>
                  <span>Tags</span>{" "}
                  <Select
                    mode="tags"
                    style={{
                      width: "100%",
                    }}
                    placeholder="Add your tags to this prompt"
                    onChange={(value) => setPromptTags(value)}
                    options={defaultPromptTags.map((tag) => {
                      return { label: tag, value: tag };
                    })}
                  />
                </Col>
                <Col span={12}>
                  <br />
                  <Checkbox
                    onChange={(e) => setPromptPrivate(e.target.checked)}
                    defaultChecked={false}
                  />{" "}
                  <span>Private</span>
                </Col>
                <Button
                  style={{ marginTop: "15px" }}
                  type="primary"
                  onClick={handleUpdatePrompt}
                >
                  Update
                </Button>
              </Panel>
            </Collapse>
          </Row>
          <Row>
            <Divider style={{ margin: "10px 0 20px" }} />
            <ShareButtons
              url={`${window.location.origin}/s/${shareCode}`}
              title="Check out this prompt on Promptly!"
            />
          </Row>
        </Col>
      </Modal>
    );
  }

  useEffect(() => {
    setShareCode(null);
  }, [
    apiBackendSelected,
    endpointSelected,
    paramValues,
    promptValues,
    setShareCode,
  ]);

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

  useEffect(() => {
    // Shared mode for logged out user or logged in user with share code set in localStorage
    if (
      (isSharedPageMode && !isLoggedIn) ||
      (isLoggedIn && localStorage.getItem("shareCode"))
    ) {
      let code = isSharedPageMode ? shareId : localStorage.getItem("shareCode");

      axios()
        .get(`/api/share/code/${code}`)
        .then((response) => {
          setApiBackendSelected(response.data.api_backend);
          setInput(response.data.input || {});
          setProcessorResult(response?.data?.output[0]);
          if (response?.data?.output?.generations) {
            setOutput(response?.data?.output?.generations);
          } else if (response?.data?.output?.chat_completions) {
            setOutput(response?.data?.output?.chat_completions);
          } else {
            setOutput([response?.data?.output]);
          }
          setParamValues(
            response.data.param_values || response.data.config_values || {},
          );
          setPromptValues(
            response.data.prompt_values || response.data.template_values || {},
          );
          setShareCode(code);

          if (
            response.data?.name !== undefined &&
            response.data?.name !== "Untitled"
          ) {
            document.title = `${response.data.name} | Promptly`;
          }
        })
        .catch((error) => {
          console.error(error);
        })
        .then(() => {
          localStorage.removeItem("shareCode");
        });
    }
  }, [
    isSharedPageMode,
    shareId,
    isLoggedIn,
    setApiBackendSelected,
    setParamValues,
    setPromptValues,
    setShareCode,
    setInput,
  ]);

  useEffect(() => {}, [paramValues, promptValues, input]);

  const isShareButtonEnabled =
    isLoggedIn &&
    apiBackendSelected &&
    ((paramValues && Object.keys(paramValues).length > 0) ||
      (promptValues && Object.keys(promptValues).length > 0));

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
      <Col style={{ width: "100%", height: "100%" }}>
        <Row gutter={[4, 4]} style={{ height: "100%" }}>
          <Col
            span={20}
            style={{
              display: "flex",
              flexDirection: "column",
              width: "100%",
            }}
            xs={24}
            md={20}
          >
            <Row>
              <Card
                style={{
                  textAlign: "left",
                  width: "100%",
                  boxShadow: "0 0 3px #ccc",
                }}
              >
                <Space
                  style={{ width: "100%", justifyContent: "space-between" }}
                >
                  <div>
                    <Radio.Group
                      options={[
                        { label: "Existing", value: true },
                        { label: "Create New", value: false },
                      ]}
                      value={useExistingEndpoint}
                      ref={tourRef1}
                      onChange={(x) => {
                        // Reset apiBackendSelected and endpointSelected so we repopulate params form
                        setEndpointSelected(null);
                        setApiBackendSelected(null);
                        setUseExistingEndpoint(x.target.value);
                        setOutput("");
                        setParamValues({});
                        setPromptValues({});
                      }}
                      optionType="button"
                    />
                    <Divider type="vertical"></Divider>
                    <Space style={{ marginRight: 17 }}>
                      {useExistingEndpoint ? (
                        <EndpointSelector />
                      ) : (
                        <ApiBackendSelector innerRef={tourRef2} />
                      )}
                    </Space>
                    {endpointSelected && (
                      <Button
                        style={{ backgroundColor: "#f7ee9d" }}
                        onClick={(e) =>
                          endpointSelected.draft
                            ? setSaveEndpointModalVisibility(true)
                            : setSaveVersionModalVisibility(true)
                        }
                      >
                        {endpointSelected.draft
                          ? "Save Endpoint"
                          : "Save Version"}
                      </Button>
                    )}
                  </div>
                  <div>
                    {false && (
                      <ShareEndpointButton
                        isShareButtonEnabled={isShareButtonEnabled}
                        componentRef={tourRef5}
                        responseId={responseId}
                        output={output}
                      ></ShareEndpointButton>
                    )}
                  </div>
                </Space>
              </Card>
            </Row>
            <Row style={{ padding: "4px 0", width: "100%", flex: 1 }}>
              <Col span={12} ref={tourRef4} xs={24} md={12}>
                <div className="home-card" style={homeCardStyle}>
                  <Row>
                    <InputForm
                      schema={
                        apiBackendSelected
                          ? apiBackendSelected.input_schema
                          : {}
                      }
                      uiSchema={
                        apiBackendSelected
                          ? apiBackendSelected.input_ui_schema
                          : {}
                      }
                      emptyMessage="Select your API Backend to see the parameters"
                    />
                  </Row>
                  <Row
                    style={{
                      justifyContent: "end",
                      margin: "10px",
                    }}
                  >
                    {apiBackendSelected && <TestPrompt />}
                  </Row>
                </div>
              </Col>
              <Col span={12} ref={tourRef4} xs={24} md={12}>
                <div className="home-card" style={homeCardStyle}>
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
                </div>
              </Col>
            </Row>
          </Col>
          <Col span={4} ref={tourRef3} xs={24} md={4}>
            <div className="home-card" style={homeCardStyle}>
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
            </div>
          </Col>
        </Row>
      </Col>

      <SaveEndpointModal />
      <SaveVersionModal />
      <ShareModal />
      <LoggedOutModal
        visibility={!isLoggedIn && loggedOutModalVisibility}
        handleCancelCb={() => setLoggedOutModalVisibility(false)}
        data={shareId}
      />
    </div>
  );
}
