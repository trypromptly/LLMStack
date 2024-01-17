import {
  EmailIcon,
  EmailShareButton,
  LinkedinIcon,
  LinkedinShareButton,
  TelegramIcon,
  TelegramShareButton,
  TwitterIcon,
  TwitterShareButton,
  WhatsappIcon,
  WhatsappShareButton,
} from "react-share";

export default function ShareButtons({ url, title }) {
  return (
    <span style={{ display: "flex", gap: "1px" }}>
      <TwitterShareButton
        url={url}
        title={title}
        via={"TryPromptly"}
        hashtags={[]}
      >
        <TwitterIcon size={24} round={true} />
      </TwitterShareButton>
      &nbsp;
      <EmailShareButton
        url={url}
        subject={title + "via trypromptly.com"}
        body={"Check out this prompt I shared on Promptly!"}
      >
        <EmailIcon size={24} round={true} />
      </EmailShareButton>
      &nbsp;
      <LinkedinShareButton
        url={url}
        title={title}
        source={"https://trypromptly.com"}
        summary={"Check out this prompt I shared on Promptly!"}
      >
        <LinkedinIcon size={24} round={true} />
      </LinkedinShareButton>
      &nbsp;
      <WhatsappShareButton url={url} title={title}>
        <WhatsappIcon size={24} round={true} />
      </WhatsappShareButton>
      &nbsp;
      <TelegramShareButton url={url} title={title}>
        <TelegramIcon size={24} round={true} />
      </TelegramShareButton>
    </span>
  );
}
