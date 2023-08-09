import {
  Row,
  Col,
  Button,
  Form,
  Input,
  Spin,
  Tooltip,
  Card,
  Upload,
  Divider,
} from "antd";
import ImgCrop from "antd-img-crop";
import { useEffect, useState } from "react";
import { CopyOutlined } from "@ant-design/icons";
import { fetchData, patchData } from "./dataUtil";
import { organizationState, profileFlagsState } from "../data/atoms";
import { useRecoilValue } from "recoil";

const onLogoPreview = async (file) => {
  let src = file.url;
  if (!src) {
    src = await new Promise((resolve) => {
      const reader = new FileReader();
      reader.readAsDataURL(file.originFileObj);
      reader.onload = () => resolve(reader.result);
    });
  }
  const image = new Image();
  image.src = src;
  const imgWindow = window.open(src);
  imgWindow?.document.write(image.outerHTML);
};

const SettingPage = () => {
  const [formData, setFormData] = useState({
    token: "",
    openai_key: "",
    stabilityai_key: "",
    cohere_key: "",
    forefrontai_key: "",
    elevenlabs_key: "",
    logo: "",
  });
  const [loading, setLoading] = useState(true);
  const [updateKeys, setUpdateKeys] = useState(new Set());
  const profileFlags = useRecoilValue(profileFlagsState);
  const organization = useRecoilValue(organizationState);

  useEffect(() => {
    fetchData(
      "api/profiles/me",
      () => {},
      (profile) => {
        setFormData({
          token: profile.token,
          openai_key: profile.openai_key,
          stabilityai_key: profile.stabilityai_key,
          cohere_key: profile.cohere_key,
          forefrontai_key: profile.forefrontai_key,
          elevenlabs_key: profile.elevenlabs_key,
          google_service_account_json_key:
            profile.google_service_account_json_key,
          azure_openai_api_key: profile.azure_openai_api_key,
          logo: profile.logo,
          user_email: profile.user_email,
        });
        setLoading(false);
      },
    );
  }, []);

  const handleUpdate = (form_field) => {
    setLoading(true);
    let data = {};
    data[form_field] = formData[form_field];

    patchData(
      "api/profiles/me",
      data,
      (loading_result) => {
        setLoading(loading_result);
      },
      (profile) => {
        setFormData({
          token: profile.token,
          openai_key: profile.openai_key,
          stabilityai_key: profile.stabilityai_key,
          cohere_key: profile.cohere_key,
          forefrontai_key: profile.forefrontai_key,
          elevenlabs_key: profile.elevenlabs_key,
          google_service_account_json_key:
            profile.google_service_account_json_key,
          azure_openai_api_key: profile.azure_openai_api_key,
          logo: profile.logo,
        });
        setLoading(false);
      },
      () => {},
    );
  };

  return (
    <div id="setting-page">
      <Spin spinning={loading} size={"large"}>
        <Form layout="vertical">
          <Card title="Settings" style={{ textAlign: "left", padding: 4 }}>
            <Row>
              <Col span={16}>
                <Form.Item label="Promptly Token">
                  <Input.Group compact>
                    <Input
                      readOnly={true}
                      style={{
                        width: "350px",
                      }}
                      value={formData.token}
                      defaultValue={formData.token}
                    />
                    <Tooltip title="Copy Promptly API Token">
                      <Button
                        icon={<CopyOutlined />}
                        onClick={() =>
                          navigator.clipboard.writeText(formData.token)
                        }
                      />
                    </Tooltip>
                  </Input.Group>
                </Form.Item>
              </Col>
            </Row>
            <Row>
              <Col xs={24} md={14}>
                <Form.Item label="OpenAI API Token">
                  <Row>
                    <Col xs={24} md={16}>
                      {" "}
                      <Input.Password
                        value={formData.openai_key}
                        disabled={!profileFlags.CAN_ADD_KEYS}
                        onChange={(e) => {
                          setFormData({
                            ...formData,
                            openai_key: e.target.value,
                          });
                          setUpdateKeys(updateKeys.add("openai_key"));
                        }}
                      />
                    </Col>
                  </Row>
                </Form.Item>
              </Col>
            </Row>
            <Row>
              <Col xs={24} md={14}>
                <Form.Item label="StabilityAI API Token">
                  <Row>
                    <Col xs={24} md={16}>
                      {" "}
                      <Input.Password
                        value={formData.stabilityai_key}
                        disabled={!profileFlags.CAN_ADD_KEYS}
                        onChange={(e) => {
                          setFormData({
                            ...formData,
                            stabilityai_key: e.target.value,
                          });
                          setUpdateKeys(updateKeys.add("stabilityai_key"));
                        }}
                      />
                    </Col>
                  </Row>
                </Form.Item>
              </Col>
            </Row>
            <Row>
              <Col xs={24} md={14}>
                <Form.Item label="Cohere API Token">
                  <Row>
                    <Col xs={24} md={16}>
                      {" "}
                      <Input.Password
                        value={formData.cohere_key}
                        disabled={!profileFlags.CAN_ADD_KEYS}
                        onChange={(e) => {
                          setFormData({
                            ...formData,
                            cohere_key: e.target.value,
                          });
                          setUpdateKeys(updateKeys.add("cohere_key"));
                        }}
                      />
                    </Col>
                  </Row>
                </Form.Item>
              </Col>
            </Row>
            <Row>
              <Col xs={24} md={14}>
                <Form.Item label="Elevenlabs API Token">
                  <Row>
                    <Col xs={24} md={16}>
                      {" "}
                      <Input.Password
                        value={formData.elevenlabs_key}
                        disabled={!profileFlags.CAN_ADD_KEYS}
                        onChange={(e) => {
                          setFormData({
                            ...formData,
                            elevenlabs_key: e.target.value,
                          });
                          setUpdateKeys(updateKeys.add("elevenlabs_key"));
                        }}
                      />
                    </Col>
                  </Row>
                </Form.Item>
              </Col>
            </Row>
            <Row>
              <Col xs={24} md={14}>
                <Form.Item label="Azure OpenAI API Key">
                  <Row>
                    <Col xs={24} md={16}>
                      {" "}
                      <Input.Password
                        value={formData.azure_openai_api_key}
                        disabled={!profileFlags.CAN_ADD_KEYS}
                        onChange={(e) => {
                          setFormData({
                            ...formData,
                            azure_openai_api_key: e.target.value,
                          });
                          setUpdateKeys(updateKeys.add("azure_openai_api_key"));
                        }}
                      />
                    </Col>
                  </Row>
                </Form.Item>
              </Col>
            </Row>
            <Row>
              <Col xs={24} md={14}>
                <Form.Item
                  label="Google Service Account JSON Key"
                  tooltip="base64 encoded JSON key."
                >
                  <Row>
                    <Col xs={24} md={16}>
                      {" "}
                      <Input.Password
                        value={formData.google_service_account_json_key}
                        disabled={!profileFlags.CAN_ADD_KEYS}
                        onChange={(e) => {
                          setFormData({
                            ...formData,
                            google_service_account_json_key: e.target.value,
                          });
                          setUpdateKeys(
                            updateKeys.add("google_service_account_json_key"),
                          );
                        }}
                      />
                    </Col>
                  </Row>
                </Form.Item>
              </Col>
            </Row>
            {process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT ===
              "true" && (
              <>
                <Row>
                  <Col span={16}>
                    <Form.Item
                      name="logo"
                      label="Custom Logo"
                      valuePropName="filelist"
                      help="[Pro Feature] Add a custom logo to your Promptly apps. 150px x 30px recommended."
                    >
                      <Row>
                        <Col span={24}>
                          {" "}
                          <ImgCrop rotationSlider aspect={5.06}>
                            <Upload
                              disabled={!profileFlags.CAN_UPLOAD_APP_LOGO}
                              accept="image/*"
                              action={(file) => {
                                return new Promise((resolve) => {
                                  const reader = new FileReader();
                                  reader.readAsDataURL(file);
                                  reader.onload = (e) => {
                                    setFormData({
                                      ...formData,
                                      logo: e.target?.result,
                                    });
                                    resolve(e.target?.result);
                                  };
                                });
                              }}
                              listType="picture-card"
                              fileList={
                                formData.logo
                                  ? [
                                      {
                                        uid: "-1",
                                        name: "logo.png",
                                        status: "done",
                                        url: formData.logo,
                                      },
                                    ]
                                  : []
                              }
                              onChange={({ fileList }) => {
                                if (fileList.length === 0) {
                                  setFormData({
                                    ...formData,
                                    logo: "",
                                  });
                                }
                                setUpdateKeys(updateKeys.add("logo"));
                              }}
                              onPreview={onLogoPreview}
                            >
                              {formData.logo ? "" : "+ Upload"}
                            </Upload>
                          </ImgCrop>
                        </Col>
                      </Row>
                    </Form.Item>
                  </Col>
                </Row>
                <Divider />
              </>
            )}
            {process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT ===
              "true" && (
              <>
                <Row style={{ flexDirection: "column" }}>
                  <strong>Subscription</strong>
                  <p
                    style={{
                      display: profileFlags.IS_ORGANIZATION_MEMBER
                        ? "none"
                        : "block",
                    }}
                  >
                    Logged in as&nbsp;<strong>{formData.user_email}</strong>.
                    You are currently subscribed to&nbsp;
                    <strong>
                      {profileFlags.IS_PRO_SUBSCRIBER
                        ? "Pro"
                        : profileFlags.IS_BASIC_SUBSCRIBER
                        ? "Basic"
                        : "Free"}
                    </strong>
                    &nbsp;tier. Click on the Manage Subscription button below to
                    change your plan.&nbsp;
                    <br />
                    <i>
                      Note: You will be needed to login with a link that is sent
                      to your email.
                    </i>
                  </p>
                  <p
                    style={{
                      display: profileFlags.IS_ORGANIZATION_MEMBER
                        ? "block"
                        : "none",
                    }}
                  >
                    Logged in as <strong>{formData.user_email}</strong>. Your
                    account is managed by your organization,&nbsp;
                    <strong>{organization?.name}</strong>. Please contact your
                    admin to manage your subscription.
                  </p>
                </Row>
                <Divider />
              </>
            )}
            <Row style={{ gap: 5 }}>
              {process.env.REACT_APP_ENABLE_SUBSCRIPTION_MANAGEMENT ===
                "true" && (
                <Button
                  href={`${
                    process.env.REACT_APP_SUBSCRIPTION_MANAGEMENT_URL
                  }?prefilled_email=${encodeURIComponent(formData.user_email)}`}
                  target="_blank"
                  style={{
                    display: profileFlags.IS_ORGANIZATION_MEMBER
                      ? "none"
                      : "inherit",
                  }}
                >
                  Manage Subscription
                </Button>
              )}
              <Button
                type="primary"
                onClick={() => {
                  updateKeys.forEach((updateKey) => handleUpdate(updateKey));
                }}
              >
                Update
              </Button>
            </Row>
          </Card>
        </Form>
      </Spin>
    </div>
  );
};

export default SettingPage;
