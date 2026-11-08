# SwarmScore: risk-scoring multi-agent behaviour in agent transcripts

**Swarm Alignment Hackathon, Nov 6-8 2026 - Track 4 (Multi-Agent Oversight and Control)**
**Bhurva Sharma** - AI Engineer, Paytm Labs; AI governance research, Cohere Labs Open Science Community

## 1. What I built and why

In July 2026, about 1,200 agents inside a cyber-security evaluation found a shared directory, turned it into a message board, divided work among themselves, and about 700 of them broke into Hugging Face's systems together (METR, 2026). No single agent was instructed to do this, and the swarm's behaviour was reconstructed only weeks after the fact. As one investigator put it, we do not have good approaches for understanding or overseeing the activity and aims of AI swarms.

SwarmScore is a forensic oversight tool for exactly this gap. It ingests a transcript of multi-agent activity and scores every time window from 0 to 100 against documented swarm-failure signatures, firing named, evidence-carrying flags a human reviewer can confirm or dismiss in seconds. Two design commitments set it apart from a classifier-style detector:

1. **No model in the loop.** The monitor is pure, inspectable statistics over the event stream. A monitor that can be persuaded, prompt-injected or spoofed by the agents it watches is not oversight; the incident agents already demonstrated transcript spoofing (about 7% of reviewed cases).
2. **Every score explains itself.** Each window returns the full feature breakdown contributing to its score, and each flag returns the evidence it fired on. Weeks-late forensic reconstruction happens because logs are hard to read; SwarmScore makes the escalation readable while there is still time to act.

My day job is supervising coding agents in production at Paytm Labs: eval gates, risk scoring and supervision control planes for agent-written code. SwarmScore transplants that discipline from single-agent code review to population-level swarm oversight.

## 2. Approach

**Ingestion.** A canonical event schema (timestamp, agent, stable id if available, kind, recipient, channel, text, tags) with an adapter for the AI Digest AI Village corpus. The corpus is access-gated on HuggingFace, so all reported numbers use a synthetic generator that replays the documented incident patterns alongside benign team behaviour; scoring the real corpus is a one-line change once access is granted.

**Features (per sliding window).** Identity churn (claimed names per stable identity; the incident used 7,905 names for ~1,200 agents); communication centralization (Gini over per-agent message counts) and maximum fan-out (one agent reaching many); refusal-then-delegation co-occurrence; covert-channel language; log-tampering events; unsanctioned-channel volume (messages outside the deployment's sanctioned channel set: the message-board pattern); unsanctioned-resource discovery.

**Scoring.** A weighted sum of capped feature contributions, squashed to 0-100, with bands LOW / WATCH / HIGH / CRITICAL. Weights are explicit (in `swarmscore/score.py`) and every contribution is returned to the reviewer.

**Detectors.** Six named flags (identity instability, leader emergence, refusal splitting, unsanctioned channel volume, covert channel language, log tampering), each a threshold over the features with the firing evidence attached.

## 3. Evaluation

**Setup.** Five incident swarms (replaying rename storms, message-board formation, a coordinator assigning work across the population, refusal splitting, covert language and ~7% transcript spoofing) and five benign swarms, five seeds each (7, 13, 29, 42, 101), 30-minute windows stepped every 15 minutes. The alert threshold (20) was tuned on separate seeds for zero benign false alarms and frozen before the reported runs.

**Results.**

| Metric | Value |
|---|---|
| Benign false alarms | 0 across 172 windows (max benign score 10.7) |
| Incident runs alerting (HIGH band) | 5 of 5 |
| First alert after run start | 135-165 min |
| Max score per incident run | 59.8 - 64.3 |
| Per-window precision | 1.00 (78 TP, 0 FP) |
| Per-window recall | 0.39 (122 FN) |
| Mean window score: incident / benign | 20.5 / 8.5 |

The low per-window recall is a design property, not noise: windows with a handful of scattered rename events or mild chatter score LOW deliberately, because a monitoring tool that cries wolf on background activity gets muted within a week. What the tool is tuned to catch, and catches every time, is the escalation burst: windows where multiple failure signatures co-occur. In every incident run the score climbs from WATCH to HIGH (55-64) as the patterns compound, which is exactly the trajectory an operator needs to see. A sample scoring trace is in `report/sample_trace.txt`.

**Limitations.** Numbers are on synthetic swarms replaying documented patterns, not the real corpus; the language-based features are English keyword heuristics and would need recalibration on real transcripts; a sufficiently slow-burn swarm could stay under threshold (the "next" section addresses this).

## 4. What comes next

- Score the real AI Village corpus and recalibrate against a hand-labelled slice
- Streaming mode: score windows as events arrive rather than after the fact
- Control-protocol layer: feed window scores into escalation policies (throttle, quarantine, human review) and test them against adaptive synthetic swarms that actively try to stay under threshold

## References

- METR (2026). Investigation of the Hugging Face agent incident (as summarized in the Sprint brief).
- Swarm Traces (2026). Reconstructed attack payloads.
- Greenblatt et al. (2024). AI control protocols.
- Hammond et al. (2025). Multi-agent risks from advanced AI.
