import "./globals.css";

export const metadata = {
  title: "AI施工图审核平台",
  description: "AI辅助施工图审核平台",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
