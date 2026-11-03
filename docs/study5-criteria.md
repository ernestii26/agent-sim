% Study 5 Replication: What the Paper Tested and How It Judged
% agent-sim / ffni_mediation
% 2026-11-03

# 5c: goal and criterion

- **Goal:** do needs predict how effective a leader who meets them seems?
- **Hypotheses:** 13 need → style pairs, all preregistered as positive
- **Data:** China, N = 367; needs at T1, effectiveness at T2
- **Test:** Model 2 (all six needs in), matched β > 0, p < .05
- **A hypothesis holds** if any of its parts does
- *Rule inferred from the paper; the preregistration leaves it open*

::: notes

**5c 想回答什麼。** 論文說（p. 774）：「we specifically hypothesize that each FFN will be positively related to the perceived effectiveness of leaders who satisfy that particular need」。意思是：一個人越需要某種東西（例如保護），就越會覺得「能滿足這個需要的領導者」（例如讓人有安全感的領導者）有效。這是 FFNI 的**效標效度**：量表分數能不能預測一個理論上應該相關的外部結果。

**假設。** 6 種需求各對應 2-3 種領導風格，共 13 個子假設（H1a 到 H6b）。這些風格來自三個領導理論：轉換型領導、家長式領導、地位取得。預先註冊（AsPredicted #223181）把每一個都寫成「正相關」，沒有預期為零的格子。

**資料。** 中國受試者 367 人，分兩次填答：第一次（T1）填需求，第二次（T2）評領導風格的有效性。隔開時間是為了降低同一時間填答造成的共同方法偏誤。我們的 arm B 只有一次作答，沒有隔開時間。

**論文怎麼判定。**

- 用 Model 2：每種領導風格的有效性，同時對六種需求做迴歸。看對應那個需求的 β，要大於 0，而且 p < .05，不做多重比較校正。控制其他五種需求，是要證明效果是「這一種需求」獨有的，不是所有需求共有的。
- 一個假設只要有一個子假設顯著就算成立。例如 H4 有 4a、4b 兩格，4b 不顯著（p = .060），但 H4 仍算成立。

**這個判定規則是從論文的做法推論出來的，論文和預先註冊都沒有明寫。** 預先註冊只寫了迴歸和 SEM 兩種分析，沒有寫顯著門檻、沒有說要不要控制其他需求、也沒有說子假設怎麼彙整成一個假設。論文正文說「These relationships remained significant even after controlling for all other FFNs」，註腳 14 說 SEM 只是「for transparency」附上，所以我們判斷論文以 Model 2 為準。

:::

# 5c result: Table 3, Model 2

| No. | Need → leader style | Model 2 β | p | Part | Hypothesis |
|-----|------------------------------------------|----------|--------|------|-----------|
| 1a | Protection → safety | .05 | .358 | ✗ | **H1 ✗** |
| 1b | Protection → authoritarianism | .01 | .904 | ✗ |  |
| 2a | Affiliation → benevolence | **.10** | .048 | ✓ | **H2 ✓** |
| 2b | Affiliation → team-building | **.36** | < .001 | ✓ |  |
| 3a | Status → narcissism | .04 | .457 | ✗ | **H3 ✗** |
| 3b | Status → authoritarianism | −.02 | .672 | ✗ |  |
| 3c | Status → dominance | .02 | .771 | ✗ |  |
| 4a | Vision → vision communication | **.18** | .001 | ✓ | **H4 ✓** |
| 4b | Vision → high expectation | .10 | .060 | ✗ |  |
| 5a | Expertise → competence | .08 | .161 | ✗ | **H5 ✓** |
| 5b | Expertise → intellectual stimulation | **.13** | .015 | ✓ |  |
| 6a | Fairness → moral character | **.25** | < .001 | ✓ | **H6 ✓** |
| 6b | Fairness → virtue | .08 | .136 | ✗ |  |

::: notes

**這是論文實際用來判定的數字。** Table 3 還有 SEM β 和 Model 1 β，但論文的結論是根據 Model 2，所以這一頁只放 Model 2。完整的 Table 3 在 `docs/study5-data.md` 第 2 節。

**怎麼讀。**

- β 是標準化迴歸係數，同時控制了另外五種需求。β = .25 的意思是：其他五種需求固定時，這種需求高 1 個標準差，有效性評分高 .25 個標準差。
- 13 格中有 5 格顯著（2a、2b、4a、5b、6a）。
- 彙整成假設：H2、H4、H5、H6 成立，H1（protection）和 H3（status）不成立。論文的結論是「our preregistered hypotheses received partial empirical support」（p. 787）。

**值得注意的地方。**

- 有幾格是勉強過關：2a 的 p = .048，剛好低於 .05。4b 的 p = .060，剛好高於 .05，所以不顯著。
- 論文判定「成立」的假設裡，有三個子假設其實不顯著（4b、5a、6b），正文沒有討論。
- 不顯著的 8 格裡，H1 和 H3 的 β 都接近 0（−.02 到 .05），是真的沒有效果。4b、5a、6b 的 β 是 .08-.10，有一點效果，只是不夠大，沒有達到顯著。

:::

# 5c ours: arm B, Model 2

| No. | Need → leader style | Model 2 β | p | Part | Hypothesis |
|-----|------------------------------------------|----------|--------|------|-----------|
| 1a | Protection → safety | **.22** | < .001 | ✓ | **H1 ✓** |
| 1b | Protection → authoritarianism | −.11 | .077 | ✗ | |
| 2a | Affiliation → benevolence | **.67** | < .001 | ✓ | **H2 ✓** |
| 2b | Affiliation → team-building | **.56** | < .001 | ✓ | |
| 3a | Status → narcissism | .07 | .240 | ✗ | **H3 ✓** |
| 3b | Status → authoritarianism | **.14** | .038 | ✓ | |
| 3c | Status → dominance | **.14** | .038 | ✓ | |
| 4a | Vision → vision communication | **.31** | < .001 | ✓ | **H4 ✓** |
| 4b | Vision → high expectation | **.31** | < .001 | ✓ | |
| 5a | Expertise → competence | **.16** | .017 | ✓ | **H5 ✓** |
| 5b | Expertise → intellectual stimulation | **.42** | < .001 | ✓ | |
| 6a | Fairness → moral character | **.17** | .013 | ✓ | **H6 ✓** |
| 6b | Fairness → virtue | .08 | .096 | ✗ | |

::: notes

**這是我們 arm B 的結果，格式和上一頁完全一樣，可以逐格對照。**

