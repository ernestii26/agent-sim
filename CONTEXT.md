# agent-sim

A framework for running social-psychology experiments on LLM personas: a room of agents
discusses a scenario, then votes for a leader. The framework knows nothing about any
particular research theme — themes live in `studies/<name>/`.

## Language

### Influence strategies

**Prestige**:
Influence that followers confer freely, in response to demonstrated competence.
_Avoid_: expert leadership, soft power

**Dominance**:
Influence that a leader claims by controlling the room and making disagreement costly.
_Avoid_: authoritarian, aggressive, strong leadership

**Style block**:
The fixed text that assigns an influence strategy to a persona. Identical for every
member of a group, so the manipulation is a constant and only personality varies.

### Follower needs

**Follower need**:
Something a follower wants a leader to supply. There are six, and the term alone is
ambiguous between the two readings below — always qualify it.

**Chronic need**:
How much a respondent wants that thing as a standing disposition, independent of the
situation. This is what the source paper measures, and what its dominance-side null
is a null about.
_Avoid_: baseline need, trait need, need level

**Induced need**:
How far the situation moved a respondent's need, measured within-persona from before
the scenario to after. A quantity the source paper conceptualises but never measures.
_Avoid_: delta, state need, need change

### The four layers

**Need**:
What I want from a leader. Asked about the respondent, naming nobody.

**Prototype**:
What counts as "a leader" in general. Asked about the category, explicitly naming
nobody in the room.
_Avoid_: ideal, ILT, implicit leadership theory, schema

**Evaluation**:
How good a specific observed person would be as my leader. An absolute rating, so
every candidate can score high at once.
_Avoid_: effectiveness (the instrument key, not the concept), rating

**Endorsement**:
A respondent picking one person to lead, out of everyone else in the room. Forced
choice and zero-sum, which is what separates it from Evaluation.
_Avoid_: vote (the mechanism, not the concept), preference, support

### Study structure

**Study**:
A complete experimental design — groups, personas, scenarios, hypotheses — living in
one directory. Never encoded in `src/`.

**Condition**:
One scenario a study puts to the room. Conditions within a study share their personas
and differ only in the situation described.

**Run**:
One simulated meeting: a cast is drawn, discusses for some rounds, then endorses.

**Cast**:
The agents in one run. Drawn per run for sampled groups, fixed for the rest.

**Matched pair**:
A Prestige persona and a Dominance persona built from the same bank row, so they are
identical in personality, occupation, age and parental status by construction. Only
their style block differs.
_Avoid_: balanced pair, twin

**Bank**:
The 3,645-persona factorial store that matched pairs are built from.

**Manipulation check**:
An instrument whose only job is to show a condition felt the way it was meant to. It
is not a dependent variable and never names a leader or a person.
