# M2 packet 2.4 auth contract review

Date: 2026-09-15  
Reviewer: independent `m2_auth_contract_reviewer`  
Base: `0290e0c`

The historical auth spec was reviewed against the current hierarchy, API, frontend,
configuration, and north-star requirements. It initially failed for unresolved login
ownership, student multiple-enrollment selection, staff route context, secret provisioning,
and route authorization details. The supervisor amended the packet in
[`m2-auth-amendment.md`](m2-auth-amendment.md) and bounded the implementation in
[`m2-auth-dispatch.md`](m2-auth-dispatch.md).

The reviewer re-read the exact amended files and returned **PASS — dispatch ready**. The
review confirms canonical JWT claims and live-user checks, exact student/TA/instructor/admin
route rules, derived `created_by`, fixed error bodies with section choices, sessionStorage and
Axios bearer behavior, deterministic seeded users, explicit secret provisioning/test setup,
same-host browser evidence, and the exact out-of-scope boundary. No unresolved dispatch
blocker remains.
