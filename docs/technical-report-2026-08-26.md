# Technical Report — `ffni_mediation` (Step 2)

**日期**：2026-08-26 執行，2026-09-01 撰寫
**研究**：`studies/ffni_mediation`
**資料**：`results/ffni_mediation/`，每條件 40 場，共 80 場
**程式版本**：commit `0067e63`（數字皆可重現；§11.9 的探索性中介是例外——可重算但
倉庫中沒有對應腳本，§12 亦未列出指令）

本報告記錄 Step 2 的完整技術細節：每個假設的估計式、公式、對應的程式路徑、以及實際結果。
設計決策的來龍去脈記在 `docs/design-log.md` §13–§29，本報告只在必要時引用。

---

## 1. 研究目標

檢驗一條被廣泛假設但從未被實證檢驗的因果鏈：

```
情境威脅  →  追隨者的保護需求上升  →  偏好支配型領導者
```

Sheng, Andrews & van Vugt (2026, *J. Applied Psychology* 111(6), 768–801) 開發並驗證了
Fundamental Follower Needs Inventory (FFNI)，並在 p.795 明確指出：先前顯示群體衝突提高
支配型領導偏好的研究「假設了追隨者需求的中介角色，卻沒有實證檢驗它——很可能是因為缺乏
經過驗證的測量工具」。

本研究提供該論文所缺的三個條件：

| | 論文 | 本研究 |
|---|---|---|
| 情境 | 觀察（相關研究） | **操弄**（隨機分派到兩個情境） |
| 需求 | 兩個時點，相隔一週，中間無事件（Sample E） | **人內前後測，中間夾一個被操弄的事件** |
| 結果 | 認知／知覺評分 | **行為**（實際投票） |

---

## 2. 實驗設計

### 2.1 母體

36 個 LLM persona，由 `tools/pair_bank.py` 從 3,645 筆的人格庫（`personas_output.json`）
決定性地產生，職業限制在 `hospital` 設定（emergency room nurse / pharmacist /
hospital administrator / social worker）。

| 組 | n | 每場抽樣 | 說明 |
|---|---|---|---|
| P (Prestige) | 6 | 1 | 聲望型候選人 |
| D (Dominance) | 6 | 1 | 支配型候選人，`pair_with: "P"` |
| N (Neutral) | 24 | 3 | 中立者，唯一的受試者與選民 |

**配對構造**：P_i 與 D_i 由**同一筆人格庫資料**產生，因此 Big Five、職業、年齡層、
父母身分完全相同，唯一差異是 style block。這消除了人格與職業的混淆
（design-log §3）。`pair_bank.py:163-171` 有斷言比對 P 組與 D 組的 OCEAN、職業、年齡層、父母身分的
**排序後多重集合**，任何破壞組間平衡的修改都會在產生階段失敗，而不是在 1,600 次 API
呼叫之後。注意它擋的是組間平衡，**不是逐一索引的配對**——後者由建構迴圈保證，置換
哪一列餵給哪個 D 索引仍會通過該斷言。

**操弄的載體**（persona spec 裡實際帶有的差異）：

- `style.influence`：D 是「Claims influence by taking control of the room…」，
  P 是「Earns influence by being worth listening to…」
- `personality.traits`：各 6 條行為描述（D 例：「treats a challenge as something to be
  shut down, not examined」）
- `speech_examples`：各 4 句（D 例：「We're doing it this way. Next.」）

`leadership_style` 標籤與 `style.register` 已於 §17 移除——前者是 demand
characteristic（TinyTroupe 把整個 persona dict 逐字放進 system prompt），後者是關於
規格本身的 meta 語言。

### 2.2 抽樣

`src/pipeline.py:31-49`，`BalancedSampler`：

```
佇列為空 → 用種子化 RNG 產生 0..size-1 的隨機排列
take(n)  → 依序取出 n 個；跨越循環邊界時，若抽到已在本場的 index，
           把它推回新循環的尾端，換下一個
```

- **平衡性**：每個 id 在下一輪重複之前必定各出場一次。24 個中立者、每場抽 3，
  40 場後每人恰好出場 5 次。
- **條件對齊**：sampler 以 `study.sampler_seed` 種子化，因此 run *i* 在兩個條件抽到
  **同一組 cast**。
- **配對組**：D 不獨立抽樣，而是取用 P 的 index（`compose_run` 的 `pair_with` 分支），
  所以 P_i 與 D_i 必定同場出現。

跨循環的重複抽樣曾是一個必然當機的 bug（8 人池抽 3，run 3 必掛），修正記於 §21。

### 2.3 條件

兩個條件共用 persona、cast 抽樣與投票題目，只有情境文字不同。`test_core.py` 釘住
`ffni_mediation` 與 `pd_matched` 的情境與 friction 文字逐字相同。

- **collaborative**：單位連續兩季未達病安與週轉目標，被授權自行診斷並提出一項變革，
  48 小時內決定。
- **threat**：醫院整併，兩個重疊單位只保留一個，48 小時內須提出保留本單位的理由，
  否則由上級決定且會有人失去職位。

兩條件都有 48 小時期限（早期版本只有威脅條件有，那會把威脅與時間壓力混淆，§13 修正）。

---

## 3. 執行流程

`src/pipeline.py:80-200`，`run_condition`。一場 run 的順序：

```
1. baseline 量表   在 fork 上施測    ffni (22題) + leader_ideal (45題)，各 3 次呼叫
2. 討論            3 rounds × 5 人   15 次呼叫，發言順序每輪重洗
3. post 量表       各自從討論後狀態分支出獨立 fork
                     ffni            3 次
                     leader_ideal    3 次
                     effectiveness   3 人 × 2 候選人 = 6 次
4. 投票            在原始 agent 上   5 次呼叫
                                     ────────────
                                     每場 38 次
```

**Fork 機制**（`src/discussion.py:99-135`）。量表施測必須不改變之後要投票的 agent，
否則一份 22 題「你想從領導者身上得到什麼」的量表本身就是強烈的 prime。實作：

```python
saved = {attr: getattr(person, attr) for attr in _LIVE_WIRING if hasattr(person, attr)}
for attr in saved: setattr(person, attr, None if attr == "environment" else [])
try:    cloned = copy.deepcopy(person)
finally: for attr, value in saved.items(): setattr(person, attr, value)
```

先拆除 live wiring（`environment`、`_accessible_agents` 等）再複製，因為 TinyWorld
持有 `_thread.RLock`，帶著它的 agent 無法被 deepcopy。**這是 §21 記錄的資料污染
bug 的修正**：原本的實作是先 deepcopy 再清欄位，並以 `except Exception: return person`
吞掉失敗，導致每一份 post 量表都寫進了正要投票的那個 agent。現在複製失敗會直接拋出。

`run_discussion` 結束時拆除 TinyWorld 並從 `TinyWorld.all_environments` 移除，
避免每場累積一個未回收的 world。

**模型設定**（`config.ini`）：

```
DISCUSSION_MODEL = gpt-4.1     DISCUSSION_TEMPERATURE = 0.7   MAX_TOKENS = 6000
VOTE_MODEL       = gpt-4.1     VOTE_TEMPERATURE       = 0.2   MAX_TOKENS = 3000
SURVEY_MODEL     = gpt-4.1     SURVEY_TEMPERATURE     = 0     MAX_TOKENS = 4500
RUNS = 40   ROUNDS = 3
```

`SURVEY_TEMPERATURE = 0` 的依據見 §7.2。`DISCUSSION_MODEL` 必須是 `gpt-4.1`：
`gpt-4o-mini` 上的支配型 persona 完全不 claim 領導（claim 率 0.00 vs 0.17），
自變項等於沒有被操弄（§22）。

**成本**：80 場 × 38 次 ≈ 3,040 次呼叫，6.5 小時，約 27 美金。

---

## 4. 測量工具與計分

### 4.1 三份工具

| key | 題數 | about | 量尺 | 施測時機 | 誰作答 |
|---|---|---|---|---|---|
| `ffni` | 22（6 分量表） | self | 1–7 | baseline, post | N |
| `leader_ideal` | 45（10 維度） | prototype | 1–10 | baseline, post | N |
| `effectiveness` | 1（每個目標） | each_candidate | 1–7 | post | N |

- **`ffni`**：Sheng et al. 原始 22 題逐字重現（Table 5, p.779；2026-09-07 逐題核對，
  修正 4 處縮寫與 1 處 toward/towards）。授權標示 CC BY-NC-ND 4.0 取自預印本，
  **published 版全文查無此授權**，各頁均為 APA 全權保留——視為未經查證，但不得改寫
  仍是安全的讀法。
  六個分量表：protection(4)、affiliation(4)、status(4)、vision(3)、expertise(3)、
  fairness(4)。
