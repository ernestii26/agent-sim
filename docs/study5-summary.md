% Study 5 on LLM Personas: What Replicated
% agent-sim / ffni_mediation
% 2026-10-20

# Conclusion

- **Half replicates:** prestige side yes, dominance side no
    - Prestige: 9/10 (arm A), 5/5 significant cells (arm B)
    - Dominance: 1/4 (arm A), none of the paper's effects (arm B)
- **Prestige success is partly OCEAN:** removing it drops r from .34-.63 to .05-.24
- **Dominance fails on model consensus:** domineering = ineffective for every persona
- **Step 2:** prestige testable with OCEAN controlled; dominance exploratory

::: notes

**結論先講：只有一半成功。**

- Prestige 側（vision、expertise、fairness 預測聲望型領導）有複製出來，方向和論文一樣。
- Dominance 側（protection、status 預測支配型領導）沒有複製出來。B 組 dominance 側成功的兩格，都是「論文不顯著、我們也不顯著」，不算預測到東西。

**但 prestige 側的成功要打折扣。** 每份量表都由 persona 的新分身填，分身之間只共用 OCEAN 和描述文字。需求和結果會相關，主要是因為兩者都跟著 OCEAN 走；扣掉 OCEAN 之後相關幾乎消失。這是假設，還沒直接驗證。

**Dominance 側失敗**，是因為 gpt-4.1 的所有 persona 都一致認為霸道、自戀的領導沒有效（narcissism 平均 1.48/7，SD 0.21），分數沒有個體差異，需求就沒有東西可以預測。

**對 Step 2 的意義**：prestige 側的假設可以測，但要控制 OCEAN；dominance 側的假設只能當探索性結果。

:::

# Where we differ from Study 5, and what it explains

| Difference | Study 5 | Ours | Explains |
|------------------------|---------------------------|-----------------------------------|----------------------------------------|
| Respondents | People | gpt-4.1 personas, temperature 0 | Few sources of individual difference |
| Individual differences | Life history, culture | OCEAN levels + one description | Prestige side follows OCEAN |
| Model values | Varied opinions | One shared consensus | Floor and ceiling on dominance side |
| Answering | Same person, all scales | Fresh fork per scale | Needs lose shared variance (r −.50 to .70 vs .21 to .72) |
| 5c language | Chinese, China | English | Some arm B cells may not transfer |

::: notes

**最根本的差異**：真人的個體差異來源很多，persona 只有「OCEAN 加一段描述」，而模型本身又有一致的價值觀。所以 OCEAN 能連起來的效果就做得出來，連不起來的就做不出來。

- **受試者**：temperature 0，同樣輸入幾乎同樣答案，變異只來自 persona 文字。
- **模型價值觀**：對齊訓練讓所有 persona 都認為「領導要強」（strength 7.75/10，SD 0.39）、「霸道沒有效」，造成 dominance 側的天花板和地板。
- **作答方式**：真人填所有量表時有共同的作答風格（例如習慣勾高分），會讓六種需求全部正相關。我們每份量表由新分身填，沒有這股共同成分，所以 protection、status 和其他需求脫鉤，status–fairness 甚至是 −.50。這一點是推論，沒有直接測試。
- **語言**：5c 是中國樣本，華人對家長式、威權式領導的接受度可能不同，B 組有幾格不一致可能和這有關，現有數據無法區分。

樣本數（261 / 367）和分析方法（六個需求同時放進迴歸）都和論文一樣。

:::

# Method: two arms, neutral personas, no meeting

| Arm | Compares with | N | Measures |
|--------|-----------------------|------|----------------------------------------------------------|
| A | Table 13 (5a) | 261 | FFNI, generic instruction; then ILT, 51 items, 1-10 |
| B | Table 3, Model 2 (5c) | 367 | FFNI, work instruction; then 57 leader descriptions, 1-7 |

::: notes

- 中立的 bank persona，沒有 P/D traits，平均分散在 243 種 OCEAN 組合，不開會。
- 每份量表都由新的分身填。
- 每個結果都對六個需求做迴歸，報告標準化 β，p 來自 ΔR² 的 F 檢定。
- **判定成功**：論文顯著 → 我們同方向且 p < .05；論文不顯著 → 我們 p ≥ .05。
- 後面表格的「Paper β*」：β 旁有 * 代表論文顯著。

和論文一樣分兩組，各自用不同的 persona：A 組對應 5a（需求預測領導原型），B 組對應 5c（需求預測領導有效性）。

persona 是 bank 裡 ffni_mediation 沒用到的列，沒有 P/D traits，也不開會。gpt-4.1，temperature 0。

判定標準是逐格比對，不做多重比較校正，和論文一樣。

:::

# Arm A results (1/2): dominance and vision

| Need → ILT dimension | Side | Paper β* | Our β | p | Replicates |
|-----------------------------|-----------|---------|-------|--------|------------|
| Protection → strength | Dominance | .26* | .04 | .557 | No |
| Status → tyranny | Dominance | .32* | .28 | < .001 | Yes |
| Status → masculinity | Dominance | .19* | .07 | .368 | No |
| Status → well-groomed | Dominance | .30* | .08 | .272 | No |
| Vision → sensitivity | Prestige | .20* | .09 | .025 | Yes |
| Vision → dedication | Prestige | .30* | .41 | < .001 | Yes |
| Vision → charisma | Prestige | .19* | .22 | .002 | Yes |
| Vision → creativity | Prestige | .24* | .18 | .010 | Yes |

