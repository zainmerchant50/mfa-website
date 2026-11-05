-- MFA Hub v4 migration (run once on D1 "mfa-hub"): finance question kind.
-- kind: 'txn' = tied to one bank/card transaction (date + amount + payee), 'other' = decisions/setup. NULL = the hub guesses from the text.
ALTER TABLE finance_questions ADD COLUMN kind TEXT CHECK (kind IS NULL OR kind IN ('txn','other'));
UPDATE finance_questions SET kind = CASE
  WHEN (question GLOB '*: $[0-9]*' OR question GLOB '*: +$[0-9]*' OR question GLOB '*: -$[0-9]*') AND question GLOB '* on 20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]*' THEN 'txn' ELSE 'other' END;
