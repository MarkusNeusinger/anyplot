/**
 * Fisher-Yates shuffle — uniformly random reordering of an array.
 *
 * Use this instead of the `[...arr].sort(() => Math.random() - 0.5)` idiom,
 * which is biased: distribution depends on the engine's sort implementation
 * and produces a non-uniform shuffle.
 */
export function shuffleArray<T>(array: readonly T[]): T[] {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}