- **`leader_ideal`**：ILT 的**重建**，而且是**與論文所用工具差距很大的重建**。論文用
  Offermann & Coats (2018) 的 46 題加 femininity 與 ethics 共 51 題。收集本研究資料時
  該工具不可得，因此以 Offermann, Kennedy & Wirtz (1994) 的八因素版（經 Bhatia et al.
  2022 附錄轉載，該附錄列出 **40** 個特質而其正文稱 41，且措辭未經原文核對）加上論文
  註 13 的 femininity 與 ethics 題目重建。

  **2026-09-07 取得 2018 原文後的逐題比對**：本研究施測的 45 個特質中，**有 17 個不存在
  於論文使用的工具裡**；共有的 28 個裡有三個歸屬不同——`bold` 屬 charisma、`attractive`
  屬 masculinity、`clever` 屬 creativity。這不是「題數較少的同一份量表」，而是不同的
  工具。正確的 51 題已建於 `instruments/leader_ideal_2018.json`（尚未接上，接上需重跑
  原型層）。後果見 §9 與 design log §31 C3。
- **`effectiveness`**：單題，「Think about how this person behaved in the meeting you
  just had. Rate how effective they would be as your own leader.」每位中立者對每位
  **候選人**評分（§21 起不再評其他中立者——那 6 次呼叫沒有任何分析讀取）。

### 4.2 題目呈現

`src/discussion.py:391-397`。整份電池在**一次 API 呼叫**內施測，題目順序隨機化：

```python
order = random.Random(f"{instrument.key}:{participant.persona_id}").sample(items, len(items))
```

**順序以「受試者 × 工具」為單位固定，不是每次施測重抽。** FFNI 的驗證程序要求題目
隨機呈現，且跨受試者的位置偏誤必須被打散；但同一個人在前後測拿到不同順序，會把
「換個順序就答不一樣」直接混進前後差異——而前後差異正是 H3 的依變項與 H6 的中介變項。
此修正使所有雜訊地板約減半（§7.3）。

### 4.3 計分

`src/instrument.py:112-126`：

```
subscale_score(s) = mean{ r_i : i ∈ items(s), r_i 在量尺範圍內且非 null }
```

**缺失值永不插補。** 超出量尺或模型漏答的題目記為 `null` 並標記，不以中點取代——
解析失敗必須讀作缺失資料，而非虛假的中庸作答。整份分量表無可用作答時記為 `NaN`。

`effectiveness` 為 `about=each_candidate`，其 `ratings()` 回傳
`{評分者: {目標: 該目標各分量表平均}}`（`src/run_record.py:84-92`）。

---

## 5. 統計原語

全部實作於 `src/stats.py`，不依賴 scipy 以外的套件（scipy 僅用於 t 分布尾機率）。
**所有函數丟棄 NaN 而非插補。**

### 5.1 平均與標準差

$$
\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i
\qquad\qquad
s = \sqrt{\frac{\sum_{i=1}^{n}(x_i-\bar{x})^2}{n-1}}
$$

僅計非 NaN 的觀察值；樣本標準差在 $n<2$ 時回傳 0。

### 5.2 OLS 斜率與相關

`slope(x, y)`，n < 3 或任一邊無變異時回傳 NaN：

$$
S_{xy}=\sum_i (x_i-\bar{x})(y_i-\bar{y}),\qquad
S_{xx}=\sum_i (x_i-\bar{x})^2,\qquad
S_{yy}=\sum_i (y_i-\bar{y})^2
$$

$$
b = \frac{S_{xy}}{S_{xx}}
\qquad\qquad
r = \frac{S_{xy}}{\sqrt{S_{xx}\,S_{yy}}}
$$

### 5.3 單尾配對 t 檢定

`paired_ttest_onesided(a, b)`，檢定 mean(a) > mean(b)：

$$
d_i = a_i - b_i,
\qquad
t = \frac{\bar{d}}{\sqrt{s_d^{2}/n}},
\qquad
s_d^{2} = \frac{\sum_i (d_i-\bar{d})^2}{n-1}
$$

$$
p = P\left(T_{n-1} > t\right)
$$

尾機率由 `scipy.stats.t.sf` 計算。

配對是因為兩組在同一場 run 內同時被觀察，run 是自然的配對單位。

### 5.4 Welch 單尾檢定（交互作用用）

`tools/interaction_test.py`：

$$
\mathrm{SE} = \sqrt{\frac{s_a^{2}}{n_a} + \frac{s_b^{2}}{n_b}}
\qquad\qquad
t = \frac{\bar{a}-\bar{b}}{\mathrm{SE}}
$$

$$
\nu = \frac{\left(\dfrac{s_a^{2}}{n_a}+\dfrac{s_b^{2}}{n_b}\right)^{2}}
           {\dfrac{(s_a^{2}/n_a)^{2}}{n_a-1}+\dfrac{(s_b^{2}/n_b)^{2}}{n_b-1}}
\qquad\qquad
p = 1-\Phi(t)
$$

$p$ 以常態近似 $t$ 分布的尾機率；$\nu$ 遠大於 30 時足夠。

用 Welch 而非配對，是保守的選擇：兩個條件的 run *i* **確實抽到同一組 cast**（§2.2，實測 40/40 場成員完全相同），但討論、量表作答與投票都是獨立產生的，配對能買到的變異縮減有限，而 Welch 不需要假設兩組變異數相等。

### 5.5 Cronbach's α

$$
\alpha = \frac{k}{k-1}\left(1 - \frac{\sum_{i=1}^{k} s_i^{2}}{s_{\text{total}}^{2}}\right)
$$

k = 題數，s²_i = 第 i 題的變異數，s²_total = 總分的變異數。整列有任何缺失即剔除
（listwise），受試者少於 3 或題數少於 2 時回傳 NaN。

### 5.6 偏迴歸係數與 ΔR²

`partial_betas(X, y)`，這是 H4/H5/H7 的核心：

**步驟 1**：listwise 刪除任何含 NaN 的列。

**步驟 2**：標準化每一欄，標準化後不需要截距，係數即為標準化 $\beta$：

$$
x^{*}_{ij} = \frac{x_{ij}-\bar{x}_j}{s_{x_j}}
\qquad\qquad
y^{*}_{i} = \frac{y_i-\bar{y}}{s_y}
$$

**步驟 3**：最小平方配適全模型（`numpy.linalg.lstsq`），並計算模型 $R^2$：

$$
\hat{\boldsymbol\beta} = \arg\min_{\boldsymbol\beta}\;\lVert \mathbf{y}^{*}-\mathbf{X}^{*}\boldsymbol\beta \rVert^{2}
\qquad\qquad
R^{2}_{\text{full}} = 1-\frac{(\mathbf{y}^{*}-\mathbf{X}^{*}\hat{\boldsymbol\beta})^{\!\top}(\mathbf{y}^{*}-\mathbf{X}^{*}\hat{\boldsymbol\beta})}{\mathbf{y}^{*\top}\mathbf{y}^{*}}
$$

**步驟 4**：對每個預測變項 $j$，重新配適不含 $j$ 的模型，取 $R^2$ 的落差：

$$
\Delta R^{2}_{j} = R^{2}_{\text{full}} - R^{2}_{(-j)}
$$

**為什麼必須用增量而非雙變量相關。** 論文 Table 8 顯示六個需求彼此相關 r = .60–.72。
論文 Table 13 對每個原型維度同時報兩欄，以 Strength 為例：

| 預測變項 | 雙變量 r | ΔR² |
|---|---|---|
| protection | .38\*\*\* | **.03\*\*** |
| affiliation | .29\*\*\* | .00 |
| status | .29\*\*\* | .01 |
| vision | .32\*\*\* | .00 |
| expertise | .26\*\*\* | .00 |
| fairness | .26\*\*\* | .00 |

六個雙變量相關全部 p < .001，只有增量能分離出 protection。H4 是關於 **specificity**
的主張（protection 應**特別地**連到支配側），若用雙變量算，H4 為真與為假會給出相同的
結果型態——**該檢定不可能失敗，因而不提供任何資訊**。此缺陷於 §23 修正，H5 與 H7 同時修正。

註：ΔR² 是**唯一變異**，共線性會壓縮它。論文自己的顯著增量落在 .01–.06，而同一批 β 是
.19–.32。把 .03 讀作「效果很小」會連同論文的結果一起否定。

### 5.7 Bootstrap 信賴區間

所有區間皆為 **percentile bootstrap，重抽單位是 run**：

對 $k = 1,\dots,B$（$B = 1000$）：對每個條件，從其 40 場中抽後放回抽出 40 場，
在重抽樣本上重跑**整個**估計式得到 $\hat{\theta}^{(k)}$。區間為

$$
\text{CI}_{95} = \left[\hat{\theta}^{(\lfloor 0.025B \rfloor)},\;
                        \hat{\theta}^{(\lfloor 0.975B \rfloor)}\right]
$$

其中 $\hat{\theta}^{(1)} \le \cdots \le \hat{\theta}^{(B)}$ 為排序後的重抽估計值。