- 設定：gpt-4.1 扮演 367 個 persona，英文版量表，temperature 0。每份量表在獨立的 fork 上作答，所以需求和有效性之間只能透過 persona 的設定產生關聯。和論文不同的是，我們沒有分 T1、T2 兩次施測。
- 數字由 `tools/study5_tables.py` 產生（`docs/study5-data.md` 第 2 節），只讀已存的資料，沒有呼叫 API。

**用論文的判定規則（Model 2 β > 0 且 p < .05，一個子假設顯著就算假設成立）：**

- 13 格中 10 格顯著，論文只有 5 格。
- 6 個假設全部成立，論文是 4 個。論文不成立的 H1（protection）和 H3（status），在我們這裡也成立。
- 3b、3c 的 p 都是 .038，剛好過關，β 只有 .14。

**這不代表我們「比論文更成功」。** 論文的規則只看方向和顯著，不看大小。我們有好幾格的 β 遠大於論文：2a 是 .67，論文是 .10；4b 是 .31，論文是 .10；5b 是 .42，論文是 .13。效果比真人大很多，也是一種沒有複製成功。這要用另一種判準來看，後面會講。

**唯一和論文方向不一致的格子：1b（protection → authoritarianism）。** β = −.11，是負的，只是不顯著（p = .077）。論文是 .01，接近 0。

:::

# 5c paper vs ours: 8 of 13 in the PI

| # | Need → leader style | Paper | p | Ours | p | 95% PI | In PI | Sig. |
|-----|------------------------------------|--------|--------|--------|--------|-------------|--------|-------|
| 1a | Protection → safety | .05 | .358 | .22 | <.001 | [−.09, .19] | ✗ ↑ | ✗ |
| 1b | Protection → authoritarianism | .01 | .904 | −.11 | .077 | [−.15, .17] | ✓ | ✓ |
| 2a | Affiliation → benevolence | .10 | .048 | .67 | <.001 | [−.02, .22] | ✗ ↑ | ✓ |
| 2b | Affiliation → team-building | .36 | <.001 | .56 | <.001 | [.22, .50] | ✗ ↑ | ✓ |
| 3a | Status → narcissism | .04 | .457 | .07 | .240 | [−.12, .20] | ✓ | ✓ |
| 3b | Status → authoritarianism | −.02 | .672 | .14 | .038 | [−.19, .15] | ✓ | ✗ |
| 3c | Status → dominance | .02 | .771 | .14 | .038 | [−.15, .19] | ✓ | ✗ |
| 4a | Vision → vision communication | .18 | .001 | .31 | <.001 | [.04, .32] | ✓ | ✓ |
| 4b | Vision → high expectation | .10 | .060 | .31 | <.001 | [−.04, .24] | ✗ ↑ | ✗ |
| 5a | Expertise → competence | .08 | .161 | .16 | .017 | [−.09, .25] | ✓ | ✗ |
| 5b | Expertise → intellectual stimulation | .13 | .015 | .42 | <.001 | [−.02, .28] | ✗ ↑ | ✓ |
| 6a | Fairness → moral character | .25 | <.001 | .17 | .013 | [.08, .42] | ✓ | ✓ |
| 6b | Fairness → virtue | .08 | .136 | .08 | .096 | [−.06, .22] | ✓ | ✓ |

::: notes

**這一頁同時看兩件事：「顯著與否」和「大小」。**

欄位：Paper、Ours 是兩邊的 Model 2 β，各自右邊是 p（檢定 β = 0）。95% PI 是論文 β 的預測區間；✗ ↑ 表示我們的 β 高於區間上限。Sig. 是判準 A。

In PI 本身也是一個 p < .05 的檢定，只是比的對象不是 0，而是論文的值：z = (我們 β − 論文 β) / √(SE論文² + SE我們²)，|z| < 1.96 就落在區間內。所以「區間外」等於「我們和論文的差異顯著」。

**Sig.（判準 A，Open Science Collaboration, 2015）：逐格看，我們的顯著與否和論文一不一致。** 論文顯著的格子，我們要同方向且 p < .05；論文不顯著的格子，我們也要不顯著。13 格中 8 格一致。

- 注意這和前兩頁「假設成立」的規則不一樣。假設成立只要求顯著，所以我們多出來的顯著格子會被算成「成立」。但如果論文是 null，我們卻顯著（3b、3c、4b、5a），以複製來說是**不一致**。

**In PI（判準 C，預測區間，Patil, Peng & Leek, 2016）：我們的 β 有沒有落在「真實效果和論文一樣時，換一批 367 人可能得到的範圍」裡。**

- 算法：論文 β ± 1.96 × √(SE論文² + SE我們²)。兩邊的抽樣誤差都算進去，所以區間比論文自己的信賴區間寬。
- 論文的 SE 從 β 和 p 反推。p < .001 的兩格（2b、6a）和 |β| < .05 的四格（1b、3a、3b、3c）反推不出來，改用其他格子的中位數 .054，這六格的區間是近似值。
- 13 格中 8 格落在區間內。**落在區間外的 5 格全部是「我們太大」**，沒有一格太小：2a（.67 vs .10）、5b（.42 vs .13）、4b、2b、1a。

**兩個判準看的是不同的東西：**

- A（Sig.）只看方向和顯著與否是否和論文一致，不看大小：8/13。
- C（In PI）只看大小是否落在論文的預測區間內，不看顯著與否：8/13。
- 兩個都要求：5/13（1b、3a、4a、6a、6b）。

兩個都是 8/13 只是巧合，沒過的格子並不相同：1a、4b 兩個都沒過；2a、2b、5b 方向和顯著都對，但太大；3b、3c、5a 大小在區間內，但論文不顯著、我們顯著。

**為什麼會太大？** 這 5 格都是 prestige 那一側，或和人格高度相關的需求。persona 的需求幾乎由 OCEAN 設定決定（affiliation 的 R² = .94），有效性評分也是，所以兩者的相關被灌大了（`docs/study5-data.md` 第 8 節）。數字由 `tools/replication_criteria.py` 產生。

:::

# Holding OCEAN fixed: 11 of 13 in the PI

