import Form from "@rjsf/mui";
import { getTemplate, getUiOptions } from "@rjsf/utils";
import {
  FormControl,
  FormHelperText,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ImageList,
  ImageListItem,
  Chip,
} from "@mui/material";
import { useState } from "react";
import { DataSourceSelector } from "./datasource/DataSourceSelector";
import MuiCustomSelect from "./MuiCustomSelect";
import ConnectionSelector from "./connections/ConnectionSelector";
import FileUploadWidget from "./form/DropzoneFileWidget";
import SecretTextField from "./form/SecretTextField";
import CustomObjectFieldTemplate from "./ConfigurationFormObjectFieldTemplate";
import { TextFieldWithVars } from "./apps/TextFieldWithVars";
import GdriveFileSelector from "./form/GdriveFileSelector";
import WebpageURLExtractorWidget from "./form/WebpageURLExtractorWidget";

function CustomGdriveFileWidget(props) {
  return <GdriveFileSelector {...props} />;
}

function CustomWebpageURLExtractorWidget(props) {
  return <WebpageURLExtractorWidget {...props} />;
}

function FieldTemplate(props) {
  const {
    id,
    children,
    classNames,
    style,
    disabled,
    displayLabel,
    hidden,
    label,
    onDropPropertyClick,
    onKeyChange,
    readonly,
    required,
    rawErrors = [],
    errors,
    help,
    rawDescription,
    schema,
    uiSchema,
    registry,
  } = props;
  const [isFocused, setIsFocused] = useState(false);

  const uiOptions = getUiOptions(uiSchema);
  const WrapIfAdditionalTemplate = getTemplate(
    "WrapIfAdditionalTemplate",
    registry,
    uiOptions,
  );

  if (hidden) {
    return <div style={{ display: "none" }}>{children}</div>;
  }
  return (
    <WrapIfAdditionalTemplate
      classNames={classNames}
      style={style}
      disabled={disabled}
      id={id}
      label={label}
      onDropPropertyClick={onDropPropertyClick}
      onKeyChange={onKeyChange}
      readonly={readonly}
      required={required}
      schema={schema}
      uiSchema={uiSchema}
      registry={registry}
    >
      <FormControl
        fullWidth={true}
        error={rawErrors.length ? true : false}
        required={required}
        onFocus={(e) => {
          setIsFocused(true);
        }}
        onBlur={(e) => {
          setIsFocused(false);
        }}
      >
        {children}
        {displayLabel && rawDescription ? (
          <FormHelperText id={id} focused={isFocused}>
            {rawDescription}
          </FormHelperText>
        ) : null}
        {errors}
        {help}
      </FormControl>
    </WrapIfAdditionalTemplate>
  );
}

function TextAreaWidget(props) {
  const { options, registry } = props;
  const BaseInputTemplate = getTemplate("BaseInputTemplate", registry, options);

  let rows = 5;

  if (typeof options.rows === "string" || typeof options.rows === "number") {
    rows = options.rows;
  }

  return (
    <BaseInputTemplate
      sx={{
        "& .MuiOutlinedInput-root": {
          "& > fieldset": { border: "1px solid rgb(204, 204, 204)" },
        },
      }}
      {...props}
      multiline
      rows={rows}
      variant={"outlined"}
    />
  );
}

function CustomselectWidget(props) {
  return <MuiCustomSelect {...props} />;
}

function CustomFileWidget(props) {
  return <FileUploadWidget {...props} />;
}

function ChatWidgetResponse({ chat_message }) {
  if (chat_message.content) {
    return <ListItemText primary={chat_message.content}></ListItemText>;
  } else if (chat_message.function_call) {
    const function_call_name = chat_message.function_call.name;
    const function_call_args = JSON.parse(chat_message.function_call.arguments);

    const fargs = Object.keys(function_call_args)
      .map((key) => `${key}="${function_call_args[key]}"`)
      .join(",");

    return (
      <div>
        <ListItemText
          primary={"Function"}
          secondary={`${function_call_name}(${fargs})`}
        ></ListItemText>
      </div>
    );
  }
  return null;
}