**為什麼重抽 run 而非受試者**：同一場的 3 個中立者觀看同一段討論，不是獨立觀察。
把他們當成 3 筆獨立資料會低估不確定性。模擬顯示忽略此聚類使偽陽性率上升約 2 個百分點（ICC 由 0 至 .25 時，12% → 14%）——
該組數字是在**未置中**的估計式上量的，其中 12% 的底是條件混淆而非聚類。§26 起 `summarize_mediation` 與
`summarize_layer_moderation` 都改為重抽 run。

---

## 6. 七個假設：估計式與結果

### 對應總表：七個假設出自何處，公式是否相同

論文頁碼為期刊頁碼（`docs/2027-27008-001.pdf` 的 PDF 頁碼 = 期刊頁碼 − 768 + 3）。

| | 出處 | 論文的估計式 | 本研究的估計式 | 相同？ |
|---|---|---|---|---|
| H1 / H2 | **非本論文**，出自雙路徑文獻 | **無**。論文完全沒有行為結果變項 | 每場票數的單尾配對 $t$ 檢定 | **不適用** |
| 交互作用 | **非本論文** | **無** | Welch 單尾檢定比較兩條件的 $D-P$ 差距 | **不適用** |
| H3 | **論文未做**，p.795 列為未來方向 | **無**。五個研究皆為自陳與相關設計，從未操弄情境 | 人內變化量的組間差，bootstrap 區間 | **不適用** |
| **H4** | **論文的正面結果**：Study 5, Sample B, **Table 13**, p.789–791, $N = 261$ | 階層多元迴歸 + relative weights analysis（Tonidandel & LeBreton 2011, 2015）。報告 $r$、$b$、$SE$、$\beta$、$\Delta R^2$、$RW$、$RW$ CI、$RW\%$ | 標準化偏迴歸 $\beta$ 與 $\Delta R^2$（§5.6） | **$\Delta R^2$ 相同**；未做 relative weights；**結果變項的聚合方式不同**，見下 |
| **H5** | **論文的結果（支配側 null）**：Study 5, Sample E, **Table 3**, p.773, $N = 367$ | 線性迴歸 Model 1（僅該需求）與 **Model 2（控制其餘五個需求）**，另附 SEM | 標準化偏迴歸 $\beta$（§5.6） | **與 Model 2 相同**；**效標本身差異很大**，見下 |
| H6 | **論文明言未檢驗**，p.795 | **無** | 路徑乘積 $a \times b$ + percentile bootstrap（重抽 run） | **不適用**（無可對照者） |
| H7 | **論文列為待答問題**，p.789 | **無** | 兩條件各自估計後相減，bootstrap 區間 | **不適用** |

四處出處的原文：

- **H1 / H2** — 雙路徑模型（Cheng et al. 2013；Henrich & Gil-White 2001）與威脅效果
  （Kakkar & Sivanathan 2017；Laustsen & Petersen 2017；Spisak et al. 2012）。本論文
  p.795 僅引述為背景。
- **H3** — p.795：「Experimental vignette studies offer a useful method for manipulating
  contextual cues…intergroup conflict may heighten the FFN for protection」。
- **H6** — p.795：「these studies often assume yet do not empirically test the mediating
  role of follower needs—likely due to a lack of validated measures」。
- **H7** — p.789：「would intergroup conflict situations (e.g., trade wars,
  organizational crises) strengthen the FFN protection–authoritarianism link?」

**七個假設中只有 H4 與 H5 在論文裡有對應的實證結果**，而它們正是本研究的兩個對照：
H4 為陽性對照（論文有效果），H5 支配側為陰性對照（論文為 null）。其餘五個假設論文
或未做（H3、H6）、或不屬於本論文（H1、H2、交互作用）、或僅列為待答問題（H7）。

#### H4 的公式異同（細節）

**相同的部分**：兩者都是「六個需求同時進入模型，讀該需求相對於其餘五個的增量」。
論文的 $\Delta R^2$ 就是本研究 §5.6 的 $\Delta R^2_j = R^2_{\text{full}} - R^2_{(-j)}$。

論文採用增量而非雙變量的理由，其正文自己說明了：需求之間高度相關，Study 5 的討論寫
「Despite strong correlations among these needs ($r$ ranged from .60 to .72; see Table 8),
hierarchical regression confirmed their incremental contributions」。Table 8（p.783）的完整相關矩陣範圍更寬，且該引句只涵蓋部分需求與部分樣本；
全表最低達 .08（Sample E T2 的 status–fairness）。

**三個不同的部分**：

1. **結果變項的聚合方式**。論文對 **11 個 ILT 維度各自**配適一個迴歸（Table 13 有 11 個
   criterion 區塊）。本研究把 `predicts` 映射到的維度**先平均成一個複合分數**再配適，
   每個需求一個迴歸。因此本研究的 `status` 是 tyranny、masculinity、attractiveness 的
   平均，而論文是三個分開報告。這使本研究無法看出某個需求只在其中一個維度上有效果，
   §9.2 的逐維度分解即是為了補回這一點。
2. **未做 relative weights analysis**。論文同時報 Johnson 相對權重及其 bootstrap 區間；
   本研究只用 $\Delta R^2$，因為它已足以回答假設，而相對權重是為一個沒有分析會讀取的
   數字增加機制。
3. **不確定性的來源**。論文以迴歸的解析標準誤與 relative weights 的 bootstrap
   （10,000 次，重抽受試者）報告；本研究以重抽 **run** 的 percentile bootstrap（§5.7），
   因為同一場的三位受試者不獨立。

**工具亦不同**：論文用 Offermann & Coats (2018) 的 51 題（46 題正式量表 + femininity 2 題
+ ethics 3 題），10 點量尺，$\alpha$ 為 .76–.92；本研究用 45 題的重建版（§4.1、§11.5），
同為 10 點量尺。

#### H5 的公式異同（細節）

**相同的部分**：論文 Table 3 的 **Model 2** 明確定義為「linear regression models control
for the other five follower needs」，這與本研究 §5.6 的偏迴歸 $\beta$ 是同一個估計式。
論文正文亦強調「These relationships remained significant even after controlling for all
other FFNs」。本研究的支配側 null 因此是與 Model 2 對照，而非與 Model 1。

**兩個不同的部分**：

1. **刺激材料的性質完全不同**（效標問句本身相同，見 design log §30）。論文讓受試者評
   **12 份量表、57 題**改寫成的領導者描述，每份量表的 4–6 題平均成一個分數，
   Table 3 因 Authoritarianism 出現兩次而有 13 列。支配側是 Authoritarianism、
   Narcissism、Dominance 三份分開的量表；聲望側是 Benevolence、Team-building、
   Vision communication、High-expectation、Competence、Intellectual stimulation、
   Moral character、Virtue，**另有 Safety**——而 Safety 正是 `protection` 強烈成立的
   那一欄（.43\*\*\*/.20\*\*\*）。**沒有任何受試者觀察過任何人。**
   本研究是**一個被觀察的具體對象、被評一次**。因此本研究的「對支配型的有效性」把論文
   分開的三份支配側量表壓成一個數字，也把 Safety 與 Authoritarianism 的區別壓掉了。
2. **時間間隔**。論文 Sample E 在 Time 1 施測 FFNI，**一週後**的 Time 2 施測有效性；
   本研究兩者在同一場會議後相隔數分鐘。

**論文支配側 null 的原始數字**（Table 3，Model 1 / Model 2）：

| 需求 → 風格 | Model 1 $\beta$ | Model 2 $\beta$ | |
|---|---|---|---|
| Protection → Authoritarianism | −.02 | −.01 | ns |
| Status → Narcissism | .04 | .03 | ns |
| Status → Authoritarianism | −.05 | −.02 | ns |
| Status → Dominance | −.12 | −.05 | ns |

對照本研究：protection → 支配型有效性 $\hat\beta = -0.002$，CI $[-0.139, +0.132]$。

**注意 Protection → Safety 在論文是 .43\*\*\* / .20\*\*\***（強烈成立）。論文的支配側 null
專指 Authoritarianism；「想要被保護」與「認為以安全為導向的領導有效」是成立的，
與「認為威權領導有效」才是不成立的。本研究的單題效標無法區分這兩者，這是 §11 未列出
的一個效度限制，於此補記。

### 6.0 選民限制

`summarize_contrast`（`src/analysis.py:82-143`）只計入**非候選組**的選票：

```python
voters = tuple(k for k in study.groups if k not in (a, b)) or None
```

P 與 D 是被比較的候選人，讓他們在自己的競賽中投票等於把對手的選票放進依變項。
cast 為 5 時那是 5 票中的 2 票。因此選民僅為 3 位中立者，每場票數上限為 3。
兩位候選人互投的票另外記錄於 `candidate_votes` 但不計入檢定。

### 6.1 H1 / H2 — 投票

**估計式**：每場計算兩組各自獲得的中立者票數，做單尾配對 t 檢定。

$$
\text{per-run}_i = \bigl(v_A(i),\, v_B(i)\bigr),\quad i = 1,\dots,40
\qquad\qquad
H_0:\; \mathbb{E}[v_A - v_B] \le 0
$$

