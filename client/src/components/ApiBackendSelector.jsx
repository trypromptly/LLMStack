import { useEffect } from "react";
import { Col, Select, Row } from "antd";
import {
  useRecoilValue,
  useRecoilState,
  useSetRecoilState,
  useResetRecoilState,
} from "recoil";
import {
  apiProviderDropdownListState,
  apiBackendDropdownListState,
  apiBackendSelectedState,
  apiBackendsState,
  apiProviderSelectedState,
  endpointSelectedState,
  endpointConfigValueState,
  inputValueState,
} from "../data/atoms";

export default function ApiBackendSelector() {
  const apiprovidersDropdown = useRecoilValue(apiProviderDropdownListState);
  const apibackendsDropdown = useRecoilValue(apiBackendDropdownListState);
  const apibackends = useRecoilValue(apiBackendsState);
  const resetEndpointSelected = useResetRecoilState(endpointSelectedState);
  const setendpointConfigValueState = useSetRecoilState(
    endpointConfigValueState,
  );
  const resetInputValueState = useResetRecoilState(inputValueState);
  const resetEndpointConfigValueState = useResetRecoilState(
    endpointConfigValueState,
  );

  const [apiProviderSelected, setApiProviderSelected] = useRecoilState(
    apiProviderSelectedState,
  );
  const [apiBackendSelected, setApiBackendSelected] = useRecoilState(
    apiBackendSelectedState,
  );

  useEffect(() => {
    if (apiBackendSelected) {
      resetEndpointSelected();
    }
  }, [apiBackendSelected, resetEndpointSelected]);

  useEffect(() => {
    if (!apiProviderSelected && apibackends && apibackends.length > 0) {
      setApiProviderSelected(
        apibackends.find(
          (backend) => backend.api_endpoint === "chat/completions",
        )?.api_provider.name,
      );
      setApiBackendSelected(
        apibackends.find(
          (backend) => backend.api_endpoint === "chat/completions",
        ),
      );
    } else if (
      !apiBackendSelected &&
      apiProviderSelected &&
      apiProviderSelected === "Open AI"
    ) {
      setApiBackendSelected(
        apibackends.find(
          (backend) => backend.api_endpoint === "chat/completions",
        ),
      );
    }
  }, [
    apibackends,
    apiBackendSelected,
    apiProviderSelected,
    setApiBackendSelected,
    setApiProviderSelected,
  ]);

  return (
    <Col id="apibackendselector">
      <Row>
        <Select
          style={{ width: "auto" }}
          options={apiprovidersDropdown}
          onChange={(x) => {
            setApiProviderSelected(x);
            setApiBackendSelected(null);
            setendpointConfigValueState({});
            resetInputValueState();
          }}
          value={
            apiProviderSelected ? apiProviderSelected : "Select API Provider"
          }
        />
        {apiProviderSelected && (
          <Select
            style={{ width: 150 }}
            options={
              apiProviderSelected
                ? apibackendsDropdown.filter(
                    (x) => x.provider === apiProviderSelected,
                  )
                : apibackendsDropdown
            }
            onChange={(x) => {
              setApiBackendSelected(
                apibackends.find((backend) => backend.id === x),
              );
              setendpointConfigValueState({});
              resetEndpointConfigValueState();
              resetInputValueState();
            }}
            value={
              apiBackendSelected
                ? apibackendsDropdown.find(
                    (x) => x.value === apiBackendSelected.id,
                  )
                : "Select Backend"
            }
          />
        )}
      </Row>
    </Col>
  );
}
