/** Paddle.js overlay checkout. The backend serves all config (environment,
 * client token, price id, custom_data) via POST /billing/checkout, so billing
 * changes never require a frontend rebuild. */

import { initializePaddle, type Paddle } from "@paddle/paddle-js";

import type { CheckoutConfig } from "./types";

let cached: { token: string; paddle: Promise<Paddle | undefined> } | null = null;

function getPaddle(config: CheckoutConfig): Promise<Paddle | undefined> {
  if (!cached || cached.token !== config.client_token) {
    cached = {
      token: config.client_token,
      paddle: initializePaddle({
        environment: config.environment,
        token: config.client_token,
      }),
    };
  }
  return cached.paddle;
}

export async function openPaddleCheckout(config: CheckoutConfig): Promise<void> {
  const paddle = await getPaddle(config);
  if (!paddle) throw new Error("The payment overlay failed to load. Please try again.");
  paddle.Checkout.open({
    items: [{ priceId: config.price_id, quantity: 1 }],
    customData: config.custom_data,
    ...(config.email ? { customer: { email: config.email } } : {}),
    settings: {
      displayMode: "overlay",
      successUrl: config.success_url,
    },
  });
}
