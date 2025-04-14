"use client";

import { useState, useEffect } from "react";
import { subscribeUser, unsubscribeUser, sendNotification } from "./actions";

function urlBase64ToUint8Array(base64String: string) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function PushNotificationManager() {
  const [isSupported, setIsSupported] = useState(false);
  const [subscription, setSubscription] = useState<PushSubscription | null>(
    null
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    if ("serviceWorker" in navigator && "PushManager" in window) {
      setIsSupported(true);
      registerServiceWorker();
    }
  }, []);

  async function registerServiceWorker() {
    const registration = await navigator.serviceWorker.register("/sw.js", {
      scope: "/",
      updateViaCache: "none",
    });
    const sub = await registration.pushManager.getSubscription();
    setSubscription(sub);
  }

  async function subscribeToPush() {
    const registration = await navigator.serviceWorker.ready;
    const sub = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(
        process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY!
      ),
    });
    setSubscription(sub);
    const serializedSub = JSON.parse(JSON.stringify(sub));
    await subscribeUser(serializedSub);
  }

  async function unsubscribeFromPush() {
    await subscription?.unsubscribe();
    setSubscription(null);
    await unsubscribeUser();
  }

  async function sendTestNotification() {
    if (subscription) {
      await sendNotification(message);
      setMessage("");
    }
  }

  if (!isSupported) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-sm border border-gray-200">
        <p className="text-gray-600 text-center">
          Push notifications are not supported in this browser.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
      <h3 className="text-xl font-semibold text-gray-800 mb-4">
        Push Notifications
      </h3>
      {subscription ? (
        <div className="space-y-4">
          <div className="flex items-center">
            <div className="h-3 w-3 bg-green-500 rounded-full mr-2"></div>
            <p className="text-gray-700">
              You are subscribed to push notifications
            </p>
          </div>
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <input
                type="text"
                placeholder="Enter notification message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={sendTestNotification}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition duration-200"
              >
                Send Test
              </button>
            </div>
            <button
              onClick={unsubscribeFromPush}
              className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition duration-200"
            >
              Unsubscribe
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-gray-600">
            You are not subscribed to push notifications.
          </p>
          <button
            onClick={subscribeToPush}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition duration-200"
          >
            Subscribe to Notifications
          </button>
        </div>
      )}
    </div>
  );
}

export default function NotificationPage() {
  return (
    <div className="max-w-md mx-auto py-10 px-4">
      <h1 className="text-2xl font-bold text-center text-gray-900 mb-8">
        Weather App
      </h1>
      <PushNotificationManager />
    </div>
  );
}
