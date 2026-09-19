import { useCallback } from "react";
import { getMedia } from "../lib/api";
import { useApiData } from "../lib/useApiData";
import { SceneImage } from "./SceneImage";
export function MediaImage({ assetId, title, imageUrl }: { assetId: string; title: string; imageUrl?: string | null }) {
  const load = useCallback(async () => imageUrl ?? (await getMedia(assetId)).signedUrl, [assetId, imageUrl]);
  const { data, loading } = useApiData(load);
  if (loading) return <span role="status">Loading image...</span>;
  return <SceneImage scene={{ title, imageUrl: data }} />;
}
