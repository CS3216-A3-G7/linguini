import { useQuery } from "@tanstack/react-query";
import { getMedia } from "../lib/api";
import { queryKeys } from "../lib/queryKeys";
import { SceneImage } from "./SceneImage";
export function MediaImage({ assetId, title, imageUrl }: { assetId: string; title: string; imageUrl?: string | null }) {
  const { data, isPending } = useQuery({
    queryKey: queryKeys.media(assetId),
    queryFn: async () => (await getMedia(assetId)).signedUrl,
    enabled: !imageUrl,
    staleTime: 10 * 60_000,
    gcTime: 30 * 60_000,
  });
  if (!imageUrl && isPending) return <span role="status">Loading image...</span>;
  return <SceneImage scene={{ title, imageUrl: imageUrl ?? data ?? null }} />;
}
