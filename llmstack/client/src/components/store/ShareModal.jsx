import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FacebookIcon,
  FacebookShareButton,
  FacebookMessengerIcon,
  FacebookMessengerShareButton,
  LinkedinIcon,
  LinkedinShareButton,
  PinterestIcon,
  PinterestShareButton,
  TelegramIcon,
  TelegramShareButton,
  TwitterShareButton,
  WhatsappIcon,
  WhatsappShareButton,
  XIcon,
} from "react-share";
import {
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  FormGroup,
  IconButton,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import ContentCopy from "@mui/icons-material/ContentCopy";
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
  const [pinned, setPinned] = useState(null);
  const [pinToProfileLoading, setPinToProfileLoading] = useState(false);
  const [shareUrlLoading, setShareUrlLoading] = useState(false);
  const [renderAsWebPage, setRenderAsWebPage] = useState(false);

  const getShareUrl = (code) => {
    if (code) {
      return `${window.location.protocol}//${window.location.host}/s/${code}`;
    }

    return window.location.href;
  };

  const handleShare = (event, sessionId, isLoggedIn, renderAsWebPage) => {
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
        render_as_web_page: renderAsWebPage,
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
        setPinned(response?.data?.share?.slug);
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
      maxWidth="xs"
    >
      <DialogTitle id="app-share-modal">Share</DialogTitle>
      <DialogContent>
        <Typography variant="body1">
          {appRunData?.sessionId && !shareCode
            ? "Share the output from this app run by clicking on the create link button to generate a shareable url."
            : !shareCode &&
              "Share this app using the link below or by clicking on the social media buttons."}
        </Typography>
        {shareCode && (
          <Box sx={{ marginTop: 2, marginBottom: 4 }}>
            <Typography variant="body1">
              Share this app session using the link below or use the buttons to
              share on social media.
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
        {(shareCode || (!shareCode && !appRunData.sessionId)) && (
          <Box sx={{ paddingTop: 4, display: "inline-table" }}>
            <TextField
              label="Share URL"
              value={getShareUrl(shareCode)}
              fullWidth
              variant="outlined"
              size="medium"
              InputProps={{
                readOnly: true,
                endAdornment: (
                  <IconButton
                    onClick={(e) => {
                      navigator.clipboard.writeText(getShareUrl(shareCode));
                      enqueueSnackbar("Share code copied successfully", {
                        variant: "success",
                      });
                    }}
                  >
                    <Tooltip title="Copy Share URL">
                      <ContentCopy fontSize="small" />
                    </Tooltip>
                  </IconButton>
                ),
              }}
            />

            <Typography variant="caption">
              Share the link with others to view the output from this app run
            </Typography>

            <Stack direction={"row"} gap={2} sx={{ paddingTop: 2 }}>
              <FacebookShareButton url={getShareUrl(shareCode)}>
                <FacebookIcon size={30} round={true} />
              </FacebookShareButton>
              <FacebookMessengerShareButton url={getShareUrl(shareCode)}>
                <FacebookMessengerIcon size={30} round={true} />
              </FacebookMessengerShareButton>
              <LinkedinShareButton url={getShareUrl(shareCode)}>
                <LinkedinIcon size={30} round={true} />
              </LinkedinShareButton>
              <PinterestShareButton url={getShareUrl(shareCode)}>
                <PinterestIcon size={30} round={true} />
              </PinterestShareButton>
              <TelegramShareButton url={getShareUrl(shareCode)}>
                <TelegramIcon size={30} round={true} />
              </TelegramShareButton>
              <WhatsappShareButton url={getShareUrl(shareCode)}>
                <WhatsappIcon size={30} round={true} />
              </WhatsappShareButton>
              <TwitterShareButton
                url={getShareUrl(shareCode)}
                title={"Check this app on Promptly!\n\n"}
                via={"TryPromptly"}
              >
                <XIcon size={30} round={true} />
              </TwitterShareButton>
            </Stack>
          </Box>
        )}
        {!shareCode && appRunData?.sessionId && (
          <Box sx={{ paddingTop: 4 }}>
            <FormGroup>
              <Tooltip title="When checked, the output will be rendered as a web page irrespective of the app's layout">
                <FormControlLabel
                  control={<Checkbox checked={renderAsWebPage} size="small" />}
                  label="Render the output as a web page"
                  onChange={(e) => setRenderAsWebPage(e.target.checked)}
                />
              </Tooltip>
            </FormGroup>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button key="cancel" onClick={handleClose}>
          Cancel
        </Button>

        {!shareCode && (
          <LoadingButton
            key="submit"
            variant="contained"
            type="primary"
            onClick={(e) => {
              appRunData?.sessionId
                ? handleShare(
                    e,
                    appRunData?.sessionId,
                    isLoggedIn,
                    renderAsWebPage,
                  )
                : handleClose(e);
            }}
            loading={shareUrlLoading}
            disabled={appRunData?.isRunning}
          >
            {appRunData?.sessionId ? "Create Link" : "Done"}
          </LoadingButton>
        )}
        {shareCode && !profile?.username && (
          <LoadingButton
            key="submit"
            variant="contained"
            type="primary"
            onClick={(e) => navigate(`/s/${shareCode}`)}
            loading={shareUrlLoading}
            disabled={appRunData?.isRunning}
          >
            View Session
          </LoadingButton>
        )}
        {shareCode && profile?.username && (
          <LoadingButton
            key="pin"
            variant="contained"
            type="primary"
            onClick={(e) => {
              if (pinned) {
                navigate(`/u/${profile.username}/${pinned}`);
              } else if (appRunData?.sessionId) {
                handlePinToProfile(e, appRunData?.sessionId, isLoggedIn);
              } else {
                handleClose(e);
              }
            }}
            loading={pinToProfileLoading}
            disabled={appRunData?.isRunning || pinToProfileLoading}
          >
            {pinned
              ? "View on Profile"
              : appRunData?.sessionId
                ? "Pin to Profile"
                : "Done"}
          </LoadingButton>
        )}
      </DialogActions>
    </Dialog>
  );
}
