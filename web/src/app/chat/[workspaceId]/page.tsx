import type { Metadata } from "next";
import { ChatPanel } from "../../../../components/chat/chat-panel";

type ChatPageProps = {
  params: Promise<{
    workspaceId: string;
  }>;
};

export const metadata: Metadata = {
  title: "Chat",
  description: "Ask grounded questions and inspect document citations.",
};

export default async function ChatPage({ params }: ChatPageProps) {
  const { workspaceId } = await params;

  return <ChatPanel workspaceId={workspaceId} />;
}
