# P1 content-types DoD

P1 adds the strict versioned command, runtime-content, bound-pack and checkpoint
DTO boundary.  Runtime content is validated against the Riverside casepack and
bound by a canonical semantic SHA-256 digest.  Reducers, database models and
service transactions remain owned by later packets.