其中 $v_G(i)$ 是第 $i$ 場中立者投給組 $G$ 的票數，以 §5.3 的單尾配對 $t$ 檢定。

**程式**：`summarize_contrast` → `group_metrics(record, group, voters=('N',))`

**結果**：

| 條件 | contrast | 平均票數 | t | p | 勝場 |
|---|---|---|---|---|---|
| collaborative | P > D | P 1.650 (sd 1.167) vs D 0.900 (sd 1.105) | 2.199 | **.0170** | 25/40 |
| threat | D > P | D 1.575 (sd 1.318) vs P 1.100 (sd 1.128) | 1.277 | .1047 | 23/40 |

**H1 成立，H2 單獨不成立。**

附帶指標（同一檢定套用於其他 DV）：threat 條件的 speech rate D .992 vs P .958
（p = .052）；words per turn D 33.5 vs P 41.4——**注意此檢定方向固定為
contrast[0] > contrast[1]，而 P 在兩條件都比 D 話多，因此該行的 p 值無意義，
應讀原始平均數**（§8 已記錄此為報表假象）。

### 6.2 交互作用 — 主要檢定

**這是唯一真正對應「威脅造成轉變」這個理論宣稱的檢定。** 兩個條件各自顯著並不等於
兩者之間有差異。

**估計式**：

$$
g_i = v_D(i) - v_P(i)
\qquad\qquad
H_0:\; \mathbb{E}\bigl[g \mid \text{threat}\bigr] \le \mathbb{E}\bigl[g \mid \text{collab}\bigr]
$$

以 §5.4 的 Welch 單尾檢定比較兩個條件的 $g$。

**程式**：`tools/interaction_test.py ffni_mediation`

**結果**：

```
threat        mean(D−P) = +0.47   sd = 2.35   n = 40
collaborative mean(D−P) = −0.75   sd = 2.16   n = 40
Welch t = 2.427, df ≈ 77.4, 單尾 p = .00762      → 成立
```

**行為效果複製。** 檢定力模擬（§4 舊表）早已顯示交互作用比單一條件更有力，因為協作條件
往反方向錨定，把待檢定的差距拉開；H2 單獨落在 .105 是預期內的。

### 6.3 H3 — 情境是否推動需求

**估計式**：人內變化的組間差。

$$
M_p = \text{score}_{\text{post}}(p) - \text{score}_{\text{baseline}}(p)
$$

$$
a = \frac{1}{|T|}\sum_{p \in T} M_p \;-\; \frac{1}{|C|}\sum_{p \in C} M_p
$$

$T$ 與 $C$ 分別為威脅與協作條件的受試者集合；信賴區間以重抽 run 的 bootstrap 求得。

**程式**：`summarize_layer_moderation` 的 `induced` 欄位（`src/analysis.py`）

**結果**（1–7 量尺，每條件 120 位受試者）：

| need | 協作 | 威脅 | 差 | 95% CI | |
|---|---|---|---|---|---|
| **protection** | −0.748 | −0.438 | **+0.310** | **[0.125, 0.496]** | 排除 0 |
| affiliation | −0.050 | −0.152 | −0.102 | [−0.229, 0.029] | |
| status | −0.371 | −0.373 | −0.002 | [−0.102, 0.092] | |
| vision | +0.233 | +0.125 | −0.108 | [−0.244, 0.019] | |
| expertise | −0.169 | −0.258 | −0.089 | [−0.203, 0.033] | |
| fairness | +0.106 | +0.077 | −0.029 | [−0.115, 0.050] | |

**H3 成立，且僅 protection 成立。** 威脅推動的正是論文預測的那一個需求，其餘五個
（含 status，論文亦預測會上升）的區間皆含 0。

**必須注意的細節**：$M_p < 0$ 在兩個條件皆成立——protection 都在**下降**，威脅只是讓它跌得較少。
組間比較成立，但這不是「威脅使需求絕對上升」。六個需求在合併資料上的人內變化
（240 人）全部顯著非零，最大是 protection −0.59 [−0.69, −0.49]——**討論本身**
使多數需求下降，而情境只調節了幅度。這也證明量表對討論有反應性：measure-check
顯示什麼都不發生時 protection 的變化 SD 僅 0.40。

### 6.4 H4 — 認知層（需求 → 領導者原型）

**這是論文的正面結果**（Study 5, Sample B, Table 13, p.789–791, $N = 261$），本研究將其設為**正對照**。估計式與論文的異同見本節開頭的對應總表。

**預測映射**（`leader_ideal.json` 的 `predicts`，取自論文 Table 13 的顯著 ΔR²）：

```
protection → strength
status     → tyranny, masculinity, attractiveness      (attractiveness 是 1994 年的名稱，2018 改名 well-groomed)
vision     → sensitivity, dedication, charisma
expertise  → sensitivity, charisma, intelligence
fairness   → dedication, intelligence, ethics
affiliation→ （無條目）
```

`affiliation` 的條目已於 §23 移除：論文 Table 13 顯示它在全部 11 個維度上 ΔR² 皆為
.00 或 .01 且無一顯著，而雙變量相關高達 .54——它正是舊估計式看不見的那種混淆。
它仍留在迴歸中作為控制變項。

**估計式（兩種讀法）**：

*(a) 水準值*（論文的問法）：

$$
y_p = \frac{1}{|D_m|}\sum_{d \in D_m} \text{prototype}_d(p)
$$

$$
\mathbf{X} = \bigl[\,m_1\;m_2\;\cdots\;m_6\,\bigr]
\quad (240 \times 6),
\qquad
\hat{\beta}_m,\; \Delta R^2_m \;\text{ 由 }\; \mathbf{X},\, \mathbf{y} \;\text{ 依 §5.6 求得}
$$

六個需求 $m_1 \dots m_6$ 全部進入模型，讀該需求自己那一欄的 $\hat{\beta}$。

*(b) 人內變化*（論文的資料問不出來的）：

$$
\Delta m_p = m_{\text{post}}(p) - m_{\text{base}}(p)
\qquad
\Delta y_p = \frac{1}{|D_m|}\sum_{d \in D_m}\bigl[\text{proto}_{d,\text{post}}(p) - \text{proto}_{d,\text{base}}(p)\bigr]
$$

$$
\hat{\beta}_m \;\text{ 由 }\; \Delta\mathbf{X},\, \Delta\mathbf{y} \;\text{ 依 §5.6 求得}
$$

(b) 之所以可能，是因為 §24 為 `leader_ideal` 加了 baseline 施測——baseline fork 不帶
逐字稿，是整個設計中最便宜的呼叫。

**程式**：`summarize_layer_moderation` 的 `cognition` 與 `cognition_induced`

**結果**（討論後資料，pooled，條件內各自置中）：

| need | 水準值 β | 95% CI | ΔR² | 變化量 β | 95% CI |
|---|---|---|---|---|---|
| protection | −0.072 | [−0.195, +0.046] | .0050 | +0.048 | [−0.089, +0.193] |
| status | −0.160 | [−0.277, −0.051] | .0222 | +0.048 | [−0.083, +0.175] |
| vision | +0.068 | [−0.042, +0.170] | .0041 | +0.015 | [−0.099, +0.135] |
| expertise | +0.123 | [−0.020, +0.243] | .0131 | +0.093 | [−0.037, +0.221] |
| fairness | +0.031 | [−0.042, +0.105] | .0008 | +0.025 | [−0.073, +0.110] |

**H4 不成立**：protection 兩種讀法的區間皆含 0。status 顯著但**方向相反**。

**與論文條件對齊的補充分析**（§28）。論文是在冷測條件下以水準值測量，而上表用的是
討論後分數。既然 `leader_ideal` 已有 baseline，最接近論文的分析是「前測需求 → 前測原型」：

| need | β | 95% CI | 論文方向 | |
|---|---|---|---|---|
| expertise | **+0.23** | [0.12, 0.34] | + | **複製** |
| vision | **+0.13** | [0.03, 0.23] | + | **複製** |
| status | −0.03 | [−0.14, 0.10] | + | null |
| **protection** | **−0.16** | **[−0.29, −0.02]** | + | **顯著反向** |
| fairness | −0.20 | [−0.31, −0.11] | + | 顯著反向 |

反向的穩健性經 8 個不同 bootstrap 種子（各 2000 次抽樣）驗證，8/8 皆排除 0，
上界穩定在 −0.02 至 −0.03。

**五條中三條排除 0，因此這不是量表在吐雜訊，而是有結構的失敗：聲望側複製、支配側反向。**
診斷見 §9。

### 6.5 H5 — 評價層（需求 → 對具體某人的有效性評分）

論文的 Study 5 (Sample E, Table 3, p.773, $N = 367$) 以線性迴歸檢定，其 Model 2
控制其餘五個需求，並明言「These relationships remained significant even after
controlling for all other FFNs」。其支配側是 **null**：「the FFNs for protection and
status failed to predict perceived effectiveness of dominance-based leadership styles」。
**因此本研究的支配側預期也是 null，那是複製成功。** 效標性質的重大差異見本節開頭的
對應總表。