| # | Need → leader style | Paper | Ours | OCEAN fixed | p | 95% PI | In PI |
|-----|---------------------------------|--------|-------|-------------|-------|-----------|-------------|
| 1a | Protection → safety | .05 | .22 | .13 | .017 | [−.10, .20] | ✗↑ → ✓ |
| 1b | Protection → authoritarianism | .01 | −.11 | −.21 | .002 | [−.16, .18] | ✓ → ✗↓ |
| 2a | Affiliation → benevolence | .10 | .67 | .31 | .007 | [−.14, .34] | ✗↑ → ✓ |
| 2b | Affiliation → team-building | .36 | .56 | .36 | .016 | [.05, .67] | ✗↑ → ✓ |
| 3a | Status → narcissism | .04 | .07 | .07 | .349 | [−.14, .22] | ✓ → ✓ |
| 3b | Status → authoritarianism | −.02 | .14 | .11 | .127 | [−.20, .16] | ✓ → ✓ |
| 3c | Status → dominance | .02 | .14 | .15 | .034 | [−.15, .19] | ✓ → ✓ |
| 4a | Vision → vision communication | .18 | .31 | .22 | <.001 | [.04, .32] | ✓ → ✓ |
| 4b | Vision → high expectation | .10 | .31 | .26 | <.001 | [−.05, .25] | ✗↑ → ✗↑ |
| 5a | Expertise → competence | .08 | .16 | .16 | .042 | [−.11, .27] | ✓ → ✓ |
| 5b | Expertise → intellectual stimulation | .13 | .42 | .12 | .016 | [−.01, .27] | ✗↑ → ✓ |
| 6a | Fairness → moral character | .25 | .17 | .17 | .021 | [.07, .43] | ✓ → ✓ |
| 6b | Fairness → virtue | .08 | .08 | .08 | .081 | [−.06, .22] | ✓ → ✓ |

::: notes

**這一頁回答：為什麼我們的效果比論文大？答案是兩邊共用同一組 OCEAN 設定。**

**背景：persona 的需求和有效性是在不同的 fork 上分開作答的。** 兩份問卷之間沒有共享記憶，所以它們之所以相關，只能是因為兩邊讀到同一份 persona 設定：OCEAN 等級和描述文字。如果 OCEAN 同時推高「需求」和「覺得這種領導有效」，兩者就會被灌出相關。

**怎麼算（`tools/ocean_confound.py`，只讀已存資料，沒有呼叫 API）：**

**這是對已有資料的統計控制，不是把 OCEAN 從 persona 拿掉重跑；persona 作答時仍然看得到 OCEAN。** 它回答的是「現有資料中，扣掉 OCEAN 的影響後還剩多少效果」，不是「沒有 OCEAN 的 persona 會怎麼答」。它也只扣得掉 OCEAN 的主效應，扣不掉特質之間的交互作用，或描述文字中和 OCEAN 相關的內容。


- Paper、Ours：兩邊原本的 Model 2 β（同前一頁）。
- OCEAN fixed（控制 OCEAN 後的 β）：同一個 Model 2，再加上 persona 的 5 個 OCEAN 等級當控制變項（每個特質用 medium、high 兩個虛擬變項，共 10 個）。意思是「OCEAN 設定完全一樣的 persona 之間，這個需求還能預測多少有效性」。p 是這個 β 的 p。
- 95% PI：用控制後的 β 的 SE 重算的論文預測區間。In PI 欄是「控制前 → 控制後」。

**結果：** In PI 從 8/13 變 11/13。偏大的 5 格裡有 4 格回到區間內。

- 5b 從 .42 降到 .12，論文 .13；2b 從 .56 降到 .36，論文 .36，幾乎一模一樣。
- 4b 仍然偏大（.26，上限 .25）。

**要小心的地方：**

1. **2a 回到區間內，有一半是因為區間變寬。** affiliation 有 94% 的變異被 OCEAN 解釋，控制 OCEAN 後它剩下的變異很少，所以 β 的 SE 從 .037 漲到 .114（2b 從 .046 到 .149），PI 跟著變寬。β 確實從 .67 降到 .31，但仍是論文 .10 的三倍。其他格子的 SE 只變動 .01 以內。
2. **1b 變成顯著的負值（−.21），跑到區間下方。** 扣掉人格之後，保護需求高的 persona 反而覺得威權式領導比較沒效。論文是 .01。
3. **判準 A（顯著與否一致）沒有改善，仍是 8/13，只是換了一批格子。** 論文顯著的 5 格，我們全部仍顯著；論文不顯著的 8 格裡，我們有 5 格顯著（1a、1b、3c、4b、5a）。兩個判準都過的格子從 5 變 8。
4. **不能說成「去掉 OCEAN 就複製成功」。** 真人的需求也和人格有關（補充資料 S9.1，|r| 最高 .27），論文的 β 裡本來就有人格的成分，只是沒有我們這麼強。比較站得住的說法是：persona 的人格對需求影響太強，大約是真人的兩倍（平均 |r| .29 vs .12）。剩下沒解釋的部分可能來自描述文字，這部分我們沒有模型化。

**用 r 看也是同樣的結論：** 原始 r .32-.82 的 9 格，扣掉 OCEAN 後剩 .15-.33，和論文的 r .20-.46 同一個量級（`docs/study5-data.md` 第 8 節）。

:::

# 結論

- **照論文的規則**：6 個假設全部成立（論文 4 個），13 格中 10 格顯著
- **逐格比較**：方向與顯著性一致 8/13，大小落在 PI 內 8/13，兩者都過只有 5/13
- **沒過的主因是效果太大**：偏離 PI 的 5 格全部偏大，沒有偏小
- **原因**：需求和有效性都被同一組 OCEAN 設定推動，人格的影響約為真人的 2 倍
- **固定 OCEAN 後** 11/13 落在 PI 內：方向對，但效果量（effect size）被放大

::: notes

**一句話：persona 抓到了「哪種需求對應哪種領導」，但效果被人格放大了。**

- 只看論文自己的規則（顯著就算成立），我們甚至比論文「更成功」。但這個規則不看大小，所以會把「效果太大」也算成成功。
- 加上預測區間之後才看得出問題：偏離的格子全部是我們太大，例如 affiliation → benevolence 論文 .10、我們 .67。
- persona 的需求和有效性是分開作答的，唯一的共同來源是 persona 設定。persona 的需求和 OCEAN 的平均 |r| 是 .29，真人是 .12（補充資料 S9.1），所以人格把兩邊一起推高。
- 固定 OCEAN 之後大部分格子回到真人範圍，代表需求本身有接近真人的預測力。但這是事後的統計控制，persona 實際的作答仍然不像真人；而且真人的數據也含有人格成分，論文沒有控制，所以不能說「去掉 OCEAN 就複製成功」。

**還沒解決的格子：**

- 4b（vision → high expectation）：固定 OCEAN 後仍偏大（.26 vs .10）。
- 2a（affiliation → benevolence）：固定 OCEAN 後 .31，仍是論文的 3 倍，進區間有一部分是因為 SE 變大。
- 1b（protection → authoritarianism）：固定 OCEAN 後變成顯著的負值（−.21），論文 .01。
- 1a（protection → safety）：論文 null，我們固定 OCEAN 後仍顯著（.13，p = .017），但在 PI 內。

