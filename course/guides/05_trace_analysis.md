# Week 5 Read traces and rank real problems
## Your destination this week

Read approximately twenty real application answers, write observations before categories, group the observations, and choose a fix target using frequency and impact.

Think of a teacher reviewing a stack of homework. A total score says how much went wrong; the teacher's notes reveal whether students misunderstood the question, forgot a condition, or used the wrong rule. Error analysis is that diagnostic work for your application.

**What was done:** the existing fifty historical traces were preserved; a reproducible random sample of twenty was selected; every selected answer and all of its retrieved chunks were read; an assistant-authored note was written for each; and a ranked taxonomy was generated. Human labels remain blank for you to supply. These are not presented as your personal review.

## 1 What a complete trace contains

A trace should make it possible to reconstruct what happened:

| Field | Why it matters |
|---|---|
| Question and request options | Shows the actual input and retrieval settings |
| Retrieved text and ordering | Shows what evidence the model saw |
| Answer and citations | Shows the behavior being evaluated |
| Timestamp and IDs | Supports correlation and provenance |
| Model and prompt identity | Identifies the system variant |
| Corpus fingerprint | Detects a changed knowledge base |
| Latency and model usage | Exposes cost and performance tradeoffs |
| Errors | Keeps failures visible rather than silently dropping them |

New /ask traces include configuration, prompt hash, corpus hash, model-call counters, and response data. The API echoes a generated X-Trace-ID header.

Historical traces are useful real outputs, but they lack some of the stronger configuration identity now recorded. Model version, source content, and runtime state can change. “Replayable” means sufficiently documented to repeat the experiment; it does not guarantee identical output.

The original corpus files are not retained in uploads. The historical trace evidence is therefore valuable, but should not be described as a perfect original-document archive.

## 2 Random and curated sampling

A curated set deliberately chooses cases: known bugs, edge cases, and important user journeys. It is excellent for regression tests but cannot estimate real traffic frequency without careful qualification.

A random sample selects cases according to a defined procedure. State the population first. Twenty randomly chosen records from a curated fifty-question experiment remain a sample of that experiment, not a random sample of every employee's needs.

The course samples twenty records without replacement using seed 42 from evaluation/traces_hr_agent.json. It stores the population hash, population size, seed, and selected trace IDs.

~~~powershell
.\.venv\Scripts\python.exe -m course.run week5
~~~

This writes **course/results/week5_sample.json** with blank review fields. Running it again recreates that worksheet, so save your annotated copy under a different name before rerunning.

Do not remove ugly answers, timeouts, or abstentions to make the report look better. If a record is excluded, document the reason and how it affects the denominator.

## 3 Open coding before categories

First read the answer and all retrieved evidence. Write one concrete sentence about what happened.

Weak note: “Bad generation.”

Better note: “The answer sends a manager-involved harassment complaint to the manager even though retrieved page 9 explicitly directs that case to HR.”

The better note identifies the output, conflicting evidence, and consequence. It does not require a category first.

Use your own words. Avoid writing the solution into every observation. “Needs a reranker” is a hypothesis, not an observation.

For correct answers, record that you found no defect under the stated rubric. For correct unknowns, mark an abstention control. You should be able to distinguish a success from a case you forgot to inspect.

## 4 Read the actual evidence

Do not grade only by whether the answer sounds sensible. Compare each material statement to the retrieved passage.

A useful sequence is:

1. What exactly did the user ask?
2. Which passage could support the answer?
3. Is the needed exception or condition present?
4. Does the answer preserve the employee group, deadline, contact, and scope?
5. Does the citation point to the supporting chunk?
6. Is the source itself authoritative, complete, and free of unresolved template choices?

An answer can be faithful to a bad source. If a handbook says “[Business / Casual / Smart Casual]” and the model chooses one, the problem is not solved by making citations prettier.

This course reviews historical HR text as application evidence, not as current legal or employment advice.

## 5 Two serious observed failures

**Wrong contact:** a historical question asked what to do when the reporting manager is involved in harassment. The retrieved evidence included an explicit HR exception. The answer instead described the generic manager route. Relevant evidence was retrieved, so this is a generation error with high user impact.

**Wrong employee group:** an overtime question received an answer assigning a ten-hour cap to non-exempt employees. The retrieved template assigned that cap to exempt employees. The answer also failed to flag template status. This is a scope error, not merely a missing citation.

These examples explain why “the correct document appeared” is an incomplete quality measure.

## 6 Name problem groups after reading

A taxonomy is a set of understandable problem categories.

The assistant review uses categories such as:

