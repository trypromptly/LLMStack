import { useEffect, useState, useMemo } from "react";
import { Chip, Button, Stack } from "@mui/material";
import { dataURItoBlob } from "@rjsf/utils";
import { LoadingButton } from "@mui/lab";

const SCOPES = [
  "https://www.googleapis.com/auth/drive.readonly",
  "https://www.googleapis.com/auth/drive.readonly.metadata",
];
const CLIENT_ID = "";
const API_KEY = "";
const APP_ID = "";

const thumbsContainer = {
  marginTop: 4,
};

function extractFileInfo(dataURLs) {
  return dataURLs
    .filter((dataURL) => dataURL)
    .map((dataURL) => {
      const { blob, name } = dataURItoBlob(dataURL);
      return {
        dataURL,
        name: name,
        size: blob.size,
        type: blob.type,
      };
    });
}

function processDocument(document) {
  return new Promise((resolve, reject) => {
    if (window.gapi && window.gapi.client.drive) {
      const supportedExportDocsMimeTypes = {
        "application/vnd.google-apps.document":
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.google-apps.spreadsheet":
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.google-apps.presentation":
          "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      };

      const isGoogleDocument = supportedExportDocsMimeTypes.hasOwnProperty(
        document.mimeType,
      );
      const exportMimeType = isGoogleDocument
        ? supportedExportDocsMimeTypes[document.mimeType]
        : null;

      const request = isGoogleDocument
        ? window.gapi.client.drive.files.export({
            fileId: document.id,
            mimeType: exportMimeType,
          })
        : window.gapi.client.drive.files.get({
            fileId: document.id,
            alt: "media",
          });

      request
        .then((response) => {
          const mimeType = isGoogleDocument
            ? exportMimeType
            : document.mimeType;

          resolve({
            dataURL:
              `data:${mimeType};name=${encodeURIComponent(
                document.name,
              )};base64,` + window.btoa(response.body),

            name: document.name,
            size: response.body.length,
            type: document.mimeType,
          });
        })
        .catch((error) => {
          console.error("Error loading the file:", error);
          reject(error);
        });
    } else {
      reject(new Error("Google Drive API is not ready"));
    }
  });
}

function processDocuments(documents) {
  return Promise.all(Array.from(documents).map(processDocument));
}

export default function GdriveFilePicker(props) {
  const { multiple, onChange, value } = props;

  const [oauthToken, setOauthToken] = useState(null);
  const [authClient, setAuthClient] = useState(null);
  const [processing, setProcessing] = useState(false);
  const extractedFilesInfo = useMemo(
    () =>
      Array.isArray(value) ? extractFileInfo(value) : extractFileInfo([value]),
    [value],
  );

  const [filesInfo, setFilesInfo] = useState(extractedFilesInfo);

  useEffect(() => {
    if (window.gapi) {
      window.gapi.load("picker");
      window.gapi.load("client", () => {
        window.gapi.client.setApiKey(API_KEY);
        window.gapi.client.load("drive", "v3");
      });
    }
    if (window.google && !authClient) {
      const client = window.google.accounts.oauth2.initTokenClient({
        client_id: CLIENT_ID,
        scope: SCOPES.join(" "),
        callback: (tokenResponse) => {
          setOauthToken(tokenResponse.access_token);
        },
      });
      setAuthClient(client);
    }
  }, [authClient]);

  const pickerCallback = (data) => {
    if (data.action === window.google.picker.Action.PICKED) {
      setProcessing(true);
      processDocuments(data[window.google.picker.Response.DOCUMENTS]).then(
        (filesInfoEvent) => {
          setFilesInfo(filesInfoEvent);
          setProcessing(false);

          const newValue = filesInfoEvent.map((fileInfo) => fileInfo.dataURL);
          if (props?.schema?.multiple || props?.schema?.maxFiles > 1) {
            onChange(newValue);
          } else {
            onChange(newValue[0]);
          }
        },
      );
    }
  };

  const removeFile = (index) => {
    const newFilesInfo = [...filesInfo];
    newFilesInfo.splice(index, 1);
    setFilesInfo(newFilesInfo);
    const newValue = newFilesInfo.map((fileInfo) => fileInfo.dataURL);
    if (multiple) {
      onChange(newValue);
    } else {
      onChange(newValue[0]);
    }
  };

  const handleOpenPicker = () => {
    if (oauthToken) {
      const view = new window.google.picker.View(
        window.google.picker.ViewId.DOCS,
      );
      if (props.schema?.accepts) {
        view.setMimeTypes(Object.keys(props.schema.accepts).join(","));
      }

      const picker = new window.google.picker.PickerBuilder()
        .enableFeature(window.google.picker.Feature.NAV_HIDDEN)
        .setDeveloperKey(API_KEY)
        .setAppId(APP_ID)
        .setOAuthToken(oauthToken)
        .addView(view)
        .setCallback(pickerCallback)
        .build();
      picker.setVisible(true);
    }
  };

  const handleAuthClick = () => {
    if (!authClient) {
      const client = window.google.accounts.oauth2.initTokenClient({
        client_id: CLIENT_ID,
        scope: SCOPES,
        callback: (tokenResponse) => {
          setOauthToken(tokenResponse.access_token);
        },
      });
      setAuthClient(client);
    }
    if (authClient) {
      if (oauthToken === null) {
        authClient.requestAccessToken({ prompt: "" });
      } else {
        authClient.requestAccessToken({ prompt: "" });
      }
    }
  };

  const handleSignoutClick = () => {
    if (oauthToken) {
      window.google.accounts.oauth2.revoke(oauthToken, () => {
        setOauthToken(null);
      });
    }
  };

  const thumbs = filesInfo.map((fileInfo, index) => {
    return (
      <Chip
        label={fileInfo.name}
        onDelete={() => removeFile(index)}
        key={index}
      />
    );
  });

  return (
    <div className="container">
      <label style={{ display: "flex" }}>{props.label}</label>
      <p></p>
      <Stack
        spacing={2}
        sx={{ alignItems: "center", justifyContent: "center" }}
      >
        {oauthToken && (
          <LoadingButton
            variant="outlined"
            onClick={() => handleOpenPicker()}
            disabled={processing}
            loading={processing}
          >
            Choose File
          </LoadingButton>
        )}
        {oauthToken && (
          <LoadingButton
            variant="outlined"
            onClick={() => handleSignoutClick()}
            size="small"
            disabled={processing}
            loading={processing}
          >
            SignOut
          </LoadingButton>
        )}
        {!oauthToken && (
          <Button variant="outlined" onClick={() => handleAuthClick()}>
            Login to Google
          </Button>
        )}

        {thumbs && <aside style={thumbsContainer}>{thumbs}</aside>}
      </Stack>
    </div>
  );
}
