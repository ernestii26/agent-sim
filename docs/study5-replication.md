% Sheng et al. (2026) Study 5, and Its Replication on LLM Personas
% agent-sim / ffni_mediation
% 2026-10-06

# Study 5 in one slide

- Source: Sheng, Andrews & van Vugt (2026), *J. Applied Psychology*, 111(6)
- Question: what do the six follower needs predict?
- Two levels of outcome
    - **Prototype** (cognition): what a leader *should* look like (ILT)
    - **Effectiveness** (perception): how well a leadership style works
- 5a: needs → prototype · 5b: FFNI vs. older need measures · 5c: needs → effectiveness
- All parts are correlational, each on a different sample

::: notes

**這份投影片講兩件事**：(1) Sheng et al. (2026) 的 Study 5 做了什麼；(2) 我們把 Study 5 搬到 LLM persona 上重做一遍，結果如何。

Study 5 想回答的問題是：**追隨者的六種需求，能不能預測他們對領導者的看法？**「看法」分兩個層次：

- **原型（prototype）**：腦中「領導者應該長什麼樣子」，用 Implicit Leadership Theories（ILT）量表來測，屬於認知層次。
- **有效性（effectiveness）**：看到一種領導方式時，覺得它「有多有效」，屬於知覺／評價層次。

Study 5 分三部分：

- 5a：需求 → 原型
- 5b：證明 FFNI 比舊的需求量表多解釋了東西
- 5c：需求 → 有效性

這份投影片只講 5a 和 5c，因為我們 replicate 的是這兩部分。

要先記住兩點：三個部分**各用不同的樣本**，而且**都是相關研究**，沒有操弄任何變項。後面講 gap 的時候，這兩點會很重要。

:::

# Study 5 at a glance

| Part | Sample | Measures | Analysis |
|--------|--------------------------|----------------------------------------|--------------------------|
| 5a | B: US, N = 261 | Generic FFNI; ILT, 51 trait words, 11 dimensions, 1-10 | Hierarchical regression (ΔR²), relative weights |
| 5b | D: UK, N = 295 | Work FFNI, older need measures, ILT | ΔR² of FFNI over older measures |
| 5c | E: China, N = 396 (T1), 367 (T2) | T1 work FFNI; T2 (+1 week) ~50 descriptions rated for effectiveness, 1-7 | Preregistered regressions, Model 1 and Model 2 |

::: notes

三個部分的總覽。重點是**三個樣本都不一樣**：5a 是美國人，5b 是英國人，5c 是中國人。這份投影片只講 5a 和 5c，後面會逐一說明。

:::

# The predictors: six follower needs (FFNI)

- **Protection**: shield me from threats → Dominance side
- **Status**: raise my group's standing → Dominance side
- **Affiliation**: keep the group together
- **Vision**: show us where to go → Prestige side
- **Expertise**: know what you are doing → Prestige side
- **Fairness**: treat people justly → Prestige side
- Instruction versions: *generic* ("leaders in your life"), *work* ("leaders in your WORK ORGANIZATION")

::: notes

**FFNI 量的是「追隨者希望領導者提供什麼」**，總共 22 題，分成六個需求。

對照「雙路徑模型」（dual model）：

- **Dominance 側**：protection 和 status。直覺上，需要被保護、想提升地位的人，應該會偏好強勢、支配型的領導者。
- **Prestige 側**：vision、expertise、fairness。需要方向、專業、公平的人，應該會偏好有真本事、讓人自願追隨的領導者。
- **Affiliation**：論文沒有把它明確歸到哪一側。

FFNI 有不同的**指導語版本**，題目一樣，只是問的對象不同。generic 版問「你生活中的領導者」，work 版問「你工作組織裡的領導者」。5a 用 generic 版，5c 用 work 版，這也是兩者的差異之一。

**一個重要的數字**：人類樣本中，六個需求彼此正相關，Sample B 的範圍是 .21 到 .72，多數在 .5-.7（Table 8）。也就是說，一個人如果某個需求高，通常其他需求也高。注意：論文內文（p. 787）寫的是「.60 to .72」，和它自己的 Table 8 對不起來，以表為準。這決定了後面分析為什麼一定要「控制其他五個需求」。

:::

# 5a: needs → leader prototype (design)

- Sample B: United States, N = 261 (p. 777)
- One sitting: generic FFNI, then ILT
- ILT (Offermann & Coats, 2018): 51 trait words, 11 dimensions, 1-10
- Dominance side: strength, tyranny, masculinity, well-groomed
- Prestige side: sensitivity, dedication, charisma, creativity, intelligence, ethics

::: notes

**5a 的設計很單純**：美國受試者在同一次填答中，先填 FFNI，再填 ILT 量表。

