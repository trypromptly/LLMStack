import ArrowCircleDownOutlinedIcon from "@mui/icons-material/ArrowCircleDownOutlined";
import DeleteIcon from "@mui/icons-material/Delete";
import { LoadingButton } from "@mui/lab";
import {
  IconButton,
  InputAdornment,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
} from "@mui/material";
import { useEffect, useState } from "react";
import { axios } from "../../data/axios";

export default function WebpageURLExtractorWidget(props) {
  const { onChange, value, schema } = props;
  const [inputUrl, setInputUrl] = useState(null);
  const [urls, setUrls] = useState(value ? value.split(",") : null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (urls !== null || inputUrl !== null) {
      const url_str = urls ? urls.join(",") : inputUrl;
      onChange(url_str);
      if (url_str.length > schema.maxLength) {
        setError("Too many URLs");
      }
      if (url_str.length < schema.maxLength) {
        setError(null);
      }
    }
  }, [urls, onChange, schema.maxLength, inputUrl]);

  const onClick = () => {
    const url = inputUrl;
    setUrls(null);
    setIsLoading(true);
    axios()
      .post("/api/datasources/url/extract_urls", {
        url: url,
      })
      .then((response) => {
        setUrls(response.data.urls || [url]);
        setIsLoading(false);
      })
      .catch((error) => {
        setUrls([url]);
        setIsLoading(false);
      });
  };

  return (
    <div className="container">
      <label style={{ display: "flex" }}>{props.label}</label>
      <p></p>
      <Stack spacing={2} sx={{}}>
        <TextField
          disabled={isLoading}
          onChange={(e) => setInputUrl(e.target.value)}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <LoadingButton
                  onClick={onClick}
                  isLoading={isLoading}
                  disabled={isLoading}
                >
                  <ArrowCircleDownOutlinedIcon />
                </LoadingButton>
              </InputAdornment>
            ),
          }}
        />
        {isLoading && <LinearProgress />}
        {urls && urls.length > 0 && (
          <div>
            <List
              dense={true}
              sx={{
                maxHeight: "200px",
                overflowY: "scroll",
                border: error ? "1px solid red" : null,
              }}
            >
              {urls.map((url, index) => {
                return (
                  <ListItem
                    key={index}
                    secondaryAction={
                      <IconButton
                        onClick={() => {
                          const newUrls = [...urls];
                          newUrls.splice(index, 1);
                          setUrls(newUrls);
                        }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    }
                  >
                    <ListItemText
                      primary={
                        <a href={url} target="_blank" rel="noreferrer">
                          {url}
                        </a>
                      }
                    />
                  </ListItem>
                );
              })}
            </List>
            {error && <p style={{ color: "red" }}>{error}</p>}
          </div>
        )}
      </Stack>
    </div>
  );
}
