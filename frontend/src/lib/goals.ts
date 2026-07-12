/** Goal checklist state for a conversation scenario. Pure so it's testable:
 * the backend is the authority on which goals are done; this only merges
 * that list with the scenario's full goal set, preserving scenario order. */

export interface GoalState {
  goal: string;
  done: boolean;
}

export function goalStates(scenarioGoals: string[], completedGoals: string[]): GoalState[] {
  const done = new Set(completedGoals);
  return scenarioGoals.map((goal) => ({ goal, done: done.has(goal) }));
}

export function allGoalsDone(states: GoalState[]): boolean {
  return states.length > 0 && states.every((state) => state.done);
}

/** Human labels for the backend's goal keys (backend/app/services/goals.py —
 * add an entry here when a pattern is added there). Unknown keys fall back to
 * de-snaked text so a new scenario never renders `raw_key` chips again. */
const GOAL_LABELS: Record<string, string> = {
  greeted: "Said hello",
  ordered_drink: "Ordered a drink",
  stated_size_or_temp: "Chose size or temperature",
  paid: "Paid for it",
  said_thanks: "Said thank you",
  ordered_food: "Ordered food",
  asked_for_water: "Asked for water",
  stated_destination: "Told the driver your destination",
  asked_duration_or_distance: "Asked how long it takes",
  asked_price: "Asked the price",
  asked_discount: "Asked for a discount",
  introduced_self: "Introduced yourself",
  asked_name: "Asked their name",
  said_nice_to_meet: "Said nice to meet you",
  shared_background: "Shared where you're from",
};

export function goalLabel(goal: string): string {
  const known = GOAL_LABELS[goal];
  if (known) return known;
  const humanized = goal.replaceAll("_", " ");
  return humanized.charAt(0).toUpperCase() + humanized.slice(1);
}
