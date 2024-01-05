// Hook to set and get validation errors for the processor and clear them
// when the processor is changed.
// ----------------------------------------------------------------------
import { useEffect } from "react";
import { appEditorValidationErrorsState } from "./atoms";
import { useRecoilState, useSetRecoilState } from "recoil";

export const useValidationErrorsForAppComponents = (index) => {
  const setValidationErrors = useSetRecoilState(appEditorValidationErrorsState);

  const setValidationErrorsForId = (id, errors) => {
    setValidationErrors((oldErrors) => {
      const newErrors = { ...oldErrors };
      newErrors[id] = errors;
      return newErrors;
    });
  };

  const clearValidationErrorsForId = (id) => {
    setValidationErrors((oldErrors) => {
      const newErrors = { ...oldErrors };
      delete newErrors[id];
      return newErrors;
    });
  };

  useEffect(() => {
    return () => {
      clearValidationErrorsForId(index);
    };
  }, [setValidationErrors]);

  return [setValidationErrorsForId, clearValidationErrorsForId];
};

export const useValidationErrorsForAppConsole = () => {
  const [validationErrors, setValidationErrors] = useRecoilState(
    appEditorValidationErrorsState,
  );

  const clearAllValidationErrors = () => {
    setValidationErrors({});
  };

  useEffect(() => {
    return () => {
      clearAllValidationErrors();
    };
  }, [setValidationErrors]);

  return validationErrors;
};
