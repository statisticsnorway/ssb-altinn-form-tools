# Error Handling & Transactions

- Insertions are wrapped in:

```begin_transaction → insert → commit```

- Any exception results in rollback
- Idempotency enforced through ```validate_form_is_new(refnr)```
