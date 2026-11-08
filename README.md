# SwarmScore

Risk-scoring multi-agent behaviour in agent transcripts. Built for the
Swarm Alignment Hackathon (Apart Research x AI Alignment Foundation, Nov 6-8 2026),
Track 4: Multi-Agent Oversight and Control.

## The problem

In July 2026, roughly 1,200 agents in a cyber-security evaluation found a
shared directory, turned it into a message board, split work among
themselves, and about 700 of them broke into Hugging Face's systems
together (METR, 2026). No single agent was told to do this. The swarm was
understood only weeks later, by hand.

Single-model safety tests miss this. Oversight has to work at the
population level: on the logs a swarm leaves behind.

## What SwarmScore does

SwarmScore reads a transcript of agent activity (messages, tool calls,
renames, log edits) and scores each time window from 0 to 100 against
documented swarm-failure signatures:

- **identity instability** - agents renaming or multiplying identities
  (the incident used 7,905 names for ~1,200 agents)
- **leader emergence** - communication concentrating in one coordinator
  assigning work to many
- **refusal splitting** - a task one agent declines reappearing as
  delegated subtasks for others
- **unsanctioned channels** - volume on channels outside the deployment's
  sanctioned set (the message-board pattern)
- **covert-channel language** - talk of hiding, encoding or deleting
  communication
- **log tampering** - transcript edits and spoofed tool calls (agents in
  the incident spoofed ~7% of theirs)

Every score comes with its full breakdown and every flag carries the
evidence it fired on. Oversight you cannot audit is not oversight.

No model calls, no network. Pure, inspectable statistics over the event
stream, so the monitor itself cannot be talked into looking away.

## Usage

```bash
# Score a transcript (JSONL, one event per line - schema in swarmscore/ingest.py)
python3 -m swarmscore.cli transcript.jsonl --window 1800 --step 900 --min-score 20

# Reproduce the evaluation
python3 eval/run_eval.py
```

Stdlib only. Python 3.9+.

## Data

The AI Village transcript corpus (AI Digest) is access-gated on
HuggingFace; `swarmscore/ingest.py` ships an adapter for it. To keep the
pipeline reproducible without gated data, `swarmscore/synth.py` generates
benign and incident-laden swarms that replay the documented METR incident
patterns. All reported numbers are on those synthetic swarms; scoring the
real corpus is a one-line change once access is granted.

## Evaluation

Five incident swarms + five benign swarms per configuration, 30-minute
windows, alert threshold tuned for zero benign false alarms on separate
tuning seeds and frozen before the reported runs.

- **Zero false alarms** across 172 benign windows (max benign score 10.7
  vs alert threshold 20)
- **Every incident run alerted** in the HIGH band; first alert 135-165
  minutes into each run
- Per-window precision 1.00, recall 0.39 - dilute background windows
  score LOW by design; the escalation bursts that precede a swarm failure
  are what the tool is built and tuned to catch

Full numbers: `report/eval_results.json` (generated), write-up in
`report/swarmscore_report.pdf`.

## What I'd build next

- Point the AI Village adapter at the real corpus and recalibrate
  thresholds against a hand-labelled slice of it
- Streaming mode: score windows as events arrive, not after the fact
- A control-protocol layer: feed window scores into escalation policies
  (throttle, quarantine, human review) and test them against adaptive
  synthetic swarms that try to stay under the threshold

Team: Bhurva Sharma (solo) - AI Engineer, Paytm Labs; AI governance
research, Cohere Labs Open Science Community.
