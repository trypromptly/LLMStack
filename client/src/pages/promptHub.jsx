import { useEffect, useState } from "react";
import { useRecoilState } from "recoil";
import { promptHubState } from "../data/atoms";
import { Col, Card, Badge, Typography, Button, Space } from "antd";
import { Result } from "../components/Output";
import { axios } from "../data/axios";

export default function PromptHub() {
  const [sharedPrompts, setSharedPrompts] = useRecoilState(promptHubState);
  const [dataSource, setDataSource] = useState([]);
  const [tags, setTags] = useState([]);
  const [tagClicked, setTagClicked] = useState("all");

  useEffect(() => {
    axios()
      .get("/api/hub")
      .then((response) => {
        // handle success
        setSharedPrompts(response.data);
      })
      .catch((error) => {
        // handle error
      })
      .then({
        // always executed
      });
  }, [setSharedPrompts]);

  useEffect(() => {
    setDataSource(sharedPrompts);
    const tags = ["all"];
    sharedPrompts.forEach((prompt) => {
      prompt.share.tags.forEach((tag) => {
        if (!tags.includes(tag.name)) {
          tags.push(tag.name);
        }
      });
    });
    setTags(tags);
  }, [sharedPrompts]);

  const onFilterClick = (event) => {
    const filterName = event.target.innerText;
    if (filterName === "all") {
      setDataSource(sharedPrompts);
    } else {
      const filteredPrompts = sharedPrompts.filter((prompt) => {
        return prompt.share.tags[0].name === filterName;
      });
      setDataSource(filteredPrompts);
    }
    setTagClicked(filterName);
  };

  return (
    <div id="prompt-hub" style={{ marginTop: "5px" }}>
      {tags.length > 1 && (
        <div
          style={{
            backgroundColor: "transparent",
            width: "100%",
            position: "sticky",
            top: "0",
            zIndex: "10",
          }}
        >
          <div style={{ display: "flex", width: "100%", height: "100%" }}>
            <Space style={{ flexWrap: "wrap" }}>
              {tags.map((tag, i) => {
                return (
                  <Col key={i}>
                    <Button
                      shape="round"
                      onClick={onFilterClick}
                      style={{
                        backgroundColor:
                          tag === tagClicked ? "#1677ff" : "white",
                        color: tag === tagClicked ? "white" : "black",
                      }}
                    >
                      {tag}
                    </Button>
                  </Col>
                );
              })}
            </Space>
          </div>
        </div>
      )}
      <div
        style={{
          display: "flex",
          width: "100%",
          height: "100%",
          marginTop: "5px",
        }}
      >
        <Space
          className="prompt-hub-container"
          direction="horizontal"
          style={{
            display: "flex",
            flexWrap: "wrap",
            overflow: "auto",
            height: "90vh",
            width: "100%",
            alignItems: "baseline",
          }}
        >
          {dataSource.map((prompt, j) => {
            return (
              <div
                onClick={() => {
                  window.location.href = `/s/${prompt.share.code}`;
                }}
                key={j}
              >
                <Badge.Ribbon
                  text={
                    <Typography.Text style={{ color: "white" }}>
                      {prompt.share?.tags[0]?.name}
                    </Typography.Text>
                  }
                  color="rgb(71, 124, 36)"
                >
                  <Card
                    className="prompt-hub-card"
                    style={{ width: "256px", textAlign: "left" }}
                    title={
                      <Typography.Text ellipsis={true}>
                        {prompt.share.name}
                      </Typography.Text>
                    }
                    hoverable
                    cover={
                      <div
                        style={{
                          minHeight: "200px",
                          maxHeight: "200px",
                          overflow: "auto",
                        }}
                      >
                        <Result
                          formData={prompt.share.output[0]}
                          result={prompt.share.output}
                          preview={false}
                          schema={prompt.share.api_backend.output_schema}
                          uiSchema={prompt.share.api_backend.output_ui_schema}
                        />
                      </div>
                    }
                    key={prompt.code}
                    size="small"
                  ></Card>
                </Badge.Ribbon>
              </div>
            );
          })}
        </Space>
      </div>
    </div>
  );
}