**ILT 量表怎麼填**：給你 51 個形容詞，例如 *strong*、*domineering*、*intelligent*、*honest*。每個詞問你「這個特質有多像一個領導者」，1 分是完全不像，10 分是極度像。

51 個詞被歸成 11 個維度。論文把它們對應到雙路徑模型：

- **Dominance 側**：strength（強壯）、tyranny（專橫）、masculinity（陽剛）、well-groomed（體面）
- **Prestige 側**：sensitivity（體貼）、dedication（投入）、charisma（魅力）、creativity（創意）、intelligence（聰明）、ethics（道德）
- 另外還有 femininity，沒有對應到哪一側

**樣本數的細節**：Sample B 總共 1,035 人，但被隨機分成四組，只有第四組（261 人）填了 ILT。所以 5a 的有效 N 是 261，我們的 arm A 也照這個數字來。

:::

# 5a: analysis, why every need is controlled

- One regression per ILT dimension, all six needs entered together
- Needs intercorrelate .21-.72 (Table 8), so *every* bivariate r is significant
- Only the increment over the other five separates them
- Reported per cell: standardised **β** and unique **ΔR²**
- ΔR² F test, df (1, n − 7): β and ΔR² share one p-value
- Relative-weights analysis as a complement

::: notes

**為什麼不直接看相關係數**：六個需求彼此相關 .21-.72，多數在 .5-.7。所以只要某個需求和 tyranny 有關，其他五個需求也會因為和它高度相關，而跟著和 tyranny 有關。論文 Table 13 的相關係數那一欄，每個需求和每個 ILT 維度都在 p < .001 顯著，完全分不出是哪個需求在起作用。

**解法**：把六個需求**同時**放進回歸，看每個需求「扣掉其他五個之後還剩多少」。

**β（標準化迴歸係數）**：其他五個需求都固定時，這個需求高 1 個標準差，ILT 分數平均高幾個標準差。標準化之後沒有單位，所以不同量尺的研究可以互相比較。

**ΔR²**：完整模型的 R²，減掉拿掉這個需求之後的 R²，也就是這個需求「獨有」的解釋力。

**p 值怎麼算**：

F = ΔR² ÷ [(1 − R²_full) / (n − 7)]

在「效果為 0」的假設下，F 服從自由度 (1, n − 7) 的 F 分佈。p 就是這個分佈裡比觀察到的 F 更極端的面積。n − 7 是因為有 6 個斜率加 1 個截距。

只檢定一個變項時，F = t²，所以 β 和 ΔR² 共用同一個 p。

**p 的意思**：假設真的沒有效果，資料仍然這麼極端的機率。它**不是** likelihood，也**不是**「沒有效果的機率」。

:::

# 5a: results (Table 13)

| Need | ILT dimensions it uniquely predicts, β (ΔR²) | Side |
|--------------|----------------------------------------------------------|--------------|
| Protection | strength .26 (.03) | Dominance |
| Status | tyranny .32 (.06), masculinity .19 (.02), well-groomed .30 (.05) | Dominance |
| Vision | sensitivity .20 (.01), dedication .30 (.03), charisma .19 (.01), creativity .24 (.02) | Prestige |
| Expertise | sensitivity .32 (.04), charisma .22 (.02), intelligence .21 (.02) | Prestige |
| Fairness | dedication .25 (.03), intelligence .26 (.03), ethics .29 (.04) | Prestige |

::: notes

**結論是兩側都成立**：

- Dominance 側的需求（protection、status）預測 dominance 側的原型（strength、tyranny、masculinity、well-groomed）。
- Prestige 側的需求（vision、expertise、fairness）預測 prestige 側的原型。

每個需求都找到了「自己的」維度。

**ΔR² 看起來很小（.01-.06），為什麼還算數**：因為這是在扣掉其他五個高度相關的需求之後，**剩下的獨有部分**。大部分的解釋力被六個需求共享，所以任何一個需求獨有的部分本來就不會多。

**Affiliation 不在這張表上**：論文中 affiliation 對全部 11 個 ILT 維度的 ΔR² 都只有 .00-.01。後面會看到，這一點在 LLM 上完全不一樣。

:::

# 5c: needs → perceived effectiveness (design)

- Sample E: China, in Chinese, preregistered (AsPredicted)
- T1: work FFNI (N = 396)
- T2, one week later: ~50 leadership descriptions (N = 367)
- "How effective would these individuals be as your own leaders?" 1-7
- Model 1: the need alone · **Model 2**: other five needs controlled

::: notes

**5c 和 5a 的流程不同**：

