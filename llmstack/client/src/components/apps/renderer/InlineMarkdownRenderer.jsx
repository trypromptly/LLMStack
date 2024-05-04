import { useEffect, useState } from "react";
import { axios } from "../../../data/axios";
import LayoutRenderer from "./LayoutRenderer";
import { getObjStreamWs } from "./utils";

const InlineMarkdownRenderer = (props) => {
  const { src, streaming } = props;
  const [data, setData] = useState(null);

  useEffect(() => {
    if (src && src.startsWith("objref://") && streaming) {
      try {
        const srcStream = getObjStreamWs(src);

        if (!srcStream) {
          return;
        }

        srcStream.setOnMessage(async (message) => {
          const blob = message.data;
          const arrayBuffer = await blob.arrayBuffer();
          const text = new TextDecoder().decode(arrayBuffer);

          setData((prevData) => {
            return prevData ? prevData + text : text;
          });
        });

        srcStream.send(new Blob(["read"], { type: "text/plain" }));
      } catch (error) {
        console.error(error);
      }
    } else if (src) {
      axios()
        .get(src)
        .then((response) => {
          setData(response.data);
        })
        .catch((error) => {
          console.error(error);
        });
    }
  }, [src, streaming]);

  if (!data) {
    return <p>Loading...</p>;
  }

  return <LayoutRenderer>{data || ""}</LayoutRenderer>;
};

export default InlineMarkdownRenderer;
