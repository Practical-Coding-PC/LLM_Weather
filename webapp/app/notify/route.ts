import { NextRequest, NextResponse } from "next/server";
import webpush, { PushSubscription } from "web-push";

webpush.setVapidDetails(
  "https://getweather.app",
  process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY!,
  process.env.VAPID_PRIVATE_KEY!
);

export async function POST(request: NextRequest) {
  const { subscription, message } = (await request.json()) as {
    subscription: PushSubscription;
    message: string;
  };

  await webpush.sendNotification(
    subscription,
    JSON.stringify({
      title: "날씨 알림",
      body: message,
      icon: "/icon-192x192.png",
    })
  );

  return NextResponse.json({ success: true });
}
