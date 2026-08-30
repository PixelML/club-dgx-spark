# RL reward design: make early termination unprofitable

A compact negative-result lesson from a simulated quadruped/biped backflip
task on a DGX Spark node (single GB10, ~0.5 s/iteration at the tested
configuration, PyTorch 2.9.1+cu129). Claims below are **measured** on that
setup unless labeled otherwise.

## The exploit

Two training runs with a head-contact termination term collapsed the same
way: mean episode length fell from ~32 to ~20 steps, the termination fired on
100% of episodes, and mean episode reward *rose* (−0.67 → −0.28). The policy
learned that dying early is cheaper than paying accumulated per-step penalty
taxes for the rest of a full episode. Termination became an escape hatch.

## The fix

Add a one-shot reward at termination:

```python
def early_termination_penalty(env) -> torch.Tensor:
    """1.0 on the step a NON-timeout termination fires, else 0.0."""
    return env.termination_manager.terminated.float()
```

Register with a negative cfg weight whose magnitude **exceeds the total
escapable tax** — the sum of per-step penalties the policy could avoid by
dying (~8 points over a 250-step episode in our configuration; we used 10).
Timeouts must pay zero: keep them in the manager's separate `time_outs`
buffer, disjoint from `terminated`, so finishing an episode is never
penalized.

## Measured outcome

With the fix, across a 10,000-iteration run:

- Mean episode length: full-length (250.00) from iteration ~300 onward;
  zero termination penalties paid late in training.
- Head-contact penalty per episode: fell from a constant −1.0 (contact every
  episode) to a noisy −0.4 to −0.7.
- Task success rate: still 0% across three domain-randomization conditions
  (150 eval episodes). The failure mode changed from "die early" to
  "insufficient exploration of the full rotation within the tested horizon."

## Generalizable lessons

1. **Termination must cost more than the taxes it escapes.** Compute the
   per-step penalty sum over a full episode; set the termination weight
   strictly above it.
2. **Timeouts are not terminations.** A survival bonus is useless (and can
   reintroduce the exploit) if the timeout path is penalized.
3. **Fixing the exploit changes the failure mode, it does not guarantee
   success.** After the fix the policy entered a survival-locked local
   optimum (full-length episodes, near-zero task progress) for ~4,000
   iterations before resuming exploration. Budget horizon for that phase or
   add curriculum/shaping.
4. **A cheap smoke gate catches the exploit cheaply.** Five iterations at
   64 environments showed the diagnostic sign immediately: mean episode
   length *rising* (12 → 72) instead of falling.

## Reproducibility notes

- MJX/Warp-based Isaac-style env, PPO, 64 envs for smoke / default population
  for full runs, seed fixed across runs. Exact task configs live in the
  private upstream project; the pattern above is implementation-independent.
- Eval separated from training reward: 3 domain-randomization conditions ×
  50 episodes, decision-grade gates (takeoff, full rotation, two-foot
  landing, stability, unsafe contacts), per-episode manifests with
  checkpoint hashes and git SHAs.
