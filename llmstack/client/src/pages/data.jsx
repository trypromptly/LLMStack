import { Table } from "antd";
import {
  Button,
  IconButton,
  Box,
  CircularProgress,
  Drawer,
  Divider,
  Chip,
  Grid,
  Stack,
  Tooltip,
} from "@mui/material";

import { TextareaAutosize } from "@mui/base";

import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import SyncOutlinedIcon from "@mui/icons-material/SyncOutlined";
import SettingsEthernetIcon from "@mui/icons-material/SettingsEthernet";
import PeopleOutlineOutlinedIcon from "@mui/icons-material/PeopleOutlineOutlined";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";

import { Alert, AlertTitle, Link } from "@mui/material";
import { useEffect, useState } from "react";
import { useRecoilState, useRecoilValue } from "recoil";
import {
  dataSourceEntriesState,
  orgDataSourceEntriesState,
  dataSourceEntriesTableDataState,
  profileFlagsState,
  profileState,
} from "../data/atoms";
import { AddDataSourceModal } from "../components/datasource/AddDataSourceModal";
import DeleteConfirmationModal from "../components/DeleteConfirmationModal";
import ShareDataSourceModal from "../components/datasource/ShareDataSourceModal";
import { axios } from "../data/axios";
import { LocaleDate, FileSize } from "../components/Utils";
import { useReloadDataSourceEntries, useReloadDataSources } from "../data/init";

