import { useState } from "react";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";
import LoadingButton from "@mui/lab/LoadingButton";
import { enqueueSnackbar } from "notistack";
import { useRecoilValue } from "recoil";
import {
  PromptlyAppChatOutput,
  PromptlyAppWorkflowOutput,
} from "../apps/renderer/LayoutRenderer";
import { axios } from "../../data/axios";
import { appRunDataState, isLoggedInState } from "../../data/atoms";

export default function ShareModal({
  open,
  onClose,
  appTypeSlug,
  appStoreUuid,
}) {
  const appRunData = useRecoilValue(appRunDataState);
  const isLoggedIn = useRecoilValue(isLoggedInState);
  const [shareCode, setShareCode] = useState("");
  const [shareUrlLoading, setShareUrlLoading] = useState(false);

  const getShareUrl = (code) => {
    return `${window.location.protocol}://${window.location.host}/s/${code}`;
  };

  const handleShare = (event, sessionId, isLoggedIn) => {
    event.stopPropagation();

    if (!isLoggedIn || !sessionId) {
      const url =
        window.location.path === "/"
          ? window.location.href + "a/super-agent"
          : window.location.href;
      navigator.clipboard.writeText(url);
      enqueueSnackbar("Link copied to clipboard", { variant: "success" });
    } else {
      if (shareCode) {
        navigator.clipboard.writeText(getShareUrl(shareCode));
        enqueueSnackbar("Link copied to clipboard", { variant: "success" });
        return;
      }

      setShareUrlLoading(true);

      const messages = appRunData?.messages || [];
      const requestIds = [
        ...new Set(
          messages.map((message) => message.requestId).filter((x) => x),
        ),
      ];

      const body = {
        session_id: sessionId,
        app_store_uuid: appStoreUuid,
        run_entry_request_uuids: requestIds,
      };

      axios()
        .post(`/api/apps/share/`, body)
        .then((response) => {
          navigator.clipboard.writeText(getShareUrl(response.data.code));
          setShareCode(response.data.code);
          enqueueSnackbar("Link copied to clipboard", { variant: "success" });
        })
        .catch((error) => {
          console.error("Error sharing app run", error);
          enqueueSnackbar("Error sharing app run", { variant: "error" });
        })
        .finally(() => {
          setShareUrlLoading(false);
        });
    }
  };

  const handleClose = (e) => {
    e.stopPropagation();
    onClose();
  };

  return (
    <Dialog
      title={"Share"}
      open={open}
      onClose={handleClose}
      fullWidth
      onClick={(e) => e.stopPropagation()}
    >
      <DialogTitle id="app-share-modal">Share</DialogTitle>
      <DialogContent>
        <Typography variant="body1">
          {appRunData?.sessionId && !shareCode
            ? "Share the output from this app run by clicking on the copy link button."
            : !shareCode &&
              "Share this app by clicking on the copy link button."}
        </Typography>
        {shareCode && (
          <Box sx={{ marginTop: 2, marginBottom: 4 }}>
            <Typography variant="body1">
              Link copied to the clipboard. Share this link with others to view
              the output from this app run:{" "}
              <a
                href={`https://trypromptly.com/s/${shareCode}`}
                target="_blank"
                rel="noreferrer"
              >
                https://trypromptly.com/s/{shareCode}
              </a>
            </Typography>
          </Box>
        )}
        {appRunData?.sessionId && (
          <Box
            sx={{
              maxHeight: "300px",
              overflow: "auto",
              border: "solid 1px",
              borderColor: "gray.main",
              marginTop: 2,
              borderRadius: 2,
              padding: 2,
            }}
          >
            {appTypeSlug === "web" ? (
              <PromptlyAppWorkflowOutput showHeader={false} />
            ) : (
              <PromptlyAppChatOutput />
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button key="cancel" onClick={handleClose}>
          Cancel
        </Button>

        <LoadingButton
          key="submit"
          variant="contained"
          type="primary"
          onClick={(e) => handleShare(e, appRunData?.sessionId, isLoggedIn)}
          loading={shareUrlLoading}
          disabled={appRunData?.isRunning}
        >
          Copy Link
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
}