- **分兩個時間點**。T1 填需求，一週後的 T2 才評有效性。目的是降低「同一次填答」造成的共同方法偏誤：如果同時填兩份問卷，當下的心情或回答習慣可能讓兩邊人為地相關。
- **評分對象是一段行為描述**，不是單一形容詞。例如一條 authoritarianism 的描述是 "Very strict with staff of other departments/divisions"（注意對象是**其他部門**的人，不是自己的下屬）。受試者評「如果這個人是你的領導，他有多有效」，1 到 7 分。

（描述涵蓋哪些領導風格，在下一頁。）

:::

# 5c: what the descriptions cover

- **Paternalistic** (Cheng et al.): authoritarianism, benevolence, moral character
- **Transformational** (Wang & Howell): vision communication, intellectual stimulation, team-building, high-expectation
- **Status attainment** (Bai et al.): dominance, narcissism, competence, virtue
- Full items: `docs/sheng-2026-S10.1-effectiveness-items.md` (57)

::: notes

描述來自三套理論：

- **家長式領導（paternalistic）**：Cheng 等人提出，華人組織常見。包括威權（authoritarianism）、仁慈（benevolence）、德行（moral character）。
- **轉換型領導（transformational）**：Wang & Howell。包括願景溝通、智力激發、團隊建立、高期望。
- **地位取得（status attainment）**：Bai et al.。包括 dominance、narcissism（自戀）、competence、virtue。

完整題目在 `docs/sheng-2026-S10.1-effectiveness-items.md`，我們整理出來是 57 條。

樣本是中國人，用中文作答，T1 有 396 人，T2 剩 367 人。

:::

# 5c: results (Table 3)

| Need → effectiveness of | Model 1 (need alone) | Model 2 (others controlled) |
|--------------------------------------------|----------------------|----------------------|
| Protection → safety | .20\*\*\* | .05 |
| Protection → authoritarianism | −.01 | .01 |
| Status → narcissism / authoritarianism / dominance | .03 / −.02 / −.05 | .04 / −.02 / .02 |
| Affiliation → benevolence / team-building | .31\*\*\* / .46\*\*\* | .10\* / .36\*\*\* |
| Vision → vision communication | .32\*\*\* | .18\*\* |
| Expertise → intellectual stimulation | .31\*\*\* | .13\* |
| Fairness → moral character | .36\*\*\* | .25\*\*\* |

::: notes

**Model 1 vs Model 2**：

- Model 1 只放一個需求，相當於看相關。
- Model 2 六個需求一起放，相當於 5a 的做法。

要和 5a 比較，看的是 **Model 2**，因為兩者用的是同一種統計量。

**Prestige 側全部成立**：affiliation、vision、expertise、fairness 都預測了理論上對應的領導風格，控制其他需求之後仍然顯著。

**Dominance 側全部不成立**：

- Protection → safety 是最值得注意的一格。單獨看時是 .20，非常顯著；但控制其他五個需求後掉到 .05。也就是說，那 .20 是其他需求「帶進來」的，protection 本身沒有獨特的貢獻。
- Protection、status 對 authoritarianism、narcissism、dominance 的有效性完全沒有預測力，β 都接近 0。

論文作者自己也說這個結果 "contrary to expectations"。

:::

# The gap (G1): prototype yes, evaluation no

| Needs | → prototype (5a) | → effectiveness (5c) |
|------------------------------|----------------------------|----------------------------|
| Dominance side (protection, status) | Yes | **No** |
| Prestige side (vision, expertise, fairness) | Yes | Yes |

- Same statistic at both levels: β, other five needs controlled
- Paper's reading: protection and status shape the prototype but not the evaluation (pp. 788-789)

::: notes

**把 5a 和 5c 放在一起看**：

- Dominance 側：原型有、有效性沒有。
- Prestige 側：原型有、有效性也有。

論文的解讀（pp. 788-789）是：protection 和 status 會影響「領導者應該長什麼樣子」，但不會讓人覺得 dominance 型的領導「有效」。

（下一頁講我們對這個解讀的質疑。）

:::

# Our reading (G5): 5a and 5c differ on everything at once

|  | 5a (prototype) | 5c (effectiveness) |
|--------------------|--------------------------------|--------------------------------|
| Country, language | US, English | China, Chinese |
| FFNI version | Generic | Work |
| Rated target | Single trait words | Behaviour descriptions |
| Timing | One sitting | One-week gap |
| Respondents | Sample B | Sample E |

- Any of these could explain the gap as well as "two levels"

::: notes

**我們的質疑（G5，論文沒有提）**：5a 和 5c 同時在很多地方不同，包括國家、語言、FFNI 版本、評分對象、時間間隔，還有受試者本身。dominance 側在 5c 消失，可能真的是「原型和評價是兩種不同層次的心理歷程」，但也可能只是因為上面任何一項不同。

例如，在華人組織文化裡，威權型領導可能本來就被普遍評為「不有效」，大家看法一致，個體差異很小，需求自然預測不了。