**估計式**：與 H4(a) 同一個設計矩陣，只換結果變項。

$$
\text{eff}_A(p) = \frac{1}{|A_p|}\sum_{t \in A_p} r(p \to t)
\qquad\qquad
\text{eff}_B(p) = \frac{1}{|B_p|}\sum_{t \in B_p} r(p \to t)
$$

$A_p$、$B_p$ 分別是該場的支配型與聲望型候選人，$r(p \to t)$ 是 $p$ 給 $t$ 的有效性評分。
以與 H4(a) **同一個** $\mathbf{X}$ 配適：

$$
\hat{\beta}^{(A)}_m \;\text{ 由 }\; \mathbf{X},\, \text{eff}_A \;\text{ 依 §5.6 求得}
$$

**注意**：每個評分組各配適**一次**迴歸（結果變項對所有需求是同一欄），
而非每個需求各配適一次——這才是論文的模型形狀。

**程式**：`summarize_layer_moderation` 的 `evaluation_a` / `evaluation_b`

**結果**：

| need | → 支配型 β | 95% CI | → 聲望型 β | 95% CI |
|---|---|---|---|---|
| protection | −0.002 | [−0.139, +0.132] | +0.053 | [−0.068, +0.171] |
| affiliation | **−0.190** | **[−0.318, −0.070]** | **+0.151** | **[+0.013, +0.303]** |
| status | +0.120 | [−0.011, +0.248] | +0.010 | [−0.129, +0.121] |
| vision | +0.033 | [−0.102, +0.168] | +0.068 | [−0.042, +0.169] |
| expertise | +0.005 | [−0.120, +0.146] | +0.113 | [−0.024, +0.275] |
| fairness | +0.105 | [−0.041, +0.206] | −0.088 | [−0.175, +0.017] |

- **支配側 null → 複製成功**（protection −0.002，status 區間含 0）
- **聲望側**：論文的 vision / expertise / fairness 三條**皆未複製**（區間全含 0）。
  唯一顯著的是 affiliation（→聲望型 +0.151、→支配型 −0.190），方向與論文報告的
  benevolence / team-building 大致相符。

### 6.6 H6 — 中介

**這是論文明言從未被檢驗的那一條（p.795），也是本研究的主軸。** 論文沒有可對照的
估計式，因此下列設計選擇皆為本研究自訂。

**估計式**（`summarize_mediation`，`src/analysis.py:337-495`）：

單位為每場的每位中立者，$40 \times 3 = 120$ 列／條件。

$$
M_p = m_{\text{post}}(p) - m_{\text{base}}(p)
\qquad\qquad
Y_p = \mathbb{1}\bigl[\text{vote}(p) = D\bigr]
$$

**path $a$** — 誘發需求的組間差：

$$
a = \frac{1}{|T|}\sum_{p \in T} M_p \;-\; \frac{1}{|C|}\sum_{p \in C} M_p
$$

**path $b$** — 條件內各自置中後合併，取 OLS 斜率：

$$
\tilde{M}_p = M_p - \bar{M}_{c(p)},
\qquad
b = \frac{\sum_p \bigl(\tilde{M}_p - \bar{\tilde{M}}\bigr)\bigl(Y_p - \bar{Y}\bigr)}
         {\sum_p \bigl(\tilde{M}_p - \bar{\tilde{M}}\bigr)^{2}}
$$

其中 $c(p)$ 是 $p$ 所屬的條件，$\bar{M}_{c}$ 是該條件的組內平均。

**間接效果**：

$$
\widehat{ab} = a \times b
$$

$$
\text{CI}_{95} = \left[ Q_{0.025}, \; Q_{0.975} \right]
\text{ of } \left\{ \widehat{ab}^{(1)}, \dots, \widehat{ab}^{(B)} \right\}, \quad B = 1000
$$

$\widehat{ab}^{(k)}$ 為第 $k$ 次重抽 run 後重算的間接效果；判準為 $\text{CI}_{95}$ 排除 0。

**三個刻意的設計選擇**：

1. **中介變項是變化量而非水準值**（§18）。論文的 null 是關於慢性的、特質式的需求；
   本研究主張的是情境誘發的狀態，水準值會把兩者混在一起。論文自己也把這個歧義
   列為限制：「it remains unclear whether perceived threats **increase** protection
   needs or whether certain individuals are **chronically inclined** toward this need」。
2. **結果變項是受試者自己的那一票**，不是全組票數。這是論文點名「從未測過」的行為
   後果；同時使 H6 與 H5 不會壓在同一個係數上卻做相反預測。
3. **path b 在條件內置中**。不置中的話，威脅同時抬高誘發需求**與**直接抬高背書
   （後者即 H2），使合併斜率在需求毫無作用時仍為正。模擬顯示不置中的偽陽性率為
   13%（5 人 30 場）至 20%（10 人 20 場），且不隨 n 縮小——只有 CI 縮小，所以場次
   越多越糟。置中後回到約 7%。

**結果**：

```
path a    = +0.3104        威脅確實推高了誘發的保護需求
path b    = −0.0055        但誘發需求完全預測不到那一票
indirect  = −0.00171       95% CI [−0.02702, +0.02413]
bootstrap draws = 1000     n = 120／條件，40 場／條件
supported = False
```

**H6 不成立。**

**此 null 的資訊量，以及它的上限**。由 $\widehat{ab} = a \times b$ 且 $a = 0.31$ 反推
path b 的隱含區間：

$$
b \in \left[\frac{-0.02702}{0.3104},\; \frac{+0.02413}{0.3104}\right] \approx [-0.087,\; +0.078]
$$

**這個區間排除中效果，不排除小效果**，理由有兩層，兩層都會把宣稱往下拉。

**第一層：模擬的 $b_{\text{vote}}$ 與估計出的 path b 不是同一個量。** `layer_power.py`
的 $P(\text{vote}=D) = 0.5 + b_{\text{vote}} \cdot M^{\text{true}}$ 乘的是**真實**誘發變化，
而估計式迴歸的是**觀測**變化 $M^{\text{obs}} = M^{\text{true}} + \eta$。兩者差一個衰減
（§11.2 的 $\rho_{MM}$）。用模擬器自己的產生器實測：

| 模擬設定 | 估計式實際看到的 path b |
|---|---|
| $b_{\text{vote}} = 0.10$（小） | **+0.023** — 落在區間**內** |
| $b_{\text{vote}} = 0.25$（中） | **+0.142** — 落在區間**外** |

**第二層：上面的除法把 $a$ 當成已知。** $a$ 自己的 95% CI 是 [0.125, 0.496]。取下界時
隱含區間變成 $[-0.216,\; +0.193]$，連中效果都框不住。

因此正確的陳述是：**這筆資料能排除中等強度的中介，不能排除微小的中介。** 這仍比
「沒看到」強——中效果在此 $n$ 下的偵測率是 95%，若它存在應該會出現——但遠不到
「排除除極小效果之外的一切」。

**退化情況的處理**（§27）：若某條路徑無變異（例如所有受試者投票一致），path b 無法
配適、bootstrap 無樣本可抽。此時報表印「NOT ESTIMABLE — 0 usable bootstrap draws.
A path is degenerate, not null.」而非「no mediation evidence」。判準亦由
「兩端同號」改為「區間排除 0」——前者會讓退化區間 [0, 0] 通過。

### 6.7 H7 — 威脅的調節作用

H7 有兩個部分。

**(a) 威脅是否強化「誘發保護需求 → 支配型背書」**：

$$
b_c = \text{slope}\bigl(\{\tilde{M}_p\}_{p \in c},\; \{Y_p\}_{p \in c}\bigr)
\qquad\qquad
\Delta b = b_{\text{threat}} - b_{\text{collab}}
$$

結果：協作 −0.005、威脅 −0.006、**差 −0.002，CI [−0.127, +0.155]** → 乾淨的 null。

**(b) 威脅是否縮小認知層與評價層的落差**：

$$
\text{gap}_c = \hat{\beta}^{\text{cog}}_{m}(c) - \hat{\beta}^{(A)}_{m}(c)
\qquad\qquad
\Delta\text{gap} = \text{gap}_{\text{threat}} - \text{gap}_{\text{collab}}
$$

兩個 $\hat{\beta}$ 都在該條件內單獨配適，且皆為標準化係數，因此可直接相減。

| need | 協作 gap | 威脅 gap | 差 | 95% CI | |
|---|---|---|---|---|---|
| **protection** | +0.130 | −0.337 | **−0.467** | **[−0.822, −0.159]** | 排除 0 |
| status | −0.107 | −0.442 | −0.335 | [−0.705, +0.028] | |
| vision | +0.071 | −0.008 | −0.079 | [−0.459, +0.250] | |
| expertise | −0.002 | +0.134 | +0.136 | [−0.235, +0.511] | |
| fairness | +0.094 | −0.168 | −0.261 | [−0.522, +0.160] | |

