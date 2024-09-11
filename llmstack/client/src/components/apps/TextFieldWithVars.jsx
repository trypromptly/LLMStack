import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Box, Typography } from "@mui/material";
import { TreeItem, TreeView } from "@mui/x-tree-view";
import { useEffect, useRef, useState } from "react";
import {
  INSERT_TEMPLATE_VARIABLE_COMMAND,
  LexicalEditor,
} from "./lexical/LexicalEditor";

const StackLabel = ({ name, apiBackend = null }) => {
  return (
    <Box>
      <Typography>{name}</Typography>
    </Box>
  );
};

const generateTreeItemsFromSchema = (
  schema,
  parentKey,
  handleNodeClick,
  pillPrefix,
) => {
  if (!schema || !schema.properties) return [null, []];

  const { properties, $defs } = schema;
  const currentKeys = [];
  const definitions = $defs || {};

  const treeItems = Object.keys(properties).map((key) => {
    const currentKey = parentKey ? `${parentKey}.${key}` : key;
    const { type, description, title, items, widget, $ref } = properties[key];

    if (type === "object") {
      const [nestedTreeItems, nestedCurrentKeys] = generateTreeItemsFromSchema(
        properties[key],
        currentKey,
        handleNodeClick,
        `${pillPrefix} / ${key}`,
      );
      currentKeys.push(...nestedCurrentKeys);

      return (
        <TreeItem key={currentKey} nodeId={currentKey} label={title || key}>
          {nestedTreeItems}
        </TreeItem>
      );
    }

    if (type === "array") {
      if (items && items.type === "object") {
        const [nestedTreeItems, nestedCurrentKeys] =
          generateTreeItemsFromSchema(
            items,
            `${currentKey}[0]`,
            handleNodeClick,
            `${pillPrefix} / ${currentKey}[0]`,
          );
        currentKeys.push(...nestedCurrentKeys);

        return (
          <TreeItem
            key={currentKey}
            nodeId={currentKey}
            label={description || key}
          >
            {nestedTreeItems}
          </TreeItem>
        );
      }

      if (items && items.type === "array") {
        const [nestedTreeItems] =
          typeof items === "object"
            ? generateTreeItemsFromSchema(
                items,
                `${currentKey}[0]`,
                handleNodeClick,
                `${pillPrefix} ${key}`,
              )
            : items.map((item, index) => {
                const [nestedTreeItems, nestedCurrentKeys] =
                  generateTreeItemsFromSchema(
                    item,
                    `${currentKey}[0]`,
                    handleNodeClick,
                    `${pillPrefix} ${key}`,
                  );
                currentKeys.push(...nestedCurrentKeys);
                return (
                  <TreeItem
                    key={`${currentKey}[0]`}
                    nodeId={`${currentKey}.${index}`}
                    label={`${key} ${index + 1}`}
                  >
                    {nestedTreeItems}
                  </TreeItem>
                );
              });

        currentKeys.push({
          key: `${currentKey}[0]`,
          pillPrefix: `${pillPrefix} / ${key}[0]`,
        });

        return (
          <TreeItem
            key={`${currentKey}`}
            nodeId={currentKey}
            label={description || key}
          >
            {nestedTreeItems}
          </TreeItem>
        );
      }

      if (
        items &&
        items.$ref &&
        Object.keys(definitions).find((d) => `#/$defs/${d}` === items.$ref)
      ) {
        const [nestedTreeItems, nestedCurrentKeys] =
          generateTreeItemsFromSchema(
            definitions[items.$ref.split("/").pop()],
            `${currentKey}[0]`,
            handleNodeClick,
            `${pillPrefix}${key}[0] /`,
          );
        currentKeys.push(...nestedCurrentKeys);

        return (
          <TreeItem
            key={currentKey}
            nodeId={currentKey}
            label={description || key}
          >
            {nestedTreeItems}
          </TreeItem>
        );
      }

      if (items) {
        currentKeys.push({
          key: `${currentKey}[0]`,
          pillPrefix: `${pillPrefix} ${key}`,
        });

        return (
          <TreeItem
            key={`${currentKey}[0]`}
            nodeId={currentKey}
            label={
              <span>
                {key} {<span style={{ color: "#999" }}> - {description}</span>}
              </span>
            }
            onClick={(e) => handleNodeClick(e, `${currentKey}[0]`, widget)}
          />
        );
      }
    }

    if (
      definitions &&
      $ref &&
      Object.keys(definitions).find((d) => `#/definitions/${d}` === $ref)
    ) {
      const [nestedTreeItems, nestedCurrentKeys] = generateTreeItemsFromSchema(
        definitions[$ref.split("/").pop()],
        `${currentKey}`,
        handleNodeClick,
        `${pillPrefix}${key} /`,
      );
      currentKeys.push(...nestedCurrentKeys);

      return (
        <TreeItem
          key={currentKey}
          nodeId={currentKey}
          label={description || key}
        >
          {nestedTreeItems}
        </TreeItem>
      );
    }

    currentKeys.push({
      key: currentKey,
      pillPrefix: `${pillPrefix} ${key}`,
    });

    return (
      <TreeItem
        key={currentKey}
        nodeId={currentKey}
        label={
          <span>
            {key} {<span style={{ color: "#999" }}> - {description}</span>}
          </span>
        }
        onClick={(e) => handleNodeClick(e, currentKey, widget)}
      />
    );
  });

  return [treeItems, currentKeys];
};

