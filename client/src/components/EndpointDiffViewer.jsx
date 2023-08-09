import ReactDiffViewer from "react-diff-viewer-continued";
import { Select } from "antd";
import { useState } from "react";
import { useRecoilValue } from "recoil";
import { endpointsState } from "../data/atoms";

export default function EndpointDiffViewer(props) {
  const endpoints = useRecoilValue(endpointsState);
  const [version, setVersion] = useState(props.endpoint.version);
  const endpointVersions = endpoints.filter(
    (ep) => ep.parent_uuid === props.endpoint.parent_uuid,
  );
  const endpointSelected = endpointVersions.find((x) => x.version === version);

  return (
    <>
      <h3>Version</h3>
      <Select
        style={{ width: "auto", minWidth: 300 }}
        options={endpointVersions.map((x) => {
          return {
            ...x,
            ...{ label: `${x.version}:${x.description}` },
            value: x.version,
          };
        })}
        onChange={(x) => setVersion(x)}
        value={
          endpointSelected ? endpointSelected.version : "Select API Version"
        }
      />
      <h3>Prompt Changes</h3>
      <ReactDiffViewer
        oldValue={endpointSelected.prompt}
        newValue={props.prompt}
        splitView={true}
      />
      <h3>Parameter Changes</h3>
      <ReactDiffViewer
        oldValue={JSON.stringify(endpointSelected.param_values, null, 2)}
        newValue={JSON.stringify(props.paramValues, null, 2)}
        splitView={true}
      />
    </>
  );
}