**protection 的區間排除 0，但方向與假設相反。** H7 預測威脅使兩層**收斂**（落差趨近 0）；
實際上落差由 +0.13 變為 −0.34，絕對值變大且穿過零點。

拆解此差異的來源：

| | 協作 | 威脅 | 差 | 95% CI |
|---|---|---|---|---|
| **認知層** | +0.052 | −0.251 | **−0.303** | **[−0.520, −0.085]** 排除 0 |
| 評價層 | −0.078 | +0.086 | +0.164 | [−0.083, +0.442] |

驅動落差的是認知層：威脅使 protection → 原型的關聯**更負**。兩個差相減
（−0.303 − 0.164 = −0.467）與表中的落差差一致。點估計取自 checkpoint 的確定性重算；
早期版本此處誤植 bootstrap 平均（−0.305 / +0.178），使算術不閉合。

**本研究不將此列為結論**，理由：(i) 五個需求做了五次檢定，α = .05 下期望 0.25 個
假陽性；(ii) 合併後兩層皆為 null，此為「差的差」，容易是雜訊；(iii) 每條件僅 120 人
40 場，per-condition 估計本身不穩；(iv) 方向與假設相反，故 H7 無論如何不成立。

**H7 兩部分皆不成立。**

---

## 7. 測量效度驗證

`run.py measure-check ffni_mediation`。在支付正式研究之前，對每個可在無會議情況下作答的
工具（`about` 為 self 或 prototype）施測**兩次**，中間不發生任何事。36 個 persona ×
2 個工具 × 2 次 = 144 次呼叫，約 8 分鐘、2 美金。

`effectiveness` 無法以此方式檢驗——它詢問「你剛開完的那場會」，而此處沒有會議。
這仍是未解的限制。

### 7.1 四個閘門

`src/render.py:199-236`：

| 閘門 | 判準 | 意義 |
|---|---|---|
| 分量表區辨 | SD(各分量表平均) > 0.30 | 工具是否區分不同構念 |
| 直線作答 | 整份給同一數字的比例 < 0.30 | agent 是否放棄作答 |
| 內部一致性 | **每個被分析讀取的分量表** α > 0.60 | 同一分量表的題目是否測同一件事 |
| 重測穩定 | 平均 test-retest r > 0.40 | 相同條件下能否重現自己的答案 |

**內部一致性閘門為 per-subscale**（§23）。原本是十個分量表取平均，而 `protection`
只對應一個原型維度 `strength`（2 題）——平均會讓 tyranny（10 題）把死掉的 strength
撐過關，使 H4 與 H6 的主線建立在雜訊上。被把關的集合是 `predicts` 值的聯集，
因此無人讀取的維度（femininity）不會擋下研究，而新加入映射的維度會自動被納入。

**重測閘門的上限已移除**（§26）。原本是 `0.40 < r < 0.85`，上限用於捕捉「agent 太穩定，
情境推不動」。但在題序固定且 temperature 為 0 之後，兩次施測是幾乎相同的 prompt，
test-retest 量到的是「相同 prompt 是否給相同答案」——那是量測應有的性質。
FFNI 隨即以 0.89「不合格」，那不是關於 FFNI 的發現。情境能否推動分數，是由 H3 的
path a 在真的發生了事情的資料上回答，不是由「什麼都不發生地問兩次」回答。

### 7.2 三次執行的結果

| | 平均 test-retest | | |
|---|---|---|---|
| | FFNI | leader_ideal | 判決 |
| temperature 0.2，題序每次重洗 | .645 | **.346** | ILT **不合格** |
| temperature 0，題序每次重洗 | .650 | .467 | 合格 |
| temperature 0，**題序依人固定** | **.894** | **.758** | 合格 |

失敗的方向與 §12 的預期相反：不是 agent 太穩定，而是**重現不了自己的答案**。
α 全程良好（.73–.99），45 題也無人直線作答——單次作答內部連貫，兩次之間對不上。

### 7.3 雜訊來源的分解

test-retest 幾乎完全由「人間 SD ÷ 雜訊 SD」決定（temperature 0.2 時）：

| | 人間 SD | 雜訊 SD | 比值 | retest |
|---|---|---|---|---|
| affiliation | 1.36 | 0.63 | 2.15 | .90 |
| sensitivity | 1.06 | 0.70 | 1.52 | .83 |
| **protection** | 0.79 | 1.01 | **0.78** | **.21** |
| **strength** | 0.49 | 0.67 | **0.74** | **.23** |

因此並非「agent 對領導者的看法完全一致而無個體變異」——人間 SD 是實在的。
問題是雜訊與訊號等大。

**temperature 只解決約三分之一**：最差的原型量表接近翻倍（strength .23→.46，
dedication .27→.56，intelligence .18→.41），FFNI 幾乎不動（.645→.650）。

**題序是主因**。固定題序後（第三列），所有雜訊地板約減半：

| | 修正前 | 修正後 |
|---|---|---|
| protection 雜訊 SD | 1.01 | **0.40** |
| protection retest | .26 | **.83** |
| strength retest | .46 | **.81** |
| masculinity retest | .01 | **.63** |

**這是本次工作對統計效力影響最大的單一改動。**

### 7.4 正式研究所用設定下的完整測量指標

`SURVEY_TEMPERATURE = 0`，題序依人固定，36 個 persona：

**FFNI**（1–7）

| 分量表 | 前測平均 | 人間 SD | Δ平均 | Δ SD | α | retest |
|---|---|---|---|---|---|---|
| protection | 5.58 | 0.64 | +0.08 | 0.40 | .93 | .83 |
| affiliation | 5.58 | 1.33 | +0.02 | 0.38 | .99 | .96 |
| status | 2.44 | 0.72 | +0.02 | 0.25 | .93 | .95 |
| vision | 5.78 | 0.77 | +0.06 | 0.30 | .97 | .92 |
| expertise | 5.62 | 0.96 | +0.17 | 0.39 | .97 | .91 |
| fairness | 6.66 | 0.81 | +0.10 | 0.50 | .99 | .79 |

**leader_ideal**（1–10）

| 維度 | 題數 | 前測平均 | 人間 SD | Δ SD | α | retest |
|---|---|---|---|---|---|---|
| strength | 2 | 7.31 | 0.56 | 0.36 | .87 | .81 |
| tyranny | 10 | 2.72 | 0.96 | 0.39 | .92 | .91 |
| masculinity | 2 | 2.53 | 0.88 | 0.70 | .94 | .63 |
| attractiveness | 4 | 4.10 | 0.62 | 0.64 | .92 | .58 |
| sensitivity | 8 | 6.92 | 1.11 | 0.46 | .99 | .91 |
| dedication | 4 | 8.69 | 0.48 | 0.27 | .87 | .84 |
| charisma | 5 | 7.68 | 0.50 | 0.34 | .89 | .76 |
| intelligence | 5 | 8.09 | 0.39 | 0.31 | .82 | .70 |
| femininity | 2 | 2.35 | 0.82 | 0.63 | .97 | .64 |
| ethics | 3 | 8.86 | 0.92 | 0.55 | .99 | .80 |

**仍未解決的問題**：重測閘門仍是取平均。`masculinity`(.63) 與 `attractiveness`(.58)
即使修正後仍偏低，而 `status` 的複合分數正是對這兩者加上 `tyranny` 取平均——
三個出口有兩個信度偏低。若把重測也改為 per-subscale 把關，需先決定門檻。

---

## 8. 檢定力模擬

`tools/layer_power.py`。此前只有投票的檢定力被計算過（`tools/power_sim.py`），
H3–H7 是不同的估計量、不同的資料結構，從未被評估。

**方法**：造合成資料，其中效果量已知，用**真正的**分析函數
（`summarize_layer_moderation`、`summarize_mediation`）去跑，計算「該估計式自己的
bootstrap 區間排除 0」的比例。不用公式，因為分析包含公式處理不了的東西：分層資料、
兩個估計相乘、bootstrap 區間。

**資料產生模型**（每場、每位受試者）：

$$
\begin{aligned}
u_{\text{room}} &\sim \mathcal{N}(0,\, 0.3^2) && \text{該場討論對所有人的共同影響}\\
\ell_p &\sim \mathcal{U}(2,\, 6) && \text{該人的基準需求水準}\\
M^{\text{true}}_p &= \text{lift} + u_{\text{room}} + \varepsilon_p,
  \quad \varepsilon_p \sim \mathcal{N}(0,\, \sigma_{\text{true}}^2)
  && \text{情境真正造成的位移}\\
M^{\text{obs}}_p &= M^{\text{true}}_p + \eta_p,
  \quad \eta_p \sim \mathcal{N}(0,\, \sigma_{\text{noise}}^2)
  && \text{量表報告的位移}\\
