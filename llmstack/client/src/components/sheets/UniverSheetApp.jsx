import "@univerjs/design/lib/index.css";
import "@univerjs/ui/lib/index.css";
import "@univerjs/docs-ui/lib/index.css";
import "@univerjs/sheets-ui/lib/index.css";
import "@univerjs/sheets-formula/lib/index.css";
import { FUniver } from "@univerjs/facade";

import { LocaleType, Tools, Univer, UniverInstanceType } from "@univerjs/core";
import { defaultTheme } from "@univerjs/design";

import { UniverUIPlugin } from "@univerjs/ui";
import {
  StringValueObject,
  UniverFormulaEnginePlugin,
} from "@univerjs/engine-formula";
import { UniverDocsPlugin } from "@univerjs/docs";
import { UniverDocsUIPlugin } from "@univerjs/docs-ui";

import { UniverSheetsPlugin } from "@univerjs/sheets";
import { UniverSheetsFormulaPlugin } from "@univerjs/sheets-formula";
import { UniverSheetsUIPlugin } from "@univerjs/sheets-ui";

import DesignEnUS from "@univerjs/design/locale/en-US";
import UIEnUS from "@univerjs/ui/locale/en-US";
import DocsUIEnUS from "@univerjs/docs-ui/locale/en-US";
import SheetsEnUS from "@univerjs/sheets/locale/en-US";
import SheetsUIEnUS from "@univerjs/sheets-ui/locale/en-US";
import SheetsFormulaEnUS from "@univerjs/sheets-formula/locale/en-US";
import { forwardRef, useRef, useEffect, useImperativeHandle } from "react";
import { BaseFunction, FunctionType } from "@univerjs/engine-formula";

import "./UniverSheetApp.css";
const APPRUN = "APPRUN";
const functionEnUS = {
  formulaCustom: {
    APPRUN: {
      description: "Run an App",
      abstract: "Add its arguments to the App's input and run the App",
      functionParameter: {
        appId: {
          name: "App ID",
        },
        input: {
          name: "App Input",
        },
      },
    },
  },
};

const FUNCTION_LIST_USER = [
  {
    functionName: APPRUN,
    aliasFunctionName: "formulaCustom.APPRUN.aliasFunctionName",
    functionType: FunctionType.User,
    description: "formulaCustom.APPRUN.description",
    abstract: "formulaCustom.APPRUN.abstract",
    functionParameter: [
      {
        name: "formulaCustom.APPRUN.functionParameter.appId.name",
        detail: "formulaCustom.APPRUN.functionParameter.appId.detail",
        example: "<App UUID>",
        require: 1,
        repeat: 0,
      },
      {
        name: "formulaCustom.APPRUN.functionParameter.input.name",
        detail: "formulaCustom.APPRUN.functionParameter.input.detail",
        example: "<App Input>",
        require: 0,
        repeat: 1,
      },
    ],
  },
];

class Apprun extends BaseFunction {
  calculate(...variants) {
    let accumulatorAll = StringValueObject.create("");

    console.log("variants", variants);
    console.log(accumulatorAll);

    return accumulatorAll;
  }
}

const functionUser = [[Apprun, APPRUN]];

// eslint-disable-next-line react/display-name
const UniverSheetApp = forwardRef(({ data }, ref) => {
  const univerRef = useRef(null);
  const workbookRef = useRef(null);
  const containerRef = useRef(null);

  useImperativeHandle(
    ref,
    () => ({
      getData,
    }),
    [workbookRef.current],
  );

  /**
   * Initialize univer instance and workbook instance
   * @param data {IWorkbookData} document see https://univer.work/api/core/interfaces/IWorkbookData.html
   */
  const init = (data = {}) => {
    if (!containerRef.current) {
      throw Error("container not initialized");
    }
    const univer = new Univer({
      theme: defaultTheme,
      locale: LocaleType.EN_US,
      locales: {
        [LocaleType.EN_US]: Tools.deepMerge(
          SheetsEnUS,
          DocsUIEnUS,
          SheetsUIEnUS,
          SheetsFormulaEnUS,
          UIEnUS,
          DesignEnUS,
          functionEnUS,
        ),
      },
    });
    univerRef.current = univer;
    univer.registerPlugin(UniverUIPlugin, {
      container: containerRef.current,
      toolbar: false,
    });

    univer.registerPlugin(UniverDocsPlugin, {
      hasScroll: false,
    });
    univer.registerPlugin(UniverDocsUIPlugin);

    containerRef.current = univer;
    // sheets
    univer.registerPlugin(UniverSheetsPlugin);
    univer.registerPlugin(UniverSheetsUIPlugin);
    univer.registerPlugin(UniverSheetsFormulaPlugin, {
      description: FUNCTION_LIST_USER,
    });

    univer.registerPlugin(UniverFormulaEnginePlugin, {
      function: functionUser,
    });

    const univerAPI = FUniver.newAPI(univer);

    // create workbook instance
    workbookRef.current = univer.createUnit(
      UniverInstanceType.UNIVER_SHEET,
      data,
    );
  };

  /**
   * Destroy univer instance and workbook instance
   */
  const destroyUniver = () => {
    // univerRef.current?.dispose();
    univerRef.current = null;
    workbookRef.current = null;
  };

  /**
   * Get workbook data
   */
  const getData = () => {
    if (!workbookRef.current) {
      throw new Error("Workbook is not initialized");
    }

    return workbookRef.current.save();
  };

  useEffect(() => {
    init(data);
    return () => {
      destroyUniver();
    };
  }, [data]);

  return (
    <div
      ref={containerRef}
      className="univer-container"
      style={{ height: "100%", width: "100%" }}
    />
  );
});

export default UniverSheetApp;
