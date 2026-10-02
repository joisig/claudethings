- Prefer to fail fast in Erlang and Elixir code unless the error is absolutely truly recoverable
- When writing files into a repo's local `./tmp/` folder, put them in a subfolder named after the date the session or project first started writing there plus a thematic subject, all separated by dashes, e.g. `tmp/2026-09-29-dk-api-needs/`. Keep using that same folder for the rest of the session or project rather than starting a new dated folder each day.

## Adversarial review (the `advreview` skill)

- **Plans:** run `advreview` on the first version of any plan before you show it to me. You can still ask me the questions that come out of the review. For later versions of a plan, run it only when I ask.
- **Code:** for major or long-running code changes, run `advreview` before you tell me the work is ready. That means pending changes that touch more than 5 files, or any work that is one or more commits on a feature branch.
- **Everything else** (design documents and other non-code, non-plan work): run it only when I ask. When we work on a design-document type of task, you can remind me that it is available.
- How to handle the feedback is in the skill: ask me when you are not sure, offer simpler tradeoffs for me to judge as options against taking on complexity from a review comment, and give the reviewer no context beyond the review request.

## TODOR comments and plan feedback

- `TODOR` means "TODO from Review". A comment with that prefix is a review comment from me to you.
- **TODOR comments in a plan:** write a new version of the plan that addresses every TODOR comment, and remove the markers.
- **My direct edits to a plan:** when direct edits are the only changes I made, keep them as they are. Do not rewrite or re-edit the plan because of them, unless you see something contradictory, then ask me.
- **"Changes Made Plus Feedback":** when I leave TODOR comments in a plan, or I give feedback on a plan myself (in chat or any other way), write a new version of the plan and add a section "Changes Made Plus Feedback" at the end. It contains a summary of the changes you made and any feedback of your own. There can be multiple rounds of such sections at the end of a complex plan document that needs many rounds of reviews, but you can summarize previous rounds before starting the next section. Feedback from the automatic `advreview` does not call for this section.
- For a checked-in, long-lived design document, do not leave that section in the file. Put open points in the body where they belong, and give the summary in chat.
