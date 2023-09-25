import { Select } from "antd";

export function AppSelector(props) {
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
        mode="single"
        options={props.apps.map((app) => ({
          label: app.name,
          value: app.published_uuid,
        }))}
        placeholder="Select a promptly app"
        status="warning"
        onChange={(value) => props.onChange(value)}
      />
    </div>
  );
}
