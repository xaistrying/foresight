"use client";

import { useEffect, useState } from "react";

type Status = "loading" | "ready" | "error";

export default function QuickSightEmbed() {
  const [embedUrl, setEmbedUrl] = useState<string | null>(null);
  const [status, setStatus]     = useState<Status>("loading");
  const [errMsg, setErrMsg]     = useState<string>("");

  useEffect(() => {
    fetch("/api/quicksight-embed")
      .then((res) => res.json())
      .then((data) => {
        if (data.embedUrl) {
          setEmbedUrl(data.embedUrl);
          setStatus("ready");
        } else {
          setErrMsg(data.error ?? "Failed to load embed URL");
          setStatus("error");
        }
      })
      .catch((err) => {
        setErrMsg(err.message);
        setStatus("error");
      });
  }, []);

  if (status === "loading") {
    return (
      <div className="flex items-center justify-center w-full h-full min-h-[400px] text-text-muted text-sm">
        Loading dashboard...
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex items-center justify-center w-full h-full min-h-[400px] text-accent-danger text-sm">
        {errMsg}
      </div>
    );
  }

  return (
    <iframe
      src={embedUrl!}
      width="100%"
      height="100%"
      className="border-0 rounded-lg"
      allowFullScreen
      title="QuickSight Dashboard"
    />
  );
}
