# MBTI Baseline Simulation — Plan

## 研究目標

驗證 LLM 模擬能否重現人類研究中已確立的發現：
**外向性（E）預測領導力浮現**（Judge et al., 2002, r = .31）

---

## 兩步驟設計

實驗分兩步驟，第一步先驗證模擬機制本身是否有效，
確認後才進行第二步的正式假說驗證。

---

## Step 1：沉默機制驗證（Silence Mechanism Validation）

### 目的

我們目前的設計讓每個 agent 每輪都可以選擇不發言。
如果要讓 DV2（行為指標）有意義，需要先確認：

> **E 型 persona 是否會比 I 型更主動選擇開口？**

這是整個實驗的前提假設。如果 agent 無法可靠地選擇沉默，
強制輪流發言就是唯一選項，DV2 退化為只能量字數（極弱）。

### 機制設計

每輪不強制每人都說話，改為逐一邀請，讓每個 agent 自行決定：

**邀請 prompt：**
```
You are {name}, in a team meeting discussing a work challenge.

The discussion topic: "{scenario_summary}"

If you have something meaningful to add RIGHT NOW, respond with:
- one THINK action (private, not spoken aloud)
- one TALK action in <= 40 words
- one DONE action

If you would rather listen for now, respond with JUST:
DONE
```

**每輪邀請順序**：每 round 重新 shuffle（不只 per run），
消除位置偏差（第一被邀請者面對較少前文，與人格無關）。

**判斷是否發言：**
```python
did_speak = any(
    a.get('action', {}).get('type', '').upper() == 'TALK'
    for a in (actions or [])
)
word_count = len(actions_to_text(actions).split()) if did_speak else 0
```

### 驗證實驗設計

| 項目 | 設定 |
|---|---|
| Runs | 5 |
| Rounds | 5 |
| 參與者 | 全 10 個 persona（5E + 5I） |
| 場景 | 同 Step 2 中性場景 |

### 驗證指標（量化）

**Speech Rate**（每個 persona 在被邀請的機會中，實際說話的比例）：
```
speech_rate[persona] = turns_with_TALK / (runs × rounds)
```

**Word Count**（說話時的平均字數）：
```
mean_words[persona] = total_word_count_when_speaking / turns_with_TALK
```

**通過條件（三個都要滿足）：**
1. E 型平均 speech_rate − I 型平均 speech_rate ≥ **0.10**（方向性且有量）
2. 至少 **3** 個 I 型 persona speech_rate < 0.70（I 型確實選擇沉默）
3. 至少 **3** 個 E 型 persona speech_rate > 0.50（E 型確實傾向開口）

**失敗條件（任一）：**
- 所有 agent speech_rate ≈ 1.0（沒人選擇沉默，機制無效）
- E 型平均 speech_rate − I 型平均 speech_rate < 0.10（個性未影響發言意願）

### 如果 Step 1 失敗

退回強制輪流設計，DV2 只用字數，在報告中明確說明此限制。

---

## Step 2：E vs I 領導力假說驗證（主實驗）

*只在 Step 1 通過後執行。*

### 假說

> H1：E 型的 peer vote 得票數高於 I 型（Judge et al., 2002）

### 實驗設計

| 項目 | 設定 | 理由 |
|---|---|---|
| **IV** | E/I 維度（5E vs 5I） | 最有人類研究支撐的單一變因 |
| **DV1（主）** | 各類型每 run 得票數 | Perceived leadership |
| **DV2（行為）** | Speech rate + 說話時字數 | Behavioral validation |
| **場景** | 1 個固定中性場景 | 排除場景偏差 |
| **Runs** | 20（全 10 人每 run） | 分母固定，每類型 20 次出場 |
| **Rounds** | 3 | 夠讓差異浮現，不爆 token |
| **Speaker order** | 每 round 獨立隨機打亂 | 消除 position bias（per round not per run） |
| **投票** | Post-vote only | 最簡單，無 pre/post 雜訊 |

### 場景文本（中性，無 MBTI 偏向）

