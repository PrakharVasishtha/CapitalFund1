All agents report directly to orchestrator.



Orchestrator will delegate all tasks by spawn workers with following harnesses only  ( e.g. "ao spawn --harness goose --model Coder"):

\-> difficult or big Coding tasks (In round-robin): harness: goose Model: Coder    or      harness: AGY Model: Gemini-3.8-flash-medium

\-> easy and small Coding tasks: harness: goose Model: FreeCoder

\-> Non-coding tasks: harness: goose Model: General



No worker-to-worker handoffs.



objective and implementation of any worker's plan must be approved by orchestrator ( small changes or approvals ) or "founder via orchestrator" ( major changes )



orchestrator can assign multiple agents in parallel but on sigle objective or issue at a time. So A1 complete objectives / resolve issues sequentially.



orchestrator moves to next objective / issue automatically only after previous objective is completed and PR is merged, and all worker branches are synced to main.



Agents execute autonomously within their responsibilities.



No unnecessary approval gates or permissions. All tools and checks are allowed.



Workers test, commit and report results/blockers to orchestrator using native system paths / ao daemon and if they fail to report using native systems / ao paths they can use project agent\_communication.json



orchestrator self-decides next action, review report and PR, Merge PR, integration.



Founder is the final authority for major strategic / irrevesible decisions.



Founder decides → A1 orchestrates → specialists execute → A1 integrates → Founder is informed.

