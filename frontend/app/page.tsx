"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Loading } from "@/components/ui";
import { api } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    api("/api/auth/me").then(() => router.replace("/dashboard/")).catch(() => router.replace("/login/"));
  }, [router]);
  return <div className="mx-auto max-w-md p-10"><Loading label="Opening…" /></div>;
}
