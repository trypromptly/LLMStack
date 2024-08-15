import "@univerjs/design/lib/index.css";
import "@univerjs/ui/lib/index.css";
import "@univerjs/docs-ui/lib/index.css";
import "@univerjs/sheets-ui/lib/index.css";
import "@univerjs/sheets-formula/lib/index.css";
import { FUniver } from "@univerjs/facade";

import { LocaleType, Tools, Univer, UniverInstanceType } from "@univerjs/core";
import { defaultTheme } from "@univerjs/design";

import { UniverUIPlugin } from "@univerjs/ui";

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
        ),
      },
    });
    univerRef.current = univer;
    univer.registerPlugin(UniverUIPlugin, {
      container: containerRef.current,
      toolbar: false,
      footer: false,
      contextMenu: false,
    });

    univer.registerPlugin(UniverDocsPlugin, {
      hasScroll: false,
    });
    univer.registerPlugin(UniverDocsUIPlugin);

    containerRef.current = univer;
    // sheets
    univer.registerPlugin(UniverSheetsPlugin);
    univer.registerPlugin(UniverSheetsUIPlugin);
    univer.registerPlugin(UniverSheetsFormulaPlugin);

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
