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
