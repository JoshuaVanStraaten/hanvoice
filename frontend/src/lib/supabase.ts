import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

let client: SupabaseClient | undefined;

/** Fail loudly on first *use*, not at import: a module-level throw is
 * statically provable when env vars are missing at build time, and Rollup
 * dead-code-eliminates the whole app behind it. */
function init(): SupabaseClient {
  if (!url || !anonKey) {
    throw new Error(
      "Missing VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY — copy .env.example to .env and fill them in.",
    );
  }
  client ??= createClient(url, anonKey);
  return client;
}

export const supabase: SupabaseClient = new Proxy({} as SupabaseClient, {
  get(_target, prop) {
    const instance = init();
    return Reflect.get(instance, prop, instance) as unknown;
  },
});
