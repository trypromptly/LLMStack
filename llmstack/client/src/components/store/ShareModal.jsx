import { useState } from "react";
import { useNavigate } from "react-router-dom";
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
import {
  appRunDataState,
  isLoggedInState,
  profileSelector,
} from "../../data/atoms";

export default function ShareModal({
  open,
  onClose,
  appTypeSlug,
  appStoreUuid,
}) {
  const appRunData = useRecoilValue(appRunDataState);
  const isLoggedIn = useRecoilValue(isLoggedInState);
  const profile = useRecoilValue(profileSelector);
  const [shareCode, setShareCode] = useState("");
  const navigate = useNavigate();
  const [pinned, setPinned] = useState(false);
  const [pinToProfileLoading, setPinToProfileLoading] = useState(false);
  const [shareUrlLoading, setShareUrlLoading] = useState(false);

  const getShareUrl = (code) => {
    return `${window.location.protocol}//${window.location.host}/s/${code}`;
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

  const handlePinToProfile = (event, sessionId, isLoggedIn) => {
    event.stopPropagation();

    if (!isLoggedIn || !sessionId || !profile || !profile.username) {
      enqueueSnackbar(
        "You must be logged in and have your username set to pin an app run",
        {
          variant: "error",
        },
      );

      return;
    }

    setPinToProfileLoading(true);

    axios()
      .post(`/api/profiles/${profile.username}/posts`, {
        share_code: shareCode,
      })
      .then((response) => {
        setPinned(response?.data?.metadata?.slug);
        enqueueSnackbar("App run pinned to profile", { variant: "success" });
      })
      .catch((error) => {
        console.error("Error pinning app run", error);
        enqueueSnackbar("Error pinning app run", { variant: "error" });
      })
      .finally(() => {
        setPinToProfileLoading(false);
      });
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
            ? "Share the output from this app run by clicking on the create link button to generate a shareable url."
            : !shareCode &&
              "Share this app by clicking on the copy link button."}
        </Typography>
        {shareCode && (
          <Box sx={{ marginTop: 2, marginBottom: 4 }}>
            <Typography variant="body1">
              Share this link with others to view the output from this app run:{" "}
              <a href={getShareUrl(shareCode)} target="_blank" rel="noreferrer">
                {getShareUrl(shareCode)}
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
          {shareCode ? "Copy Link" : "Create Link"}
        </LoadingButton>
        {shareCode && profile?.username && (
          <LoadingButton
            key="pin"
            variant="contained"
            type="primary"
            onClick={(e) => {
              if (pinned) {
                navigate(`/u/${profile.username}/${pinned}`);
              } else {
                handlePinToProfile(e, appRunData?.sessionId, isLoggedIn);
              }
            }}
            loading={pinToProfileLoading}
            disabled={appRunData?.isRunning || pinToProfileLoading}
          >
            {pinned ? "View on Profile" : "Pin to Profile"}
          </LoadingButton>
        )}
      </DialogActions>
    </Dialog>
  );
}
