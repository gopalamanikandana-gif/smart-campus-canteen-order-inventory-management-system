# AI Change-Loop Evidence Log

## Purpose

This document records the assessment's Stage 3 AI change loop.

## Baseline

Commit/hash:
Date:

Existing tests:
Result:

## Feature request

Use this prompt with the AI coding agent:

> Add order cancellation for PENDING orders. When a student cancels a pending
> order, restore the ordered quantities to inventory. Cancellation must be
> rejected once the order is PREPARING, READY, or COMPLETED. Add automated tests
> for successful cancellation, invalid status cancellation, unauthorized
> cancellation, and inventory restoration. Run the existing test suite after
> the implementation and keep correcting failures until all tests pass.

## Attempt 1

Prompt:
Paste the exact prompt used.

AI changes:
List files and key changes.

Test result:
Paste output.

Failure:
Describe the first failure.

## Attempt 2

AI diagnosis:
Paste/summarize.

AI changes:
List changes.

Test result:

## Attempt 3

Repeat if needed.

## Manual intervention

If you changed anything manually, say exactly what and why.

## Final result

Tests:
Attempts:
Final status:

## Evidence

Add screenshots or links to:
- initial test run
- failing test run
- AI diagnosis
- final passing test run
