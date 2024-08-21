import {
  AddOutlined,
  DeleteOutlineOutlined,
  EditOutlined,
  KeyboardArrowDownOutlined,
  KeyboardArrowRightOutlined,
  PeopleOutlineOutlined,
  PersonOutlineOutlined,
  SettingsEthernet,
  SyncOutlined,
  VisibilityOutlined,
} from "@mui/icons-material";
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  Container,
  Grid,
  IconButton,
  Pagination,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import moment from "moment";
import { enqueueSnackbar } from "notistack";
import { useEffect, useState } from "react";
import { useRecoilState, useRecoilValue } from "recoil";
import { AddDataSourceModal } from "../components/datasource/AddDataSourceModal";
import { DatasourceFormModal } from "../components/datasource/DataSourceFormModal";
import { AddSourceEntryDataModal } from "../components/datasource/AddSourceEntryDataModal";
import DataSourceEntryContent from "../components/datasource/DataSourceEntryContent";
import ShareDataSourceModal from "../components/datasource/ShareDataSourceModal";
import DeleteConfirmationModal from "../components/DeleteConfirmationModal";
import { FileSize, LocaleDate } from "../components/Utils";
import {
  dataSourceEntriesState,
  dataSourceEntriesTableDataState,
  orgDataSourceEntriesState,
  profileFlagsSelector,
} from "../data/atoms";
import { axios } from "../data/axios";
import { useReloadDataSourceEntries, useReloadDataSources } from "../data/init";

