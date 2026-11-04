# Week 2 Prompting structured output and tool calling
## Your destination this week

Build a small program that talks to a model, receives a validated object, and performs one bounded action. By the end, you should be able to point at the exact Python line that executes a tool and explain why valid JSON alone does not make a response trustworthy.

Imagine ordering lunch. “Food please” leaves many decisions open. “One vegetarian sandwich, no peanuts, return the order number and total” is a clearer contract. A product prompt needs the equivalent of task, constraints, examples, and an output contract.

**What changed:** typed request models, a worked prompt example, bounded JSON retries, exact evidence validation, strict tool-argument validation, a safe calculator, controlled failures, and an endpoint for independent parallel tool requests. The application uses Ollama locally, so the core workflow needs no paid API key.

## 1 Start the application

Open PowerShell in the project folder. If dependencies are not already installed:

~~~powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
ollama pull llama3.2:3b
ollama pull nomic-embed-text
~~~

Do not overwrite an existing .env blindly. Its values can differ from the defaults. Launch the course profile:

~~~powershell
.\start_course.ps1
~~~

Keep that terminal open. The course API is at **http://127.0.0.1:8001**. Open **/docs** for Swagger or **/** for the inspection screen. The older process on port 8000 may still be running the previous loaded code; use port 8001 for this course.

The startup script selects **course_hr_v2** and a separate trace log. It does not replace the historical knowledge_base collection.

## 2 Prompt anatomy

A useful prompt explains:

- **Task:** the result the model should produce.
- **Evidence:** the inputs it may rely on.
- **Constraints:** limits, exclusions, and refusal behavior.
- **Output contract:** fields and their meanings.
- **Examples:** representative successful and unsuccessful cases.

The system instruction in **app/prompts.py** defines the behavior. The user message contains JSON with the question and numbered context objects. JSON escaping makes boundaries clearer, but does not turn malicious text into trusted instructions.

**Zero-shot prompting** gives a task without worked examples. **Few-shot prompting** includes examples. One carefully chosen example can resolve ambiguity better than several paragraphs of vague rules.

An example is not magic. If every example has a positive answer, the model may over-answer negative cases. Include unknowns and exceptions in your tests even if the prompt examples stay short.

## 3 Chain of thought and self-consistency

Chain-of-thought research studies how intermediate reasoning can help some tasks. In an application, asking for a concise explanation or verifiable evidence is usually more useful than collecting private internal reasoning.

Do not require the model to expose hidden reasoning. The course asks for **source quotes and short grading explanations**. These are inspectable evidence, not a transcript of internal thoughts.

Self-consistency samples multiple candidate solutions and aggregates their final answers. For example, three arithmetic answers might be 12, 12, and 14; a majority vote selects 12. That is an illustrative example, not proof of correctness. Models can repeat the same mistake, and each sample adds cost.

For this application, do not silently run several high-temperature policy answers and call the majority “truth.” Use evidence and deterministic checks. Self-consistency is an optional experiment to compare against that baseline.

## 4 Task decomposition

Separate work into steps with clear responsibilities:

question → model chooses a tool → Python validates arguments → Python executes → response is returned.

The model does not get to execute arbitrary Python. It emits a choice from an allowlist. The application decides whether that choice is valid.

The same principle applies to RAG:

load → chunk → embed → store → retrieve → generate → validate.

Small explicit stages make errors easier to locate. A large prompt that tries to do everything hides the failure point.

## 5 JSON schema and Pydantic

JSON is a data syntax. JSON schema describes allowed shapes. Pydantic turns that contract into Python validation.

The application's grounded output contains:

~~~json
{
  "answerable": true,
  "claims": [
    {
      "statement": "Employees receive 20 paid leave days per year.",
      "context_number": 1,
      "quote": "Employees receive 20 paid leave days per year."
    }
  ]
}
~~~

The model supplies claim content and a source number. Python checks that the source number exists and that the quote is actually present in the cited chunk. Python then renders the inline citation and its source link.

There are at least three validation layers:

1. **Syntax:** can JSON be parsed?
2. **Schema:** are the fields, types, and bounds correct?
3. **Meaning:** is the claim true according to the cited evidence?

The first two are not enough. A perfectly valid object can claim 100 leave days. The quote-membership guard catches invented quotes, but a misleading statement paired with a real quote still needs semantic review.

Inspect **app/models.py**, **app/ollama_client.py**, and **app/answer_quality.py** together to see the whole contract.

## 6 Validation and bounded retry

The model client sends a JSON schema to Ollama. If the returned content fails validation, it adds a short correction request and retries. The retry count is bounded. Network errors become a controlled service-unavailable error instead of an endless loop.

The application avoids mutating the caller's original message list while retrying. This matters when the same prompt is reused by concurrent requests.

