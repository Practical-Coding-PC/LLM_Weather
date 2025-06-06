import { NextRequest, NextResponse } from "next/server";
import webpush from "web-push";

webpush.setVapidDetails(
  "https://getweather.app",
  process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY!,
  process.env.VAPID_PRIVATE_KEY!
);

export async function POST(request: NextRequest) {
  const { subscription, message } = (await request.json()) as {
    subscription: {
      endpoint: string;
      p256dh: string;
      auth: string;
    };
    message: string;
  };

  await webpush.sendNotification(
    {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: subscription.p256dh,
        auth: subscription.auth,
      },
    },
    JSON.stringify({
      title: "날씨 알림",
      body: message,
      icon: "/icon-192x192.png",
    })
  );

  return NextResponse.json({ success: true });
}