- Citation traceability: missing numbered citations, incorrect context reference, or internal label leakage.
- Wrong scope or contact: a policy rule applies to the wrong group or sends the user to the wrong responsible person.
- Incomplete conditions: a material qualification is omitted.
- Unresolved template: unapproved bracketed choices are treated as settled policy.
- False abstention: the app declines despite relevant evidence.
- Abstention format: the answer declines correctly but breaks the exact output contract.
- Correct abstention: a successful control, with severity zero.

These are provisional categories. If two reviewers interpret a category differently, refine its definition and examples. Keep a short rubric so future reviewers can use the same boundaries.

One trace can have secondary defects. For the main frequency table, assign one primary group to avoid double-counting. Preserve secondary notes in the observation text.

## 7 Frequency times severity

Frequency measures how often a group occurs in the defined sample. Severity estimates the harm when it occurs.

A simple severity scale is:

| Score | Meaning |
|---:|---|
| 0 | Successful control or no observed defect |
| 1 | Cosmetic or minor format issue |
| 2 | Traceability or usability problem |
| 3 | Material omission or avoidable wrong abstention |
| 4 | Wrong actionable scope or unapproved policy presented as fact |
| 5 | High-impact wrong routing or similar serious consequence |

A category with four severity-three cases has priority score 12. A category with one severity-five case scores five. The multiplication helps organize work, but it does not mean frequent cosmetic issues should always outrank rare serious risks. Document any risk-based override.

The ranker uses count × mean severity, which equals the sum of case severities. It also reports count and frequency separately. Successful controls remain visible with priority zero.

## 8 Your review files

- **week5_sample.json:** blank human worksheet with the sampled traces.
- **week5_assistant_review.json:** observations written by the assistant, with human_pass still null.
- **week5_taxonomy.json:** ranked groups from the assistant review.
- **course/review_notes.py:** reproducible record of those assistant notes.

To regenerate the assistant example:

~~~powershell
.\.venv\Scripts\python.exe -m course.review_notes
~~~

To rank your own annotated copy:

~~~powershell
.\.venv\Scripts\python.exe -m course.run rank --notes course/results/my_review.json
~~~

Every row needs an open_note, problem_type, and severity from zero to five. Set reviewer to your name or an agreed identifier. Preserve your notes separately from the assistant example.

## 9 Choose a target and write a prediction first

A good prediction is narrow and testable:

“If the prompt explicitly preserves exception contacts, then manager-involved harassment questions should cite the HR route, while ordinary reporting questions should remain correct.”

Specify the cases and scoring rule before changing the prompt. Otherwise it is easy to redefine success after seeing outputs.

The assistant's frequency ranking makes citation traceability a substantial group. However, wrong-contact and wrong-scope cases have higher individual impact. A responsible next target could prioritize those serious cases even if they are less frequent. Explain that choice.

Week 6's controlled prompt experiment tests material completeness and exceptions. It records its prediction before generating results.

## 10 Benchmarks versus your application

MMLU measures broad academic/professional knowledge tasks. HumanEval evaluates code-generation solutions to programming problems. They answer useful model-level questions, but they do not establish whether your assistant retrieves the right HR paragraph or preserves a local approval condition.

Your application needs its own test set, grounded in its inputs and failure modes. A larger public benchmark score does not repair an unindexed policy file.

Do not compare percentages across unrelated benchmarks as if they meant the same thing. A ninety-percent source hit rate, a ninety-percent human agreement rate, and a ninety-percent coding benchmark score have different denominators and meanings.

## 11 Avoid these traps

**Cherry-picking:** reading only successful cases.

**Category-first thinking:** forcing observations into a preferred diagnosis before examining evidence.

**Unfair denominators:** omitting failures or mixing answerable and unanswerable retrieval cases.

**Label laundering:** calling assistant-generated or imported labels “independent human review.”

**Confusing provenance and correctness:** a citation can identify a source without proving the claim follows.

**Ignoring source quality:** a template is not an approved policy just because it is in a PDF.

**Changing several things:** a better score does not reveal causality if the model, corpus, prompt, and k all change together.

## 12 Brief testing workflow

1. Generate the seeded sample.
2. Copy it to your own review file.
3. Read every answer and retrieved chunk.
4. Write observations first.
5. Assign primary categories and severity.
6. Run the ranker.
7. Choose one target and record a prediction.
8. Carry representative failures and successful controls into Week 6.

If you disagree with the assistant note, write why and cite the source passage. The purpose is evidence-based judgment, not agreement with the assistant.

## 13 Friday demonstration

Show the population and seed, one open note, its supporting passage, the final category definitions, the ranked table, and your chosen target. Be able to explain why a correct abstention is a success and why a high source hit rate can coexist with a serious answer error.

**Self-check:** Is random sampling from curated questions equivalent to random production traffic? No. Does the assistant review count as your independent human grading? No. Must the most frequent category always be fixed first? No; severity and risk can justify a different choice.
