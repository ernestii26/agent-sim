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
nobody in the room. Measured on named dimensions of a leader concept (strength,
tyranny, sensitivity…), not on one dimension per need.
_Avoid_: ideal, schema

**Prediction map**:
Which prototype dimensions a given need is expected to move. Many-to-many: one need
can reach several dimensions and one dimension can be reached by several needs.
_Avoid_: mapping, matching dimension

**Evaluation**:
How good a specific observed person would be as my leader. An absolute rating, so
every candidate can score high at once.
_Avoid_: effectiveness (the instrument key, not the concept), rating

**Endorsement**:
A respondent picking one person to lead, out of everyone else in the room. Forced
choice and zero-sum, which is what separates it from Evaluation.
_Avoid_: vote (the mechanism, not the concept), preference, support

**Electorate**:
The groups whose endorsements count towards a result. Never includes a group being
contrasted — those are the candidates, and a rival's ballot is not evidence about them.

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

**Fork**:
A throwaway copy of an agent, used so that answering an instrument never changes the
agent that goes on to discuss or endorse. Everything the agent has lived through carries
over; nothing the fork does comes back. A fork that cannot be made is an error, never a
measurement taken on the original.
_Avoid_: clone, copy

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
