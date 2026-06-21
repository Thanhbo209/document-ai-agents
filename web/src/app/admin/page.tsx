import type { Metadata } from "next";
import { AdminConsole } from "../../../components/admin/admin-console";

export const metadata: Metadata = {
  title: "Admin Console",
  description: "Internal metadata-first support console.",
};

export default function AdminPage() {
  return <AdminConsole />;
}
