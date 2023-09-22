import { useEffect, forwardRef, useLayoutEffect } from "react";
import { LexicalComposer } from "@lexical/react/LexicalComposer";
import { ContentEditable } from "@lexical/react/LexicalContentEditable";
import { HistoryPlugin } from "@lexical/react/LexicalHistoryPlugin";
import { PlainTextPlugin } from "@lexical/react/LexicalPlainTextPlugin";
import { RichTextPlugin } from "@lexical/react/LexicalRichTextPlugin";
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { HeadingNode, QuoteNode } from "@lexical/rich-text";
import { TableCellNode, TableNode, TableRowNode } from "@lexical/table";
import { ListItemNode, ListNode } from "@lexical/list";
import { CodeHighlightNode, CodeNode } from "@lexical/code";
import { AutoLinkNode, LinkNode } from "@lexical/link";
import { LinkPlugin } from "@lexical/react/LexicalLinkPlugin";
import { ListPlugin } from "@lexical/react/LexicalListPlugin";
import { $generateHtmlFromNodes, $generateNodesFromDOM } from "@lexical/html";
import LexicalErrorBoundary from "@lexical/react/LexicalErrorBoundary";
import {
  DecoratorNode,
  $createTextNode,
  $createParagraphNode,
  $insertNodes,
  $getRoot,
  COMMAND_PRIORITY_EDITOR,
  createCommand,
} from "lexical";
import { Chip } from "@mui/material";
import ToolbarPlugin from "./plugins/ToolbarPlugin";

import "./LexicalEditor.css";

const theme = {
  ltr: "ltr",
  rtl: "rtl",
  placeholder: "editor-placeholder",
  paragraph: "editor-paragraph",
  quote: "editor-quote",
  heading: {
    h1: "editor-heading-h1",
    h2: "editor-heading-h2",
    h3: "editor-heading-h3",
    h4: "editor-heading-h4",
    h5: "editor-heading-h5",
  },
  list: {
    nested: {
      listitem: "editor-nested-listitem",
    },
    ol: "editor-list-ol",
    ul: "editor-list-ul",
    listitem: "editor-listitem",
  },
  image: "editor-image",
  link: "editor-link",
  text: {
    bold: "editor-text-bold",
    italic: "editor-text-italic",
    overflowed: "editor-text-overflowed",
    hashtag: "editor-text-hashtag",
    underline: "editor-text-underline",
    strikethrough: "editor-text-strikethrough",
    underlineStrikethrough: "editor-text-underlineStrikethrough",
    code: "editor-text-code",
  },
  code: "editor-code",
  codeHighlight: {
    atrule: "editor-tokenAttr",
    attr: "editor-tokenAttr",
    boolean: "editor-tokenProperty",
    builtin: "editor-tokenSelector",
    cdata: "editor-tokenComment",
    char: "editor-tokenSelector",
    class: "editor-tokenFunction",
    "class-name": "editor-tokenFunction",
    comment: "editor-tokenComment",
    constant: "editor-tokenProperty",
    deleted: "editor-tokenProperty",
    doctype: "editor-tokenComment",
    entity: "editor-tokenOperator",
    function: "editor-tokenFunction",
    important: "editor-tokenVariable",
    inserted: "editor-tokenSelector",
    keyword: "editor-tokenAttr",
    namespace: "editor-tokenVariable",
    number: "editor-tokenProperty",
    operator: "editor-tokenOperator",
    prolog: "editor-tokenComment",
    property: "editor-tokenProperty",
    punctuation: "editor-tokenPunctuation",
    regex: "editor-tokenVariable",
    selector: "editor-tokenSelector",
    string: "editor-tokenSelector",
    symbol: "editor-tokenProperty",
    tag: "editor-tokenProperty",
    url: "editor-tokenOperator",
    variable: "editor-tokenVariable",
  },
};

export const INSERT_TEMPLATE_VARIABLE_COMMAND = createCommand();