\Delta\text{proto}_p &= \beta_{\text{proto}} M^{\text{true}}_p + \mathcal{N}(0,1) &&\\
\text{eff}_p &= 4 + \beta_{\text{eff}} M^{\text{true}}_p + \mathcal{N}(0,1) &&\\
P(\text{vote}_p = D) &= \operatorname{clip}\bigl(0.5 + b_{\text{vote}} M^{\text{true}}_p,\; 0,\; 1\bigr) &&
\end{aligned}
$$

**參數分離**（§26 修正）：`sd_true` 是情境真正推動各人的差異，`sd_noise` 是量表加上的
雜訊，即 measure-check 的 Δ SD。兩者方向相反——原型與投票追隨**真實**變化，而所有
估計式只看得到**觀測**變化，因此雜訊衰減斜率、真實變異支撐檢定力。原本用單一參數
`sd_induced` 同時代表兩者，會使「雜訊地板降低」看起來像「檢定力下降」。

**結果**（`sd_noise = 0.40` 為實測值，`sd_true = 0.5`、`beta_proto = 0.5`、
`beta_eff = 0`、100 reps、200 draws）：

| runs／條件 | H3 | H4 人內 | H5 偽陽性 | H6 (b=.10) | H6 (b=.25) |
|---|---|---|---|---|---|
| 20 | 92% | 65% | **13%** | 20% | — |
| **40** | **100%** | **94%** | **2%** | 31% | **95%** |
| 60 | 100% | 97% | 4% | 44% | 100% |

`beta_eff = 0` 時 H5 那欄是**偽陽性率**而非檢定力——論文的 null 是預期結果，
重要的是它維持在名目 5% 附近。

**樣本數決定：每條件 40 場。**

- H3 已飽和。雜訊地板減半使其由 84%（舊參數）升至 100%。
- **H5 的偽陽性率在 20 場是 13%，40 場才回到名目。這是「40 場是下限」的真正理由，
  而該理由與檢定力無關。** H5 的支配側是預註的預期 null，而由偽陽性率 13% 的檢定
  得出的 null 不可解讀。
- H4 人內為 94%。
- **H6 是懸崖而非斜坡**：小效果時 40 場 31%、60 場 44%（皆不足）；中效果時 40 場已
  95%（無需增加）。多花 50% 預算在兩端都無回報。

H6 的命運因此取決於誘發需求對投票的真實效果量，而非預算。

---

## 9. H4 失敗的診斷

正對照失敗會限制其他結果能推論多遠，因此需要具體診斷而非籠統歸因。

### 9.1 排除計分錯誤

顯著**反向**最明顯的候選原因是反向題未被反轉計分。**兩份工具都沒有反向題**：
FFNI 的四個 protection 題目全為正向敘述（「I wish to have a leader who positions
themselves between my group and an outside threat」），`leader_ideal` 全為特質形容詞
（strong、bold、domineering），評「多符合領導者」。

### 9.2 反向有結構，不是雜訊

protection 對**十個**原型維度分別的偏迴歸係數（前測，六需求模型，240 列）：

| 維度 | β | | 維度 | β |
|---|---|---|---|---|
| charisma | **+0.21** | | strength | **−0.16** |
| ethics | **+0.17** | | masculinity | −0.07 |
| dedication | **+0.15** | | femininity | −0.06 |
| attractiveness | +0.12 | | tyranny | −0.05 |
| sensitivity | +0.04 | | intelligence | −0.02 |

正向側是 charisma、ethics、dedication；負向側是 strength、masculinity、tyranny。
這正是聲望側與支配側的分界，且分割乾淨。**壞掉的量表回傳雜訊，不會回傳一個沿著
理論軸線的連貫反轉。**

### 9.3 「bold」這個詞扛了整個反向

`strength` 只有兩題。分開檢視（24 位中立者的跨場平均分數）：

| | strong | bold |
|---|---|---|
| protection → | **−0.02** | **−0.29** |
| openness → | +0.39 | +0.24 |
| 平均分數 | 7.25 | 7.11 |
| 人間 SD | 0.45 | 0.37 |

**protection 對 "strong" 幾乎無關聯（−0.02），整個反向來自 "bold"（−0.29）。**

一個高保護需求的 persona 是安全取向的，而 "bold（大膽）" 在語義上是**冒險**。
它給 bold 低分不是因為不想要強壯的領導者，而是因為「大膽」讀起來像會冒險。

論文的量表在 Strength 維度上有更多題目來稀釋單一詞的語義；本研究的重建只有 2 題，
其中 1 題的語義恰好與保護需求對衝。**這是量表重建的缺陷（§19 已記錄此風險），
不是心理學發現。**

### 9.4 變異範圍嚴重受限

```
strength   平均 7.18/10   人間 SD 0.39   範圍 6.2 – 8.0
charisma   平均 7.61/10   人間 SD 0.37   範圍 7.0 – 8.2
```

24 個 persona 全部落在 1.8 分的區間內（滿分 10）。所有 agent 都同意領導者該強壯、
該有魅力，剩餘變異極小，一個語義偏誤即足以蓋過真實訊號。

### 9.5 Big Five 在兩端留下相反印記

persona 的需求與原型**皆由同一份 Big Five 描述生成**：

| Big Five | → protection | → strength | → charisma |
|---|---|---|---|
| **openness** | **−0.33** | **+0.34** | +0.10 |
| conscientiousness | +0.23 | +0.17 | −0.19 |
| extraversion | +0.16 | −0.03 | +0.58 |
| agreeableness | +0.28 | +0.15 | +0.22 |
| neuroticism | +0.10 | −0.09 | −0.29 |

openness 把兩者往相反方向拉：低開放性 → 想要保護、但覺得領導者不需要 bold。

人層次的 protection ↔ strength 相關為 **−0.15**（n = 24），與 240 列的偏迴歸係數
−0.16 幾乎相同——**確認此反向完全來自 24 個 persona 之間的既有差異，與討論或情境無關。**

### 9.6 診斷結論與解釋排序

按證據強度：

1. **量表重建的語義缺陷**（§9.3）。直接證據，且可修：Strength 維度僅 2 題，其中
   "bold" 與保護需求語義對衝。
2. **變異範圍受限**（§9.4）。所有原型維度都擠在高分區間，訊號空間小。
3. **persona 生成方式**（§9.5）。需求與原型出自同一份人格描述，其間的關聯是模型
   自身的一致性邏輯，無理由重現人類的個體差異結構。

**此排序修正了 §28 的初始判斷**，該節將「這些是 LLM persona 而非人」列為首要解釋。
證據顯示應反過來：反向的直接來源是可修的量表缺陷。至於「LLM persona 的需求–原型
結構天生不同於人類」這個更大的主張，目前僅 `fairness`（−0.20）尚無此類簡單解釋，
證據強度弱於 §28 所述。

---

## 10. 結果總表

| 假設 | 內容 | 論文做過？ | 結果 | 關鍵數字 |
|---|---|---|---|---|
| H1 | 協作：P > D | 無（雙路徑文獻） | **成立** | p = .017 |
| H2 | 威脅：D > P | 無（同上） | 單獨不成立 | p = .105 |
| — | **交互作用** | 無 | **成立** | Welch p = **.0076** |
| H3 | 威脅提高保護需求 | 無：p.795 列為未來方向 | **成立，且僅此一個需求** | +0.310 [0.125, 0.496] |
| H4 | 需求 → 原型 | **有**：Table 13, p.789 | **不成立；前測顯著反向** | −0.16 [−0.29, −0.02] |
| H5 | 需求 → 有效性（支配側） | **有**：Table 3, p.773 | **null，複製成功** | −0.002 [−0.139, +0.132] |
| H5 | 需求 → 有效性（聲望側） | **有**：Table 3, p.773 | vision/expertise/fairness 未複製；**affiliation 複製** | affiliation +0.151 [+0.013, +0.303] |
| H6 | 中介 | 無：p.795 明言未檢驗 | **不成立** | a×b = −0.0017 [−0.027, +0.024] |
| H7a | 威脅強化 need→票 | 無：p.789 列為待答 | 不成立（null） | −0.002 [−0.127, +0.155] |
| H7b | 威脅縮小兩層落差 | 無 | 不成立（方向相反） | −0.467 [−0.822, −0.159] |

**七個假設中，論文做過的只有 H4 與 H5 兩個**，而它們正是本研究的兩個對照：
H4 為陽性對照、H5 支配側為陰性對照。

---

## 11. 效度威脅

### 11.1 正對照失敗（最嚴重）

H4 是論文的正面結果，本研究做成不成立且前測顯著反向（該反向的成因見 §9，並參見
design log §31 C3——`bold` 在論文實際使用的工具裡屬於 charisma，不屬於 strength）。
H5 聲望側論文預測的 vision / expertise / fairness 三條也未複製。

**但「論文做過的預期有效果部分全部沒複製」並不成立。** `affiliation` 對兩側都複製到了：

| | 我們 | 論文 (Table 3, Model 2) |
|---|---|---|
| affiliation → 聲望側有效性 | **+0.151** [+0.013, +0.303] | Benevolence .31\*\*\*、Team-building .46\*\*\* |
| affiliation → 支配側有效性 | **−0.190** [−0.318, −0.070] | （論文未預測支配側） |

