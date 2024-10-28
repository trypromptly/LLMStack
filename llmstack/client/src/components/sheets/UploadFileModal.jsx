import React, { useState, useRef } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Button,
  DialogActions,
} from "@mui/material";
import { LoadingButton } from "@mui/lab";
import { axios } from "../../data/axios";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";

const getFileDataURI = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64Data = reader.result.split(",")[1];
      const dataURI = `data:${file.type};name=${file.name};base64,${base64Data}`;

      resolve({ file_name: file.name, mime_type: file.type, data: dataURI });
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};

function InputFileUpload({ fileRef, maxFiles }) {
  const [files, setFiles] = useState([]);
  const handleFileChange = (event) => {
    setFiles(Array.from(event.target.files).slice(0, maxFiles));
  };

  return (
    <>
      <Button
        component="label"
        role={undefined}
        variant="contained"
        tabIndex={-1}
        startIcon={<CloudUploadIcon />}
      >
        Upload up to {maxFiles} files
        <input
          ref={fileRef}
          style={{
            clip: "rect(0 0 0 0)",
            clipPath: "inset(50%)",
            height: 1,
            overflow: "hidden",
            position: "absolute",
            bottom: 0,
            left: 0,
            whiteSpace: "nowrap",
            width: 1,
          }}
          type="file"
          onChange={handleFileChange}
          multiple
        />
      </Button>
      <div style={{ marginTop: 10 }}>
        {files &&
          Array.from(files)
            .slice(0, maxFiles)
            .map((file, index) => (
              <span
                key={index}
                style={{
                  display: "inline-block",
                  padding: "5px 10px",
                  margin: "5px",
                  backgroundColor: "#e0e0e0",
                  borderRadius: "15px",
                }}
              >
                {file.name}
              </span>
            ))}
      </div>
    </>
  );
}

const UploadFileModal = ({ open, onClose, sheetUuid, selectedGrid }) => {
  const fileRef = useRef(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const maxFilesAllowed = 5;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Upload Files</DialogTitle>
      <DialogContent>
        <InputFileUpload fileRef={fileRef} maxFiles={maxFilesAllowed} />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={isProcessing}>
          Cancel
        </Button>
        <LoadingButton
          variant="contained"
          type="primary"
          onClick={() => {
            const startCell = selectedGrid[0].split("-")[0];
            setIsProcessing(true);
            // Convert the file to a data URI
            const fileConvertPromises = Array.from(fileRef.current.files)
              .slice(0, maxFilesAllowed)
              .map(getFileDataURI);
            Promise.all(fileConvertPromises).then((dataURIs) => {
              axios()
                .post(`/api/sheets/${sheetUuid}/upload_assets`, {
                  files: dataURIs,
                })
                .then((response) => {
                  setIsProcessing(false);
                  onClose({
                    files: response.data,
                    startCell: startCell,
                  });
                })
                .finally(() => {
                  setIsProcessing(false);
                });
            });
          }}
          disabled={isProcessing}
          loading={isProcessing}
        >
          Upload
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

export default UploadFileModal;
