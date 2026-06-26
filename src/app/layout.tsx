import Sidebar from "@/src/components/Sidebar";
import MainContent from "@/src/components/MainContent";
import "@/src/app/globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="flex h-screen overflow-hidden">
        <Sidebar />
        <MainContent>{children}</MainContent>
      </body>
    </html>
  );
}