const ChatWidget = (props) => {
  let result = props.value || [];
  let key = 0;

  if (typeof result === "string") {
    result = [{ content: result }];
  }

  return (
    <List className="output-chat" style={{ paddingTop: 0 }}>
      {result.map((input) => (
        <ListItem
          key={key++}
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            padding: "10px",
            background: "rgb(255, 250, 236)",
            border: "1px solid rgb(235, 230, 236)",
            borderRadius: 10,
          }}
        >
          <ListItemAvatar>
            <Chip color="primary" label={input.role || "System"}></Chip>
          </ListItemAvatar>
          <ChatWidgetResponse chat_message={input}></ChatWidgetResponse>
        </ListItem>
      ))}
    </List>
  );
};

const TextWidget = (props) => {
  const result = props.value || [];
  let key = 0;
  return (
    <List className="output-text" style={{ paddingTop: 0 }}>
      {result.map((input) => (
        <ListItem
          key={key++}
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            padding: "10px",
            background: "rgb(255, 250, 236)",
            border: "1px solid rgb(235, 230, 236)",
            borderRadius: 10,
          }}
        >
          <ListItemText primary={input}></ListItemText>
        </ListItem>
      ))}
    </List>
  );
};

const ImageWidget = (props) => {
  let key = 0;
  return (
    <ImageList className="output-image" cols={2} gap={8}>
      {props.value.map((item) => (
        <ImageListItem key={key++}>
          <img src={`${item}`} loading="lazy" alt="" />
        </ImageListItem>
      ))}
    </ImageList>
  );
};

const AudioWidget = (props) => {
  return <audio src={props.value} controls />;
};

const CustomObjectFieldTemplateWithAdvanced = (props) => {
  return <CustomObjectFieldTemplate {...props} disableAdvanced={false} />;
};

const CustomObjectFieldTemplateWithoutAdvanced = (props) => {
  return <CustomObjectFieldTemplate {...props} disableAdvanced={true} />;
};

const PasswordWidget = (props) => {
  return <SecretTextField {...props} />;
};

const ConnectionSelectorWidget = (props) => {
  return <ConnectionSelector {...props} />;
};

const RichTextWidget = (props) => {
  return <TextFieldWithVars {...props} richText={true} />;
};

const DatasourceWidget = (props) => {
  return <DataSourceSelector {...props} />;
};

const ThemedJsonForm = ({
  schema,
  uiSchema,
  formData,
  onChange,
  submitBtn = <div></div>,
  theme,
  validator,
  templates = {},
  widgets = {},
  disableAdvanced = false,
  ...props
}) => {
  return (
    <Form
      {...props}
      schema={schema}
      uiSchema={uiSchema}
      validator={validator}
      formData={formData}
      onChange={onChange}
      templates={{
        ...templates,
        FieldTemplate,
        ObjectFieldTemplate: disableAdvanced
          ? CustomObjectFieldTemplateWithoutAdvanced
          : CustomObjectFieldTemplateWithAdvanced,
      }}
      widgets={{
        ...{
          customselect: CustomselectWidget,
          TextareaWidget: TextAreaWidget,
          FileWidget: CustomFileWidget,
          output_chat: ChatWidget,
          output_text: TextWidget,
          output_image: ImageWidget,
          output_audio: AudioWidget,
          datasource: DatasourceWidget,
          gdrive: CustomGdriveFileWidget,
          webpageurls: CustomWebpageURLExtractorWidget,
          password: PasswordWidget,
          connection: ConnectionSelectorWidget,
          richtext: RichTextWidget,
        },
        ...widgets,
      }}
    >
      {submitBtn}
    </Form>
  );
};

export default ThemedJsonForm;
