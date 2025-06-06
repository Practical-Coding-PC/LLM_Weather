"use client";

export default function Notify() {
  const handleSendNotification = async () => {
    const userId = localStorage.getItem("userId");

    if (!userId) {
      alert("localStorage에 userId가 없습니다.");
      return;
    }

    try {
      await fetch("http://localhost:8000/notification-test", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ userId }),
      });
    } catch (error) {
      console.error(error);
      alert("알림 전송 실패");
    }
  };

  return (
    <div className="flex justify-center items-center h-screen">
      <button
        onClick={handleSendNotification}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
      >
        알림 테스트
      </button>
    </div>
  );
}
