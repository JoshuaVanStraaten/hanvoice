import { LegalLayout } from "../components/LegalLayout";

export function RefundsPage() {
  return (
    <LegalLayout title="Refund Policy" updated="12 July 2026">
      <section>
        <h2>1. The short version</h2>
        <p>
          If HanVoice isn&rsquo;t for you, tell us within 14 days of your purchase and
          you&rsquo;ll get your money back. No forms, no hoops.
        </p>
      </section>

      <section>
        <h2>2. Founder Pass (one-time purchase)</h2>
        <p>
          Full refund within 14 days of purchase, no questions asked. After 14 days the
          purchase is final, except where the law of your country gives you longer.
        </p>
      </section>

      <section>
        <h2>3. Premium subscription</h2>
        <ul>
          <li>
            Full refund of your <strong>first</strong> payment if you request it within 14
            days of starting the subscription.
          </li>
          <li>
            You can cancel anytime; access continues to the end of the paid month and no
            further payments are taken. We don&rsquo;t give partial refunds for unused days
            of a billing period already charged, except for renewals charged in error —
            those we refund in full.
          </li>
        </ul>
      </section>

      <section>
        <h2>4. How to request a refund</h2>
        <p>
          Email{" "}
          <a href="mailto:hanvoice@joshuavanstraaten.com" className="text-taegeuk-blue">
            hanvoice@joshuavanstraaten.com
          </a>{" "}
          from your account email, or use the link in your Paddle receipt. Purchases are
          processed by Paddle.com as merchant of record, so approved refunds are issued by
          Paddle to your original payment method, usually within 5–10 business days.
        </p>
      </section>

      <section>
        <h2>5. Statutory rights</h2>
        <p>
          Nothing here limits the consumer rights you hold under the mandatory law of your
          country of residence (for example EU/UK withdrawal rights or South Africa&rsquo;s
          CPA).
        </p>
      </section>
    </LegalLayout>
  );
}