**這正是我們 Step 2 的設計理由**：讓**同一批 neutral、在同一個 run 裡**同時回答原型和有效性，把上面這些干擾因素都排除掉。

:::

# Why replicate on LLM personas first

- Step 2 tests H4, H5, H5b, H7b against Sheng et al.'s results
- Before reading those, check: do LLM personas reproduce Study 5 *at all*?
- If not, a Step 2 null cannot be read as a finding
- No meeting, no situation: only the questionnaires
- `tools/replicate_study5.py`, `gpt-4.1`, temperature 0; data in `results/replication/`

::: notes

**為什麼要先做這一步**：Step 2 的好幾個假設（H4、H5、H5b、H7b）都是拿論文的結果來比較的。如果 LLM persona 連最基本的 Study 5 都重現不出來，那 Step 2 出現的任何 null 結果都無法解讀：分不出是「真的沒有效果」，還是「這個環境本來就測不到」。

所以這一步拿掉所有東西：**沒有會議、沒有威脅情境**，只讓 persona 填問卷，看結果和論文像不像。

它的角色類似實驗裡的 **positive control**：先確認儀器能測到一個已知存在的效果，再去測未知的效果。

:::

# Replication: method

| Arm | Compares with | N | Measures |
|--------|----------------------|--------|------------------------------------------------|
| A | Table 13 (5a) | 261 | Generic FFNI, then ILT (51 items, 1-10) |
| B | Table 3, Model 2 (5c) | 367 | Work FFNI, then the 57 descriptions (1-7) |

- Personas: unused bank rows over the 243 OCEAN profiles; neutral (no P/D traits)
- Each instrument on a fresh fork; same analysis as the paper

::: notes

**兩個 arm 分別對應論文的兩部分**，樣本數也照論文：

- **Arm A**：261 個 persona，用 generic 指導語填 FFNI，再填 51 題的 ILT。
- **Arm B**：367 個 persona，用 work 指導語填 FFNI，再評 57 條領導描述的有效性。

**Persona 從哪來**：從 persona bank 裡挑 `ffni_mediation` 主實驗沒用到的列，平均分布在 243 種 OCEAN（Big Five）組合上。全部是 neutral，沒有 P/D 特質。

**Fresh fork**：每份問卷都在一個新的 fork 上作答。也就是說，persona 填 ILT 時，「記憶」裡沒有自己剛剛填過的 FFNI 答案。這是為了避免 LLM 為了「前後一致」而刻意讓答案互相呼應。

**分析完全照論文**：每個維度跑一次回歸，六個需求一起放，報告 β 和 ΔR² F 檢定的 p。

:::

# Replication: what counts as "replicates"

- Paper significant → ours has the **same sign** at p < .05
- Paper null → ours p ≥ .05
- No multiple-comparison correction, as in the paper
- Differences we cannot remove
    - Respondents are LLM personas, not people
    - Arm B is in English; Sample E answered in Chinese
    - No one-week gap: two separate sittings with nothing in between

::: notes

**判準**：

- 論文顯著的格子：我們也要 p < .05，而且 β 的方向相同。
- 論文不顯著的格子：我們 p ≥ .05 就算 replicate。

**這個判準的弱點，要先講清楚**：「p ≥ .05」只代表沒辦法排除效果為 0，不代表**證明**效果是 0。例如後面 Protection → authoritarianism 的 p = .077，β = −.11，被算作「Yes (null)」，但這其實只是「差一點顯著」。要真正主張「沒有效果」，需要等價檢定（例如 TOST）。所以表上的「Yes (null)」是比較弱的證據。

**沒做多重比較校正**：照論文的做法。但要記得，arm B 有 13 個檢定，就算全部都沒有真實效果，平均也會有 13 × .05 ≈ 0.65 個格子「碰巧」p < .05。

**無法消除的差異**：受試者是 LLM、arm B 是英文、沒有一週的間隔。

:::

# Arm A (Table 13), dominance side: 1 of 4

| Need → dimension | Paper β | Our β | p | Replicates |
|----------------------------------------|------------|------------|------------|--------------|
| Protection → strength | .26\* | .04 | .557 | No |
| Status → tyranny | .32\* | .28 | < .001 | Yes |
| Status → masculinity | .19\* | .07 | .368 | No |
| Status → well-groomed | .30\* | .08 | .272 | No |

- \* significant in the paper
- Dominance side: 1 of 4 replicates

::: notes

**Arm A 對應 Table 13**，14 格中有 10 格 replicate，拆成 dominance 側（這頁）和 prestige 側（下一頁）兩張表。這 14 格在論文裡全部顯著，所以判準都是「我們也要 p < .05 且方向相同」。

**失敗的 4 格裡，有 3 格在 dominance 側**：protection → strength、status → masculinity、status → well-groomed。dominance 側只有 status → tyranny 成功，而且效果大小和論文很接近（.28 vs .32）。

