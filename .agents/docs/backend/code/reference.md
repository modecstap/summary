# Reference Guide: Code Inside a Module

The target form of code inside a module: classes, functions, methods, and error handling. How to achieve it: [instructions](howto.md). Module, file, and naming rules: [structure reference](../structure/reference.md).

## Design

* Every class, module, and function has one clear responsibility.
* OOP, functional constructs, and composition are chosen to fit the task.
* A class is not created only to hold functions. Stateless functions stay plain functions in a module.
* A simple solution is preferred over an extra abstraction. An abstraction is added when it removes real complexity, not "for the future."
* Names reflect the meaning of entities and operations. Non-obvious abbreviations are prohibited.
* Public interfaces are stable, clear, and typed.

Example. Bad:

```text
class TaxUtils {
  static func calcVat(amt) = amt * 0.2
  static func calcGst(amt) = amt * 0.1
}
```

Good:

```text
// module tax
func calculateVat(amount: Money): Money = amount * 0.2
func calculateGst(amount: Money): Money = amount * 0.1
```

`TaxUtils` has no state and exists only to hold functions. `calc` and `amt` are abbreviations.

## Methods

### Responsibility

* A method performs one logically connected operation.
* Method length and parameter count are signals to review the responsibility, not quality criteria by themselves.

| Signal                                  | What to check                                                        |
| --------------------------------------- | -------------------------------------------------------------------- |
| The method is long                      | Does it do several independent steps that can be named separately?   |
| Many parameters                         | Do some parameters always travel together and form a missing type?   |
| A boolean flag parameter                | Does the flag switch between two different operations?               |
| The name needs "and" to be accurate     | The method does two things                                           |

A long method that performs one sequential algorithm without independent steps stays as it is.

### Queries and Commands

* A query returns data and does not change state. A command changes state.
* Queries and commands are separated when this makes the interface clearer.
* Justified exceptions are allowed: for example, an atomic operation that must change state and return the result in one step (`popNext()`, `reserveAndReturnId()`).

Bad:

```text
func getOrder(id): Order {
  order = repository.find(id)
  order.lastViewedAt = now()   // hidden state change in a query
  repository.save(order)
  return order
}
```

Good:

```text
func getOrder(id): Order = repository.find(id)
func markOrderViewed(id): void { ... }
```

### Docstrings

Every public method has a docstring. It describes:

| Section        | Content                                                           |
| -------------- | ----------------------------------------------------------------- |
| Purpose        | What the method does, in terms of the interface                   |
| Preconditions  | Significant requirements for arguments and state                  |
| Result         | What is returned, including empty and boundary cases              |
| Side effects   | State changes, I/O, events                                        |
| Errors         | Expected exceptions and when they occur                           |

Sections without content are omitted. The docstring does not retell the implementation.

```text
/**
 * Reserves stock for an order.
 *
 * Preconditions: quantity > 0.
 * Returns: the reservation ID.
 * Side effects: decreases available stock; publishes StockReserved.
 * Errors: InsufficientStock if available stock is less than quantity.
 */
func reserveStock(productId: ProductId, quantity: int): ReservationId
```

### Types

* Type annotations describe input and output values.
* Imprecise types (`any`, `object`, untyped dictionaries) and static-check suppressions require a justification next to them.

Bad:

```text
func applyDiscount(order: any, discount): any
```

Good:

```text
func applyDiscount(order: Order, discount: Percent): Order

// type-check suppressed: the SDK returns an untyped payload; validated by parsePayment below
payload = sdk.fetch(id)  // ignore-type
```

### Comments

* A comment explains a non-obvious reason, constraint, or decision that code cannot express clearly enough.
* A comment does not retell what the code does.

Bad:

```text
// increase the counter by one
retries = retries + 1
```

Good:

```text
// the payment provider rate-limits to 1 request per second per merchant
sleep(1s)
```

## Error Handling

### Error Contract

* A public operation has a clear error contract: the errors the caller can react to.
* The error type reflects its meaning at the level of the interface.
* Implementations follow the error contract of their abstraction. Low-level exceptions are converted into errors of the public contract when needed.

Example. The `OrderRepository` interface promises `OrderNotFound`. The SQL implementation does not leak driver errors:

```text
interface OrderRepository {
  // Errors: OrderNotFound if no order has this ID.
  func find(id: OrderId): Order
}

class SqlOrderRepository implements OrderRepository {
  func find(id) {
    row = db.queryOne("...", id)
    if row == null: throw OrderNotFound(id)
    return toOrder(row)
  }
}
```

### Preconditions and Invariants

* A component checks preconditions and enforces invariants within its own responsibility.
* A component does not re-check what another component already guarantees through its contract or types.

### Catching Exceptions

* Errors are not suppressed or caught without need.
* An exception is caught only for one of these reasons:

| Reason                                    | Example                                                        |
| ----------------------------------------- | -------------------------------------------------------------- |
| Execution can be recovered                | Retry a timed-out request; use a cached value                  |
| Cleanup is required                       | Release a lock, close a file, roll back a transaction          |
| Conversion at an abstraction boundary     | A driver error becomes `OrderNotFound` or `StorageUnavailable` |

* When an exception is converted, the original cause is preserved if the language supports it.

Bad:

```text
try { sendInvoice(invoice) }
catch (e) { }   // the error is lost

try { db.save(order) }
catch (e) { throw StorageUnavailable() }   // the cause is lost
```

Good:

```text
try { db.save(order) }
catch (e: ConnectionError) { throw StorageUnavailable(cause: e) }
```

### Failure of State-Changing Operations

* An operation that changes state preserves invariants when it fails.
* If full atomicity is impossible, the behavior on partial execution is defined: what has been applied, what has not, and how to recover. This is stated in the docstring.

```text
/**
 * Transfers stock between warehouses.
 *
 * Errors: TransferFailed. Not atomic: if the target update fails,
 * the source decrease is compensated by a return; if compensation also
 * fails, the transfer is marked NeedsReconciliation.
 */
func transferStock(from, to, productId, quantity): void
```

### Error Context

* Error context helps find the place and cause of the failure: operation, entity IDs, relevant values.
* Error context does not include secrets or sensitive data: passwords, tokens, keys, full personal data.

Bad:

```text
throw Error("failed")
throw AuthFailed("login failed for token=" + token)
```

Good:

```text
throw OrderNotFound("order not found: id=" + orderId)
throw AuthFailed("login failed: userId=" + userId + ", reason=expired")
```