**dominance 那一側（H1b、H3）不是問題：** 論文 H1、H3 本來就不成立，所以複製目標是 null。我們的 1b、3a、3b、3c 全部在 PI 內；3b、3c 的 p = .038 剛好顯著，但 13 格做 Bonferroni 校正（門檻 .0036）就不顯著，可以算大致和論文一致。要正式宣稱 null 也複製成功，需要等價檢定（判準 D），還沒有算。

:::

# 還沒複製的部分：可能的方向

- **校準人格強度**：OCEAN 和需求的相關降到真人水準（S9.1 平均 .12）
- **加入 OCEAN 以外的屬性**：誠實謙遜、不確定焦慮、年齡、性別
- **用 S9 校準、Study 5 驗證**，避免對答案調參
- *都需要呼叫 API，執行前先估次數並確認*

::: notes

**1. 校準人格的強度（最優先）。** 問題的根源是 persona 的人格對需求影響太強。目標是讓 persona 的「OCEAN 和需求的相關」接近補充資料 S9.1 的真人數據（|r| ≤ .27，平均 .12），而不是現在的平均 .29、最高 .89。可能的做法：OCEAN 不只用低、中、高三級，或在描述中降低人格的份量。這就是先前提的 S9 校準 pilot，估計約 260 次呼叫。

**2. 加入 OCEAN 以外的個體差異。** 目前 persona 的個體差異幾乎只來自 OCEAN（affiliation 有 94% 被 OCEAN 解釋），所以所有相關都會經過 OCEAN。加入其他有文獻支持、而且和需求有關的屬性，讓需求有獨立於 OCEAN 的變異：

- 誠實謙遜（HEXACO 的 Honesty-Humility）：S9.1 中和 status 需求 −.26、fairness 需求 +.27。
- 對未來的不確定焦慮（prospective uncertainty anxiety）：S9.1 中和 protection 需求 .22。
- 年齡：S9.1 中和 status 需求 −.19。性別也是論文的人口變項。

**3. 驗證方式。** 用 S9（需求和人格的相關）當校準目標，Study 5 只用來驗證，不拿 Study 5 的結果來調 persona。這樣如果 Study 5 變好，才能說是 persona 更像真人，而不是對著答案調參數。

**另一個選項：Park et al. (2024) 的訪談式 agent。** 他們用 2 小時訪談逐字稿建立 agent，比 persona 段落更接近真人（GSS .85 vs .70），但逐字稿資料受限，每份約 6,491 字，token 成本高，目前不建議優先做。

:::

# 5a: goal and criterion

- **Goal:** which needs shape followers' picture of the ideal leader (implicit leadership theories, ILT)?
- **No hypotheses:** "the precise pattern … remains to be determined empirically" (p. 774)
- **Data:** US, N = 261; ILT has 11 dimensions, 51 items rated 1-10
- **Test:** each dimension on all six needs (11 × 6 = 66 cells); a need counts if its ΔR² has p < .05
- **Which need leads:** relative weights split each R² among the six needs (RW%)
- **Reading:** results grouped by the dual model, dominance vs prestige prototypes

::: notes

**5a 想回答什麼。** ILT（implicit leadership theories，內隱領導理論）是一個人心中「理想的領導者應該長什麼樣」的原型，例如要有魄力、要聰明、要有道德。5a 問的是：不同的需求，會不會讓人心中的理想領導者長得不一樣？例如需要保護的人，會不會更看重領導者的「強壯」（strength）？

**沒有假設。** 和 5c 不同，5a 沒有預先註冊，也沒有事先預測哪個需求對應哪個維度。論文說（p. 774）：「we expect that distinct FFNs will systematically align with different leadership prototypes, though the precise pattern of these associations remains to be determined empirically」。所以 5a 是探索性分析，沒有「成立 / 不成立」的判定。

**資料。** 美國受試者 261 人（Sample B 的一組），用 generic 版的需求量表（不限定工作情境）。ILT 量表是 Offermann & Coats (2018)，51 題，1-10 分，分成 11 個維度：sensitivity、dedication、tyranny、charisma、strength、creativity、well-groomed、masculinity、intelligence、femininity、ethics。我們的 arm A 也是 261 個 persona。

**做法。** 每個 ILT 維度各做一次迴歸，同時放進六個需求，所以是 11 × 6 = 66 格。每一格看 ΔR²：把這個需求從模型中拿掉，R² 會掉多少。ΔR² 的 p < .05，論文就說這個需求「uniquely predicts」這個維度，意思是控制其他五個需求後，它還有獨特的預測力。ΔR² 的檢定和 Model 2 β 的 t 檢定是同一個檢定（F = t²），所以 p 相同。

**哪個需求主導：relative weights。** ΔR² 只回答「有沒有獨特貢獻」。論文另外用 relative weights（Johnson, 2000）回答「六個需求裡誰最重要」：把這個維度的 R² 分給六個需求，RW% 是每個需求分到的比例，六個加起來是 100%。和 ΔR² 不同，RW 會把需求之間共享的解釋力也分出去，所以就算需求彼此高度相關，也能比較誰比較重要。正文的用法例如：「Relative weights analysis further revealed protection had the largest weight (.06), accounting for 35.35% of the total R²」（strength）。

**論文怎麼解讀。** 論文用雙模型（dual model）把結果分成兩類：

- dominance 類原型（strength、tyranny、masculinity、well-groomed）：主要由 protection 和 status 預測。
- prestige 類原型（sensitivity、dedication、charisma、creativity、intelligence、ethics）：主要由 vision、expertise、fairness 預測。

5c 的討論也用到這個結果：protection 和 status 會影響理想領導者的原型（5a 有效果），但不影響對 dominance 類風格有效性的判斷（5c 沒效果）。

:::

# 5a result, part 1: the 14 significant cells

| Type | Need → ILT dimension | ΔR² | p | RW% | RW rank |
|------|------------------------------------|------|--------|-------|--------|
| D | Protection → strength | .03 | .004 | 35.4 | 1 |
| D | Status → tyranny | .06 | <.001 | 64.0 | 1 |
| D | Status → masculinity | .02 | .019 | 55.1 | 1 |
| D | Status → well-groomed | .05 | <.001 | 55.1 | 1 |
| P | Vision → sensitivity | .01 | .044 | 23.8 | 2 |
| P | Vision → dedication | .03 | .001 | 28.2 | 2 |
| P | Vision → charisma | .01 | .049 | 22.1 | 2 |
| P | Vision → creativity | .02 | .018 | 27.5 | 1 |
| P | Expertise → sensitivity | .04 | <.001 | 34.7 | 1 |
| P | Expertise → charisma | .02 | .008 | 26.5 | 1 |
| P | Expertise → intelligence | .02 | .018 | 22.8 | 2 |
| P | Fairness → dedication | .03 | <.001 | 29.8 | 1 |
| P | Fairness → intelligence | .03 | .003 | 31.9 | 1 |
| P | Fairness → ethics | .04 | <.001 | 39.0 | 1 |

