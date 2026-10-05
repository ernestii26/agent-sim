## Step 1: Build personas and verify that show P and D traits

### Sample Method

Sample 160 rows from the 3,645 in `personas_output.json`, each with a different OCEAN profile, and build 200 personas from them: 40 casts of 1P + 1D + 3N, one cast per run. P_i and D_i are built from the same row, so the only difference between them is their traits.

Each persona keeps the row's `OCEAN` as `big_five` and `description_en` as `description`. P and D personas also get `traits`, adapted from Ronay et al. (2023) Table 2, Study 3. Neutral personas have no `traits` field.

<details>
<summary>Example: D1 (Dominance)</summary>

```
{
  "type": "TinyPerson",
  "persona": {
    "name": "Participant 122",
    "age": "not specified",
    "nationality": "not specified",
    "occupation": "not specified",
    "personality": {
      "description": "This person is usually sociable and energetic, often initiating conversations, keeping a lively tone, and drawing others into the discussion. In daily routines, they tend to stay moderately organized while leaving room for flexibility, and they may try a few new approaches as long as familiar structure is still present. When faced with moral dilemmas, they are likely to consider how each option affects other people, lean toward the most compassionate and harmonious choice, and feel significant tension if any decision might hurt someone. In group discussions, they speak freely and warmly, but their anxious side can make them worry about saying the wrong thing, so they may seek reassurance and avoid sharp disagreement.",
      "big_five": {
        "openness": "medium",
        "conscientiousness": "medium",
        "extraversion": "high",
        "agreeableness": "high",
        "neuroticism": "high"
      },
      "traits": [
        "has assertively moved up the ranks into positions of leadership",
        "prioritizes having control and authority over others",
        "makes quick and definitive decisions, and once a decision is made it is usually final",
        "has their own views of how tasks should be accomplished",
        "uses reward and punishment to get people to follow their ideas"
      ]
    }
  },
  "persona_id": "D1"
}
```

</details>

### Persona Checking Method

Neutrals rate the P and D they just watched on Cheng, Tracy & Henrich's (2010) peer-rated Dominance and Prestige scales (16 items; one item omitted 
  following Cheng et al., 2013, for briefly acquainted groups). 20 runs per condition. Passes when, in each condition, D > P on dominance and P > D on 
  prestige (paired t-test, two-sided p < .05).

### Results

`gpt-4.1`, 10 runs per condition, 3 rounds per run, no votes. Data: `results/dp_check/`.

| Condition | Scale | Expected | D | P | t | p (two-sided) | d_av | ICC(1,1) | |
|---|---|---|---|---|---|---|---|---|---|
| Routine | Dominance | D > P | 2.77 | 1.90 | 5.16 | .0006 | 1.14 | .71 | Pass |
| Routine | Prestige | P > D | 4.51 | 4.45 | -0.34 | .74 | -0.15 | .31 | Fail |
| Threat | Dominance | D > P | 3.15 | 1.77 | 2.96 | .016 | 1.74 | .95 | Pass |
| Threat | Prestige | P > D | 4.32 | 4.64 | 2.16 | .059 | 0.92 | .36 | Fail |

- **D, P**: mean score on the 1-7 scale (reverse-keyed items flipped). Each target's score is the mean of its three neutral raters.
- **t, p**: paired t-test over runs (one run = one P/D pair), two-sided.
- **d_av**: effect size, the mean difference in the expected direction divided by the mean of the two SDs. Comparable to the between-subjects d in Ronay et al. (2023).
- **ICC(1,1)**: agreement between the three neutrals rating the same target.

Comparison with Ronay et al. (2023), in-study manipulation checks:

| | D on dominance | P on dominance | Dominance d | Prestige d |
|---|---|---|---|---|
| Ronay Study 2 (Table 4, N = 400) | 4.66 | 3.48 | 1.26 | 0.69 |
| Ronay Study 3 (Table 6, N = 494) | 5.59 | 3.42 | 2.08 | 0.96 |
| This check, routine | 2.77 | 1.90 | 1.14 | -0.15 |
| This check, threat | 3.15 | 1.77 | 1.74 | 0.92 |

Verdict: fails the pre-set criterion (all four tests must pass). We proceed with these personas anyway.

