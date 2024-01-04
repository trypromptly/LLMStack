import { useState } from "react";
import {
  Box,
  Card,
  CardActions,
  CardContent,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import {
  AutoFixHighOutlined,
  QuestionAnswerOutlined,
  WebOutlined,
} from "@mui/icons-material";
import Grid from "@mui/material/Unstable_Grid2";
import { AppFromTemplateDialog } from "./AppFromTemplateDialog";
import { appTemplatesState, isMobileState } from "../../data/atoms";
import { useRecoilValue } from "recoil";
import startCase from "lodash/startCase";
import selectAllIcon_light from "../../assets/images/icons/templates/select-all.png";
import blankIcon_light from "../../assets/images/icons/templates/blank.png";
import agentsIcon_light from "../../assets/images/icons/templates/agents.png";
import customerSupportIcon_light from "../../assets/images/icons/templates/customer-support.png";
import entertainmentIcon_light from "../../assets/images/icons/templates/entertainment.png";
import financeIcon_light from "../../assets/images/icons/templates/finance.png";
import hrIcon_light from "../../assets/images/icons/templates/hr.png";
import marketingIcon_light from "../../assets/images/icons/templates/marketing.png";
import productivityIcon_light from "../../assets/images/icons/templates/productivity.png";
import programmingIcon_light from "../../assets/images/icons/templates/programming.png";
import salesIcon_light from "../../assets/images/icons/templates/sales.png";
import botIcon_light from "../../assets/images/icons/templates/bot.png";
import internetIcon_light from "../../assets/images/icons/templates/internet.png";
import textIcon_light from "../../assets/images/icons/templates/text.png";
import toolIcon_light from "../../assets/images/icons/templates/tool.png";
import voiceIcon_light from "../../assets/images/icons/templates/voice.png";

const AppTemplateCategoryIcon = ({ category }) => {
  switch (category) {
    case "all":
      return <img src={selectAllIcon_light} alt="select all" width={24} />;
    case "blank":
      return <img src={blankIcon_light} alt="blank" width={24} />;
    case "agents":
      return <img src={agentsIcon_light} alt="agents" width={24} />;
    case "customer-support":
      return (
        <img
          src={customerSupportIcon_light}
          alt="customer support"
          width={24}
        />
      );
    case "entertainment":
      return (
        <img src={entertainmentIcon_light} alt="entertainment" width={24} />
      );
    case "finance":
      return <img src={financeIcon_light} alt="finance" width={24} />;
    case "hr":
      return <img src={hrIcon_light} alt="hr" width={24} />;
    case "marketing":
      return <img src={marketingIcon_light} alt="marketing" width={24} />;
    case "productivity":
      return <img src={productivityIcon_light} alt="productivity" width={24} />;
    case "programming":
      return <img src={programmingIcon_light} alt="programming" width={24} />;
    case "sales":
      return <img src={salesIcon_light} alt="sales" width={24} />;
    default:
      return <img src={selectAllIcon_light} alt="select all" width={24} />;
  }
};

const AppTemplateIcon = ({ template }) => {
  switch (template.icon) {
    case "bot":
      return <img src={botIcon_light} alt="bot" width={24} />;
    case "internet":
      return <img src={internetIcon_light} alt="internet" width={24} />;
    case "text":
      return <img src={textIcon_light} alt="text" width={24} />;
    case "tool":
      return <img src={toolIcon_light} alt="tool" width={24} />;
    case "voice":
      return <img src={voiceIcon_light} alt="voice" width={24} />;
    default:
      return <img src={selectAllIcon_light} alt="select all" width={24} />;
  }
};

const AppTypeIcon = ({ type }) => {
  switch (type) {
    case "web":
      return <WebOutlined sx={{ color: "#999", fontSize: "1.4em", m: 1 }} />;
    case "text-chat":
      return (
        <QuestionAnswerOutlined
          sx={{ color: "#999", fontSize: "1.4em", m: 1 }}
        />
      );
    case "agent":
      return (
        <AutoFixHighOutlined sx={{ color: "#999", fontSize: "1.4em", m: 1 }} />
      );
    default:
      return <WebOutlined sx={{ color: "#999", fontSize: "1.4em", m: 1 }} />;
  }
};

const AppTemplateCard = ({
  template,
  setSelectedAppTemplateSlug,
  setOpenAppFromTemplateDialog,
}) => {
  return (
    <Card
      sx={{
        display: "flex",
        flexDirection: "column",
        minWidth: "250px",
        maxWidth: "300px",
        minHeight: "250px",
        maxHeight: "300px",
        ":hover": {
          cursor: "pointer",
          boxShadow: "0px 0px 10px 0px rgba(4, 45, 120, 0.5)",
          backgroundColor: "#f5f5f5",
        },
      }}
      elevation={1}
      onClick={() => {
        setOpenAppFromTemplateDialog(true);
        setSelectedAppTemplateSlug(template.slug);
      }}
    >
      <CardContent sx={{ m: 2, maxHeight: "200px" }}>
        <ListItem
          sx={{ flexDirection: "column", alignItems: "baseline", pl: 0 }}
        >
          <ListItemIcon
            sx={{
              backgroundColor: "#fff9e4",
              p: 2,
              minWidth: "24px",
              borderRadius: 2,
            }}
          >
            <AppTemplateIcon template={template} />
          </ListItemIcon>
          <ListItemText>
            <Typography sx={{ fontSize: "1.1rem", fontWeight: 550, pt: 3 }}>
              {template.name}
            </Typography>
          </ListItemText>
        </ListItem>
        <Typography
          variant="subtitle2"
          sx={{
            color: "#666",
            display: "-webkit-box",
            WebkitLineClamp: 4,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "normal",
            margin: "2px",
            lineHeight: "1.6em",
            maxHeight: "6.4em",
          }}
        >
          {template.description}
        </Typography>
      </CardContent>
      <CardActions
        sx={{ justifyContent: "flex-start", flexGrow: 1, ml: 4, mt: 1, pb: 4 }}
      >
        <Chip
          label={
            template?.app?.type_slug === "text-chat"
              ? "chat"
              : template?.app?.type_slug
          }
          icon={<AppTypeIcon type={template?.app?.type_slug} />}
          sx={{
            borderRadius: 2,
            height: 24,
            mb: 4,
            "& .MuiChip-label": {
              fontSize: "0.8rem",
              fontWeight: 600,
              color: "#666",
              pl: 0,
            },
          }}
        />
      </CardActions>
    </Card>
  );
};

const AppTemplatesContainer = () => {
  const [openAppFromTemplateDialog, setOpenAppFromTemplateDialog] =
    useState(false);
  const appTemplates = useRecoilValue(appTemplatesState);
  const isMobile = useRecoilValue(isMobileState);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedAppTemplateSlug, setSelectedAppTemplateSlug] = useState("");

  const blankTemplates = [
    {
      name: "Web App",
      description:
        "Provides a web app that takes in a user input and returns a rendered output in the provided template.",
      slug: "_blank_web",
      icon: "tool",
      category_slugs: ["blank"],
      app: {
        type_slug: "web",
      },
    },
    {
      name: "Chat Bot",
      description:
        "Provides a chat bot that takes in a user input and returns a rendered output in the provided template.",
      slug: "_blank_text-chat",
      icon: "text",
      category_slugs: ["blank"],
      app: {
        type_slug: "text-chat",
      },
    },
    {
      name: "Agent",
      description:
        "Provides an agent that takes in a user input and returns a rendered output in the provided template.",
      slug: "_blank_agent",
      icon: "bot",
      category_slugs: ["blank"],
      app: {
        type_slug: "agent",
      },
    },
  ];

  const categories = [
    "all",
    "blank",
    ...new Set(
      appTemplates
        .map((template) => template.category_slugs)
        .flatMap((category) => category)
        .filter((category) => category !== "blank")
        .sort(),
    ),
  ];

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppFromTemplateDialog
        open={openAppFromTemplateDialog}
        setOpen={setOpenAppFromTemplateDialog}
        appTemplateSlug={selectedAppTemplateSlug}
      />
      <Grid container spacing={0}>
        <Grid xs={2} md={2}>
          <List>
            {!isMobile && (
              <ListItem>
                <ListItemText>
                  <Typography
                    sx={{
                      textTransform: "uppercase",
                      color: "#666",
                      fontSize: "0.9rem",
                    }}
                  >
                    Categories
                  </Typography>
                </ListItemText>
              </ListItem>
            )}
            {categories.map((category) => {
              return (
                <ListItemButton
                  key={category}
                  selected={selectedCategory === category}
                  onClick={() => setSelectedCategory(category)}
                  sx={{
                    "&.Mui-selected": {
                      borderBottom: "1px solid #046fda66",
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: "40px" }}>
                    <AppTemplateCategoryIcon category={category} />
                  </ListItemIcon>
                  {!isMobile && (
                    <ListItemText>
                      <Typography variant="subtitle">
                        {category === "hr" ? "HR" : startCase(category)}
                      </Typography>
                    </ListItemText>
                  )}
                </ListItemButton>
              );
            })}
          </List>
        </Grid>
        <Grid xs={10}>
          <Stack
            direction="row"
            sx={{
              display: "flex",
              flexWrap: "wrap",
              gap: 5,
              mt: isMobile ? 0 : 4,
              padding: "10px 0 10px 10px",
              mr: 1,
              height: "600px",
              overflowY: "scroll",
              backgroundColor: "#edeff7",
            }}
          >
            {appTemplates
              .filter((template) => {
                if (selectedCategory === "all") {
                  return true;
                }
                return template.category_slugs.includes(selectedCategory);
              })
              .map((template) => {
                return (
                  <AppTemplateCard
                    key={template.slug}
                    template={template}
                    setSelectedAppTemplateSlug={setSelectedAppTemplateSlug}
                    setOpenAppFromTemplateDialog={setOpenAppFromTemplateDialog}
                  />
                );
              })}
            {selectedCategory === "all" && (
              <Box sx={{ display: "block", width: "100%" }}>
                <Divider>
                  <Typography
                    variant="subtitle2"
                    sx={{ fontWeight: 600, color: "#666" }}
                  >
                    {"  "}
                    Use Blank Templates
                    {"  "}
                  </Typography>
                </Divider>
              </Box>
            )}
            {blankTemplates
              .filter((template) => {
                if (selectedCategory === "all") {
                  return true;
                }
                return template.category_slugs.includes(selectedCategory);
              })
              .map((template) => {
                return (
                  <AppTemplateCard
                    key={template.slug}
                    template={template}
                    setSelectedAppTemplateSlug={setSelectedAppTemplateSlug}
                    setOpenAppFromTemplateDialog={setOpenAppFromTemplateDialog}
                  />
                );
              })}
          </Stack>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AppTemplatesContainer;
