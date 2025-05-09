import Link from "next/link";

export default function Page() {
  return (
    <div className="h-screen flex flex-col items-center justify-center gap-4">
      <Link href="/notification" className="text-blue-500">
        알림 테스트 페이지
      </Link>
      <Link href="/chat" className="text-blue-500">
        채팅 테스트 페이지
      </Link>
    </div>
  );
}