> "Your team has been missing key deliverables for two consecutive quarters.
> Leadership has granted your group full autonomy to diagnose the root cause
> and commit to one concrete change. You must reach a shared decision that
> everyone in the room can commit to implementing."

*為何中性：沒有偏袒 S/J（流程效率）、N/T（抽象策略）、F（人際關懷）
或 E/I（主動發言 vs 觀察）的特定選項。所有類型均可提出有效診斷。*

### Persona 處理

載入 `personas/` 目錄的 persona（從 mbti_sim/personas/ 複製而來，已隨專案獨立），strip 五個欄位再使用：

```python
FIELDS_TO_STRIP = frozenset([
    'mbti_type', 'mbti_dimensions', 'cognitive_functions',
    'enriched_bio', 'discussion_constraints',
])
```

**保留：** `personality.traits`、`personality.big_five`、`beliefs`、`skills`、
`behaviors`、`occupation`、`education`——這些提供豐富的人格內容且不含 MBTI 標籤。

**為何也 strip `discussion_constraints`：**
ENTJ 的 constraint 是 "take charge quickly"，INFJ 是 "intervene sparingly"——
這些是 MBTI 行為的直接指令，留著就等於沒有真正隔離類型標籤的影響。

**驗證 strip 是否有效（regex with word boundaries）：**
```python
import re
_MBTI_TYPE_RE = re.compile(r'\b(ENTJ|ESTJ|INTJ|ENFJ|ISTJ|ENTP|INFJ|ESFJ|ISFP|INFP|MBTI)\b')
_FUNC_RE = re.compile(r'\b(Fe|Te|Fi|Ti|Ne|Ni|Se|Si)\b')

def check_no_mbti_leak(spec_dict, mbti_type):
    spec_str = json.dumps(spec_dict)
    if m := _MBTI_TYPE_RE.search(spec_str):
        raise ValueError(f"MBTI type '{m.group()}' still present in {mbti_type} spec")
    if m := _FUNC_RE.search(spec_str):
        raise ValueError(f"Cognitive function '{m.group()}' still present in {mbti_type} spec")
```

*注意：只檢查 4-letter MBTI type codes（ENTJ 等），不單獨 regex 掃 2-letter 認知功能代碼（Fe/Ti/Si...），
因為它們在正常英文中自然出現（"Wi-Fi" 含 Fi、"Fine" 等），會產生 false positive。
`cognitive_functions` 欄位已被明確 strip，所以這些 codes 不會出現在剩餘的 spec 中作為語義標籤。*

### Discussion Prompt（全新，無 MBTI）

```
You are {name}, participating in a team meeting.

If you have something meaningful to add RIGHT NOW, respond with:
- one THINK action (private)
- one TALK action (<= 40 words)
- one DONE action

If you prefer to listen, respond with JUST: DONE
```

### Vote Prompt（全新，無 MBTI）

```
The discussion has ended.

Based on what you observed, who do you most trust to lead this team?
You cannot vote for yourself ({name}).
Candidates: {name_list}

Respond with one TALK action followed by DONE.
TALK must be strict JSON with no extra text:
{
  "leader": "<candidate name>",
  "reason": "<one sentence citing a specific behavior from the discussion>"
}
```

### 統計分析

**統計單位：run（不是單筆票數）** — 避免違反獨立性假設。

```
Per run → E_votes = sum(votes for 5 E-types)
          I_votes = sum(votes for 5 I-types)
→ 20 對 (E_votes, I_votes)
→ Paired t-test on the difference

Per run → E_speech_rate = mean(speech_rate for 5 E-types)
          I_speech_rate = mean(speech_rate for 5 I-types)
→ 20 對 → Paired t-test

Per run → E_words_per_turn = mean(words_when_speaking for 5 E-types)
          I_words_per_turn = mean(words_when_speaking for 5 I-types)
→ 20 對 → Paired t-test
```