::: notes

**這是論文 66 格中 ΔR² 顯著的 14 格**，也是論文正文逐一討論、給出精確 p 的格子（pp. 786-787）。欄位用的是論文正文實際在看的指標：ΔR² 和 relative weights。

**欄位：**

- Type：D = dominance 類原型，P = prestige 類原型（論文的分類）。
- ΔR²：控制其他五個需求後，這個需求獨特解釋的變異比例。ΔR² = .03 代表多解釋了 3%。論文用它判斷「有沒有獨特預測力」。
- p：ΔR² 的 p（和 Model 2 β 的 p 相同，是同一個檢定）。
- RW%：relative weight 占 R² 的百分比。把這個維度的 R² 分給六個需求，這個需求分到多少。論文用它判斷「哪個需求最重要」，例如「protection had the largest weight (.06), accounting for 35.35% of the total R²」。
- RW rank：這個需求的 RW% 在六個需求中排第幾。1 = 主導這個維度的需求。

**怎麼讀：**

- dominance 類 4 格的需求都排第 1，而且 status 占了 tyranny、masculinity、well-groomed 的 55-64%。這就是論文說「status 主導 dominance 類原型」的根據。
- prestige 類 10 格都由 vision、expertise、fairness 預測，排第 1 或第 2。這三個需求在 prestige 類原型裡互相競爭，例如 dedication 是 fairness（29.8%）和 vision（28.2%）幾乎平分。
- affiliation 一格都沒有。
- ΔR² 都不大（.01-.06）。有兩格是勉強過關：vision → sensitivity（p = .044）、vision → charisma（p = .049）。

:::

# 5a result, part 2: the 52 null cells

| ILT dimension | Protection | Affiliation | Status | Vision | Expertise | Fairness |
|---------------------|-----------|-----------|-----------|-----------|-----------|-----------|
| Sensitivity | 7.1 | 19.7 | 2.8 | ● | ● | 11.9 |
| Dedication | 9.5 | 20.4 | 1.8 | ● | 11.2 | ● |
| Tyranny | 21.2 | 2.9 | ● | 3.1 | 3.6 | 5.2 |
| Charisma | 10.1 | 19.4 | 11.9 | ● | ● | 10.1 |
| Strength | ● | 10.2 | 19.0 | 17.8 | 7.5 | 10.2 |
| Creativity | 11.6 | 22.7 | 5.6 | ● | 18.6 | 14.0 |
| Well-groomed | 19.4 | 5.5 | ● | 8.7 | 8.9 | 2.4 |
| Masculinity | 11.2 | 4.9 | ● | 12.9 | 13.6 | 2.2 |
| Intelligence | 9.2 | 10.3 | 3.3 | 22.5 | ● | ● |
| Femininity | 29.3 | 20.2 | 8.2 | 6.3 | 23.5 | 12.6 |
| Ethics | 3.9 | 15.8 | 2.4 | 23.6 | 15.2 | ● |

::: notes

**這是論文 66 格中另外 52 格，ΔR² 都不顯著（p ≥ .05）。** 數字是 RW%。● 是上一頁的 14 格顯著格子。論文沒有給這 52 格的精確 p，只能從沒有星號知道 p ≥ .05。

**為什麼要看這一頁：** 複製不只要做出論文有的效果，也要在論文沒有效果的地方「沒有效果」。如果 persona 在這裡也顯著，代表 persona 的需求「什麼都預測」，不像真人。

**怎麼讀：**

- RW% 不小但 ΔR² 不顯著的格子很多，例如 affiliation 在 sensitivity、dedication、creativity 都占 20% 左右。RW 包含和其他需求「共享」的解釋力，ΔR² 只算「獨特」的部分。affiliation 和其他需求相關很高，所以分得到解釋力，但沒有獨特的貢獻。
- femininity 整列都不顯著（R² 只有 .02），RW% 雖然分得很散，但總量極小。
- affiliation 整欄都不顯著。

:::

# 5a ours, part 1: 10 of 14 significant

| Type | Need → ILT dimension | ΔR² | p | RW% | RW rank | p < .05 |
|------|------------------------------------|------|--------|-------|--------|-------|
| D | Protection → strength | .00 | .557 | 0.7 | 6 | ✗ |
| D | Status → tyranny | .04 | <.001 | 21.5 | 2 | ✓ |
| D | Status → masculinity | .00 | .368 | 5.8 | 5 | ✗ |
| D | Status → well-groomed | .00 | .272 | 3.8 | 6 | ✗ |
| P | Vision → sensitivity | .00 | .025 | 8.3 | 4 | ✓ |
| P | Vision → dedication | .07 | <.001 | 48.7 | 1 | ✓ |
| P | Vision → charisma | .02 | .002 | 21.5 | 3 | ✓ |
| P | Vision → creativity | .01 | .010 | 29.0 | 2 | ✓ |
| P | Expertise → sensitivity | .01 | .005 | 14.2 | 3 | ✓ |
| P | Expertise → charisma | .01 | .036 | 18.1 | 4 | ✓ |
| P | Expertise → intelligence | .03 | <.001 | 35.6 | 1 | ✓ |
| P | Fairness → dedication | .01 | .033 | 14.1 | 3 | ✓ |
| P | Fairness → intelligence | .00 | .261 | 12.3 | 4 | ✗ |
| P | Fairness → ethics | .01 | .032 | 20.9 | 2 | ✓ |

::: notes

**這是我們 arm A 的結果，格子和論文的 14 格一一對應，欄位相同。** gpt-4.1 扮演 261 個 persona，用 generic 版需求量表和 ILT 量表，temperature 0。數字由 `tools/study5_tables.py` 產生（`docs/study5-data.md` 第 3 節），沒有呼叫 API。

**怎麼讀：**

- **顯著與否：** 14 格中 10 格顯著。沒過的 4 格裡 3 格是 dominance 類（strength、masculinity、well-groomed），另一格是 fairness → intelligence。
- **主導的需求換人了（RW rank）：** 論文 14 格中有 10 格排第 1；我們只有 2 格（vision → dedication、expertise → intelligence）。
  - dominance 類：論文 4 格都排第 1，我們排第 2、5、6、6。strength 的 protection 只占 0.7%（論文 35.4%）。
  - 連顯著的 prestige 格子，排名也往後掉，因為第 1 名大多被 affiliation 拿走（見下一頁）。