const convertTemplateVariableElement = (domNode) => {
  const text = domNode.getAttribute("data-lexical-template-variable-text");
  const data = domNode.getAttribute("data-lexical-template-variable-data");
  if (text) {
    const node = $createTemplateVariableNode(text, data);
    return { node };
  }
  return null;
};

class TemplateVariableNode extends DecoratorNode {
  __text = "";
  __data = {};

  static getType() {
    return "template-variable";
  }

  static clone(node) {
    return new TemplateVariableNode(node.__text, node.__data, node.__key);
  }

  static importJSON(serializedNode) {
    const node = $createTemplateVariableNode(
      serializedNode.text,
      serializedNode.data,
    );
    return node;
  }

  exportJSON() {
    return {
      ...super.exportJSON(),
      text: this.getText(),
      data: this.getData(),
    };
  }

  createDOM(editor, config) {
    const element = document.createElement("div");
    element.setAttribute("style", "display: inline-block;");
    element.setAttribute("data-lexical-template-variable-text", this.__text);
    element.setAttribute("data-lexical-template-variable-data", this.__data);
    return element;
  }

  updateDOM(prevNode, dom, config) {}

  static importDOM() {
    return {
      div: (domNode) => {
        if (!domNode.hasAttribute("data-lexical-template-variable-text")) {
          return null;
        }
        return {
          conversion: convertTemplateVariableElement,
          priority: 2,
        };
      },
    };
  }

  exportDOM() {
    const element = document.createElement("div");
    element.setAttribute("data-lexical-template-variable-text", this.__text);
    element.setAttribute("data-lexical-template-variable-data", this.__data);
    const text = document.createTextNode(this.getTextContent());
    element.append(text);
    return { element };
  }

  constructor(text, data, format, key) {
    super(format, key);
    this.__text = text;
    this.__data = data;
  }

  getText() {
    return this.__text;
  }

  getData() {
    return this.__data;
  }

  getTextContent(_includeInert, _includeDirectionless) {
    return this.__text;
  }

  decorate(editor, config) {
    return <Chip label={this.__data} size="small" />;
  }

  isInline() {
    return true;
  }
}

function $createTemplateVariableNode(text, data = null) {
  return new TemplateVariableNode(text, data);
}

function TemplateVariablesPlugin({
  templateVariables,
  text,
  setText,
  richText,
}) {
  const findVariable = (variables, textContent, index) => {
    for (const [key, value] of Object.entries(variables)) {
      if (textContent.startsWith(key, index)) {
        return [key, value];
      }
    }

    return null;
  };

  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    if (editor && !editor.hasNodes([TemplateVariableNode])) {
      throw new Error("TemplateVariableNode not registered!");
    }

    const removeUpdateListener = editor.registerUpdateListener(
      ({ editorState }) => {
        if (setText) {
          editorState.read(() => {
            if (richText) {
              setText($generateHtmlFromNodes(editor));
            } else {
              const root = $getRoot();
              const text = root.getTextContent();
              setText(text);
            }
          });
        }
      },
    );

    editor.registerCommand(
      INSERT_TEMPLATE_VARIABLE_COMMAND,
      (payload) => {
        if (payload) {
          editor.update(() => {
            const templateVariableNode = $createTemplateVariableNode(
              payload,
              payload,
            );

            $insertNodes([templateVariableNode, $createTextNode(" ")]);
          });
        }

        return true;
      },
      COMMAND_PRIORITY_EDITOR,
    );

    if (removeUpdateListener) {
      return removeUpdateListener;
    }
  }, [editor, text, setText, richText]);

  // Load initial text into editor
  useEffect(() => {
    if (editor) {
      editor.getEditorState().read(() => {
        const root = $getRoot();
        if (root.getTextContent() === "") {
          editor.update(() => {
            if (!root.isDirty() && text !== "") {
              if (!richText || (text && !text.startsWith("<"))) {
                const paragraphNode = $createParagraphNode();
                const textNode = $createTextNode(text);
                paragraphNode.append(textNode);
                root.getFirstChild().replace(paragraphNode);
              } else {
                const domParser = new DOMParser();
                const doc = domParser.parseFromString(text, "text/html");
                const nodes = $generateNodesFromDOM(editor, doc);
                $insertNodes(nodes);
              }
            }
          });
        }
      });
    }
  }, [text, editor, richText]);

  useEffect(() => {
    if (
      editor &&
      text !== "" &&
      Object.keys(templateVariables).length > 0 &&
      !richText
    ) {
      editor.getEditorState().read(() => {
        setTimeout(() => {
          editor.update(() => {
            const root = $getRoot();
            if (root.isDirty()) {
              return;
            }
            const paragraphNode = $createParagraphNode();
            const nodes = [];
            let textContent = text;
            let index = 0;

            while (index < textContent?.length) {
              const variable = findVariable(
                templateVariables,
                textContent,
                index,
              );
              if (variable) {
                if (index > 0) {
                  nodes.push($createTextNode(textContent.slice(0, index)));
                  textContent = textContent.slice(index);
                  index = 0;
                }
                nodes.push(
                  $createTemplateVariableNode(variable[0], variable[1]),
                );
                textContent = textContent.slice(variable[0].length);
              } else {
                index++;
              }
            }
            if (textContent?.length > 0) {
              nodes.push($createTextNode(textContent));
            }

            paragraphNode.append(...nodes);
            root.getFirstChild().replace(paragraphNode);
            paragraphNode.select();
          });
        }, 0);
      });
    }
  }, [templateVariables, text, editor, richText]);

  return null;
}