function getLiquidTemplateString(variable, widget) {
  let templateString = `{{${variable}}}`;
  if (widget === "output_image") {
    templateString = `![Image]({{${variable}}})`;
  } else if (widget === "output_audio") {
    templateString = `![Audio]({{${variable}}})`;
  }

  return templateString;
}
export default function TextFieldWithVars({
  templateStringResolver = getLiquidTemplateString,
  ...props
}) {
  const { value, onChange } = props;
  const [treeViewVisible, setTreeViewVisible] = useState(false);
  const [textFocus, setTextFocus] = useState(false);
  const [treeFocus, setTreeFocus] = useState(false);
  const [text, setText] = useState(value || "");
  const schemas = props.schemas;

  useEffect(() => {
    if (textFocus || treeFocus) {
      setTreeViewVisible(true);
    } else {
      setTreeViewVisible(false);

      // Update value
      if (onChange && text !== value) {
        onChange(text);
      }
    }
  }, [textFocus, treeFocus, text, value, onChange]);

  const [memoizedSchemaTrees, setMemoizedSchemaTrees] = useState([]);
  const [templateVariables, setTemplateVariables] = useState([]);
  const editorRef = useRef(null);

  useEffect(() => {
    if (schemas && schemas.length > 0) {
      const [memoizedSchemaTrees, templateVariables] = schemas
        .map((schema, index) =>
          generateTreeItemsFromSchema(
            schema.items,
            schema.id,
            (e, k, widget) => {
              const templateString = templateStringResolver(k, widget);
              editorRef.current.dispatchCommand(
                INSERT_TEMPLATE_VARIABLE_COMMAND,
                templateString,
              );
            },
            schema.pillPrefix,
          ),
        )
        .reduce(
          (acc, val) => {
            acc[0].push(val[0]);
            acc[1].push(...val[1]);
            return acc;
          },
          [[], []],
        );

      // Collect keys and pill prefixes in templateVariables into a map of key to pill prefix
      const templateVariablesMap = templateVariables.reduce((acc, val) => {
        acc[`{{${val.key}}}`] = val.pillPrefix;
        return acc;
      }, {});

      setMemoizedSchemaTrees(memoizedSchemaTrees);
      setTemplateVariables(templateVariablesMap);
    }
  }, [
    schemas,
    editorRef,
    setMemoizedSchemaTrees,
    setTemplateVariables,
    templateStringResolver,
  ]);

  const textCopy = value;

  return (
    <Box>
      <Box
        onKeyDown={(e) => {
          setTextFocus(true);
          editorRef.current.setEditable(true);
        }}
        onMouseDown={(e) => {
          setTextFocus(true);
          editorRef.current.setEditable(true);
        }}
        onBlur={() => {
          setTextFocus(false);
          editorRef.current.setEditable(false);
        }}
        sx={{ marginBottom: "-20px" }}
        onClick={(e) => {
          editorRef.current.setEditable(true);
        }}
      >
        <LexicalEditor
          templateVariables={templateVariables}
          ref={editorRef}
          text={textCopy}
          setText={setText}
          placeholder={props?.placeholder || props?.schema?.description}
          label={props?.label}
          richText={props?.richText}
        />
      </Box>
      <div
        onMouseEnter={() => {
          setTreeFocus(true);
        }}
        onMouseLeave={() => {
          setTreeFocus(false);
          setTextFocus(false);
        }}
      >
        {treeViewVisible && memoizedSchemaTrees.length > 0 && (
          <Box
            style={{
              marginTop: 30,
              marginBottom: 10,
              backgroundColor: "#fffeeb",
              borderRadius: 5,
              border: "1px solid #eee",
              padding: 5,
            }}
          >
            <Typography variant="h6" style={{ fontWeight: 600, color: "#666" }}>
              Template Variables
            </Typography>
            <Typography variant="body2" style={{ marginBottom: 10 }}>
              {props.introText ||
                `Below are the available variables across your input and 
              processors. Click on a variable to insert it into the text field 
              and use it during processing.`}
            </Typography>
            {memoizedSchemaTrees
              .map((val, index, array) => array[array.length - 1 - index])
              .map((schemaTree, index) => (
                <TreeView
                  key={index}
                  defaultCollapseIcon={<ExpandMoreIcon />}
                  defaultExpandIcon={<ChevronRightIcon />}
                >
                  <TreeItem
                    nodeId={index.toString()}
                    label={
                      <StackLabel
                        name={schemas[schemas.length - 1 - index].label}
                      />
                    }
                    onClick={(e) =>
                      schemaTree
                        ? e.stopPropagation()
                        : editorRef.current.dispatchCommand(
                            INSERT_TEMPLATE_VARIABLE_COMMAND,
                            `{{${schemas[schemas.length - 1 - index].id}}}`,
                          )
                    }
                  >
                    {schemaTree}
                  </TreeItem>
                </TreeView>
              ))}
          </Box>
        )}
      </div>
    </Box>
  );
}
