import type { Metadata } from "next";
import { LoginForm } from "../../../components/auth/login-form";

export const metadata: Metadata = {
  title: "Login",
  description: "Log in to your RAG Platform workspace.",
};

export default function LoginPage() {
  return <LoginForm />;
}
