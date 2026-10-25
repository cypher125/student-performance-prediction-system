"use client";

import { createContext, useContext } from "react";
import type { User } from "@/lib/types";

export const SessionContext = createContext<User | null>(null);

export function useUser(): User {
  const user = useContext(SessionContext);
  if (!user) throw new Error("useUser must be used inside the signed-in layout");
  return user;
}

export const isStaff = (user: User) => user.role !== "student";
