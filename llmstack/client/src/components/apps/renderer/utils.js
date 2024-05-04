import { Ws } from "../../../data/ws";

export const getObjStreamWs = (objref) => {
  // Connect to a websocket to stream the media

  try {
    const urlParts = objref.replace("objref://", "").split("/");
    const [category, assetId] = [urlParts[0], urlParts[1]];

    const wsUrlPrefix = `${
      window.location.protocol === "https:" ? "wss" : "ws"
    }://${
      process.env.NODE_ENV === "development"
        ? process.env.REACT_APP_API_SERVER || "localhost:9000"
        : window.location.host
    }/ws/assets/${category}/${assetId}`;

    return new Ws(wsUrlPrefix, "blob");
  } catch (error) {
    console.error(error);
  }

  return null;
};