## FFNI experiment 
The experiment is inspired by Implicit Leadership Theories and the future research raise in Sheng et al. (2026).
According to the Study 5 of Sheng etal. (2026), FFN can predict people's perspective towards leader in two level.
- Cognition: How should the leader look like.(ILT / Leader Prototype)
- Perception: How effectiveness you think in this leadership style.(Effectiveness)


### Sheng et al. (2026), Study 5

Source: Sheng, Andrews & van Vugt (2026), *Journal of Applied Psychology, 111*(6), pp. 785-790 and Table 3 (p. 775). PDF: `docs/2027-27008-001.pdf`.

Study 5 asks what the six follower needs predict. It looks at two levels: the leader prototype (ILT, cognition) and perceived leadership effectiveness (perception). Each part uses a different sample, and all three parts are correlational.

**Method**

| Part | Sample | Measures | Analysis |
|---|---|---|---|
| 5a. FFN → ILT | B: United States, N = 261 (the fourth of four random groups from Sample B's 1,035; only this group took the ILT, p. 777) | FFNI (generic); ILT: Offermann & Coats (2018), 51 trait words, 11 dimensions, 1-10 ("not at all" to "extremely characteristic of a leader") | Hierarchical regression (ΔR² of each need over the other five) and relative weights |
| 5b. FFNI vs. older need measures | D: United Kingdom, N = 295 | FFNI (work), need for leadership, fundamental social motives, basic psychological needs, ILT | Hierarchical regression: ΔR² of FFNI over the older measures |
| 5c. FFN → effectiveness | E: China, N = 396 at T1, 367 at T2 | T1: FFNI (work). T2, one week later: about 50 leadership descriptions rated "as effective if these individuals were your own leaders", 1-7 | Preregistered regressions, each need alone (Model 1) and controlling for the other five (Model 2) |

The 50 descriptions in 5c were adapted from paternalistic leadership (Cheng et al., 2004, 2014), transformational leadership (Wang & Howell, 2010) and status attainment (Bai et al., 2020).

**Results: 5a, needs → ILT** (Table 13: standardised β with the other five needs in the model, and unique ΔR² over them)

| Need | ILT dimensions it uniquely predicts, β (ΔR²) | Side of the dual model |
|---|---|---|
| Protection | strength .26 (.03) | Dominance |
| Status | tyranny .32 (.06), masculinity .19 (.02), well-groomed .30 (.05) | Dominance |
| Vision | sensitivity .20 (.01), dedication .30 (.03), charisma .19 (.01), creativity .24 (.02) | Prestige |
| Expertise | sensitivity .32 (.04), charisma .22 (.02), intelligence .21 (.02) | Prestige |
| Fairness | dedication .25 (.03), intelligence .26 (.03), ethics .29 (.04) | Prestige |

β and ΔR² come from the same test (ΔR² = squared semipartial correlation, F = t²), so they share a p-value. Compare β here with Model 2 β in 5c, not ΔR².

**Results: 5b.** FFNI adds variance on every ILT dimension beyond the older need measures. This holds whether they are entered separately or together.

**Results: 5c, needs → effectiveness** (Table 3, β)

| Need → effectiveness of | Model 1 (need alone) | Model 2 (other needs controlled) |
|---|---|---|
| Protection → safety | .20*** | .05 |
| Protection → authoritarianism | −.01 | .01 |
| Status → narcissism / authoritarianism / dominance | .03 / −.02 / −.05 | .04 / −.02 / .02 |
| Affiliation → benevolence / team-building | .31*** / .46*** | .10* / .36*** |
| Vision → vision communication | .32*** | .18** |
| Expertise → intellectual stimulation | .31*** | .13* |
| Fairness → moral character | .36*** | .25*** |

**The gap.** See *Research gaps* below.

**How this study maps onto ours**

| Sheng et al. Study 5 | `ffni_mediation` |
|---|---|
| FFNI | `ffni` (respondents: N, at baseline and post) |
| ILT, Offermann & Coats (2018), 51 items, 1-10 | `ilt` (prototype level) |
| Effectiveness, their instruction and 1-7 anchors | `effectiveness` (evaluation level) |
| Effectiveness of ~50 written descriptions | Effectiveness of the P and D the rater just watched, one item each |
| No situation manipulated | Threat vs. routine HiddenBench pools |
| Prototype and effectiveness in different samples | Both levels from the same neutrals in the same run |

### Research gaps

<details>

<summary>**Gaps the paper names**</summart>

**G1. Needs shape the prototype but not the evaluation.**

> "Contrary to expectations, the FFNs for protection and status failed to predict perceived effectiveness of dominance-based leadership styles (e.g., authoritarianism, narcissism, dominance), despite their established relationships with dominance-based ILT (strength, tyranny, masculinity, well-groomed; as shown in Sample B)." (pp. 788-789)

Read on the same statistic at both levels (β with the other five needs controlled), the split is sharper than the prose says. Protection has a unique link to the Strength prototype (β = .26, Table 13). In Model 2 of Table 3 it has no unique link to the effectiveness of *any* style, including Safety, its closest match (.20*** alone, .05 controlled). Status is the same: β = .19 to .32 on three prototype dimensions, and .02 to .04 on the dominance-side effectiveness criteria.

**G2. Whether the situation moderates the link was never tested.**

> "For instance, would intergroup conflict situations (e.g., trade wars, organizational crises) strengthen the FFN protection–authoritarianism link?" (p. 789)

**G3. Follower needs are assumed to mediate, but this has not been tested.**

> "While prior research has shown, for example, that intergroup conflict increases preference for dominant leaders (Laustsen & Petersen, 2017; Laustsen et al., 2025; Spisak et al., 2012) … these studies often assume yet do not empirically test the mediating role of follower needs—likely due to a lack of validated measures." (p. 795)

**G4. The designs are correlational and the outcomes are not behaviour.**

> "Experimental vignette studies offer a useful method for manipulating contextual cues that reflect evolutionarily recurrent challenges and thereby activate specific follower needs. For example, intergroup conflict may heighten the FFN for protection (Laustsen & Petersen, 2017)" (pp. 795-796)

> "Third, our research relied entirely on self-report measures and correlational designs, limiting causal inference. … Future studies should use experimental manipulations (e.g., vignettes or simulations of threat, inequality, or uncertainty) to test how specific environmental cues activate FFNs and influence leadership evaluations." (p. 796)

> "Future research should also go beyond cognitive and perceptual outcomes to examine behavioral consequences of follower needs, such as voting in elections, leader support, resistance, or insubordination in organizational settings." (p. 795)

**Gaps we infer** (not claimed by the paper)

**G5. G1 is confounded with sample.** The prototype half comes from Sample B (United States, generic FFNI, N = 261), and the effectiveness half from Sample E (China, work FFNI, N = 367). The rated targets also differ: trait words in one, written descriptions in the other. The gap could come from country, version or target as much as from a difference between psychological levels. Measuring both levels on the same raters in the same run removes those readings.

**G6. No one has rated a leader they actually watched.** The 5c effectiveness ratings are of written descriptions. Rating a person just observed leading a group is untested on both sides of the dual model, not only the dominance side.
</details>


**Hypotheses and the gaps they answer** (full text in `studies/ffni_mediation/study.json`)

| H | Claim | Gap | Why it is needed |
|---|---|---|---|
| H1, H2 | Routine: P > D endorsement; threat: D > P | G4 (behaviour) | The vote is the behavioural outcome p. 795 asks for. H2 is exploratory: our threat is environmental disaster, not intergroup conflict |
| H3 | Threat raises protection need | G4 (manipulation) | The paper measured only stable antecedents. pp. 795-796 propose manipulating the cue |
| H4 | Needs predict prototype dimensions (Table 13) | Positive control | Reproduces a supported result first. If it fails, the environment is the problem, not the new hypotheses |
| H5 | Needs predict effectiveness of P and D (Table 3, Model 2) | G1, G5, G6 | Same raters, same run, observed targets. A protection-to-D null replicates G1. A non-null result would point to G5 or G6 |
| H5b | The same needs predict effectiveness of the paper's 57 descriptions (Table 3, Model 2), at baseline | G5 | Same stimulus as the paper, same raters as the prototype layer. Separates the dominance-side scales (authoritarianism, dominance, narcissism) that H5's single rating collapses. Items: `docs/sheng-2026-S10.1-effectiveness-items.md` |
| H6 | Protection need mediates condition → D endorsement | G3 | The paper names the gap but gives no estimator, so the estimator is ours |
| H7 | Threat strengthens protection → D effectiveness | G2 | Extends rather than replicates: environmental threat, not intergroup conflict |
| H7b | Threat strengthens protection → authoritarianism effectiveness (post, threat minus routine β, run-level bootstrap) | G2 | p. 789's question in its own words. The authoritarianism items target other departments, an outgroup our scenarios lack |