- 所以「顯著」10/14 看起來不錯，但論文要講的「哪個需求主導哪個原型」，我們大部分沒有複製出來。
- ΔR² 顯示 .00 的顯著格子（例如 vision → sensitivity）是四捨五入，實際約 .004。

:::

# 5a ours, part 2: 26 of 52 nulls significant

| ILT dimension | Protection | Affiliation | Status | Vision | Expertise | Fairness |
|---------------------|-----------|-----------|-----------|-----------|-----------|-----------|
| Sensitivity | 3.8 | **54.0** | **4.2** | ● | ● | 16.3 |
| Dedication | 0.5 | 7.2 | **6.4** | ● | 23.8 | ● |
| Tyranny | 3.5 | **42.2** | ● | 6.5 | 10.4 | 16.6 |
| Charisma | **1.1** | **26.6** | **25.8** | ● | ● | 7.6 |
| Strength | ● | **9.7** | **49.5** | **24.8** | 9.0 | 7.1 |
| Creativity | **8.4** | 10.5 | **5.4** | ● | **36.0** | **11.4** |
| Well-groomed | **22.3** | **35.4** | ● | **20.8** | 6.5 | 12.0 |
| Masculinity | 27.8 | **51.4** | ● | 1.8 | 6.8 | 7.2 |
| Intelligence | **4.3** | **16.3** | 2.4 | **29.8** | ● | ● |
| Femininity | 14.6 | **60.6** | 1.2 | 4.0 | **5.0** | 15.4 |
| Ethics | 2.4 | **39.1** | 4.0 | **14.3** | **20.0** | ● |

::: notes

**這是論文不顯著的 52 格，我們的 RW%。** 粗體 = 我們的 ΔR² p < .05（論文在這些格子都不顯著）。● 是論文顯著的 14 格。

**怎麼讀：**

- 52 格中 26 格我們顯著，論文一格都沒有。persona 的需求「什麼都預測」。
- **affiliation 最嚴重：** 論文整欄不顯著，我們 11 格中 9 格顯著，而且在 7 個維度排第 1：sensitivity 54%、femininity 61%、masculinity 51%、tyranny 42%、ethics 39%、well-groomed 35%、charisma 27%。原因是 persona 的 affiliation 有 92% 的變異被 OCEAN 解釋（arm A），幾乎就等於「親和性設定」，所以會滲進所有和親和性有關的原型。
- **strength 被 status 拿走：** 論文 strength 由 protection 主導（35%），我們是 status（50%），protection 只有 0.7%。
- 有些粗體格的 RW% 很小（例如 charisma 的 protection 1.1%）。那是因為 β 是負的：控制其他需求後有獨特的負向效果，但 RW 只算解釋力的大小，不分正負。

**和 5c 的關係：** 5c 只看 13 個假設格子，看不到這種「多出來的效果」。5a 有完整的 66 格，才看得出 persona 的需求之間缺乏區辨力。

:::

# 5a paper vs ours: 9 of 14 pass both

| Type | Need → ILT dimension | Paper | p | Ours | p | 95% PI | In PI | Sig. | RW rank |
|------|------------------------------|-------|-------|-------|-------|------------|-------|------|---------|
| D | Protection → strength | .26 | .004 | .04 | .557 | [.05, .47] | ✗ ↓ | ✗ | 1 → 6 |
| D | Status → tyranny | .32 | <.001 | .28 | <.001 | [.11, .53] | ✓ | ✓ | 1 → 2 |
| D | Status → masculinity | .19 | .019 | .07 | .368 | [−.03, .41] | ✓ | ✗ | 1 → 5 |
| D | Status → well-groomed | .30 | <.001 | .08 | .272 | [.09, .51] | ✗ ↓ | ✗ | 1 → 6 |
| P | Vision → sensitivity | .20 | .044 | .09 | .025 | [−.01, .41] | ✓ | ✓ | 2 → 4 |
| P | Vision → dedication | .30 | .001 | .41 | <.001 | [.07, .53] | ✓ | ✓ | 2 → 1 |
| P | Vision → charisma | .19 | .049 | .22 | .002 | [−.04, .42] | ✓ | ✓ | 2 → 3 |
| P | Vision → creativity | .24 | .018 | .18 | .010 | [.00, .48] | ✓ | ✓ | 1 → 2 |
| P | Expertise → sensitivity | .32 | <.001 | .12 | .005 | [.13, .51] | ✗ ↓ | ✓ | 1 → 3 |
| P | Expertise → charisma | .22 | .008 | .15 | .036 | [.01, .43] | ✓ | ✓ | 1 → 4 |
| P | Expertise → intelligence | .21 | .018 | .27 | <.001 | [−.02, .44] | ✓ | ✓ | 2 → 1 |
| P | Fairness → dedication | .25 | <.001 | .20 | .033 | [.01, .49] | ✓ | ✓ | 1 → 3 |
| P | Fairness → intelligence | .26 | .003 | .11 | .261 | [.01, .51] | ✓ | ✗ | 1 → 4 |
| P | Fairness → ethics | .29 | <.001 | .16 | .032 | [.07, .51] | ✓ | ✓ | 1 → 2 |

::: notes

**這一頁把論文和我們的 14 格並排，用和 5c 一樣的兩個判準，再加上論文正文看的 RW 排名。** 數字由 `tools/replication_criteria.py` 和 `tools/study5_tables.py` 產生，沒有呼叫 API。

**欄位：**

- Paper β、Ours β：Model 2 的標準化係數；各自右邊的 p 是 ΔR² 的 p（和 β 是同一個檢定）。論文的 p 用正文的精確值。
- 95% PI：論文 β 的預測區間，論文 β ± 1.96 × √(SE論文² + SE我們²)。論文的 SE(β) 由 Table 13 的 SE(b) 換算：SE(b) × β / b。✗ ↓ = 我們低於區間下限。
- In PI（判準 C）：大小是否和論文相容，等於「和論文的差異不顯著」。
- Sig.（判準 A）：論文這 14 格都顯著，所以我們要同方向且 p < .05。
- RW rank：論文 → 我們，這個需求的 RW% 在六個需求中排第幾。

**結果：**

- Sig. 10/14，In PI 11/14，兩者都過 9/14。
- **和 5c 方向相反：** 5c 偏離 PI 的格子全部偏大；5a 偏離 PI 的 3 格全部偏小（strength、well-groomed、expertise → sensitivity）。5a 的問題不是效果被放大，而是該有的效果沒出來，或者被別的需求搶走。
- **dominance 類只有 tyranny 過關。** strength、well-groomed 兩個判準都沒過；masculinity 在 PI 內但不顯著（論文 .19 本來就不大，PI 很寬）。
- **RW rank：** 論文 14 格中 10 格排第 1，我們只有 2 格。即使兩個判準都過的 9 格，大多數排名也往後掉（例如 fairness → ethics 1 → 2、expertise → charisma 1 → 4）。第 1 名大多被 affiliation 拿走（前一頁）。

