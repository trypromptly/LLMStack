import { useState } from "react";
import { Modal, Button, Input, Radio, Space } from "antd";
import { useRecoilValue, useRecoilState } from "recoil";
import { dataSourcesState, dataSourceTypesState } from "../../data/atoms";
import { axios } from "../../data/axios";
import validator from "@rjsf/validator-ajv8";
import ThemedJsonForm from "../ThemedJsonForm";
import { useReloadDataSourceEntries } from "../../data/init";
import GdriveFilePicker from "../form/GdriveFilePicker";
import WebpageURLExtractorWidget from "../form/WebpageURLExtractorWidget";
import { enqueueSnackbar } from "notistack";

function CustomGdriveFileWidget(props) {
  return <GdriveFilePicker {...props} />;
}

function CustomWebpageURLExtractorWidget(props) {
  return <WebpageURLExtractorWidget {...props} />;
}

export function AddDataSourceModal({
  open,
  handleCancelCb,
  dataSourceAddedCb,
  modalTitle = "Add New Data Source",
  datasource = null,
}) {
  const dataSourceTypes = useRecoilValue(dataSourceTypesState);
  const [dataSourceName, setDataSourceName] = useState(
    datasource?.name ? datasource.name : "",
  );
  const [dataSourceNameError, setDataSourceNameError] = useState(false);

  const [dataSources, setDataSources] = useRecoilState(dataSourcesState);
  const [dataSourceType, setDataSourceType] = useState(
    datasource?.type ? datasource.type : dataSourceTypes?.[0],
  );
  const [formData, setFormData] = useState({});
  const reloadDataSourceEntries = useReloadDataSourceEntries();

  return (
    <Modal
      title={modalTitle}
      open={open}
      onCancel={handleCancelCb}
      footer={[
        <Button key="back" onClick={handleCancelCb}>
          Cancel
        </Button>,
        <Button
          key="submit"
          type="primary"
          onClick={() => {
            if (datasource) {
              axios()
                .post(`/api/datasources/${datasource.uuid}/add_entry`, {
                  entry_data: formData,
                })
                .then(() => {
                  reloadDataSourceEntries();
                });
              handleCancelCb();
              enqueueSnackbar(
                "Processing Data, please refresh the page in a few minutes",
                {
                  variant: "success",
                },
              );
            } else {
              if (dataSourceName === "") {
                setDataSourceNameError(true);
                return;
              }

              axios()
                .post("/api/datasources", {
                  name: dataSourceName,
                  type: dataSourceType.id,
                })
                .then((response) => {
                  const dataSource = response.data;
                  setDataSources([...dataSources, dataSource]);
                  axios()
                    .post(`/api/datasources/${dataSource.uuid}/add_entry`, {
                      entry_data: formData,
                    })
                    .then((response) => {
                      dataSourceAddedCb(dataSource);
                    });
                });
              handleCancelCb();
              enqueueSnackbar(
                "Processing Data, please refresh the page in a few minutes",
                {
                  variant: "success",
                },
              );
            }
          }}
        >
          Submit
        </Button>,
      ]}
    >
      <Space direction="vertical" style={{ width: "100%" }}>
        <Input
          value={dataSourceName}
          onChange={(e) => setDataSourceName(e.target.value)}
          placeholder="Data Source Name"
          disabled={datasource ? true : false}
          required={true}
          defaultValue={datasource?.name || "Untitled"}
          status={dataSourceNameError ? "error" : ""}
        />
        <span>Data Source Type</span>
        <Radio.Group
          optionType="button"
          value={dataSourceType?.id}
          onChange={(e) => {
            setDataSourceType(
              dataSourceTypes.find(
                (dataSourceType) => dataSourceType.id === e.target.value,
              ),
            );
          }}
          options={dataSourceTypes.map((dataSourceType) => ({
            label: dataSourceType.name,
            value: dataSourceType.id,
          }))}
          disabled={datasource ? true : false}
        />
        <ThemedJsonForm
          schema={dataSourceType?.entry_config_schema || {}}
          validator={validator}
          uiSchema={{
            ...(dataSourceType?.entry_config_ui_schema || {}),
            ...{
              "ui:submitButtonOptions": {
                norender: true,
              },
              "ui:DescriptionFieldTemplate": () => null,
              "ui:TitleFieldTemplate": () => null,
            },
          }}
          widgets={{
            gdrive: CustomGdriveFileWidget,
            webpageurls: CustomWebpageURLExtractorWidget,
          }}
          formData={formData}
          onChange={({ formData }) => {
            setFormData(formData);
          }}
        />
      </Space>
    </Modal>
  );
}