那是論文最強的兩條支持性連結，方向一致且區間排除 0。所以正確的說法是：**論文的正面
結果我們複製到一條、沒複製到四條**（H4 的 protection/status、H5 的 vision/expertise/
fairness），而唯一預期為 null 的那條複製成功。

這使 H6 的 null 必須分兩個範圍陳述：

- **關於本模擬**：誘發的保護需求不預測這些 agent 的背書，而且能排除**中等強度**的中介
  （§6.6）。**此宣稱成立，但範圍比先前版本所寫的小**：小效果排除不了。
- **關於人類**：證據力有限。一群重現不出已知關聯（甚至做成反向）的受試者，在一個
  從未被檢驗的關聯上回報 null，對真實人類母體的推論力薄弱。

行為層結果（交互作用 p = .0076）不受影響——它不依賴原型層。

### 11.2 中介變項的測量

protection 的 retest 為 .83（題序修正後的最佳值），Δ SD 為 0.40。這是整條鏈上
最弱的一環。若真實 path b 存在但被衰減，本研究可能低估它。以 $\sigma_{\text{true}} = 0.5$、
$\sigma_{\text{noise}} = 0.40$ 估計中介變項的信度：

$$
\rho_{MM} = \frac{\sigma_{\text{true}}^{2}}{\sigma_{\text{true}}^{2}+\sigma_{\text{noise}}^{2}}
= \frac{0.25}{0.25+0.16} \approx 0.61
$$

古典衰減公式下，觀測斜率約為真值的 $\rho_{MM}$ 倍。

### 11.3 中介變項的測量時點

中介變項在討論**之後**測量，而投票隨後發生。**一個在討論期間升起、於結束前回落的
需求，在本設計中不可見。**

### 11.4 房間層次的共同原因

path b 在條件內以 40 場中的 120 位受試者估計。bootstrap 重抽 run，因此區間誠實；
但房間層次的共同原因（例如某場的 D 特別強勢，使該場的中立者同時需求上升且投給 D）
不會以中介的形式現形，也不會被此設計排除。

### 11.5 ILT 為重建工具

`leader_ideal` 是 1994 年八因素版加補充題目的重建，非論文所用的 2018 年修訂版
（§19）。已知兩個缺陷：來源附錄列出 40 個特質而其正文稱 41，可能遺漏一個；
所有措辭未經 1994 或 2018 原文核對。`strength` 僅 2 題，而 §9.3 顯示這正是問題所在。

### 11.6 自變項從未被檢核

**沒有任何研究對 P/D 的操弄做過操縱檢核。** `pd_matched` 的 `instruments` 是空的，
`ffni_mediation` 只有 ffni、leader_ideal、effectiveness 三份，全部問的是需求、原型或
對某人的評價，**沒有一份問「你覺得這個人有多支配／多有聲望」**。design log §13 的
操縱檢核測的是**威脅情境**（位置不安穩、時間緊迫、後果嚴重），不是領導風格，而且它
已於 §13 退場。

`tools/sample_bank.py` 的 `STYLE_BLOCKS` 是為本研究撰寫的，沒有引用任何已發表的操弄
材料或量表（本報告亦未宣稱有）。構念定義（Cheng et al. 2013；Henrich & Gil-White
2001）說 dominance 是「透過恐懼與強制」取得影響力，而文字只寫到「讓異議代價高昂」；
§11.6 記錄的投票理由掃描顯示恐懼／強制語言為 **0%**。

支持操弄有效的唯一證據是**行為的**：支配型 claim 領導權的比率在 `gpt-4.1` 上是
0.17–0.25，聲望型是 0.00（§9 的診斷同一批資料）。那證明兩組行為不同，**不證明**它們
是雙路徑模型意義下的支配型與聲望型。

補救最直接的是把 Cheng, Tracy & Henrich 的 Dominance-Prestige Scale 當成
`about: each_candidate` 的操縱檢核，讓中立者在討論後對兩位候選人各評一次。結構與
`effectiveness` 相同，每場多 6 次呼叫。

### 11.7 §13 的操縱證據早於 deadline 修正

§13 的威脅操縱檢核（5.38 vs 3.21）是在 `pd_matched` 的**舊協作情境文字**下收集的，
當時只有威脅條件有 48 小時期限。§2.3 引用該修正時未註明操縱證據位於修正之前。
§13 論證該證據仍可轉移；此處記錄的是那個論證尚未被新資料檢驗。

### 11.8 投票理由與機制的關係

`tools/vote_reason_scan.py` 對 Step 1 的分析顯示：恐懼／強制語言在投票理由中
**完全不存在**（0%），而果斷／負責的措辭占 84%（D 票）。但該比率在協作條件是 82%，
**兩條件幾乎相同**，因此它解釋不了「為什麼威脅造成轉變」。

兩種無法由現有資料區分的解釋：(i) 支配型的行為在威脅情境下**功能上**就是果斷，
而被獎勵的是果斷本身；(ii) LLM 投票者系統性地把支配行為的投票重寫成社會上較體面的
能力語言——若為真，則投票理由與自陳量表皆非通往機制的可靠窗口，而那是本研究
唯一擁有的機制資料。

### 11.9 未預註的探索性發現

以下**不是**預註假設，是在「還有什麼可能」的探索中得出，且在找到它之前檢視了
4 個行為指標，區間未針對此搜尋做校正。**應視為下一個研究的假設，不是本研究的結論。**

以 D 在該場討論的**發言字數佔比**為中介變項，重跑同一個中介估計式：

```
path a    = +0.0182       威脅使 D 多佔約 1.8 個百分點的發言空間   CI [0.001, 0.037]
path b    = +4.464        發言佔比強烈預測該場投 D 的比例          CI [2.965, 6.109]
indirect  = +0.0814       95% CI [+0.0064, +0.1663]
總效果    = +0.2250       被中介的比例 36%，CI [6%, 104%]
```

（對照：protection 的間接效果為 −0.002，CI [−0.027, +0.024]。）

四項限制：(i) 事後分析；(ii) path a 很弱，下界 0.001；(iii) 被中介比例的區間寬至 104%；
(iv) 房間內的因果方向未確立。

此發現與其他所有觀察一致：投票理由 0% 恐懼／84% 果斷、果斷措辭在兩條件幾乎相同
（改變的不是理由而是 D 佔了多少地板）、六個需求與十個原型維度全部不承載效果。

---

## 12. 重現方式

```bash
cd /tmp2/b12902056/agent-sim
python3 test_core.py                                          # 42 項離線檢查

# 不呼叫 API，從既有 checkpoint 重算
python3 run.py report  ffni_mediation threat
python3 run.py report  ffni_mediation collaborative
python3 run.py layers  ffni_mediation                          # H3, H4, H5, H7
python3 run.py mediate ffni_mediation --need protection --group D   # H6
python3 tools/interaction_test.py ffni_mediation               # 交互作用

# 需呼叫 API
python3 run.py measure-check ffni_mediation                    # 144 次，約 2 美金
python3 run.py run ffni_mediation threat                       # 40 場，約 3 小時

# 純 CPU
python3 tools/layer_power.py --reps 100 --runs 20 40 60 --sd-noise 0.4 --sd-true 0.5
python3 tools/power_sim.py                                     # 投票的檢定力
```

`results/**/checkpoints/` 與 `logs/` 不進版控（`.gitignore`），摘要 JSON 與圖表進版控。
重跑同一道 `run` 指令會跳過已完成的場次，只補缺的——中斷、配額用盡或機器重開皆可續跑。

**已知的記錄缺口**：`save_summary` 不記錄產生該摘要的模型與 temperature，因此
`results/` 下的摘要 JSON 無法自證其產生條件。三次 measure-check 的區分目前依賴
檔名後綴（`_t0`、`_fixorder`）與本報告。

---

## 13. 主要程式路徑索引

| 功能 | 位置 |
|---|---|
| CLI | `run.py`（`list` / `validate` / `measure-check` / `run` / `report` / `mediate` / `layers`） |
| 設計載入與驗證 | `src/study.py` |
| 量表載入、`predicts` 驗證、分量表計分 | `src/instrument.py` |
| 抽樣、組場、執行、checkpoint | `src/pipeline.py` |
| 討論、投票、量表施測、fork、題序 | `src/discussion.py` |
| checkpoint 的唯一格式知識 | `src/run_record.py` |
| 統計原語 | `src/stats.py` |
| H1–H7 的估計式 | `src/analysis.py` |
| 報表輸出與閘門判定 | `src/render.py` |
| 交互作用檢定 | `tools/interaction_test.py` |
| 投票檢定力 | `tools/power_sim.py` |
| 層次假設檢定力 | `tools/layer_power.py` |
| persona 產生 | `tools/pair_bank.py` |
| 投票理由掃描 | `tools/vote_reason_scan.py` |