**舉兩個例子看 p 怎麼算出來的**：

- Status → tyranny：ΔR² = .042，R² = .315，F = .042 × 254 / .685 ≈ 15.6，p ≈ .0001。
- Protection → strength：ΔR² = .0009，R² = .314，F ≈ 0.35，p = .557。這個 F 落在 F 分佈的正中間，完全看不出效果。

:::

# Arm A (Table 13), prestige side: 9 of 10

| Need → dimension | Paper β | Our β | p | Replicates |
|----------------------------------------|------------|------------|------------|--------------|
| Vision → sensitivity | .20\* | .09 | .025 | Yes |
| Vision → dedication | .30\* | .41 | < .001 | Yes |
| Vision → charisma | .19\* | .22 | .002 | Yes |
| Vision → creativity | .24\* | .18 | .010 | Yes |
| Expertise → sensitivity | .32\* | .12 | .005 | Yes |
| Expertise → charisma | .22\* | .15 | .036 | Yes |
| Expertise → intelligence | .21\* | .27 | .001 | Yes |
| Fairness → dedication | .25\* | .20 | .033 | Yes |
| Fairness → intelligence | .26\* | .11 | .261 | No |
| Fairness → ethics | .29\* | .16 | .032 | Yes |

::: notes

**Prestige 側 10 格中有 9 格成功**，唯一失敗的是 fairness → intelligence（.11，p = .261）。合計 arm A 是 14 格中 10 格 replicate。

:::

# Arm B (Table 3, Model 2), paper-significant cells: 5 of 5

| Need → dimension | Paper β | Our β | p | Replicates |
|----------------------------------------|------------|------------|------------|--------------|
| Affiliation → benevolence | .10\* | .67 | < .001 | Yes |
| Affiliation → team-building | .36\* | .56 | < .001 | Yes |
| Vision → vision communication | .18\* | .31 | < .001 | Yes |
| Expertise → intellectual stimulation | .13\* | .42 | < .001 | Yes |
| Fairness → moral character | .25\* | .17 | .013 | Yes |

- \* significant in the paper: all 5 replicate, 4 with larger β

::: notes

**Arm B 對應 Table 3 Model 2**，13 格中有 8 格 replicate，拆成論文顯著的 5 格（這頁）和論文不顯著的 8 格（下一頁）。

**論文顯著的 5 格全部 replicate**，其中 4 格效果比論文大（fairness → moral character 是 .17，比論文的 .25 小）。例如 affiliation → benevolence，論文是 .10，我們是 .67。

（論文不顯著的 8 格在下一頁。）

:::

# Arm B, paper-null cells: 3 of 8

| Need → dimension | Paper β | Our β | p | Replicates |
|----------------------------------------|------------|------------|------------|--------------|
| Protection → safety | .05 | .22 | < .001 | No |
| Protection → authoritarianism | .01 | −.11 | .077 | Yes (null) |
| Status → narcissism | .04 | .07 | .240 | Yes (null) |
| Status → authoritarianism | −.02 | .14 | .038 | No |
| Status → dominance | .02 | .14 | .038 | No |
| Vision → high-expectation | .10 | .31 | < .001 | No |
| Expertise → competence | .08 | .16 | .017 | No |
| Fairness → virtue | .08 | .08 | .096 | Yes (null) |

::: notes

**論文不顯著的 8 格，只有 3 格維持不顯著**。失敗的 5 格是我們出現了論文沒有的效果：

- Protection → safety .22：論文控制其他需求後是 .05，我們仍然很顯著。另外要注意，safety 指的是**職場安全**（安全和產量、營收之間的取捨），不是保護群體免受威脅；它只有 3 題，α = .57。
- Status → authoritarianism、dominance 都是 .14，p = .038。p 剛好低於 .05，又是在 13 個未校正的檢定裡，所以證據很弱。
- Vision → high-expectation、expertise → competence：效果合理，只是論文沒有找到。

**整體來說，LLM persona 的效果偏大、偏「乾淨」**：需求和對應風格之間的連結比人類更強。

:::

# Reading 1: the prestige side reproduces

- Arm A: 9 of 10 vision, expertise and fairness cells
- Arm B: all 5 paper-significant cells, 4 with larger effects
- But much of it may run through the persona's OCEAN settings (Reading 6, a hypothesis)

::: notes

**第一個結論是好消息**：prestige 側在兩個 arm 都穩定重現。

表面上看，「需求 → prestige 原型」和「需求 → prestige 風格有效性」這兩條路在 LLM persona 上都測得到，可以當 Step 2 的 positive control。

但 Reading 6 會提出一個假設：這些相關有很大一部分來自 persona 的 OCEAN 設定，而不是需求本身。如果這個假設成立，prestige 側當 positive control 的價值會打折扣。

