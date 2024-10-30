import { Box, Stack } from "@mui/material";
import { AssetRenderer } from "./AssetRenderer";
import PCMStreamPlayer from "./PCMStreamPlayer";

export const AgentMultiModalContent = ({ content }) => {
  const { text, audio, transcript } = content;

  return (
    <Stack>
      <Box>{text}</Box>
      {audio && <PCMStreamPlayer src={audio} sampleRate={24000} channels={1} />}
      {transcript && (
        <Box>
          Transcript: <AssetRenderer url={transcript} type="text/markdown" />
        </Box>
      )}
    </Stack>
  );
};
