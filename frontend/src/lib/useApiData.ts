import { useCallback, useEffect, useRef, useState } from "react";
import type { SetStateAction } from "react";

export function useApiData<T>(load: (signal?: AbortSignal) => Promise<T>) {
  const [data, setValue] = useState<T | null>(null);
  const revision = useRef(0);
  const [error, setError] = useState<string | null>(null);
  const setData = useCallback((value: SetStateAction<T | null>) => {
    revision.current += 1;
    setError(null);
    setValue(value);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    const initialRevision = revision.current;
    load(controller.signal).then((value) => {
      if (!controller.signal.aborted && revision.current === initialRevision) setValue(value);
    }).catch((reason: unknown) => {
      if (!controller.signal.aborted && revision.current === initialRevision) {
        setError(reason instanceof Error ? reason.message : "Unable to load data.");
      }
    });
    return () => controller.abort();
  }, [load]);
  return { data, setData, error, loading: data === null && error === null };
}
