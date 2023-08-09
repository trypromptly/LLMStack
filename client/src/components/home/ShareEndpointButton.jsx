import { Button } from "antd";
import { ShareAltOutlined } from "@ant-design/icons";
import { useRecoilState, useRecoilValue } from "recoil";
import {
  endpointShareCodeValueState,
  shareEndpointModalVisibleState,
  apiBackendSelectedState,
  inputValueState,
  templateValueState,
  endpointConfigValueState,
} from "../../data/atoms";
import { axios } from "../../data/axios";

export default function ShareEndpointButton({
  isShareButtonEnabled,
  responseId,
  componentRef,
  output,
}) {
  const [shareCode, setShareCode] = useRecoilState(endpointShareCodeValueState);
  const [, setShareModalVisibility] = useRecoilState(
    shareEndpointModalVisibleState,
  );
  const apiBackendSelected = useRecoilValue(apiBackendSelectedState);
  const input = useRecoilValue(inputValueState);
  const prompt_values = useRecoilValue(templateValueState);
  const param_values = useRecoilValue(endpointConfigValueState);

  const sharePage = () => {
    const prompt = JSON.stringify(input);
    if (shareCode == null) {
      axios()
        .post(`/api/share`, {
          api_backend: apiBackendSelected.id,
          prompt,
          prompt_values,
          param_values,
          response_id: responseId,
          input,
          output,
          config_values: param_values,
          template_values: prompt_values,
        })
        .then((response) => {
          setShareCode(response.data.code);
          setShareModalVisibility(true);
        })
        .catch((error) => {
          setShareCode(null);
          setShareModalVisibility(false);
        })
        .then(() => {});
    } else {
      setShareModalVisibility(true);
    }
  };

  return (
    <Button
      ref={componentRef}
      style={{
        backgroundColor: "#3c84b0",
        borderColor: "#2d5e7c",
        color: "#fff",
      }}
      disabled={!isShareButtonEnabled}
      onClick={sharePage}
    >
      <ShareAltOutlined style={{ color: "#fff" }} />
      <span style={{ marginLeft: "4px" }}>Share</span>
    </Button>
  );
}
