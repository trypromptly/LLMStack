import { Button, IconButton, Box, Chip, Grid } from "@mui/material";
import { TextareaAutosize } from "@mui/base";

import { axios } from "../../data/axios";

import { Table } from "antd";
import { useEffect, useState } from "react";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import PlayCircleFilledWhiteOutlinedIcon from "@mui/icons-material/PlayCircleFilledWhiteOutlined";

import { LocaleDate } from "../../components/Utils";
import { AddTestSetModal } from "../testset/AddTestSetModal";
import DeleteConfirmationModal from "../../components/DeleteConfirmationModal";
// import RunTestSetModal from "../testset/RunTestSetModal";

export function AppTests({ app }) {
  const [deleteModalTitle, setDeleteModalTitle] = useState("");
  const [deleteModalMessage, setDeleteModalMessage] = useState("");
  const [deleteId, setDeleteId] = useState(null);
  const [addTestSetModalOpen, setAddTestSetModalOpen] = useState(false);
  const [deleteConfirmationModalOpen, setDeleteConfirmationModalOpen] =
    useState(false);
  const [table_data, setTableData] = useState({});
  const [modalTitle, setModalTitle] = useState("Create Test Set");
  const [selectTestSet, setSelectTestSet] = useState(null);
  const [testSetStatus, setTestSetStatus] = useState({});
  const [testCaseStatus, setTestCaseStatus] = useState({});
  const [testCaseRunOutput, setTestCaseRunOutput] = useState({});

  useEffect(() => {
    // Get data from API
    let data_map = {};

    axios()
      .get(`/api/apps/${app.uuid}/testsets`)
      .then((response) => {
        let data = response.data;
        data.forEach((entry) => {
          data_map[entry.uuid] = {
            ...entry,
            testcases: entry.testcases.map((testcase) => {
              return { ...testcase };
            }),
          };
          setTableData(data_map);
        });
      })
      .catch((error) => {});
  }, [setTableData, app?.uuid]);

  async function runTestSet(testset) {
    setTestSetStatus((prev) => {
      return { ...prev, [testset.uuid]: "RUNNING" };
    });

    const runTestCase = async (testcase) => {
      setTestCaseStatus((prev) => {
        return { ...prev, [testcase.uuid]: "RUNNING" };
      });

      const res = await axios().post(`/api/apps/${app.uuid}/run`, {
        input: testcase.input_data,
        stream: false,
      });

      setTestCaseRunOutput((prev) => {
        return { ...prev, [testcase.uuid]: res.data };
      });

      setTestCaseStatus((prev) => {
        return { ...prev, [testcase.uuid]: "COMPLETED" };
      });

      return res;
    };

    const chunkArray = function (arr, chunkSize) {
      var R = [];
      for (var i = 0, len = arr.length; i < len; i += chunkSize)
        R.push(arr.slice(i, i + chunkSize));
      return R;
    };

    var chunkedTestcases = chunkArray(testset.testcases, 2);

    for (let i = 0; i < chunkedTestcases.length; i++) {
      await Promise.all(chunkedTestcases[i].map(runTestCase)).catch(
        console.error,
      );
    }

    setTestSetStatus((prev) => {
      return { ...prev, [testset.uuid]: "COMPLETED" };
    });
  }

  function runTestCase(testcase) {
    setTestSetStatus((prev) => {
      return { ...prev, [testcase.testset_uuid]: "RUNNING" };
    });
    setTestCaseStatus((prev) => {
      return { ...prev, [testcase.uuid]: "RUNNING" };
    });
    axios()
      .post(`/api/apps/${app.uuid}/run`, {
        input: testcase.input_data,
        stream: false,
      })
      .then((res) => {
        setTestCaseRunOutput((prev) => {
          return { ...prev, [testcase.uuid]: res?.data };
        });
      })
      .catch((err) => {})
      .finally(() => {
        setTestSetStatus((prev) => {
          return { ...prev, [testcase.testset_uuid]: "COMPLETED" };
        });
        setTestCaseStatus((prev) => {
          return { ...prev, [testcase.uuid]: "COMPLETED" };
        });
      });
  }

  const expandedRowRender = (data) => {
    const testcases = data.testcases;

    const columns = [
      {
        title: "Input Data",
        width: "20%",
        render: (record) => {
          return (
            <TextareaAutosize
              disabled={true}
              minRows={3}
              value={JSON.stringify(record.input_data, null, 2)}
            />
          );
        },
      },

      {
        title: "Expected Output",
        width: "20%",
        scroll: { x: 400 },
        render: (record) => {
          return (
            <TextareaAutosize
              disabled={true}
              minRows={3}
              value={record.expected_output}
            />
          );
        },
      },
      {
        title: "Output Data",
        width: "20%",
        render: (record) => {
          const output_result = testCaseRunOutput[record.uuid];

          return (
            <TextareaAutosize
              disabled={true}
              minRows={3}
              value={
                output_result
                  ? JSON.stringify(output_result?.output, null, 2)
                  : ""
              }
            />
          );
        },
      },
      {
        title: "Status",
        width: "10%",
        render: (record) => {
          const record_status = testCaseStatus[record.uuid];

          if (!record_status) {
            return null;
          }

          if (record_status === "RUNNING") {
            return <Chip label="Running" color="primary" />;
          } else if (record_status === "COMPLETED") {
            return <Chip label="Completed" color="success" />;
          } else {
            return null;
          }
        },
      },
      {
        title: "Action",
        width: "10%",
        key: "operation",
        render: (record) => {
          return (
            <Box>
              <IconButton
                onClick={() => {
                  setDeleteId(record);
                  setDeleteModalTitle("Delete Test Case");
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
                <DeleteOutlineOutlinedIcon />
              </IconButton>
              <IconButton
                onClick={() => {
                  setTestSetStatus({});
                  setTestCaseStatus({});
                  setTestCaseRunOutput({});
                  runTestCase(record);
                }}
              >
                <PlayCircleFilledWhiteOutlinedIcon />
              </IconButton>
            </Box>
          );
        },
      },
    ];

    return (
      <Table
        columns={columns}
        dataSource={testcases}
        rowKey={(record) => record.uuid}
        pagination={false}
      />
    );
  };

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      width: "35%",
    },
    {
      title: "Last Modified",
      width: "25%",
      dataIndex: "last_updated_at",
      ellipsis: true,
      key: "last_updated_at",
      render: (record) => {
        return <LocaleDate value={record} />;
      },
    },
    {
      title: "Status",
      width: "20%",
      render: (record) => {
        const record_status = testSetStatus[record.uuid];
        if (record_status === undefined) {
          return null;
        }

        if (record_status === "RUNNING") {
          return <Chip label="Running" color="primary" />;
        } else if (record_status === "COMPLETED") {
          return <Chip label="Completed" color="success" />;
        } else {
          return null;
        }
      },
    },
    {
      title: "Action",
      width: "20%",
      key: "operation",
      render: (record) => {
        return (
          <Box>
            <IconButton
              onClick={() => {
                setModalTitle("Add Test Entry");
                setSelectTestSet(record);
                setAddTestSetModalOpen(true);
              }}
            >
              <AddOutlinedIcon />
            </IconButton>
            <IconButton
              onClick={() => {
                setDeleteId(record);
                setDeleteModalTitle("Delete Test Set");
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
            <IconButton
              onClick={() => {
                setTestSetStatus({});
                setTestCaseStatus({});
                setTestCaseRunOutput({});
                runTestSet(record);
              }}
            >
              <PlayCircleFilledWhiteOutlinedIcon />
            </IconButton>
          </Box>
        );
      },
    },
  ];

  return (
    <div id="tests-page">
      <Grid span={24} style={{ padding: "10px" }}>
        <Grid item style={{ width: "100%", padding: "15px 0px" }}>
          <Button
            onClick={() => {
              setAddTestSetModalOpen(true);
            }}
            type="primary"
            variant="contained"
            sx={{ float: "left", marginBottom: "10px", textTransform: "none" }}
          >
            Create Test Set
          </Button>
        </Grid>
        <Grid item style={{ width: "100%" }}>
          <Table
            dataSource={Object.values(table_data)}
            columns={columns}
            pagination={false}
            expandable={{
              expandedRowRender,
              expandRowByClick: true,
              defaultExpandAllRows: true,
            }}
            rowKey={(record) => record.uuid}
            style={{ width: "100%" }}
          ></Table>
        </Grid>
      </Grid>
      {addTestSetModalOpen && (
        <AddTestSetModal
          open={addTestSetModalOpen}
          testSet={selectTestSet}
          modalTitle={modalTitle}
          handleCancelCb={() => {
            setSelectTestSet(null);
            setAddTestSetModalOpen(false);
          }}
          onSubmitCb={(testset) => {
            setTableData((prev) => {
              prev[testset.uuid] = testset;
              return prev;
            });
            setSelectTestSet(null);
            setAddTestSetModalOpen(false);
          }}
          app={app}
        />
      )}
      {deleteConfirmationModalOpen && (
        <DeleteConfirmationModal
          id={deleteId}
          title={deleteModalTitle}
          text={deleteModalMessage}
          open={deleteConfirmationModalOpen}
          onOk={(param) => {
            if (param?.testset_uuid === undefined) {
              axios()
                .delete(`/api/apptestsets/${param.uuid}`)
                .then((res) => {
                  setTableData((prev) => {
                    delete prev[param.uuid];
                    return prev;
                  });
                })
                .finally(() => {
                  setDeleteConfirmationModalOpen(false);
                });
            } else {
              axios()
                .delete(`/api/apptestcases/${param.uuid}`)
                .then((res) => {
                  setTableData((prev) => {
                    let testset = prev[param.testset_uuid];
                    testset.testcases = testset.testcases.filter(
                      (entry) => entry.uuid !== param.uuid,
                    );
                    prev[param.testset_uuid] = testset;
                    return prev;
                  });
                })
                .finally(() => {
                  setDeleteConfirmationModalOpen(false);
                });
            }
          }}
          onCancel={() => {
            setDeleteConfirmationModalOpen(false);
          }}
        />
      )}
    </div>
  );
}
