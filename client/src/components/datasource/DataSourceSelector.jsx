import { useState } from "react";
import { Button, Select } from "antd";
import { useRecoilValue } from "recoil";
import { dataSourcesState, orgDataSourcesState } from "../../data/atoms";
import { FolderAddOutlined } from "@ant-design/icons";
import { AddDataSourceModal } from "./AddDataSourceModal";

export function DataSourceSelector(props) {
  const dataSources = useRecoilValue(dataSourcesState);
  const orgDataSources = useRecoilValue(orgDataSourcesState);
  const [showAddDataSourceModal, setShowAddDataSourceModal] = useState(false);
  const uniqueDataSources = dataSources.concat(
    orgDataSources.filter(
      (orgDataSource) =>
        !dataSources.some(
          (dataSource) => dataSource.uuid === orgDataSource.uuid,
        ),
    ),
  );

  return (
    <div style={{ width: "100%", display: "flex" }}>
      <Select
        style={{
          width: "auto",
          textAlign: "left",
          flex: 1,
          borderColor: "#000",
        }}
        value={props.value}
        mode="multiple"
        options={uniqueDataSources.map((dataSource) => ({
          label: dataSource.name,
          value: dataSource.uuid,
        }))}
        placeholder="Select a datasource"
        status="warning"
        onChange={(value) => props.onChange(value)}
      />
      <Button
        onClick={() => setShowAddDataSourceModal(true)}
        style={{ backgroundColor: "#6287ac", color: "#fed766" }}
      >
        <FolderAddOutlined />
      </Button>
      <AddDataSourceModal
        open={showAddDataSourceModal}
        handleCancelCb={() => setShowAddDataSourceModal(false)}
        dataSourceAddedCb={(dataSource) => props.onChange(dataSource.uuid)}
      />
    </div>
  );
}
