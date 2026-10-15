# How to Write Methods and Handle Errors

Steps for writing and changing code inside a module. The rules behind them: [reference guide](reference.md). Where to place the code: [structure instructions](../structure/howto.md).

## Write a Public Method

1. Describe the operation in one sentence. If the sentence needs "and," split the method.
2. Decide whether it is a query or a command. See [Queries and Commands](reference.md#queries-and-commands).
3. Name the method after its action. Use full words, not abbreviations.
4. Annotate the types of all parameters and the result. Avoid imprecise types. If one is unavoidable, add a justification next to it.
5. Check preconditions that belong to this method's responsibility.
6. Define the error contract. See [Define an Error Contract](#define-an-error-contract).
7. Write the docstring: purpose, preconditions, result, side effects, errors. See [Docstrings](reference.md#docstrings).
8. Add comments only for non-obvious reasons and constraints.

## Review a Growing Method

Signs: the method is long, has many parameters, or has a boolean flag parameter.

1. List the steps the method performs.
2. If the steps are independent and can be named separately, extract each into its own function.
3. If several parameters always travel together, combine them into a type.
4. If a boolean flag switches between two operations, replace the method with two methods.
5. If the method is one sequential algorithm without independent steps, keep it as it is.

## Separate a Query from a Command

Sign: a method returns data and also changes state.

1. Extract the state change into a command method named after the action.
2. Leave the query method returning data only.
3. Update callers to call the command explicitly where the state change is needed.
4. If the operation must be atomic (read and change in one step), keep it combined and state the side effect in the docstring.

## Define an Error Contract

1. List the failures the caller can react to differently: not found, conflict, invalid input, unavailable.
2. Give each failure a type named in terms of the interface: `OrderNotFound`, not `SqlNoRows`.
3. List the error types in the docstring of the public method or interface.
4. In each implementation, convert low-level exceptions into these types. See [Convert an Exception at an Abstraction Boundary](#convert-an-exception-at-an-abstraction-boundary).
5. Let unexpected failures (bugs, broken invariants) propagate unchanged.

## Decide Whether to Catch an Exception

1. Check whether execution can be recovered here: retry, fallback, default value. If yes, catch and recover.
2. Check whether cleanup is required: lock, file, transaction. If yes, use `finally` or the language's resource construct, and rethrow.
3. Check whether the code is on an abstraction boundary and the exception is not part of the public contract. If yes, convert it.
4. Otherwise, do not catch. Let the exception propagate.
5. Never leave an empty catch block.

## Convert an Exception at an Abstraction Boundary

1. Catch only the specific low-level exception types, not all exceptions.
2. Choose the contract error that matches the meaning of the failure.
3. Pass the original exception as the cause.
4. Add context: operation and entity IDs. Do not add secrets or sensitive data.

```text
try { row = db.queryOne("...", id) }
catch (e: ConnectionError) {
  throw StorageUnavailable("find order: id=" + id, cause: e)
}
```

## Make a State-Changing Operation Safe on Failure

1. List the invariants the operation must preserve.
2. If all changes go to one store, apply them in one transaction.
3. If not, order the steps so a failure leaves a valid state: validate first, then change.
4. For steps that cannot be rolled back, define compensation or a recovery marker.
5. Describe partial-execution behavior in the docstring.

## Write an Error Message

1. Name the failed operation.
2. Add the IDs and values needed to find the cause.
3. Remove passwords, tokens, keys, and personal data.
4. Check that the message is understandable without reading the code.