::: notes

A 組：需求預測 ILT 領導原型（Table 13），共 14 格，成功 10 格。

Dominance 側 4 格只成功 1 格（status → tyranny）。protection → strength 失敗，因為 strength 有天花板：平均 7.75/10，SD 只有 0.39，大家都認為領導要強。

Vision 的 4 格全部成功。

:::

# Arm A results (2/2): expertise and fairness

| Need → ILT dimension | Side | Paper β* | Our β | p | Replicates |
|-----------------------------|-----------|---------|-------|--------|------------|
| Expertise → sensitivity | Prestige | .32* | .12 | .005 | Yes |
| Expertise → charisma | Prestige | .22* | .15 | .036 | Yes |
| Expertise → intelligence | Prestige | .21* | .27 | .001 | Yes |
| Fairness → dedication | Prestige | .25* | .20 | .033 | Yes |
| Fairness → intelligence | Prestige | .26* | .11 | .261 | No |
| Fairness → ethics | Prestige | .29* | .16 | .032 | Yes |
| **Total** | | | | | **10/14** |
| Dominance side | | | | | 1/4 |
| Prestige side | | | | | 9/10 |

::: notes

Prestige 側 10 格成功 9 格，只有 fairness → intelligence 沒過。

:::

# Arm B results (1/2): dominance side

| Need → effectiveness of | Paper β* | Our β | p | Replicates |
|--------------------------------|---------|-------|--------|------------|
| Protection → safety | .05 | .22 | < .001 | No |
| Protection → authoritarianism | .01 | −.11 | .077 | Yes (null) |
| Status → narcissism | .04 | .07 | .240 | Yes (null) |
| Status → authoritarianism | −.02 | .14 | .038 | No |
| Status → dominance | .02 | .14 | .038 | No |
| **Dominance side** | | | | **2/5, both nulls** |

::: notes

B 組：需求預測 57 段領導描述的有效性（Table 3 Model 2），共 13 格，成功 8 格。

論文在 dominance 側的 5 格全部不顯著。我們成功的 2 格也是「不顯著對不顯著」，不代表預測到東西。

反而有 3 格是我們顯著、論文不顯著。不過 status 那兩格 p = .038，在 13 個沒校正的檢定裡，證據很弱。

這些結果量表都在地板：narcissism 平均 1.48/7（SD 0.21）、dominance 1.81（0.30）、authoritarianism 2.11（0.29）。

:::

# Arm B results (2/2): prestige and other

| Need → effectiveness of | Paper β* | Our β | p | Replicates |
|--------------------------------------|---------|-------|--------|------------|
| Affiliation → benevolence | .10* | .67 | < .001 | Yes |
| Affiliation → team-building | .36* | .56 | < .001 | Yes |
| Vision → vision communication | .18* | .31 | < .001 | Yes |
| Vision → high-expectation | .10 | .31 | < .001 | No |
| Expertise → competence | .08 | .16 | .017 | No |
| Expertise → intellectual stimulation | .13* | .42 | < .001 | Yes |
| Fairness → moral character | .25* | .17 | .013 | Yes |
| Fairness → virtue | .08 | .08 | .096 | Yes (null) |
| **Total** | | | | **8/13** |

::: notes

論文顯著的 5 格全部成功，其中 4 格效果比論文大。

affiliation 的效果特別大（benevolence β = .67，論文只有 .10），因為 affiliation 和 persona 的親和性設定相關 r = .89，幾乎是同一個變項。

失敗的 2 格（high-expectation、competence）是我們顯著、論文不顯著：效果太強，不是太弱。

:::

# Why the prestige side replicates: OCEAN (hypothesis)

| Paper cell | Side | r | r, OCEAN removed | r of OCEAN parts | Replicates |
|----------------------------------|----------------|-----------|------------------|------------------|---------------|
| A: protection → strength | Dominance | .01 | .06 | −.06 | No |
| A: status → tyranny | Dominance | .31 | .22 | .48 | Yes |
| A: status → masculinity | Dominance | .08 | .08 | .08 | No |
| A: status → well-groomed | Dominance | .07 | .01 | .15 | No |
| A: 10 prestige cells | Prestige | .34 to .63 | .05 to .24 | .56 to .97 | 9/10 |
| B: 9 prestige and other cells | Prestige | .32 to .82 | .15 to .32 | .64 to .95 | 6/9 |


::: notes

用 `tools/ocean_confound.py`，把每個需求和每個結果都對 OCEAN 做迴歸，看兩者被 OCEAN 預測出來的部分有多相關（「r of OCEAN parts」這一欄）。

- **Prestige 側**：需求和結果被同一組 OCEAN 特質推動（.56-.97），扣掉 OCEAN 後相關大幅下降。所以這裡的成功，很大一部分是 persona 設定前後一致。
- **Dominance 側**：需求和結果被不同的特質推動，或沒有特質推動（−.06 到 .48），沒有共同來源，就連不起來。唯一成功的 status → tyranny，正好是共用 OCEAN 最多的一格（.48）。

**限制**：描述文字沒有建模，所以「扣掉 OCEAN 後」剩下的相關可能有一部分來自描述文字。直接的驗證方法是固定 OCEAN、只改描述，需要另外花 API。

:::