function DataSourceEntryContent({ onCancel, dataSourceEntryData, open }) {
  const [data, setData] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (dataSourceEntryData?.config?.document_ids) {
      setLoading(true);
      axios()
        .get(`/api/datasource_entries/${dataSourceEntryData.uuid}/text_content`)
        .then((response) => {
          setData(
            <TextareaAutosize
              value={response.data?.content}
              disabled={true}
              autoSize
              style={{
                maxHeight: "80vh",
                width: "100%",
                overflow: "auto",
              }}
            />,
          );
          setMetadata(response.data?.metadata);
        })
        .finally(() => setLoading(false));
    } else {
      setData(
        <TextareaAutosize
          value={JSON.stringify(dataSourceEntryData?.config?.errors)}
          disabled={true}
          autoSize
          style={{ maxHeight: "80vh", width: "100%", overflow: "auto" }}
        ></TextareaAutosize>,
      );
    }
  }, [
    dataSourceEntryData?.config?.document_ids,
    dataSourceEntryData?.config?.errors,
    dataSourceEntryData.uuid,
  ]);
  return (
    <Drawer
      open={open}
      onClose={onCancel}
      anchor="right"
      sx={{ "& .MuiDrawer-paper": { minWidth: "40%" } }}
    >
      <Box>
        <Stack direction={"row"} gap={1} sx={{ mb: "10px", mt: "10px" }}>
          <Button onClick={() => onCancel()} sx={{ alignSelf: "left" }}>
            X
          </Button>
          {Object.keys(metadata || {}).map((key) => (
            <Chip
              label={`${key}: ${metadata[key]}`}
              size="small"
              key={key}
              sx={{ borderRadius: "10px", marginTop: "5px" }}
            />
          ))}
        </Stack>
        <Divider />
        {loading ? (
          <CircularProgress />
        ) : (
          <div style={{ margin: "0px 10px" }}>{data}</div>
        )}
      </Box>
    </Drawer>
  );
}
export default function DataPage() {
  const [deleteModalTitle, setDeleteModalTitle] = useState("");
  const [deleteModalMessage, setDeleteModalMessage] = useState("");
  const [deleteId, setDeleteId] = useState(null);
  const [addDataSourceModalOpen, setAddDataSourceModalOpen] = useState(false);
  const [deleteConfirmationModalOpen, setDeleteConfirmationModalOpen] =
    useState(false);
  const [shareDataSourceModalOpen, setShareDataSourceModalOpen] =
    useState(false);

  const [dataSourceEntryData, setDataSourceEntryData] = useState(null);
  const [dataSourceEntryDrawerOpen, setDataSourceEntryDrawerOpen] =
    useState(false);
  const dataSourceEntriesTable = useRecoilValue(
    dataSourceEntriesTableDataState,
  );
  const [dataSourceEntries, setDataSourceEntries] = useRecoilState(
    dataSourceEntriesState,
  );
  const [orgDataSourceEntries, setOrgDataSourceEntries] = useRecoilState(
    orgDataSourceEntriesState,
  );
  const [dataSourceEntriesLoading, setDataSourceEntriesLoading] =
    useState(null);
  const profile = useRecoilValue(profileState);
  const [table_data, setTableData] = useState([]);
  const [modalTitle, setModalTitle] = useState("Add New Data Source");
  const [selectedDataSource, setSelectedDataSource] = useState(null);
  const reloadDataSourceEntries = useReloadDataSourceEntries();
  const reloadDataSources = useReloadDataSources();
  const profileFlags = useRecoilValue(profileFlagsState);

  useEffect(() => {
    if (dataSourceEntriesTable.length > 0) {
      setTableData(dataSourceEntriesTable);
    }
  }, [dataSourceEntriesTable]);

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Owner",
      key: "owner",
      render: (record) => {
        return <span>{record.isUserOwned ? "me" : record.owner_email}</span>;
      },
    },
    {
      title: "Data Source Type",
      dataIndex: ["type", "name"],
      key: "type",
    },

    {
      title: "Size",
      dataIndex: "size",
      key: "size",
      render: (record) => {
        return <FileSize value={record} />;
      },
    },
    {
      title: "Created At",
      dataIndex: "created_at",
      key: "created_at",
      render: (record) => {
        return <LocaleDate value={record} />;
      },
    },
    {
      title: "Last Modified",
      dataIndex: "updated_at",
      key: "updated_at",
      render: (record) => {
        return <LocaleDate value={record} />;
      },
    },
    {
      title: "Action",
      key: "operation",
      render: (record) => {
        return (
          <Box>
            {!record?.type?.is_external_datasource && (
              <IconButton
                disabled={!record.isUserOwned}
                onClick={() => {
                  setModalTitle("Add New Data Entry");
                  setSelectedDataSource(record);
                  setAddDataSourceModalOpen(true);
                }}
              >
                <AddOutlinedIcon />
              </IconButton>
            )}
            {record?.type?.is_external_datasource && (
              <Tooltip title="External Connection">
                <span>
                  <IconButton disabled={true}>
                    <SettingsEthernetIcon />
                  </IconButton>
                </span>
              </Tooltip>
            )}
            <IconButton
              disabled={!record.isUserOwned}
              onClick={() => {
                setDeleteId(record);
                setDeleteModalTitle("Delete Data Source");
                setDeleteModalMessage(
                  <div>
                    Are you sure you want to delete{" "}
                    <span style={{ fontWeight: "bold" }}>{record.name}</span> ?
                  </div>,
                );
                setDeleteConfirmationModalOpen(true);
              }}
            >
              <DeleteOutlineOutlinedIcon />
            </IconButton>
            {profileFlags.IS_ORGANIZATION_MEMBER && record.isUserOwned && (
              <IconButton
                onClick={() => {
                  setModalTitle("Share Datasource");
                  setSelectedDataSource(record);
                  setShareDataSourceModalOpen(true);
                }}
              >
                {record.visibility === 0 ? (
                  <PersonOutlineOutlinedIcon />
                ) : (
                  <PeopleOutlineOutlinedIcon />
                )}
              </IconButton>
            )}
          </Box>
        );
      },
    },
  ];

  const expandedRowRender = (data) => {
    const data_source_entries = data.data_source_entries;

    if (dataSourceEntriesLoading === data.uuid) {
      return (
        <div style={{ display: "flex", justifyContent: "center" }}>
          <CircularProgress />
        </div>
      );
    }

    const columns = [
      {
        title: "Name",
        dataIndex: "name",
        key: "name",
      },
      {
        title: "Size",
        key: "size",
        dataIndex: "size",
        render: (record) => {
          return <FileSize value={record} />;
        },
      },
      {
        title: "Status",
        key: "status",
        render: (record) => {
          let color = "success";
          if (record.status === "FAILED") {
            color = "error";
          } else if (record.status === "READY") {
            color = "success";
          } else {
            color = "info";
          }
          return (
            <Chip
              color={color}
              key={record.uuid}
              style={{ cursor: "pointer" }}
              onClick={() => {
                setDataSourceEntryData(record);
                setDataSourceEntryDrawerOpen(true);
              }}
              label={
                record.status.charAt(0) + record.status.slice(1).toLowerCase()
              }
              size="small"
            ></Chip>
          );
        },
      },
      {
        title: "Created At",
        dataIndex: "created_at",
        key: "created_at",
        render: (record) => {
          return <LocaleDate value={record} />;
        },
      },
      {
        title: "Last Modified",
        dataIndex: "updated_at",
        key: "updated_at",
        render: (record) => {
          return <LocaleDate value={record} />;
        },
      },
      {
        title: "Action",
        key: "operation",
        render: (record) => {
          const isAdhocSyncSupported = record?.sync_config;

          return (
            <Box>
              <IconButton
                disabled={!record.isUserOwned}
                onClick={() => {
                  setDeleteId(record);
                  setDeleteModalTitle("Delete Data Source Entry");
                  setDeleteModalMessage(
                    <div>
                      Are you sure you want to delete{" "}
                      <span style={{ fontWeight: "bold" }}>{record.name}</span>{" "}
                      ?
                    </div>,
                  );
                  setDeleteConfirmationModalOpen(true);
                }}
              >
                <DeleteOutlineOutlinedIcon className="delete-dataentry-icon" />
              </IconButton>
              {isAdhocSyncSupported && (
                <IconButton
                  onClick={() => {
                    axios()
                      .post(`/api/datasource_entries/${record.uuid}/resync`)
                      .then((response) => {
                        reloadDataSourceEntries();
                        reloadDataSourceEntries();
                      });
                  }}
                >
                  <SyncOutlinedIcon className="resync-dataentry-icon" />
                </IconButton>
              )}
            </Box>
          );
        },
      },
    ];

    return (
      <Table
        columns={columns}
        dataSource={data_source_entries}
        rowKey={(record) => record.uuid}
        pagination={false}
        style={{ cursor: "pointer" }}
        onRow={(record, rowIndex) => {
          return {
            onClick: (event) => {
              if (event.target.tagName === "TD") {
                setDataSourceEntryData(record);
                setDataSourceEntryDrawerOpen(true);
              }
            },
          };
        }}
      />
    );
  };

  const onDataSourceExpand = (expanded, record) => {
    if (expanded) {
      let url = `/api/datasources/${record.uuid}/entries`;
      if (!record.isUserOwned) {
        url = `/api/org/datasources/${record.uuid}/entries`;
      }
      setDataSourceEntriesLoading(record.uuid);

      axios()
        .get(url)
        .then((response) => {
          if (record.isUserOwned) {
            setDataSourceEntries([
              ...dataSourceEntries.filter(
                (dataSourceEntry) =>
                  dataSourceEntry.datasource.uuid !== record.uuid,
              ),
              ...response.data,
            ]);
          } else {
            setOrgDataSourceEntries([
              ...orgDataSourceEntries.filter(
                (dataSourceEntry) =>
                  dataSourceEntry.datasource.uuid !== record.uuid,
              ),
              ...response.data,
            ]);
          }
        })
        .finally(() => {
          setDataSourceEntriesLoading(null);
        });
    }
  };

  return (
    <div id="data-page">
      {false &&
        profile &&
        !profile.openai_key &&
        !profileFlags?.IS_ORGANIZATION_MEMBER && (
          <Alert
            severity="error"
            style={{ width: "100%", margin: "10px 0", textAlign: "left" }}
          >
            <AlertTitle>Missing API Keys</AlertTitle>
            <p>
              You are missing API keys for <strong>Open AI</strong>. Please add
              them in your <Link href="/settings">profile</Link> before you a
              add datasource. If you don't have an API key, you can get one by
              visiting your{" "}
              <Link
                href="https://platform.openai.com/account/api-keys"
                target="_blank"
                rel="noreferrer"
              >
                Open AI account
              </Link>
              .
            </p>
          </Alert>
        )}
      <Grid span={24} style={{ padding: "10px" }}>
        <Grid item style={{ width: "100%", padding: "15px 0px" }}>
          <Button
            onClick={() => {
              setAddDataSourceModalOpen(true);
            }}
            type="primary"
            variant="contained"
            sx={{ float: "left", marginBottom: "10px", textTransform: "none" }}
          >
            Add Data Source
          </Button>
        </Grid>
        <Grid item style={{ width: "100%" }}>
          <Table
            dataSource={table_data}
            columns={columns}
            pagination={{ pageSize: 10 }}
            expandable={{ expandedRowRender, onExpand: onDataSourceExpand }}
            rowKey={(record) => record.uuid}
            style={{ width: "100%" }}
          ></Table>
        </Grid>
      </Grid>
      {addDataSourceModalOpen && (
        <AddDataSourceModal
          open={addDataSourceModalOpen}
          handleCancelCb={() => {
            setSelectedDataSource(null);
            setAddDataSourceModalOpen(false);
          }}
          dataSourceAddedCb={() => {
            setSelectedDataSource(null);
            reloadDataSourceEntries();
            reloadDataSources();
            setAddDataSourceModalOpen(false);
          }}
          modalTitle={modalTitle}
          datasource={selectedDataSource}
        />
      )}
      {deleteConfirmationModalOpen && (
        <DeleteConfirmationModal
          id={deleteId}
          title={deleteModalTitle}
          text={deleteModalMessage}
          open={deleteConfirmationModalOpen}
          onOk={(param) => {
            if (param?.data_source_entries !== undefined) {
              axios()
                .delete(`api/datasources/${param.uuid}`)
                .then((res) => {
                  reloadDataSources();
                  setDeleteConfirmationModalOpen(false);
                });
            } else {
              axios()
                .delete(`api/datasource_entries/${param.uuid}`)
                .then((res) => {
                  reloadDataSourceEntries();
                  setDeleteConfirmationModalOpen(false);
                });
            }
          }}
          onCancel={() => {
            setDeleteConfirmationModalOpen(false);
          }}
        />
      )}
      {dataSourceEntryDrawerOpen && (
        <DataSourceEntryContent
          onCancel={() => setDataSourceEntryDrawerOpen(false)}
          dataSourceEntryData={dataSourceEntryData}
          open={dataSourceEntryDrawerOpen}
        />
      )}
      {shareDataSourceModalOpen && (
        <ShareDataSourceModal
          title={modalTitle}
          onCancel={() => setShareDataSourceModalOpen(false)}
          onOk={() => {
            setShareDataSourceModalOpen(false);
          }}
          open={shareDataSourceModalOpen}
          dataSource={selectedDataSource}
        />
      )}
    </div>
  );
}