:::

# Reading 2: dominance-side outcomes sit at the floor or ceiling

| Arm | Dimension | Scale | M | SD |
|--------|------------------------------------|----------|----------|----------|
| A | Strength (prototype) | 1-10 | 7.75 | 0.39 |
| B | Narcissism (effectiveness) | 1-7 | 1.48 | 0.21 |
| B | Dominance (effectiveness) | 1-7 | 1.81 | 0.30 |
| B | Authoritarianism (effectiveness) | 1-7 | 2.11 | 0.29 |

- Ceiling in A (protection–strength r = .01), floor in B (R² .04-.09)
- Personas nearly agree, so little variance is left for any need to predict
- Not every failure fits: masculinity M 2.96, SD 0.89 on 1-10, yet r = .08

::: notes

**Dominance 側的結果變數卡在量尺邊緣。** README 原本把這當成失敗的原因，現在我們認為它比較可能是結果，見 Reading 6。

**天花板效應（arm A）**：strength 在 1-10 分裡平均 7.75，標準差只有 0.39。幾乎所有 persona 都給「強壯」很高的分數。protection 和 strength 的相關只有 .01，連控制其他需求之前都沒有關係。

**地板效應（arm B）**：narcissism、dominance、authoritarianism 在 1-7 分裡平均都只有 1.5-2.1，標準差 0.2-0.3。幾乎所有 persona 都覺得支配型領導「不有效」。

**為什麼這會讓效果消失**：回歸要找的是「需求高的人，分數是不是也比較高」。如果每個人的分數都差不多，結果變數就沒有變異可以解釋，任何預測變項都預測不了。

**但地板和天花板解釋不了全部**：masculinity 平均 2.96、標準差 0.89（1-10 分），分數有空間變動，但 status 和 masculinity 的相關還是只有 .08。所以應該有一個更根本的原因，同時解釋「沒有相關」和「分數擠在一起」。Reading 6 提出一個假設。

:::

# Reading 3: affiliation is the persona's agreeableness

- r(affiliation, agreeableness setting) = .89 in arm A
- Large unique effects the paper lacks
    - Arm A: sensitivity .74, ethics .45, tyranny −.41
    - Arm B: benevolence .67, virtue .58
- Paper: affiliation ΔR² = .00-.01 on all 11 ILT dimensions

::: notes

**Affiliation 幾乎等於 persona 的 agreeableness 設定**：兩者相關 .89。所以 affiliation 在回歸裡帶進了「這個 persona 有多 agreeable」，產生很多論文裡沒有的大效果，例如對 sensitivity 的 β = .74。affiliation → tyranny 的 β 甚至是 −.41，意思是越 agreeable 的 persona 越不認為領導者應該專橫。這些效果反映的是 persona 的設定方式，不是人類的需求結構。

（另外兩點差異在下一頁。）

:::

# Reading 4: need intercorrelations, dominance-side pairs

| Pair | Paper B (US, generic) | Arm A | Paper E (China, work) | Arm B |
|------------------------------|----------------------|------------|----------------------|------------|
| Protection–affiliation | .60 | .33 | .24 | .34 |
| Protection–status | .52 | .07 | .33 | −.06 |
| Protection–vision | .57 | .00 | .21 | .06 |
| Protection–expertise | .52 | −.01 | .20 | .06 |
| Protection–fairness | .49 | .29 | .39 | .41 |
| Affiliation–status | .38 | −.14 | .20 | −.10 |
| Status–vision | .42 | .09 | .19 | .10 |
| Status–expertise | .46 | −.07 | .22 | .01 |
| Status–fairness | .21 | **−.50** | .10 | **−.45** |

::: notes

**需求之間的相關結構不同，而且差異集中在 dominance 側。**

這張表是每一對需求的 Pearson 相關。論文數字取自 Table 8 的下三角：Sample B（美國，generic，N = 1,035）對照 arm A，Sample E T1（中國，work，N = 396）對照 arm B。我們的數字是每個需求取題目平均後算的。

**先更正一件事**：論文內文（p. 787）寫「r ranged from .60 to .72; see Table 8」，但 Table 8 裡 Sample B 的實際範圍是 .21 到 .72。我們之前的 README 照抄了內文，已經改掉。另外，論文沒有單獨報告做 ILT 的那 261 人的矩陣，所以拿全部 1,035 人來比。

**這一頁是有 protection 或 status 的 9 對**：

- **Protection**：在論文裡和每個需求都有 .49-.60 的相關；在 arm A 裡和 status、vision、expertise 幾乎是 0。
- **Status**：在論文裡全部正相關；在我們這裡和 affiliation、expertise、fairness 變成負的。
- **Status–fairness**：論文裡本來就是最低的一對（.21），LLM persona 把它推到 −.50。所以這不是全新的模式，而是論文模式的放大版。persona 似乎把「想要地位」和「想要公平」當成互相衝突的價值，人類則只是兩者比較不相關。

