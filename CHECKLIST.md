# Production Readiness Checklist

**Instructions:** Complete all sections below. Check the box when an item is implemented, and provide descriptions where requested. This checklist is a required deliverable.

---

## Approach

Describe how you approached this assignment and what key problems you identified and solved.

- [X] **System works correctly end-to-end**

**What were the main challenges you identified?**

```
[Describe the key problems you needed to solve for the system to work correctly]
1. Local code setup using UV.
2. Dataset analysis for meta data extraction.
3. OPENROUTER Integration with key (this currently has a lot of issues due to rate limiting for free tier).
4. Column filter for context before sql query generation for drilling down the required rows to reduce tokens and use the meta data efficiently
5. Token calculation
6. SQL generation needed prompts modification.
7. SQL validation implentation.
8. front and backend development using streamlit and flask.
9. Session management for the backend.
10. Dockerization.
```

**What was your approach?**

```
[Explain your solution at a high level. What did you implement and why?]
I have implemented a Text to SQL pipeline using the skeleton code provided.
I added context wise column filtering, sql generation and validation. This was then used for token calculation.
A raw UI and Backend code base was written for this project.
The project was dockerized for reproducibility.
```

---

## Observability

- [X] **Logging**

  - Description:
- [X] **Metrics**

  - Description:
- [X] **Tracing**

  - Description:

---

## Validation & Quality Assurance

- [X] **SQL validation**

  - Description:
- [X] **Answer quality**

  - Description:
- [X] **Result consistency**

  - Description:
- [X] **Error handling**

  - Description:

---

## Maintainability

- [X] **Code organization**

  - Description:
- [X] **Configuration**

  - Description:
- [X] **Error handling**

  - Description:
- [X] **Documentation**

  - Description:

---

## LLM Efficiency

- [X] **Token usage optimization**

  - Description:
- [X] **Efficient LLM requests**

  - Description:

---

## Testing

- [X] **Unit tests**

  - Description:
- [X] **Integration tests**

  - Description:
- [X] **Performance tests**

  - Description:
- [X] **Edge case coverage**

  - Description:

---

## Optional: Multi-Turn Conversation Support

**Only complete this section if you implemented the optional follow-up questions feature.**

- [X] **Intent detection for follow-ups**

  - Description: [How does your system decide if a follow-up needs new SQL or uses existing context?]
- [X] **Context-aware SQL generation**

  - Description: [How does your system use conversation history to generate SQL for follow-ups?]
- [X] **Context persistence**

  - Description: [How does your system maintain state across multiple conversation turns?]
- [X] **Ambiguity resolution**

  - Description: [How does your system resolve ambiguous references like "what about males?"]

**Approach summary:**

```
[Describe your approach to implementing follow-up questions. What architecture did you choose?]
I had an inital setup using UV for my python env and i kept adding packages when necessary.
There were a lot of issues with openrouter while I was working on it on Friday. I felt using ollama or even openai's base models
made my work much faster.

My main method was to add a context checker to filter out the columns required to solve the current user query.
Next I extracted metadata for the llm to read and understand column data.
This first step was very good at picking and choosing columns to run for the query and saved a lot of tokens.

Next, I worked on codebase errors and token calculation. I made a mistake and wanted to calculate costs. I have left
that code still there but since I am not sure which model the user intends to add in openrouter, I have left it commented out
for the future.

Initially for this part, I built a simple validation part to check the generated sql. a lot of this section of the code was
built from claude opus4.6.

I also used claude for frontend as I am not an expert on streamlit but I had a back and forth with it to improve it to
my standards(its bare minimum still).
The backend was flask and I have a similar setup in my current workspace in office.

I wrote a simple session manager per each app run to manage previous queries to potentially cut down tokens but its not fully realized.
The one I have in office is more complex but this was not improved as I felt I already exceeded the given time requirements.
I think the context manager should end the conversation if the session manager has previously encountered similar questions.

I finially dockerized it and composed it for a clean docker compose up.
```

---

## Production Readiness Summary

**What makes your solution production-ready?**

```
[Your answer here]
For me as a developer of similar chat interfaces, I prefer these above all else.
Swift and highly accurate resolution to the query.

I felt I acomplished it in this project using session manager, context checker, validation and dockerization.
I fast fast deployment servers and quick builds which allow me to experiment with differnt setups.

```

**Key improvements over baseline:**

```
[Your answer here]
The llm effectively works on the query in this pipeline with the given validation provided by me.
```

**Known limitations or future work:**

```
[Your answer here]
Openrouter had a lot of issues, causing slow development on Friday. Only after switching it to paid services like openai,
I made swift progress.
I understand why this was setup by the interviewer. But I felt the need to point out the frustration of waiting and hoping for
openrouter to work on a free account. I had to make 3 different accounts and cycle through them and still it was very slow.
```

---

## Benchmark Results

Include your before/after benchmark results here.

**Baseline (if you measured):**

- Average latency: `3424.17 ms`
- p50 latency: `390.31 ms`
- p95 latency: `28119.58 ms`
- Success rate: `0 %`

**Your solution:**

- Average latency: `4358.18 ms`
- p50 latency: `4335.52 ms`
- p95 latency: `5396.61 ms`
- Success rate: `100 %`

**LLM efficiency:**

- Average tokens per request: `1863.33`
- Average LLM calls per request: `3`

---

**Completed by:** Mohamed Faheem Thanveer
**Date:** 06/04/2026
**Time spent:** 15
