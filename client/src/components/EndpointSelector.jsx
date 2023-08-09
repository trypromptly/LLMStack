import { Badge, Col, Select, Row } from "antd";
import { useRecoilState, useRecoilValue, useSetRecoilState } from "recoil";
import {
  endpointsState,
  endpointDropdownListState,
  endpointSelectedState,
  apiBackendSelectedState,
  isLoggedInState,
  endpointConfigValueState,
  templateValueState,
  inputValueState,
} from "../data/atoms";

const { Option } = Select;

export default function ApiBackendSelector() {
  const endpoints = useRecoilValue(endpointsState);
  const endpointsDropdown = useRecoilValue(endpointDropdownListState);
  const setApiBackendSelected = useSetRecoilState(apiBackendSelectedState);
  const [endpointSelected, setEndpointSelected] = useRecoilState(
    endpointSelectedState,
  );
  const setParamValues = useSetRecoilState(endpointConfigValueState);
  const setPromptValues = useSetRecoilState(templateValueState);
  const setInputValue = useSetRecoilState(inputValueState);
  const isLoggedIn = useRecoilValue(isLoggedInState);

  const selectEndpoint = (id_and_version) => {
    const [parent_uuid, version] = id_and_version.split(":");
    const endpoint = endpoints.find(
      (e) => e.parent_uuid === parent_uuid && e.version === parseInt(version),
    );
    setApiBackendSelected(endpoint.api_backend);
    setEndpointSelected(endpoint);
    setParamValues(endpoint.param_values);
    setPromptValues(endpoint.prompt_values);
    setInputValue(endpoint.input);
  };

  const optGroupStyle = {
    color: "#000",
    cursor: "default",
    fontWeight: 500,
  };

  const optStyle = {
    color: "#838383",
    fontSize: "12px",
  };

  const getEndpointDropdownOptions = () => {
    let options = [];

    for (const parentEndpoint of endpointsDropdown) {
      options.push({
        label: parentEndpoint.label,
        parent: true,
        isLive: false,
        key: `parent-${parentEndpoint.uuid}`,
      });

      const latestLiveVersion = parentEndpoint.options
        .map((x) => (x.is_live ? x.version : -1))
        .reduce((a, b) => Math.max(a, b), -Infinity);

      for (const endpoint of [...parentEndpoint.options].sort(
        (a, b) => b.version - a.version,
      )) {
        options.push({
          label: endpoint.label,
          parent: false,
          value: endpoint.value,
          isLive: endpoint.is_live && endpoint.version === latestLiveVersion,
          key: `child-${endpoint.uuid}`,
        });
      }
    }

    return options;
  };

  return (
    <Col id="endpointselector">
      <Row>
        <Select
          style={{ width: "auto", minWidth: 300 }}
          showSearch
          onChange={(x) => selectEndpoint(x)}
          filterOption={(input, option) =>
            (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
          }
          value={
            endpointSelected && !endpointSelected.draft
              ? `${endpointSelected.name}:${endpointSelected.version}`
              : "Select API Endpoint"
          }
          notFoundContent={
            isLoggedIn ? (
              "No endpoints found"
            ) : (
              <p>
                <a href="/login">Log in</a> to see your endpoints
              </p>
            )
          }
        >
          {getEndpointDropdownOptions().map((option) => (
            <Option
              key={option.key}
              value={option.value}
              style={option.parent ? optGroupStyle : optStyle}
              disabled={option.parent}
            >
              {option.isLive && <Badge color={"green"} />}&nbsp;{option.label}
            </Option>
          ))}
        </Select>
      </Row>
    </Col>
  );
}
