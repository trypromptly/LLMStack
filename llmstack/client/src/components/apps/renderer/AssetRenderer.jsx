import { useEffect, useState } from "react";
import { axios } from "../../../data/axios";
import loadingImage from "../../../assets/images/loading.gif";

const Image = (props) => {
  const { url, alt } = props;
  return <img src={url} alt={alt || "Asset"} width={"100%"} />;
};

export const AssetRenderer = (props) => {
  const { url, type } = props;
  const [file, setFile] = useState(null);

  useEffect(() => {
    try {
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
    } catch (error) {
      console.error(error);
    }
  }, [url]);

  if (type.startsWith("image")) {
    return (
      <Image url={file?.url || loadingImage} alt={file?.name || "Loading"} />
    );
  }

  return <p>AssetRenderer</p>;
};