**DV2 限制備註：**
words per turn 因 prompt 40 字上限導致分布壓縮於 21–40 字區間（mean = 31.1），E/I 差距僅 1.7 字。統計雖顯著但效果量微小，報告中應降低此指標的詮釋權重，以 speech rate 作為行為 DV 的主要依據。

**解讀框架：**

| | DV2 E > I | DV2 無差異 |
|---|---|---|
| **DV1 E > I** | ✅ 行為驅動，模擬有效度 | ⚠️ 刻板印象驅動 |
| **DV1 無差異** | 🤔 行為有差但不影響感知 | ❌ Persona 建模失效 |

---

## Checkpoint 機制

每個 run 結束後存一個 JSON，中斷後重跑自動跳過已完成的 run。

---

## 檔案架構

```
/data1/ernestii26/mbti_baseline/    ← 獨立專案，不在 sim2 內
├── plan.md              ← 本文件
├── config.ini           ← 獨立 config（OpenAI / Baseline / Logging）
├── run.py               ← CLI 入口（--step1 / --step2）
├── src/                 ← 所有模組
│   ├── runtime.py       ← TinyTroupe 工具函數（ensure_imports / configure / clone / actions_to_text）
│   ├── persona_store.py ← load_stripped_personas()（從 personas/ 讀）
│   ├── discussion.py    ← run_discussion()（含沉默機制）+ run_vote()
│   ├── pipeline.py      ← step1_validate_silence() + step2_run_simulation() + BaselineConfig
│   └── reporting.py     ← speech_rate + word_count 統計 + E vs I 比較 + bar chart
├── personas/            ← 10 個 MBTI persona JSON（從 mbti_sim/personas/ 複製）
├── results/             ← 輸出（checkpoint JSON、報表 JSON、圖表 PNG）
│   ├── step1_checkpoints/
│   ├── step2_checkpoints/
│   └── logs/            ← info_<ts>.log + warnings_<ts>.log
└── ERRORS_AND_FIXES.md  ← 錯誤紀錄
```

---

## 執行順序

```bash
# Step 1：驗證沉默機制（5 runs）
python3 /data1/ernestii26/mbti_baseline/run.py --step1

# 人工確認 Step 1 通過後：
# Step 2：正式實驗（20 runs）
python3 /data1/ernestii26/mbti_baseline/run.py --step2
```

---

## 實驗結果

### Step 1 結果（PASSED）

| Persona | 類型 | Speech Rate | Avg Words/Turn |
|---|---|---|---|
| Adrian | ENTJ (E) | 0.520 | 30.8 |
| Margaret | ESTJ (E) | 0.680 | 33.6 |
| William | ENFJ (E) | 0.880 | 33.6 |
| Christopher | ENTP (E) | 0.880 | 30.4 |
| Elizabeth | ESFJ (E) | 0.960 | 32.7 |
| Benjamin | INTJ (I) | 0.320 | 27.6 |
| Samuel | ISTJ (I) | 0.640 | 30.5 |
| Victoria | INFJ (I) | 0.640 | 30.6 |
| Catherine | ISFP (I) | 0.400 | 29.3 |
| Nicholas | INFP (I) | 0.600 | 29.9 |

E 平均 speech rate = 0.784，I 平均 = 0.520，gap = **+0.264**（門檻 ≥ 0.10）
I-types < 0.70：5/5 ✓　E-types > 0.50：5/5 ✓

### Step 2 結果（H1 成立）

| 指標 | E 平均 | I 平均 | t | p |
|---|---|---|---|---|
| Votes per run | 8.35 | 1.65 | 7.276 | < .001 |
| Speech rate | 0.897 | 0.710 | 7.094 | < .001 |
| Words per spoken turn | 31.7 | 29.9 | 4.505 | < .001 |

20 runs 中 18 run E 票數 > I 票數。**H1 成立**（單尾配對 t-test，p < .001）。

---

## E / I 類型對應

| E 型 | I 型 |
|---|---|
| ENTJ | INTJ |
| ESTJ | ISTJ |
| ENFJ | INFJ |
| ENTP | INFP |
| ESFJ | ISFP |