export function DataSourceEntries({
  dataSourceEntryData,
  onDatasourceEntryDelete = () => {},
}) {
  const [dataSourceEntryDrawerOpen, setDataSourceEntryDrawerOpen] =
    useState(false);
  const [dataSourceEntry, setDataSourceEntry] = useState(null);
  const [deleteConfirmationModalOpen, setDeleteConfirmationModalOpen] =
    useState(false);
  const [resyncEntries, setResyncEntries] = useState(new Set());
  const reloadDataSourceEntries = useReloadDataSourceEntries();

  const columns = [
    {
      title: "Name",
      key: "name",
    },
    {
      title: "Size",
      key: "size",
      render: (record) => {
        return <FileSize value={record} />;
      },
    },
    {
      title: "Status",
      key: "status",
      render: (record, row) => {
        let color = "success";
        if (record === "FAILED") {
          color = "error";
        } else if (record === "READY") {
          color = "success";
        } else {
          color = "info";
        }
        return (
          <Chip
            color={color}
            key={row.uuid}
            style={{ cursor: "pointer" }}
            label={row.status.charAt(0) + row.status.slice(1).toLowerCase()}
            size="small"
          ></Chip>
        );
      },
    },
    {
      title: "Created At",
      key: "created_at",
      render: (record) => {
        return <LocaleDate value={record} />;
      },
    },
    {
      title: "Last Modified",
      key: "updated_at",
      render: (record) => {
        return moment(record).fromNow();
      },
    },
    {
      title: "Action",
      key: "operation",
      render: (record, row) => {
        return (
          <Box>
            <Tooltip title="View contents">
              <IconButton
                onClick={() => {
                  setDataSourceEntryDrawerOpen(true);
                  setDataSourceEntry(row);
                }}
                disabled={resyncEntries.has(row.uuid)}
              >
                <VisibilityOutlined />
              </IconButton>
            </Tooltip>
            {row?.datasource?.has_source && (
              <Tooltip title="Resync contents">
                <IconButton
                  onClick={() => {
                    enqueueSnackbar("Resyncing data source entry", {
                      variant: "success",
                    });
                    setResyncEntries((oldResyncEntries) => {
                      return new Set([...oldResyncEntries, row.uuid]);
                    });
                    axios()
                      .post(`/api/datasource_entries/${row.uuid}/resync_async`)
                      .then((res) => {
                        reloadDataSourceEntries();
                      })
                      .catch((err) => {
                        enqueueSnackbar("Failed to resync data source entry", {
                          variant: "error",
                        });
                      })
                      .finally(() => {
                        setResyncEntries((oldResyncEntries) => {
                          return new Set(
                            [...oldResyncEntries].filter(
                              (entry) => entry !== row.uuid,
                            ),
                          );
                        });
                      });
                  }}
                >
                  <SyncOutlined />
                </IconButton>
              </Tooltip>
            )}
            <Tooltip title="Delete entry">
              <IconButton
                onClick={() => {
                  setDataSourceEntry(row);
                  setDeleteConfirmationModalOpen(true);
                }}
              >
                <DeleteOutlineOutlined />
              </IconButton>
            </Tooltip>
          </Box>
        );
      },
    },
  ];

  return dataSourceEntryData.length === 0 ? (
    <Container>
      <Alert severity="info" sx={{ maxWidth: "300px", margin: "0 auto" }}>
        <AlertTitle>No entries found</AlertTitle>
        Click on the <strong>+</strong> icon to add a new entry.
      </Alert>
    </Container>
  ) : (
    <Table stickyHeader aria-label="sticky table contents" colSpan={7}>
      <TableHead>
        <TableRow>
          {columns.map((column) => (
            <TableCell key={column.key} sx={{ padding: "5px 16px" }}>
              <strong>{column.title}</strong>
            </TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody sx={{ borderBottom: "none" }}>
        {dataSourceEntryData?.map((row, index) => {
          return (
            <TableRow role="checkbox" tabIndex={-1} key={row.uuid}>
              {columns.map((column) => {
                const value = row[column.key];
                return (
                  <TableCell key={column.key} sx={{ padding: "0 16px" }}>
                    {column.render ? column.render(value, row) : value}
                  </TableCell>
                );
              })}
            </TableRow>
          );
        })}
      </TableBody>
      <DataSourceEntryContent
        onCancel={() => setDataSourceEntryDrawerOpen(false)}
        dataSourceEntry={dataSourceEntry}
        open={dataSourceEntryDrawerOpen}
      />
      <DeleteConfirmationModal
        id={dataSourceEntry}
        title="Delete Data Source Entry"
        text={
          <div>
            Are you sure you want to delete{" "}
            <span style={{ fontWeight: "bold" }}>{dataSourceEntry?.name}</span>{" "}
            ?
          </div>
        }
        open={deleteConfirmationModalOpen}
        onOk={(param) => {
          axios()
            .delete(`/api/datasource_entries/${param.uuid}`)
            .then((res) => {
              onDatasourceEntryDelete();
              reloadDataSourceEntries();
              setDeleteConfirmationModalOpen(false);
            });
        }}
        onCancel={() => {
          setDeleteConfirmationModalOpen(false);
        }}
      />
    </Table>
  );
}

export default function DataPage() {
  const entriesPerPage = 10;
  const [pageNumber, setPageNumber] = useState(1);
  const [deleteModalTitle, setDeleteModalTitle] = useState("");
  const [deleteModalMessage, setDeleteModalMessage] = useState("");
  const [deleteId, setDeleteId] = useState(null);
  const [addDataSourceEntryModalOpen, setAddDataSourceEntryModalOpen] =
    useState(false);
  const [addDataSourceModalOpen, setAddDataSourceModalOpen] = useState(false);
  const [editDataSourceModalOpen, setEditDataSourceModalOpen] = useState(false);
  const [deleteConfirmationModalOpen, setDeleteConfirmationModalOpen] =
    useState(false);
  const [shareDataSourceModalOpen, setShareDataSourceModalOpen] =
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
  const [tableData, setTableData] = useState([]);
  const [modalTitle, setModalTitle] = useState("Add New Data Source");
  const [selectedDataSource, setSelectedDataSource] = useState(null);
  const [dataSourceBeingLoaded, setDataSourceBeingLoaded] = useState(null); // uuid of the data source being loaded
  const reloadDataSourceEntries = useReloadDataSourceEntries();
  const reloadDataSources = useReloadDataSources();
  const profileFlags = useRecoilValue(profileFlagsSelector);

  useEffect(() => {
    if (dataSourceEntriesTable.length > 0) {
      setTableData((oldTableData) =>
        dataSourceEntriesTable.map((item) => ({
          ...item,
          expand:
            oldTableData.find((row) => row.uuid === item.uuid)?.expand || false,
        })),
      );
    }
  }, [dataSourceEntriesTable]);

  const columns = [
    {
      title: "Name",
      key: "name",
      render: (record, row) => {
        return (
          <Typography
            sx={{
              display: "flex",
              fontSize: "0.9rem",
              fontWeight: row.expand ? "600" : "inherit",
              gap: 1,
            }}
          >
            {row.expand ? (
              <KeyboardArrowDownOutlined
                fontSize="10px"
                sx={{ color: "#999", margin: "auto 0" }}
              />
            ) : (
              <KeyboardArrowRightOutlined
                fontSize="10px"
                sx={{ color: "#999", margin: "auto 0" }}
              />
            )}
            {record}
          </Typography>
        );
      },
    },
    {
      title: "Owner",
      key: "owner_email",
      render: (record, row) => {
        return <span>{row.isUserOwned ? "me" : row.owner_email}</span>;
      },
    },
    {
      title: "Data Source Type",
      key: "type",
      render: (record) => {
        return <span>{record["name"]}</span>;
      },
    },

    {
      title: "Size",
      key: "size",
      render: (record) => {
        return <FileSize value={record} />;
      },
    },
    {
      title: "Created At",
      key: "created_at",
      render: (record) => {
        return <LocaleDate value={record} />;
      },
    },
    {
      title: "Last Modified",
      key: "updated_at",
      render: (record) => {
        return moment(record).fromNow();
      },
    },
    {
      title: "Action",
      key: "operation",
      render: (record, row) => {
        return (
          <Box>
            <Tooltip title="Edit entry">
              <IconButton
                onClick={(e) => {
                  setSelectedDataSource(row);
                  console.log(row);
                  setEditDataSourceModalOpen(true);
                  e.stopPropagation();
                }}
              >
                <EditOutlined />
              </IconButton>
            </Tooltip>

            {row?.has_source && (
              <IconButton
                disabled={!row.isUserOwned}
                onClick={(e) => {
                  setModalTitle("Add New Data Entry");
                  setSelectedDataSource(row);
                  setAddDataSourceEntryModalOpen(true);

                  e.stopPropagation();
                }}
              >
                <AddOutlined />
              </IconButton>
            )}
            {row?.has_source && (
              <Tooltip title="Resync data">
                <IconButton
                  onClick={() => {
                    axios()
                      .post(`/api/datasources/${row.uuid}/resync_async`)
                      .then((res) => {
                        enqueueSnackbar("Resyncing data source", {
                          variant: "success",
                        });
                      })
                      .catch((err) => {
                        enqueueSnackbar("Failed to resync data source entry", {
                          variant: "error",
                        });
                      });
                  }}
                >
                  <SyncOutlined />
                </IconButton>
              </Tooltip>
            )}
            {row?.is_destination_only && (
              <Tooltip title="External Connection">
                <span>
                  <IconButton disabled={true}>
                    <SettingsEthernet />
                  </IconButton>
                </span>
              </Tooltip>
            )}
            <IconButton
              disabled={!row.isUserOwned}
              onClick={() => {
                setDeleteId(row);
                setDeleteModalTitle("Delete Data Source");
                setDeleteModalMessage(
                  <div>
                    Are you sure you want to delete{" "}
                    <span style={{ fontWeight: "bold" }}>{row.name}</span> ?
                  </div>,
                );
                setDeleteConfirmationModalOpen(true);
              }}
            >
              <DeleteOutlineOutlined />
            </IconButton>
            {profileFlags.IS_ORGANIZATION_MEMBER && row.isUserOwned && (
              <IconButton
                onClick={() => {
                  setModalTitle("Share Datasource");
                  setSelectedDataSource(row);
                  setShareDataSourceModalOpen(true);
                }}
              >
                {row.visibility === 0 ? (
                  <PersonOutlineOutlined />
                ) : (
                  <PeopleOutlineOutlined />
                )}
              </IconButton>
            )}
          </Box>
        );
      },
    },
  ];

  // Expand the datasource row on click and load the datasource entries
  const handleRowClick = (row) => {
    setTableData(
      tableData.map((item) => {
        if (item.uuid === row.uuid) {
          item.expand = !item.expand;
        }
        return item;
      }),
    );

    setDataSourceEntriesLoading(true);
    setDataSourceBeingLoaded(row.uuid);

    let url = `/api/datasources/${row.uuid}/entries`;
    if (!row.isUserOwned) {
      url = `/api/org/datasources/${row.uuid}/entries`;
    }

    axios()
      .get(url)
      .then((response) => {
        if (row.isUserOwned) {
          setDataSourceEntries([
            ...dataSourceEntries.filter(
              (dataSourceEntry) => dataSourceEntry.datasource.uuid !== row.uuid,
            ),
            ...response.data,
          ]);
        } else {
          setOrgDataSourceEntries([
            ...orgDataSourceEntries.filter(
              (dataSourceEntry) => dataSourceEntry.datasource.uuid !== row.uuid,
            ),
            ...response.data,
          ]);
        }
      })
      .finally(() => {
        setDataSourceEntriesLoading(null);
      });
  };

  return (
    <div id="data-page" style={{ marginBottom: "120px" }}>
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
          <Table stickyHeader aria-label="sticky table">
            <TableHead>
              <TableRow>
                {columns.map((column) => (
                  <TableCell
                    key={column.key}
                    sx={{
                      paddingLeft: column.key === "name" ? "40px" : "inherit",
                    }}
                  >
                    <strong>{column.title}</strong>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {tableData
                .slice(
                  (pageNumber - 1) * entriesPerPage,
                  pageNumber * entriesPerPage,
                )
                .map((row, index) => {
                  return [
                    [
                      <TableRow
                        hover
                        key={row.uuid}
                        sx={{
                          cursor: "pointer",
                          backgroundColor: row.expand ? "#f5f5f5" : "inherit",
                        }}
                        onClick={() => {
                          handleRowClick(row);
                        }}
                      >
                        {columns.map((column) => {
                          const value = row[column.key];
                          return (
                            <TableCell
                              key={column.key}
                              sx={{
                                fontWeight: row.expand ? "bold" : "inherit",
                              }}
                            >
                              {column.render
                                ? column.render(value, row)
                                : value}
                            </TableCell>
                          );
                        })}
                      </TableRow>,
                      <TableRow key={`${row.uuid}_details`}>
                        <TableCell
                          colSpan={7}
                          sx={{ padding: row.expand ? "0" : "inherit" }}
                        >
                          <Collapse
                            in={row.expand}
                            timeout="auto"
                            unmountOnExit
                          >
                            <Box sx={{ margin: 1 }}>
                              {dataSourceEntriesLoading &&
                              dataSourceBeingLoaded === row.uuid ? (
                                <CircularProgress />
                              ) : (
                                <DataSourceEntries
                                  dataSourceEntryData={
                                    row.data_source_entries || []
                                  }
                                />
                              )}
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>,
                    ],
                  ];
                })}
            </TableBody>
          </Table>
          <Pagination
            count={Math.ceil(tableData.length / entriesPerPage)}
            variant="outlined"
            shape="rounded"
            page={pageNumber}
            onChange={(event, value) => {
              setPageNumber(value);
            }}
            sx={{ marginTop: 2, float: "right" }}
          />
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
      {editDataSourceModalOpen && (
        <DatasourceFormModal
          open={editDataSourceModalOpen}
          cancelCb={() => {
            setEditDataSourceModalOpen(false);
          }}
          datasource={selectedDataSource}
          submitCb={() => {
            setEditDataSourceModalOpen(false);
            reloadDataSources();
          }}
        />
      )}
      {addDataSourceEntryModalOpen && (
        <AddSourceEntryDataModal
          open={addDataSourceEntryModalOpen}
          onCancel={() => {
            setAddDataSourceEntryModalOpen(false);
          }}
          onSubmit={(sourceEntryData) => {
            axios()
              .post(
                `/api/datasources/${selectedDataSource.uuid}/add_entry_async`,
                {
                  source_data: sourceEntryData,
                },
              )
              .then(() => {
                reloadDataSourceEntries();
                enqueueSnackbar(
                  "Processing Data, please refresh the page in a few minutes",
                  {
                    variant: "success",
                  },
                );
              })
              .catch((error) => {
                enqueueSnackbar(
                  `Failed to add entry. ${error?.response?.data}`,
                  {
                    variant: "error",
                  },
                );
              })
              .finally(() => {
                setAddDataSourceEntryModalOpen(false);
              });
          }}
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
            }
          }}
          onCancel={() => {
            setDeleteConfirmationModalOpen(false);
          }}
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
