import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getMedia } from "../lib/api";
import { queryKeys } from "../lib/queryKeys";
import { SceneImage } from "./SceneImage";

type Props = {
  assetId: string;
  title: string;
  imageUrl?: string | null;
  width?: number | null;
  height?: number | null;
  /** Requested transform width for the signed URL this component fetches. */
  requestWidth?: number;
  loading?: "lazy" | "eager";
};

export function MediaImage({ assetId, title, imageUrl, width, height, requestWidth, loading }: Props) {
  const queryClient = useQueryClient();
  const retried = useRef(false);
  const [refetching, setRefetching] = useState(false);
  const { data, isPending } = useQuery({
    queryKey: queryKeys.media(assetId, requestWidth),
    queryFn: async () => (await getMedia(assetId, requestWidth)).signedUrl,
    enabled: !imageUrl || refetching,
    staleTime: 10 * 60_000,
    gcTime: 30 * 60_000,
  });
  const resolved = refetching ? data ?? null : imageUrl ?? data ?? null;
  if (!resolved && isPending) return <span role="status">Loading image...</span>;
  return (
    <SceneImage
      scene={{ title, imageUrl: resolved }}
      width={width}
      height={height}
      loading={loading}
      onError={() => {
        // One self-heal per asset: an expired signed URL is replaced once.
        if (retried.current) return;
        retried.current = true;
        setRefetching(true);
        void queryClient.invalidateQueries({ queryKey: queryKeys.media(assetId, requestWidth) });
      }}
    />
  );
}