**所以 5a 的結論要分兩層：** 逐格看，prestige 類大致複製（9/10 顯著）；但論文用 RW 講的「哪個需求主導哪個原型」，我們幾乎沒有複製，dominance 類更是幾乎全部失敗。

:::

# 5a: OCEAN drives prestige only

| Type | Need → ILT dimension | Paper | Ours | Overlap | OCEAN fixed | p | In PI |
|------|------------------------------|-------|-------|---------|-----------|-------|------------|
| D | Protection → strength | .26 | .04 | −.06 | .01 | .908 | ✗↓ → ✗↓ |
| D | Status → tyranny | .32 | .28 | .48 | .27 | .001 | ✓ → ✓ |
| D | Status → masculinity | .19 | .07 | .08 | .11 | .237 | ✓ → ✓ |
| D | Status → well-groomed | .30 | .08 | .15 | .04 | .651 | ✗↓ → ✗↓ |
| P | Vision → sensitivity | .20 | .09 | .60 | .03 | .423 | ✓ → ✓ |
| P | Vision → dedication | .30 | .41 | .97 | .18 | .026 | ✓ → ✓ |
| P | Vision → charisma | .19 | .22 | .75 | −.00 | .959 | ✓ → ✓ |
| P | Vision → creativity | .24 | .18 | .84 | .04 | .512 | ✓ → ✓ |
| P | Expertise → sensitivity | .32 | .12 | .75 | .10 | .018 | ✗↓ → ✗↓ |
| P | Expertise → charisma | .22 | .15 | .67 | .07 | .262 | ✓ → ✓ |
| P | Expertise → intelligence | .21 | .27 | .96 | .12 | .159 | ✓ → ✓ |
| P | Fairness → dedication | .25 | .20 | .56 | .14 | .148 | ✓ → ✓ |
| P | Fairness → intelligence | .26 | .11 | .62 | .13 | .186 | ✓ → ✓ |
| P | Fairness → ethics | .29 | .16 | .92 | .17 | .022 | ✓ → ✓ |

::: notes

**這一頁回答：5a 為什麼 prestige 類做得出來、dominance 類做不出來？** 方法和 5c 那頁一樣（`tools/ocean_confound.py`，只讀已存資料，沒有呼叫 API）。

**欄位：**

- Paper、Ours：Model 2 β（同前一頁）。
- Overlap：需求被 OCEAN 預測的部分，和 ILT 維度被 OCEAN 預測的部分，兩者的相關。接近 1 = 兩邊被同一組人格特質推動；接近 0 = 兩邊沒有共同的人格來源。
- OCEAN fixed：同一個 Model 2 再加上 OCEAN 的 10 個虛擬變項當控制變項後的 β；p 是它的 p。**這是對已有資料的統計控制，不是重跑 persona。**
- In PI：控制前 → 控制後，PI 用控制後的 SE 重算。

**怎麼讀：**

- **prestige 類：overlap .56-.97，靠 OCEAN 撐起來。** 固定 OCEAN 後，10 格中只剩 3 格顯著（vision → dedication、expertise → sensitivity、fairness → ethics），其他 7 格的 β 掉到 −.00 到 .14。也就是說，我們在 5a 複製出來的 prestige 效果，大部分只是「需求和 ILT 都跟著同一組人格設定走」。
- **dominance 類：overlap 只有 −.06 到 .15（tyranny 例外，.48）。** OCEAN 推不動這一側，persona 也沒有其他來源，所以 strength、masculinity、well-groomed 本來就沒有效果，固定 OCEAN 前後都一樣。
- **tyranny 是唯一的例外：** overlap .48，而且固定 OCEAN 後 β 幾乎不變（.28 → .27）。status → tyranny 有一部分獨立於 OCEAN 的連結。
- In PI 前後都是 11/14，但兩個判準都過的格子從 9 掉到 3（tyranny、vision → dedication、fairness → ethics），因為顯著的格子變少了。

**和 5c 的對比：**

- 5c：效果被 OCEAN **放大**，固定 OCEAN 後大多回到論文的大小，而且仍然顯著。
- 5a：prestige 類效果大多**只靠** OCEAN，固定後就消失；dominance 類則是 OCEAN 沒有作用，效果一開始就不存在。
- 兩邊的共同點：persona 的個體差異幾乎只來自 OCEAN。OCEAN 有關的地方效果太強或全靠它，OCEAN 無關的地方就沒有效果。

**要小心的地方：** 真人的數據也含有人格成分，論文沒有控制人格，我們不知道真人的效果在控制人格後還剩多少。所以這一頁不是拿「固定 OCEAN 後」和論文比，而是說明 persona 的效果從哪裡來。

:::

# 5a 結論

- **逐格看**：14 格中 10 格顯著、11 格在 PI 內，兩者都過 9 格
- **主導的需求沒複製**：RW 排第 1 的格子論文 10 格、我們 2 格，多被 affiliation 拿走
- **論文 null 的 52 格，我們 26 格顯著**：persona 的需求缺乏區辨力
- **dominance 類只做出 tyranny**：OCEAN 推不動這一側，persona 沒有其他來源
- **prestige 類靠 OCEAN 撐起來**：固定 OCEAN 後 10 格只剩 3 格顯著

::: notes

**一句話：5a 表面上複製了 prestige 類，但論文真正要講的「不同需求對應不同原型」，persona 沒有做出來。**

- **逐格看還可以。** 照和 5c 一樣的判準，14 格中 9 格兩個判準都過，比 5c 的 5/13 好。但這只看了論文顯著的 14 格。
- **論文用 RW 講「哪個需求主導哪個原型」，這一點沒有複製。** 論文 14 格中 10 格的需求在該維度排第 1，我們只有 2 格。affiliation 在論文中一格都不顯著，在我們這裡卻在 7 個維度排第 1。
- **多出來的效果很多。** 論文不顯著的 52 格，我們有 26 格顯著。persona 的六個需求沒有各自的分工，而是一起跟著人格設定走，什麼都預測。
- **dominance 類失敗的原因：** strength、masculinity、well-groomed 和需求之間沒有共同的人格來源（overlap −.06 到 .15）。persona 的個體差異幾乎只來自 OCEAN，OCEAN 推不動的地方就沒有效果。唯一做出來的 tyranny，有一部分連結不經過 OCEAN。
- **prestige 類成功的原因也是 OCEAN：** overlap .56-.97，固定 OCEAN 後 10 格只剩 3 格顯著。我們做出來的效果，大部分是「需求和原型都跟著同一組人格設定走」。

