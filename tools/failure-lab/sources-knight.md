# Knight Capital Failure Lab source register

## Primary source

**S1** — U.S. Securities and Exchange Commission, *In the Matter of Knight Capital Americas LLC*, Exchange Act Release No. 70694, File No. 3-15570, administrative order, October 16, 2013. [Official SEC PDF](https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf).

References below are to Section III of the order and its numbered findings.

## Register

- **S1 — Incident date and scale:** §III, ¶1. August 1, 2012; 212 retail parent orders; about 45 minutes; more than 4 million executions in 154 stocks; more than 397 million shares; approximate long and short positions; loss greater than $460 million. The specific findings in ¶17 give 4 million executions and a $460 million loss.
- **S2 — RLP code, retained code, and flag:** §III, ¶¶12–13, 15–16. The RLP change added code to SMARS; the Power Peg functionality was no longer used but remained present and callable; the new code reused its flag; one of eight servers missed the new code and retained the old code.
- **S3 — Fill tracking and repeated child orders:** §III, ¶¶14, 16. In 2005, the cumulative-share tracking function moved earlier in the SMARS sequence and the unused Power Peg code was not retested. When the eighth server received orders carrying the reused flag, its code sent child orders rapidly without regard to executions already received.
- **S4 — Pre-open e-mails:** §III, ¶19. Beginning around 8:01 a.m. ET, 97 automated BNET reject e-mails referencing SMARS and Power Peg were sent to personnel before the 9:30 a.m. open. The order says these messages were not designed as system alerts and generally were not reviewed.
- **S5 — Removing the new code worsened the incident:** §III, ¶27. Knight removed the new RLP code from the seven servers that had received it correctly; the order says this led additional parent orders to activate Power Peg on those servers, like on the eighth.
- **S6 — Controls and response procedures:** §III, ¶¶21, 26–27. The order found inadequate SMARS output monitoring, no procedures to halt SMARS in response to its own aberrant activity, no written SMARS deployment procedures, and no supervisory incident-response procedures to guide employees.

## Source/spec distinctions

- The task brief describes a manual copy to all eight servers. The order says deployment began in stages and that one technician did not copy the new RLP code to one of eight servers (§III, ¶15); it does not say that every server was deployed by hand. The UI labels manual copy as a decision option and models a missed per-server copy, while this register preserves the narrower historical wording.
- The brief requests a 9:30 to 10:15 timeline. The order reports an approximately 45-minute incident and identifies 9:30 a.m. as the market open; 10:15 is a derived endpoint, not an exact stop time stated in the order.
- The introduction says Knight lost more than $460 million (§III, ¶1). The detailed impact finding reports a $460 million loss (§III, ¶17). The reveal uses the introduction's greater-than figure.
- The order does not name a particular kill-switch device. The UI states only that the order found no procedures to halt SMARS in response to aberrant activity and no incident-response procedures to guide employees (§III, ¶¶21, 27).

## Simulation boundary

The eight-server counterfactual, order counter, animation pace, choice costs, and the outcomes of safe choices are illustrative model behavior. Historical figures and events are attributed to the cited findings. The simulation does not claim a counterfactual firm outcome.
