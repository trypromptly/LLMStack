import { useEffect, useState } from "react";
import { axios } from "../../../data/axios";

const Image = (props) => {
  const { url, alt } = props;
  return <img src={url} alt={alt || "Asset"} />;
};

export const AssetRenderer = (props) => {
  const { url, type } = props;
  const [file, setFile] = useState(null);

  useEffect(() => {
    const urlParts = url.split("objref://")[1].split("/");
    const [category, assetId] = [urlParts[0], urlParts[1]];
    axios()
      .get(`/api/assets/${category}/${assetId}`)
      .then((response) => {
        setFile(response.data);
      })
      .catch((error) => {
        console.error(error);
      });
  }, [url]);

  if (type.startsWith("image") && file) {
    return <Image url={file?.url} alt={file?.name} />;
  }

  return <p>AssetRenderer</p>;
};