dominance 側正是 replication 失敗的那一側。

:::

# Reading 4: need intercorrelations, prestige cluster

| Pair | Paper B (US, generic) | Arm A | Paper E (China, work) | Arm B |
|------------------------------|----------------------|------------|----------------------|------------|
| Affiliation–vision | .72 | .39 | .37 | .37 |
| Affiliation–expertise | .67 | .52 | .35 | .47 |
| Affiliation–fairness | .69 | .64 | .38 | .64 |
| Vision–expertise | .64 | .70 | .34 | .65 |
| Vision–fairness | .65 | .46 | .31 | .39 |
| Expertise–fairness | .55 | .54 | .29 | .50 |
| **Range, all 15 pairs** | .21 to .72 | −.50 to .70 | .10 to .39 | −.45 to .65 |

::: notes

**Prestige 群組的相關保留得很好**：affiliation、vision、expertise、fairness 之間，論文是 .55-.72，arm A 是 .39-.70，大致相同。

**Sample E（中國）的相關本來就低很多**，全部只有 .10-.39。arm B 的 prestige 群組（.37-.65）反而比 Sample E 更像 Sample B。所以 arm B 拿來對照的 Sample E，需求結構本身就和美國樣本不同，這也是 G5 提到的國家差異之一。

最後一列是全部 15 對的範圍。

:::

# Reading 4: need means (1-7)

| Arm | Protection | Affiliation | Status | Vision | Expertise | Fairness |
|--------|--------------|--------------|--------------|--------------|--------------|--------------|
| A | 5.67 (0.87) | 5.21 (1.79) | 2.86 (1.07) | 5.69 (1.02) | 5.75 (0.87) | 6.55 (0.87) |
| B | 5.55 (0.88) | 5.25 (1.82) | 3.02 (1.06) | 5.82 (0.99) | 5.84 (0.87) | 6.56 (0.86) |

- M (SD) per need
- Fairness sits near the ceiling; this may hold down its correlations
- Status is the only need below the midpoint

::: notes

兩個 arm 的需求平均數幾乎一樣。

- **Fairness** 平均 6.55，接近 7 分的天花板。分數擠在頂端時，變異變小，和其他變數的相關也容易被壓低。
- **Status** 是唯一低於量尺中點的需求（2.86、3.02），persona 普遍不想要「提升地位」的領導者。
- **Affiliation** 的標準差（1.8）是其他需求的兩倍左右。這和 Reading 3 一致：affiliation 跟著 persona 的 agreeableness 設定（高／中／低）走，所以分布特別寬。

:::

# Reading 5: G1 does not appear

- Protection reaches effectiveness (safety .22) but not the prototype (strength .04)
- The reverse of the paper
- Floor and ceiling effects mean this cannot count against G1 either

::: notes

**G1 沒有出現，甚至方向相反**：論文是「原型有、有效性沒有」；我們的 protection 是「原型沒有（.04）、有效性有（.22）」。不過因為上一頁講的地板和天花板效應，這個結果不能拿來反駁 G1。

:::

# Reading 6 (hypothesis): the persona is the only link

- **A proposed explanation, not a tested one**
- Each instrument runs on a fresh fork
- So a need and an outcome can correlate only through what both share: OCEAN levels and description
- One trait drives both → they correlate in the paper's direction, with no need doing work
    - e.g. high agreeableness → needs affiliation *and* rates benevolence effective
- No trait drives both → nothing links them

::: notes

**這一頁開始是假設，不是結論。** 它是一個符合目前資料的解釋，但還沒有用實驗直接檢驗過。

**出發點**：replication 裡每份問卷都在新的 fork 上作答。persona 填 ILT 的時候，看不到自己剛填的 FFNI。那需求分數和 ILT 分數為什麼會相關？唯一可能的管道，是兩次作答共用的東西：persona 的 OCEAN 設定和描述文字。

**推論**：

- 如果某個 OCEAN 特質同時推動一個需求和一個結果，兩者就會相關。例如高 agreeableness 的 persona，既會「需要 affiliation」，也會「覺得 benevolence 有效」。這樣的相關方向和論文一致，看起來像複製成功，但其實不需要「需求影響評價」這個心理歷程。
- 如果沒有任何特質同時推動兩者，兩者之間就沒有任何連結。

**假設**：prestige 側屬於第一種，dominance 側屬於第二種。下一頁是數據。

:::

# Reading 6 (hypothesis): the evidence

