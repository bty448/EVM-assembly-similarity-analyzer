# EVM-assembly similarity analyzer.

## Motivation

In smart-contracts' world forks are quite ubiquitous and it is usually useful to know whether functions in contracts differ only in names.
This may find a good use in auditors' work.

## Plan

1. Collect base of contracts, which we would like to analyze, via a simple JavaScript/Python script using EtherScan public API.
2. Implement the basic analyzer in Java/C++ that will only check on complete similarity (except for name).
3. Try to improve our analyzer by taking into consideration inner calls and check recursively (and possibly some other things).
4. Run the analyzer on our contracts base.
5. Calculate some statistics and showcase results.
