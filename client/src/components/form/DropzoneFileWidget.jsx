import React, { useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import { dataURItoBlob } from "@rjsf/utils";
import { Chip } from "@mui/material";
import prettyBytes from "pretty-bytes";

const baseStyle = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  padding: "20px",
  borderWidth: 2,
  borderRadius: 2,
  borderColor: "#eeeeee",
  borderStyle: "dashed",
  backgroundColor: "#fafafa",
  color: "#bdbdbd",
  outline: "none",
  transition: "border .24s ease-in-out",
};

const focusedStyle = {
  borderColor: "#2196f3",
};

const acceptStyle = {
  borderColor: "#00e676",
};

const rejectStyle = {
  borderColor: "#ff1744",
};

const thumbsContainer = {
  marginTop: 4,
};

function addNameToDataURL(dataURL, name) {
  if (dataURL === null) {
    return null;
  }
  return dataURL.replace(";base64", `;name=${encodeURIComponent(name)};base64`);
}

function processFile(file) {
  const { name, size, type } = file;
  return new Promise((resolve, reject) => {
    const reader = new window.FileReader();
    reader.onerror = reject;
    reader.onload = (event) => {
      if (typeof event.target?.result === "string") {
        resolve({
          dataURL: addNameToDataURL(event.target.result, name),
          name,
          size,
          type,
        });
      } else {
        resolve({
          dataURL: null,
          name,
          size,
          type,
        });
      }
    };
    reader.readAsDataURL(file);
  });
}

function processFiles(files) {
  return Promise.all(Array.from(files).map(processFile));
}

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

export default function DropzoneFileWidget(props) {
  const { multiple, onChange, value } = props;

  const extractedFilesInfo = useMemo(
    () =>
      Array.isArray(value) ? extractFileInfo(value) : extractFileInfo([value]),
    [value],
  );

  const [filesInfo, setFilesInfo] = useState(extractedFilesInfo);

  const thumbs = filesInfo.map((fileInfo, index) => {
    return (
      <Chip
        label={fileInfo.name}
        onDelete={() => removeFile(index)}
        key={index}
      />
    );
  });

  const onDrop = (acceptedFiles) => {
    processFiles(acceptedFiles).then((filesInfoEvent) => {
      setFilesInfo(filesInfoEvent);
      const newValue = filesInfoEvent.map((fileInfo) => fileInfo.dataURL);
      if (props?.schema?.multiple || props?.schema?.maxFiles > 1) {
        onChange(newValue);
      } else {
        onChange(newValue[0]);
      }
    });
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

  const { getRootProps, getInputProps, isFocused, isDragAccept, isDragReject } =
    useDropzone({
      accept: props.schema?.accepts || {},
      onDrop,
      multiple: props.schema.multiple || props.schema.maxFiles > 1 || false,
      maxSize: props.schema.maxSize || 20000000,
      maxFiles: props.schema.maxFiles || 1,
    });

  const style = useMemo(
    () => ({
      ...baseStyle,
      ...(isFocused ? focusedStyle : {}),
      ...(isDragAccept ? acceptStyle : {}),
      ...(isDragReject ? rejectStyle : {}),
    }),
    [isFocused, isDragAccept, isDragReject],
  );

  return (
    <div className="container">
      <label style={{ display: "flex" }}>{props.label}</label>
      <p></p>
      <div {...getRootProps({ style })}>
        <input {...getInputProps()} multiple={false} />
        <p>
          Drag 'n' drop some files here, or click to select files. Maximum size
          of each file is {prettyBytes(props?.schema?.maxSize || 20000000)}
        </p>
      </div>
      {thumbs && <aside style={thumbsContainer}>{thumbs}</aside>}
    </div>
  );
}
