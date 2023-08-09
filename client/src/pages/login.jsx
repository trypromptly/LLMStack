import { Col, Divider, Row, Card, Button, Form, Input } from "antd";
import { postData } from "./dataUtil";

export default function LoginPage() {
  const [form] = Form.useForm();

  const onSignInClick = async () => {
    form
      .validateFields()
      .then((values) => {
        postData(
          "/api/login",
          values,
          () => {},
          (result) => {
            window.location.href = "/";
          },
          () => {},
        );
      })
      .catch((error) => {});
  };

  return (
    <div id="login-page">
      <Row gutter={16}>
        <Col span={6}></Col>
        <Col span={10} align="middle">
          <Card title="Sign In" bordered={true}>
            <Row>
              <Form layout="vertical" style={{ width: "100%" }} form={form}>
                <Form.Item
                  label="Username"
                  name="username"
                  rules={[
                    { required: true, message: "Please input your username!" },
                  ]}
                >
                  <Input />
                </Form.Item>
                <Form.Item
                  label="Password"
                  name="password"
                  rules={[
                    { required: true, message: "Please input your password!" },
                  ]}
                >
                  <Input.Password />
                </Form.Item>
              </Form>
            </Row>
            <Row>
              <Divider />
            </Row>
            <Row>
              <Divider />
            </Row>
            <Row align="middle" style={{ display: "inline-flex" }}>
              <Button size="large" onClick={onSignInClick}>
                Sign In
              </Button>
            </Row>
          </Card>
        </Col>
        <Col span={6}></Col>
      </Row>
    </div>
  );
}
