import { Link } from "react-router-dom";

import { LegalLayout } from "../components/LegalLayout";

export function TermsPage() {
  return (
    <LegalLayout title="Terms of Service" updated="12 July 2026">
      <section>
        <h2>1. Who we are</h2>
        <p>
          HanVoice (&ldquo;the Service&rdquo;) is a web application for learning to speak
          Korean, operated by Joshua van Straaten, a sole trader based in South Africa
          (&ldquo;we&rdquo;, &ldquo;us&rdquo;). Contact:{" "}
          <a href="mailto:hanvoice@joshuavanstraaten.com" className="text-taegeuk-blue">
            hanvoice@joshuavanstraaten.com
          </a>
          . By creating an account or using the Service you agree to these terms.
        </p>
      </section>

      <section>
        <h2>2. The Service</h2>
        <p>
          HanVoice provides Korean lessons, pronunciation and handwriting practice with
          automated feedback, and AI conversation practice. Feedback, corrections, and
          conversation replies are generated automatically. They are self-study learning
          aids only, not a language assessment, qualification, or credential — they can
          be wrong, no specific learning outcome is guaranteed, and they have no use or
          effect outside the Service.
        </p>
      </section>

      <section>
        <h2>3. Accounts</h2>
        <ul>
          <li>You must provide a valid email address and keep your password secure.</li>
          <li>You are responsible for activity under your account.</li>
          <li>One account per person; accounts are not transferable.</li>
        </ul>
      </section>

      <section>
        <h2>4. Plans, payments, and billing</h2>
        <ul>
          <li>
            The free plan includes limited daily usage. Paid plans (a monthly Premium
            subscription and a one-time lifetime Founder Pass) unlock higher daily limits,
            as described on the <Link to="/#pricing" className="text-taegeuk-blue">pricing page</Link>.
          </li>
          <li>
            Purchases are processed by Polar (polar.sh), our merchant of record. Your
            purchase is also subject to Polar&rsquo;s buyer terms, and Polar handles
            applicable taxes, invoices, and payment data.
          </li>
          <li>
            Subscriptions renew monthly until cancelled. You can cancel at any time and
            keep access until the end of the paid period.
          </li>
          <li>
            The Founder Pass grants the Premium usage limits for the lifetime of the
            Service — for as long as HanVoice operates.
          </li>
          <li>
            Refunds are handled per our{" "}
            <Link to="/refunds" className="text-taegeuk-blue">
              Refund Policy
            </Link>
            .
          </li>
        </ul>
      </section>

      <section>
        <h2>5. Acceptable use</h2>
        <p>
          Don&rsquo;t abuse the Service: no attempts to break, overload, or reverse the
          scoring systems, no automated scraping or bulk API use, no unlawful, abusive, or
          infringing content in conversation practice, and no sharing accounts to
          circumvent plan limits. We may suspend or terminate accounts that violate these
          terms; if we terminate a paid account without cause, we will refund the unused
          portion.
        </p>
      </section>

      <section>
        <h2>6. Availability and changes</h2>
        <p>
          The Service is provided &ldquo;as is&rdquo;. We aim for high availability but do
          not guarantee uninterrupted operation, and we may change or discontinue features.
          If we discontinue the Service entirely, active subscriptions will not renew. To
          the maximum extent permitted by law, our total liability is limited to the amount
          you paid us in the 12 months before the claim.
        </p>
      </section>

      <section>
        <h2>7. Your content</h2>
        <p>
          Audio you record and characters you draw are processed to give you scores and
          feedback (see the{" "}
          <Link to="/privacy" className="text-taegeuk-blue">
            Privacy Policy
          </Link>
          ). You retain any rights in your content; you grant us the licence needed to
          operate the Service.
        </p>
      </section>

      <section>
        <h2>8. Changes to these terms and governing law</h2>
        <p>
          We may update these terms; material changes will be announced in the app or by
          email, and continued use after the effective date is acceptance. These terms are
          governed by the laws of the Republic of South Africa, without affecting any
          consumer rights you hold under the mandatory law of your country of residence.
        </p>
      </section>
    </LegalLayout>
  );
}
