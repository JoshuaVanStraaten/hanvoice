import { LegalLayout } from "../components/LegalLayout";

export function PrivacyPage() {
  return (
    <LegalLayout title="Privacy Policy" updated="12 July 2026">
      <section>
        <h2>1. Who is responsible</h2>
        <p>
          HanVoice is operated by Joshua van Straaten (South Africa). For anything
          privacy-related — questions, access requests, deletion — email{" "}
          <a href="mailto:hanvoice@joshuavanstraaten.com" className="text-taegeuk-blue">
            hanvoice@joshuavanstraaten.com
          </a>
          .
        </p>
      </section>

      <section>
        <h2>2. What we collect and why</h2>
        <ul>
          <li>
            <strong>Account data</strong> — email, display name, and a securely hashed
            password, stored with Supabase in the EU (Ireland). Needed to run your account.
          </li>
          <li>
            <strong>Learning progress</strong> — lessons completed, practice attempts and
            their scores, conversation transcripts with the AI partner. Needed to show your
            progress and resume where you left off.
          </li>
          <li>
            <strong>Voice recordings</strong> — when you practice pronunciation, your
            recording is sent to Microsoft Azure Speech (EU, North Europe) for scoring. We
            store the resulting scores, not the audio: recordings are not retained after
            scoring.
          </li>
          <li>
            <strong>Handwriting drawings</strong> — sent to an AI vision model (NVIDIA
            cloud) for scoring. We store the scores, not the image.
          </li>
          <li>
            <strong>Conversation text</strong> — your practice conversation turns are
            processed by an NVIDIA-hosted language model to generate replies.
          </li>
          <li>
            <strong>Usage analytics</strong> — we use PostHog (EU cloud) to understand how
            the app is used (pages viewed, features used, anonymised device data), using
            cookies/local storage. This helps us improve the product.
          </li>
          <li>
            <strong>Error reports</strong> — we use Sentry to collect technical error
            reports (stack traces, browser/OS info) so we can fix bugs.
          </li>
          <li>
            <strong>Payment data</strong> — purchases are processed by Polar (polar.sh)
            as merchant of record. Polar collects your billing details; we never see your
            card number. Polar&rsquo;s own privacy policy applies to checkout.
          </li>
          <li>
            <strong>Emails</strong> — account emails (confirmation, password reset) are
            delivered via Resend.
          </li>
        </ul>
      </section>

      <section>
        <h2>3. What we don&rsquo;t do</h2>
        <p>
          We don&rsquo;t sell your data, we don&rsquo;t use your recordings or drawings to
          train AI models, and we don&rsquo;t send you marketing email unless you joined
          the waitlist or opted in.
        </p>
      </section>

      <section>
        <h2>4. Where your data lives</h2>
        <p>
          Primary storage is in the European Union (Supabase, Ireland; Azure, North Europe;
          PostHog EU). Our API runs on Fly.io (London). AI conversation and handwriting
          scoring use NVIDIA&rsquo;s hosted models, which may process data in the United
          States during the request.
        </p>
      </section>

      <section>
        <h2>5. Your rights</h2>
        <p>
          You can ask for a copy of your data, correct it, or have your account and all
          associated data deleted — email us and we&rsquo;ll action it within 30 days.
          Depending on where you live (e.g. GDPR in the EU/UK, POPIA in South Africa) you
          may have additional statutory rights; we honour them.
        </p>
      </section>

      <section>
        <h2>6. Changes</h2>
        <p>
          If this policy changes materially we&rsquo;ll announce it in the app or by email.
          The &ldquo;last updated&rdquo; date at the top always reflects the current
          version.
        </p>
      </section>
    </LegalLayout>
  );
}