function EditorRefPlugin({ editorRef }) {
  const [editor] = useLexicalComposerContext();

  useLayoutEffect(() => {
    editorRef.current = editor;
    return () => {
      editorRef.current = null;
    };
  }, [editor, editorRef]);

  return null;
}

function onError(error) {
  console.error(error);
}

export const LexicalEditor = forwardRef(function LexicalEditor(props, ref) {
  const initialConfig = {
    namespace: "MyEditor",
    nodes: [
      TemplateVariableNode,
      HeadingNode,
      ListNode,
      ListItemNode,
      QuoteNode,
      CodeNode,
      CodeHighlightNode,
      TableNode,
      TableCellNode,
      TableRowNode,
      AutoLinkNode,
      LinkNode,
    ],
    theme,
    onError,
  };

  return (
    <LexicalComposer initialConfig={initialConfig} editorRef={ref}>
      <div className="editor-container">
        {props.richText && <ToolbarPlugin />}
        {props.richText && (
          <RichTextPlugin
            contentEditable={
              <ContentEditable
                style={{
                  border: "solid 1px rgb(204, 204, 204)",
                  padding: "20px 15px",
                  borderRadius: 5,
                }}
              />
            }
            placeholder={
              !props.richText && (
                <div className="editor-placeholder">{props.placeholder}</div>
              )
            }
            ErrorBoundary={LexicalErrorBoundary}
          />
        )}
        {!props.richText && (
          <PlainTextPlugin
            contentEditable={
              <ContentEditable
                style={{
                  border: "solid 1px rgb(204, 204, 204)",
                  padding: "20px 15px",
                  borderRadius: 5,
                }}
              />
            }
            placeholder={
              !props.richText && (
                <div className="editor-placeholder">{props.placeholder}</div>
              )
            }
            ErrorBoundary={LexicalErrorBoundary}
          />
        )}
        <div className="editor-label">{props.label}</div>
        <HistoryPlugin />
        {props.templateVariables && (
          <TemplateVariablesPlugin
            templateVariables={props.templateVariables}
            text={props.text}
            setText={props.setText}
            richText={props.richText || false}
          />
        )}
        {ref && <EditorRefPlugin editorRef={ref} />}
        <ListPlugin />
        <LinkPlugin />
      </div>
    </LexicalComposer>
  );
});