| Paper cell | Side | r | r, OCEAN removed | r of OCEAN parts | Replicates |
|----------------------------------------|--------------|--------------|--------------|--------------|--------------|
| A: protection → strength | Dom. | .01 | .06 | −.06 | No |
| A: status → tyranny | Dom. | .31 | .22 | **.48** | Yes |
| A: status → masculinity | Dom. | .08 | .08 | .08 | No |
| A: status → well-groomed | Dom. | .07 | .01 | .15 | No |
| A: 10 vision, expertise, fairness cells | Prest. | .34 to .63 | .05 to .24 | **.56 to .97** | 9 of 10 |
| B: protection → authoritarianism | Dom. | −.12 | −.17 | .00 | Yes (null) |
| B: status → narcissism / authorit. / dominance | Dom. | .11 / .12 / .18 | .07 / .07 / .15 | .30 / .36 / .37 | 1 of 3 |
| B: 9 other cells | Prest./other | .32 to .82 | .15 to .32 | **.64 to .95** | 6 of 9 |

::: notes

**怎麼算的**（`tools/ocean_confound.py`）：把每個需求、每個結果都拿去對 OCEAN 做回歸，每個特質用「中」「高」兩個虛擬變項。然後算三個數字：

- **r**：原始相關。
- **r, OCEAN removed**：兩邊都扣掉 OCEAN 能預測的部分後，剩下的相關。
- **r of OCEAN parts**：兩邊「被 OCEAN 預測出來的部分」之間的相關。這個值高，代表需求和結果是被**同一組特質**推動的。

**看到的模式**：

- **Prestige 側**：OCEAN 部分的相關是 .56-.97，需求和結果吃的是同一組特質。扣掉 OCEAN 之後，原始相關大部分不見了（arm A 從 .34-.63 掉到 .05-.24）。
- **Dominance 側**：OCEAN 部分的相關是 −.06 到 .48，需求和結果吃的是不同的特質，或根本不吃 OCEAN。所以沒有共同的來源可以產生相關。
- **arm A 裡唯一 replicate 的 dominance 格子 status → tyranny，正好是 OCEAN 部分重疊最多的一格（.48）**，和假設一致。
- **地板和天花板也能用同一個假設解釋**：dominance 側的結果幾乎不受 OCEAN 影響（arm B 的 R² 只有 .09-.11，arm A 是 .19-.40；arm A 的 prestige 維度是 .40-.83）。persona 設定推不動這些分數，剩下的只有模型本身的共識，而這個共識是一致的，所以分數擠在一起。

**限制**：

- 10 個虛擬變項放在 n = 261 或 367 上，R² 會有點高估。
- 描述文字沒有放進模型，所以「扣掉 OCEAN 後還剩的相關」有一部分可能來自描述文字。
- **直接的檢驗**還沒做：例如固定 OCEAN、只改描述文字，或在 persona 裡加入一個專門推動 dominance 側需求的屬性，看 dominance 側的格子會不會出現。

:::

# What this means for Step 2

- **Dominance side** (H4, H5, H5b, H7b): not comparable with the paper, null or significant
- **Prestige side**: comparable, but if Reading 6 holds it shows coherent persona settings, not needs at work
- Control OCEAN, or report r with OCEAN removed beside the raw r
- Rewording dominance items alone would not tie their scores to needs
- Read β and ΔR² sizes, not just p; "Yes (null)" is not "shown to be 0"

::: notes

**對 Step 2 的影響**：

- **Prestige 側**的結果可以和論文比較。
- **Dominance 側**的結果，不管出來是 null 還是顯著，都**不能直接和論文比較**。在還沒操弄任何情境之前，這個環境的量尺就已經限制了它。如果 Step 2 的 H5 出現 protection → D 有效性的 null，那不能解讀成「replicate 了 G1」，因為這個 null 在 replication 階段就已經可以預期。

**判讀時的兩個提醒**：

1. **看效果大小，不只看 p**。F 的分子乘上了 (n − 7)，所以同樣的 ΔR²，n 越大 p 越小。真人研究受限於預算，但模擬加跑 persona 幾乎沒有成本，只要 n 夠大，幾乎任何非零效果都會顯著。
2. **「Yes (null)」是弱證據**。p ≥ .05 只代表沒有排除 0。

**如果 Reading 6 的假設成立**：

- Prestige 側的結果，主要說明 persona 的設定前後一致，而不是需求在起作用。Step 2 分析需求時應該控制 OCEAN，或至少在原始 r 旁邊同時報告扣掉 OCEAN 後的 r。
- 單靠改 dominance 題目的措辭讓分數散開沒有用，因為多出來的變異還是和需求無關。要讓 dominance 側出現，persona 設定本身就要帶有和 dominance 相關的個體差異。

這些都建立在一個還沒被直接檢驗的假設上，所以目前只是方向，還沒有決定要做。

:::
