import { Spin, Table, Tag, Space, Button, Drawer } from "antd";
import { Grid, Typography } from "@mui/material";

import { useEffect, useState } from "react";
import moment from "moment";
import AceEditor from "react-ace";

import { axios } from "../data/axios";

export default function HistoryPageOld() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [processedData, setProcessedData] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(null);

  useEffect(() => {
    setLoading(true);
    axios()
      .get(`/api/responses/history?page=${page}`)
      .then((response) => {
        if (total === null) {
          setTotal(response.data?.count);
        }
        setData(response.data?.results);
      })
      .catch((error) => {
        console.log(error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [page, total]);

  const showDrawer = (processed_records) => {
    setOpen(true);
    setProcessedData(processed_records);
  };

  const onClose = () => {
    setOpen(false);
  };

  const table_data = [];
  const columns = [
    {
      title: "Date",
      dataIndex: "created_on",
      key: "created_on",
      width: "10%",
    },
    {
      title: "Endpoint",
      key: "endpoint_name",
      width: "10%",
      render: (record) => {
        if (record.endpoint_name.startsWith("Playground -")) {
          return (
            <Space size="middle">
              <Typography variant="body2">
                {record.endpoint_name.split("-")[0].trim()}
              </Typography>
            </Space>
          );
        } else {
          return (
            <Space size="middle">
              <Typography variant="body2">
                {record?.app_session?.app
                  ? record.endpoint_name.split(":")[1]
                  : record.endpoint_name}
              </Typography>
              <Tag color="purple">{`Version: ${record.endpoint_version}`}</Tag>
              {record?.app_session?.app && (
                <Tag color="blue">{`App: ${record.app_session.app.name}`}</Tag>
              )}
            </Space>
          );
        }
      },
    },
    {
      title: "Input",
      dataIndex: "input",
      key: "input",
      width: "5%",
      render: (record) => {
        return (
          <Space size="middle">
            <Button
              style={{ color: "#1677ff" }}
              type="text"
              onClick={() => {
                showDrawer(JSON.stringify(record, null, 2));
              }}
            >
              View
            </Button>
          </Space>
        );
      },
    },
    {
      title: "Processed Response",
      dataIndex: "processed_response",
      key: "processed_response",
      width: "10%",
      render: (record) => {
        return (
          <Space size="middle">
            <Button
              style={{ color: "#1677ff" }}
              type="text"
              onClick={() => {
                showDrawer(JSON.stringify(JSON.parse(record), null, 2));
              }}
            >
              View
            </Button>
          </Space>
        );
      },
    },
    {
      title: "Response Code",
      dataIndex: "response_code",
      key: "response_code",
      width: "10%",
      // filterMode: "tree",
      // filterSearch: true,
      // filters: [
      //   {
      //     text: "2xx",
      //     value: "2",
      //   },
      //   {
      //     text: "4xx",
      //     value: "4",
      //   },
      //   {
      //     text: "5xx",
      //     value: "5",
      //   },
      // ],
      // onFilter: (value, record) =>
      //   record.response_code.toString().startsWith(value),
      render: (response_code) => {
        let color = response_code === 200 ? "green" : "red";
        return (
          <Tag color={color} key={response_code}>
            {response_code}
          </Tag>
        );
      },
    },
  ];

  if (loading) {
    return (
      <div id="history-page">
        <Spin />
      </div>
    );
  } else {
    if (data) {
      for (let i = 0; i < data.length; i++) {
        table_data.push({
          key: i,
          created_on: moment
            .utc(data[i].created_on)
            .local()
            .format("D-MMM-YYYY h:mm:ss A"),
          input: data[i].request.input,
          processed_response: data[i].processed_response,
          response_code: data[i].response_code,
          endpoint_name: data[i].request.endpoint.name,
          endpoint_version: data[i].request.endpoint.version,
          app_session: data[i]?.request?.app_session,
        });
      }
    }

    return (
      <div id="history-page">
        <Grid container spacing={1}>
          <Grid item xs={12}>
            <Table
              dataSource={table_data}
              columns={columns}
              size="small"
              pagination={{
                pageSize: 10,
                total: total,
                current: page,
                showSizeChanger: false,
                onChange: (pageNumber, _) => setPage(pageNumber),
              }}
            />
            <Drawer
              title="Processed Response"
              placement="left"
              onClose={onClose}
              open={open}
            >
              <AceEditor
                mode="json"
                theme="github"
                value={processedData}
                editorProps={{ $blockScrolling: true }}
                width="100%"
                height="100%"
                wrapEnabled={true}
                setOptions={{
                  useWorker: false,
                  showGutter: false,
                  readOnly: true,
                }}
              />
            </Drawer>
          </Grid>
        </Grid>
      </div>
    );
  }
}
