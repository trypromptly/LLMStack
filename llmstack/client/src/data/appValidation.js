// Hook to set and get validation errors for the processor and clear them
// when the processor is changed.
// ----------------------------------------------------------------------
import { useCallback, useEffect } from "react";
import { appEditorValidationErrorsState } from "./atoms";
import { useRecoilState, useSetRecoilState } from "recoil";

export const useValidationErrorsForAppComponents = (index) => {
  const setValidationErrors = useSetRecoilState(appEditorValidationErrorsState);

  const setValidationErrorsForId = useCallback(
    (id, errors) => {
      setValidationErrors((oldErrors) => {
        const newErrors = { ...oldErrors };
        newErrors[id] = errors;
        return newErrors;
      });
    },
    [setValidationErrors],
  );

  const clearValidationErrorsForId = useCallback(
    (id) => {
      setValidationErrors((oldErrors) => {
        const newErrors = { ...oldErrors };
        delete newErrors[id];
        return newErrors;
      });
    },
    [setValidationErrors],
  );

  return [setValidationErrorsForId, clearValidationErrorsForId];
};

export const useValidationErrorsForAppConsole = () => {
  const [validationErrors, setValidationErrors] = useRecoilState(
    appEditorValidationErrorsState,
  );

  const clearAllValidationErrors = useCallback(() => {
    setValidationErrors({});
  }, [setValidationErrors]);

  useEffect(() => {
    return () => {
      clearAllValidationErrors();
    };
  }, [clearAllValidationErrors]);

  return validationErrors;
};