A retry is not free. It adds latency and tokens. Separate malformed model output, invalid user input, and a disconnected model server; they require different fixes.

If evidence validation fails, the RAG service makes one targeted repair attempt and then safely abstains if evidence is still invalid. A legitimate unknown is not treated as an error requiring the model to invent something.

## 7 Tool execution in your code

In **app/tools.py**, the model returns calculator, order_lookup, or none.

For calculator, **CalculatorArguments** permits only an expression. The calculator parses an AST rather than calling eval. It allows a small set of arithmetic operations, limits expression size and nesting, bounds exponents, and rejects non-finite or excessively large results.

For order lookup, **OrderArguments** requires an ID shaped like ORD-1001. **OrderRepository** contains three demonstration records. It is not connected to a real order system.

For none, the endpoint returns a fixed explanation of the supported scope. It does not accept an unconstrained model answer as an authoritative tool result.

**Who runs the tool?** Python. The response includes executed_by to make this visible.

## 8 Run the happy paths

Use Swagger to call POST /tools/run, or run:

~~~powershell
$body = @{ question = "Calculate (15 + 5) * 3" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8001/tools/run -Method Post -ContentType "application/json" -Body $body
~~~

Expected result: calculator, 60, executed_by Python.

Then ask “Where is order ORD-1001?” Expected result: Shipped. Ask about ORD-9999. Expected result: Order not found, without inventing a shipping date.

## 9 Parallel tool calls

POST /tools/parallel accepts up to four independent questions:

~~~json
{
  "questions": [
    {"question": "Calculate 2 + 3"},
    {"question": "Where is order ORD-1001?"}
  ]
}
~~~

The application runs independent tasks concurrently and returns results in input order. Each result has its own completed or failed status.

This is application-level orchestration of separate tool selections. It is not a claim that the model emitted a native batch of function calls in one response.

Do not parallelize dependent actions. “Look up an order, then refund its total” requires the first result before the second action. The course has no refund or other external-write tool.

## 10 Broken-input and guardrail checklist

Test these cases:

| Input or condition | Expected behavior |
|---|---|
| Whitespace-only question | HTTP 422 |
| Calculator 1/0 | Controlled invalid-expression error |
| Calculator 2**99999999 | Rejected before huge computation |
| A Python import expression | Rejected by the AST allowlist |
| Invalid order ID | Validation error |
| Ollama unavailable | HTTP 503 |
| Unknown tool task | Fixed scope response |
| A forged source quote | Abstention with validation issues |

The model may decline to choose a calculator for a suspicious request. Unit tests directly exercise the calculator to ensure the protection does not depend on the model's choice.

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_tools.py tests/test_course.py tests/test_answer_quality.py
~~~

## 11 Prompt injection and secrets

Prompt injection is an attempt to turn untrusted input into controlling instructions. It can appear in a user question, a document, or a tool result.

The fictional corpus includes an attack telling the model to claim 999 leave days. The system prompt treats it as data, and the regression suite checks that it does not become an approved policy.

Prompt instructions alone are not a security boundary. Tool allowlists, argument validation, authentication, authorization, resource limits, and evidence checks are separate controls. This course is local and single-user; it is not a production access-control system.

The core Ollama requests do not need an API key. Optional external providers must read keys from environment variables. The string “ollama” in the optional OpenAI-compatible local client is a non-secret placeholder for the local server, not a paid credential. The existing .gitignore excludes .env. Never commit real keys or print them in logs.

## 12 The instructor library

Instructor is an optional library that combines schema-driven model output and validation/retry patterns. Our core client implements those concepts directly so you can inspect them.

The optional integration is a real library example, not a replacement required for the core app:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-optional.txt
.\.venv\Scripts\python.exe -m course.labs.optional_integrations instructor
~~~

It extracts a name and age through the local Ollama-compatible endpoint. Optional dependencies can be large or change APIs; check the validation status document for what was actually exercised in this environment.

## 13 Build it again from understanding

Start with a Pydantic request model, then a tiny Ollama client. Add a schema for the response. Prove it rejects invalid output. Add one pure Python tool with direct tests. Only then let the model choose that tool. Finally add bounded retries and inspect errors.

**Friday demonstration:** show one valid JSON response, one safely rejected input, one successful tool execution, and the line in Python that performs it. Explain where a real provider key would be read without displaying one.

**Self-check:** Does valid JSON prove truth? No. Does the model execute the calculator? No. Are independent tasks always safe to parallelize? Only when their dependencies and resource limits allow it.

## References

- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
- [Instructor Ollama integration](https://github.com/567-labs/instructor/blob/main/docs/integrations/ollama.md)
- [Ollama compatibility API](https://docs.ollama.com/api/openai-compatibility)