**和 5c 的關係：**

- 5c 的問題是效果被 OCEAN **放大**；5a 的問題是效果**只靠** OCEAN，沒有 OCEAN 的地方就沒有效果。
- 根源相同：persona 的個體差異幾乎只來自 OCEAN（affiliation 有 92% 被 OCEAN 解釋），而且影響比真人強（需求和人格的平均 |r|：persona .29、真人 .12）。
- 5c 的 dominance 那一側看起來和論文一樣是 null，但論文的 null 是「需求有作用（5a 有效果），只是不影響有效性」；我們的 null 比較可能是「persona 的這兩種需求本來就沒有作用」（5a 也沒有效果）。

:::

# 5a 深入（1）：需求是 OCEAN 的代理

| 需求 | 綁定的特質（r） | 同一特質驅動的 ILT 維度（r） | 結果 |
|-------------|----------------------|----------------------------------------|----------------------------------|
| Affiliation | 親和性 .89 | sensitivity .86、ethics .67、tyranny −.51 | RW 第 1 名拿走 7 個維度 |
| Status | 外向性 .54 | charisma .66、strength .37 | 搶走 strength（49%） |
| Expertise | 開放性 .52 | creativity .71、intelligence .44 | creativity、intelligence 第 1 |
| Vision | 開放性 .44 | creativity .71、dedication .33 | dedication 第 1 |
| Protection | 開放性 −.42 | creativity（負向） | strength 只剩 0.7% |
| Fairness | 親和性 .56 | 和 affiliation 同一特質 | 被 affiliation 蓋過 |

**哪個需求和原型共用最強的特質，它就是第 1 名，與需求的內容無關**

::: notes

**這一頁解釋：為什麼論文中主導的需求，在我們這裡換人了。** 數字是 arm A 中 persona 的 OCEAN 等級（低 0、中 1、高 2）和需求、ILT 維度的相關，由已存資料計算，沒有呼叫 API。

**機制：** persona 的個體差異幾乎只來自 OCEAN，所以每個需求都變成某一個特質的代理變項；每個 ILT 維度也由某些特質驅動。需求能預測哪個維度，取決於兩邊有沒有共用同一個特質。

**逐一看：**

- **affiliation 幾乎等於親和性（r = .89）**，而且 SD 是六個需求中最大的（1.79，其他 .87-1.07）。凡是由親和性驅動的維度，affiliation 都是最乾淨的預測變項：sensitivity 54%、tyranny 42%（負向）、ethics 39%。論文中 affiliation 一格都不顯著。
- **strength 被 status 搶走。** 我們的 strength 主要由外向性（.37）和盡責性（.34）驅動，status 綁著外向性，所以 status 拿到 49%。protection 綁的是低開放性和神經質（.32），和 strength 沒有共同特質，所以只剩 0.7%。論文是 protection 主導（35%）。
- **charisma 由外向性驅動（.66）**，所以 status 的 β 有 .39，論文這格是 null。
- **creativity 由開放性驅動（.71）**：expertise、vision 綁著高開放性，所以是正向；protection 綁著低開放性，所以是負向（β = −.24），論文這格是 null。
- **fairness 也綁著親和性（.56）**，但比 affiliation 弱，所以在親和性驅動的維度上被 affiliation 蓋過。

**和真人的差別：** 論文找到的對應是有內容的，例如「需要保護的人看重強壯的領導者」。persona 的對應來自共用的特質，例如「外向的 persona 需要地位，也覺得領導者應該強壯」。

:::

# 5a 深入（2）：null 格為何有效果

| 指標 | 論文 | 我們 |
|--------------------------------------|----------|----------|
| 六個需求之間的平均 r | .54 | .22 |
| 最低的需求間相關 | .21 | −.50（status–fairness） |
| Sensitivity 的 R² | .26 | .81 |
| Ethics 的 R² | .23 | .60 |
| Femininity 的 R² | .02 | .21 |

- **需求缺少共同因素**：真人的需求都正相關，控制彼此後獨特的部分很少
- **R² 太高**：殘差小、SE 小，β .10 就能顯著
- **OCEAN 之外幾乎沒有東西**：固定 OCEAN 後 R² 只剩 .01-.19

::: notes

**這一頁解釋：為什麼論文不顯著的 52 格，我們有 26 格顯著。** 有兩個原因疊加。

**1. 真人的需求有共同因素，persona 的沒有。**

- 論文 Sample B（N = 1,035，5a 的 261 人是其中一組；論文沒有單獨報告這 261 人）六個需求兩兩都正相關，平均 .54，最低 .21。像是有一個共同的「需要領導者」因素。所以每個需求在控制其他五個之後，獨特的部分很少，ΔR² 很難顯著。
- 我們的需求平均只有 .22，status 和 fairness 甚至是 −.50。原因是親和性：低親和性的 persona 需要地位、不在乎公平。每個需求分別綁在不同特質上，各自有很多獨特變異，只要它的特質和某個維度有關，ΔR² 就顯著。
- **更正：** 先前我說「我們的需求彼此重疊得更多」，是錯的。實際上是我們的需求重疊得比真人少。

**2. 我們的 R² 高很多，小效果也容易顯著。**

- persona 的 ILT 評分幾乎完全由 persona 設定決定，殘差很小，SE 跟著變小。例如 charisma 的 protection β 只有 −.10，p = .049 就顯著了。
- 真人的評分有很多其他來源的變異（R² 只有 .02-.39），同樣大小的效果在論文中不會顯著。

**3. 固定 OCEAN 後，剩下的東西很少。**

- 把 OCEAN 固定後，六個需求對 ILT 的 R² 只剩 .01-.19。
- 剩下的部分 RW 第 1 名多數換成 status（tyranny 73%、strength 73%）。status 的變異只有 41% 被 OCEAN 解釋，是 OCEAN 以外成分最多的需求，可能來自描述文字。

**總結成一條機制：** persona 只有 OCEAN 一個個體差異來源 → 每個需求變成某個特質的代理 → 需求之間失去真人的共同因素 → 需求和原型的對應由「共用特質」決定 → 主導的需求換人，論文的 null 格出現效果。

**對改進方向的意義：** 只把 OCEAN 的影響調弱還不夠。persona 還需要一個讓所有需求一起變動的來源，才能做出真人那種共同因素，例如整體的不確定感或對領導者的依賴程度。**這個想法目前沒有文獻支持，需要再查。**

:::
