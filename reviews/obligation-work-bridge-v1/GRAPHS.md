# Exact work-view catalog

Source `2322512c61f3ff387abcb402f1638c25b92f9add`. All IDs, complete input captures and raw graph JSON are in the bundle. Graphs below use exact IDs; display ordering is not a scheduler. Unresolved global review items remain outside positive witness lists.

## finite-method-gap / unregistered / primary

View `97d9e1c348209dda5d7774c1d95e3a070a8bd3b0c88b689dec84ae8a7195df51`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / UNKNOWN. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-method-gap / unregistered / shared_method

View `8a4895fddf91530025cb55d48932f6ffacad3e1f64f8d6afe5ff6ec3b29b1a93`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / UNKNOWN. No execution authority.

- `obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].
- `obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1` (`method-review`, any): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].
- `obligation:dba14c8fbc14f001c1f99e60a4fda629a402f38a8935c34eab0d6cdc19d5ef10` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "existing-execution:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:dba14c8fbc14f001c1f99e60a4fda629a402f38a8935c34eab0d6cdc19d5ef10",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "observed-goal:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-method-gap / registered / primary

View `b44b8beca7f07b1830d8975dbf486450b633569184bb15320c5be122768cc74c`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / UNKNOWN. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT']; witnesses []; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769` | revision ['model-ab'] | INPUTS_PRESENT | ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16', 'probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "target": "premise:ca6aa0ab0bf93d54f5f415831e8e85fafe2268b00fd1b9598cb960bcdfc94980",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "target": "premise:acfee2a1237f20d543d7837bc456943631fe65255b1ea84bb5490b23816d87e8",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "target": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-method-gap / registered / shared_method

View `2117e5063600f3d07f918156f94e7f8895c8910a33b6d42be8e1543a2151a6fe`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / UNKNOWN. No execution authority.

- `obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT']; witnesses []; insufficient []; stale [].
- `obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1` (`method-review`, any): UNKNOWN; reasons ['MISSING_ASSESSMENT']; witnesses []; insufficient []; stale [].
- `obligation:dba14c8fbc14f001c1f99e60a4fda629a402f38a8935c34eab0d6cdc19d5ef10` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769` | revision ['model-ab'] | INPUTS_PRESENT | ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16', 'probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "target": "premise:ca6aa0ab0bf93d54f5f415831e8e85fafe2268b00fd1b9598cb960bcdfc94980",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "target": "premise:acfee2a1237f20d543d7837bc456943631fe65255b1ea84bb5490b23816d87e8",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb",
    "target": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1",
    "target": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "existing-execution:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:dba14c8fbc14f001c1f99e60a4fda629a402f38a8935c34eab0d6cdc19d5ef10",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "observed-goal:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-method-gap / produced / primary

View `6ce2a5ad4490b85a4570904ffb72d715a1f6363179c9a4fae16ff0902bbdd4b2`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / PASS. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:c5fc4e3a6d794c12384c780df6710e40cb178f61226d4c2589c9f95d68a73acd']; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16', 'probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "UNKNOWN",
    "B": "PASS",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  },
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "target": "premise:ca6aa0ab0bf93d54f5f415831e8e85fafe2268b00fd1b9598cb960bcdfc94980",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "target": "premise:acfee2a1237f20d543d7837bc456943631fe65255b1ea84bb5490b23816d87e8",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "target": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-method-gap / produced / shared_method

View `274d84479a3d1baa72eacf99c6aa3222ef8fc68e73e4bd2e9c48cbc62aac4afe`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / PASS. No execution authority.

- `obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:c5fc4e3a6d794c12384c780df6710e40cb178f61226d4c2589c9f95d68a73acd']; insufficient []; stale [].
- `obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1` (`method-review`, any): PASS; reasons []; witnesses ['probability-belief/v1:c5fc4e3a6d794c12384c780df6710e40cb178f61226d4c2589c9f95d68a73acd']; insufficient []; stale [].
- `obligation:dba14c8fbc14f001c1f99e60a4fda629a402f38a8935c34eab0d6cdc19d5ef10` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16', 'probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "UNKNOWN",
    "B": "PASS",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  },
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "target": "premise:ca6aa0ab0bf93d54f5f415831e8e85fafe2268b00fd1b9598cb960bcdfc94980",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "target": "premise:acfee2a1237f20d543d7837bc456943631fe65255b1ea84bb5490b23816d87e8",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb",
    "target": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1",
    "target": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "existing-execution:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:dba14c8fbc14f001c1f99e60a4fda629a402f38a8935c34eab0d6cdc19d5ef10",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "observed-goal:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "operation:239af9bfca84f68a5509284281a4b587ceac316422c8877fb76e217bb7076769",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-optional-weak / before / primary

View `168ecdc744253b9ae7aa94ff047feae7905608241a366d384e5adfe86a6343ab`; complete: True; reason: COMPLETE.

A/B numerical: PASS / PASS. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:0a68e6a46720eac334b773acff4efc4e3f8c797fc2e2be2d70a35417900eb629']; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16'] | [] |
| `operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477` | deduction ['r-estimate', '1'] | INPUTS_PRESENT | ['probability-belief/v1:b586e4eaffc7abf0c36611c5d7371eb5eb874fc6eaba6d27281f81aaed88cc6a', 'probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd', 'probability-belief/v1:9f508e727ccd8fcfa81cc7d1077a6ed34949eda4f9fdb258942ea3f2b73ebae2', 'probability-belief/v1:49a16950e623096b5c1eef6d8f54a1a217c12fca3b907fe8e92291a074d58a0a', 'probability-belief/v1:da6a3e223eb3ab330c7c159d6f52dc6ecaf2f20eb198d03c44f462e10c561624'] | [] |

Global review reasons (full objection records retained):

```json
[]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "target": "premise:5abc6031f344c6a29c1497b47c3c02af6305cb6fac294017ff471de3ac9d6c1e",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 0,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:62cff1b64d5df965f5f216495efb7a3e16fa48eccf748438aa37896774506a5d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "target": "premise:ff3f1ca56f37d9a78ff82020309bf4d0f6a664df7182a726520aafbe063bfe39",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:5fc27b8db67c39d89fc96d7b8c5ed0955ab0c26037c4f570864d5296e2f9a15b",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:7f8d292deb695311d362cc5d30959b0fb5a60cb45c1f8b0595ba62f620e7eca3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:1dc4417f5089cd7bb5d05177903083a8b961aa46eed85452c8724f5c06753a19",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:2b11e908cc6c642d33631e389d06034c58c3c3c3bcc6af4d0d5dda081494423e",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "target": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "target": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-optional-weak / before / forecast_all

View `84550c9b8ae77443e4ccd25dcf45ad11b6c4878f127a74a9e82766897e37990f`; complete: True; reason: COMPLETE.

A/B numerical: PASS / PASS. No execution authority.

- `obligation:4c14055aa8b3da716f6f81b83305ccafab641b88306f4a1e4a95b02b7abccea8` (`forecast`, all): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient []; stale [].
- `obligation:826f679cfa82513de3a6a562f102ca6f9898833ae0630678a9b7e8c1b162baf9` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:0a68e6a46720eac334b773acff4efc4e3f8c797fc2e2be2d70a35417900eb629']; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16'] | [] |
| `operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477` | deduction ['r-estimate', '1'] | INPUTS_PRESENT | ['probability-belief/v1:b586e4eaffc7abf0c36611c5d7371eb5eb874fc6eaba6d27281f81aaed88cc6a', 'probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd', 'probability-belief/v1:9f508e727ccd8fcfa81cc7d1077a6ed34949eda4f9fdb258942ea3f2b73ebae2', 'probability-belief/v1:49a16950e623096b5c1eef6d8f54a1a217c12fca3b907fe8e92291a074d58a0a', 'probability-belief/v1:da6a3e223eb3ab330c7c159d6f52dc6ecaf2f20eb198d03c44f462e10c561624'] | [] |

Global review reasons (full objection records retained):

```json
[]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "target": "premise:5abc6031f344c6a29c1497b47c3c02af6305cb6fac294017ff471de3ac9d6c1e",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 0,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:62cff1b64d5df965f5f216495efb7a3e16fa48eccf748438aa37896774506a5d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "target": "premise:ff3f1ca56f37d9a78ff82020309bf4d0f6a664df7182a726520aafbe063bfe39",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:5fc27b8db67c39d89fc96d7b8c5ed0955ab0c26037c4f570864d5296e2f9a15b",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:7f8d292deb695311d362cc5d30959b0fb5a60cb45c1f8b0595ba62f620e7eca3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:1dc4417f5089cd7bb5d05177903083a8b961aa46eed85452c8724f5c06753a19",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:2b11e908cc6c642d33631e389d06034c58c3c3c3bcc6af4d0d5dda081494423e",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:4c14055aa8b3da716f6f81b83305ccafab641b88306f4a1e4a95b02b7abccea8",
    "target": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:826f679cfa82513de3a6a562f102ca6f9898833ae0630678a9b7e8c1b162baf9",
    "target": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "target": "existing-execution:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "target": "obligation:4c14055aa8b3da716f6f81b83305ccafab641b88306f4a1e4a95b02b7abccea8",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "target": "obligation:826f679cfa82513de3a6a562f102ca6f9898833ae0630678a9b7e8c1b162baf9",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "target": "observed-goal:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "target": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "target": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-optional-weak / before / mandatory_weak

View `e16aeebe5039b9f8e002360895d883b89a085e450e855f3755e779e4fb9f7e8d`; complete: True; reason: COMPLETE.

A/B numerical: PASS / UNKNOWN. No execution authority.

- `obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient []; stale [].
- `obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:0a68e6a46720eac334b773acff4efc4e3f8c797fc2e2be2d70a35417900eb629']; insufficient []; stale [].
- `obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6` (`weak-method`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT']; witnesses []; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16'] | [] |
| `operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477` | deduction ['r-estimate', '1'] | INPUTS_PRESENT | ['probability-belief/v1:b586e4eaffc7abf0c36611c5d7371eb5eb874fc6eaba6d27281f81aaed88cc6a', 'probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd', 'probability-belief/v1:9f508e727ccd8fcfa81cc7d1077a6ed34949eda4f9fdb258942ea3f2b73ebae2', 'probability-belief/v1:49a16950e623096b5c1eef6d8f54a1a217c12fca3b907fe8e92291a074d58a0a', 'probability-belief/v1:da6a3e223eb3ab330c7c159d6f52dc6ecaf2f20eb198d03c44f462e10c561624'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "PASS",
    "B": "UNKNOWN",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "target": "premise:5abc6031f344c6a29c1497b47c3c02af6305cb6fac294017ff471de3ac9d6c1e",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 0,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:62cff1b64d5df965f5f216495efb7a3e16fa48eccf748438aa37896774506a5d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "target": "premise:ff3f1ca56f37d9a78ff82020309bf4d0f6a664df7182a726520aafbe063bfe39",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:5fc27b8db67c39d89fc96d7b8c5ed0955ab0c26037c4f570864d5296e2f9a15b",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:7f8d292deb695311d362cc5d30959b0fb5a60cb45c1f8b0595ba62f620e7eca3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:1dc4417f5089cd7bb5d05177903083a8b961aa46eed85452c8724f5c06753a19",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:2b11e908cc6c642d33631e389d06034c58c3c3c3bcc6af4d0d5dda081494423e",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade",
    "target": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6",
    "target": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "existing-execution:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "observed-goal:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-optional-weak / after / primary

View `e960fe458a33bb3f1e67aa0aa9ceb1f51c592e76543437c876ca34c3f9d24411`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / PASS. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:0a68e6a46720eac334b773acff4efc4e3f8c797fc2e2be2d70a35417900eb629']; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:8ece60b13ab260392433629eb565d82c84519750f3d734eab4cf92d569cf0280']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16'] | [] |
| `operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477` | deduction ['r-estimate', '1'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:b586e4eaffc7abf0c36611c5d7371eb5eb874fc6eaba6d27281f81aaed88cc6a', 'probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd', 'probability-belief/v1:9f508e727ccd8fcfa81cc7d1077a6ed34949eda4f9fdb258942ea3f2b73ebae2', 'probability-belief/v1:49a16950e623096b5c1eef6d8f54a1a217c12fca3b907fe8e92291a074d58a0a', 'probability-belief/v1:da6a3e223eb3ab330c7c159d6f52dc6ecaf2f20eb198d03c44f462e10c561624'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "UNKNOWN",
    "B": "PASS",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  },
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "target": "premise:5abc6031f344c6a29c1497b47c3c02af6305cb6fac294017ff471de3ac9d6c1e",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 0,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:62cff1b64d5df965f5f216495efb7a3e16fa48eccf748438aa37896774506a5d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "target": "premise:ff3f1ca56f37d9a78ff82020309bf4d0f6a664df7182a726520aafbe063bfe39",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:5fc27b8db67c39d89fc96d7b8c5ed0955ab0c26037c4f570864d5296e2f9a15b",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:7f8d292deb695311d362cc5d30959b0fb5a60cb45c1f8b0595ba62f620e7eca3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:1dc4417f5089cd7bb5d05177903083a8b961aa46eed85452c8724f5c06753a19",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:2b11e908cc6c642d33631e389d06034c58c3c3c3bcc6af4d0d5dda081494423e",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "target": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "target": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-optional-weak / after / forecast_all

View `71070ce083a209e7e07d5a7c3caaba3d61c416aa0ad09aacf3617b6d49dfd377`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / UNKNOWN. No execution authority.

- `obligation:4c14055aa8b3da716f6f81b83305ccafab641b88306f4a1e4a95b02b7abccea8` (`forecast`, all): UNKNOWN; reasons ['INADEQUATE_SUPPORT', 'NO_REGISTERED_ROUTE']; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:8ece60b13ab260392433629eb565d82c84519750f3d734eab4cf92d569cf0280']; stale [].
- `obligation:826f679cfa82513de3a6a562f102ca6f9898833ae0630678a9b7e8c1b162baf9` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:0a68e6a46720eac334b773acff4efc4e3f8c797fc2e2be2d70a35417900eb629']; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16'] | [] |
| `operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477` | deduction ['r-estimate', '1'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:b586e4eaffc7abf0c36611c5d7371eb5eb874fc6eaba6d27281f81aaed88cc6a', 'probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd', 'probability-belief/v1:9f508e727ccd8fcfa81cc7d1077a6ed34949eda4f9fdb258942ea3f2b73ebae2', 'probability-belief/v1:49a16950e623096b5c1eef6d8f54a1a217c12fca3b907fe8e92291a074d58a0a', 'probability-belief/v1:da6a3e223eb3ab330c7c159d6f52dc6ecaf2f20eb198d03c44f462e10c561624'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:4c14055aa8b3da716f6f81b83305ccafab641b88306f4a1e4a95b02b7abccea8"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "target": "premise:5abc6031f344c6a29c1497b47c3c02af6305cb6fac294017ff471de3ac9d6c1e",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 0,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:62cff1b64d5df965f5f216495efb7a3e16fa48eccf748438aa37896774506a5d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "target": "premise:ff3f1ca56f37d9a78ff82020309bf4d0f6a664df7182a726520aafbe063bfe39",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:5fc27b8db67c39d89fc96d7b8c5ed0955ab0c26037c4f570864d5296e2f9a15b",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:7f8d292deb695311d362cc5d30959b0fb5a60cb45c1f8b0595ba62f620e7eca3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:1dc4417f5089cd7bb5d05177903083a8b961aa46eed85452c8724f5c06753a19",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:2b11e908cc6c642d33631e389d06034c58c3c3c3bcc6af4d0d5dda081494423e",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:4c14055aa8b3da716f6f81b83305ccafab641b88306f4a1e4a95b02b7abccea8",
    "target": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:826f679cfa82513de3a6a562f102ca6f9898833ae0630678a9b7e8c1b162baf9",
    "target": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "target": "existing-execution:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "target": "obligation:4c14055aa8b3da716f6f81b83305ccafab641b88306f4a1e4a95b02b7abccea8",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "target": "obligation:826f679cfa82513de3a6a562f102ca6f9898833ae0630678a9b7e8c1b162baf9",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "target": "observed-goal:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "target": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:00fbba81c8ec500f038f5fed508363b003ad48d12f87456079b6d3055da12ef7",
    "target": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-optional-weak / after / mandatory_weak

View `77e42b20175648d8c0248f4424340358033f4d71a7e570d8f0c0fff9b09021fc`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / UNKNOWN. No execution authority.

- `obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient []; stale [].
- `obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:0a68e6a46720eac334b773acff4efc4e3f8c797fc2e2be2d70a35417900eb629']; insufficient []; stale [].
- `obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6` (`weak-method`, all): UNKNOWN; reasons ['INADEQUATE_SUPPORT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient ['probability-belief/v1:8ece60b13ab260392433629eb565d82c84519750f3d734eab4cf92d569cf0280']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16'] | [] |
| `operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477` | deduction ['r-estimate', '1'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:b586e4eaffc7abf0c36611c5d7371eb5eb874fc6eaba6d27281f81aaed88cc6a', 'probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd', 'probability-belief/v1:9f508e727ccd8fcfa81cc7d1077a6ed34949eda4f9fdb258942ea3f2b73ebae2', 'probability-belief/v1:49a16950e623096b5c1eef6d8f54a1a217c12fca3b907fe8e92291a074d58a0a', 'probability-belief/v1:da6a3e223eb3ab330c7c159d6f52dc6ecaf2f20eb198d03c44f462e10c561624'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "target": "premise:5abc6031f344c6a29c1497b47c3c02af6305cb6fac294017ff471de3ac9d6c1e",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 0,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:62cff1b64d5df965f5f216495efb7a3e16fa48eccf748438aa37896774506a5d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "target": "premise:ff3f1ca56f37d9a78ff82020309bf4d0f6a664df7182a726520aafbe063bfe39",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:5fc27b8db67c39d89fc96d7b8c5ed0955ab0c26037c4f570864d5296e2f9a15b",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:7f8d292deb695311d362cc5d30959b0fb5a60cb45c1f8b0595ba62f620e7eca3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:1dc4417f5089cd7bb5d05177903083a8b961aa46eed85452c8724f5c06753a19",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "target": "premise:2b11e908cc6c642d33631e389d06034c58c3c3c3bcc6af4d0d5dda081494423e",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade",
    "target": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6",
    "target": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "existing-execution:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "observed-goal:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:b254411a9b9d82c938c9f7333cd9b317ba66b5d7ed9a90a63f4b9bd262f1089d",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:ffef154feb5834f395ac143873fe1911a73f9afe46522c30f5d8f7a7de593477",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-copied-source / copied / distinct_source

View `7fb79bb2cbe0c12890626ecfb0fd924a1fd50a5d387f8f751eb373b08bfd9a6d`; complete: True; reason: COMPLETE.

A/B numerical: PASS / UNKNOWN. No execution authority.

- `obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528']; insufficient []; stale [].
- `obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb` (`source-b`, any): UNKNOWN; reasons ['MISSING_ASSESSMENT']; witnesses []; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:3b7b43096c2f898838662871fef80adc3aabae6a845554efedb90788eda6d04e` | observation ['source-b'] | OBSERVATION_OPPORTUNITY | [] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "PASS",
    "B": "UNKNOWN",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  },
  {
    "category": "APPLICABILITY_REQUIRES_REVIEW",
    "detail": "current unclassified record remains visible",
    "record": {
      "adequate": true,
      "applicability": [
        {
          "class_id": "a",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "b",
          "eligible": false,
          "identity_match": true,
          "lineage_requirement": false
        },
        {
          "class_id": "derived",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "objection",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "revision",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        }
      ],
      "belief": {
        "accepted_at_revision": 12,
        "belief_revision_id": "probability-belief/v1:411ccbb07e33ec27ec1951aef6b54bc14efd13e4b2be1ede87acb46a51eb04af",
        "context_id": "ctx",
        "hard_policy_revision": "finite-hard-policy/v1",
        "interpretation": "scoped-estimate-alternatives/v1",
        "post_certificate_id": "probability-certificate/v1:c98d82ee316ae2c41db0e63f56de3a46155d4bb8a9aeed5a4bbf40c158bb2c86",
        "pre_certificate_id": "probability-certificate/v1:87318a66950dde5ca155bbf4bf2f0f37e66d1790af95d07f4bab9b9026bcfb4d",
        "probability_policy_revision": "semantic-input/v1",
        "proposal": {
          "assumptions": [
            "trusted-source-finite-estimate"
          ],
          "context_id": "ctx",
          "formula_id": "probability-observation/v1",
          "knowledge_revision": 11,
          "premise_ids": [],
          "proposal_id": "probability-proposal/v1:0c87c08fe49df91576e2384640e5722b2ea8e7069b801bbbf2e6790f155cf196",
          "support": {
            "ancestors": [],
            "conclusion": {
              "positive": true,
              "statement": {
                "arguments": [
                  "tested",
                  "healthy"
                ],
                "predicate": "pln:implication"
              }
            },
            "context_id": "ctx",
            "evidence_ids": [
              "copy"
            ],
            "lineage_roots": [
              "root:a"
            ],
            "support_id": "probability-observation/v1:630545f60779bf8b5f72dd37f397eb2d1917089da19f38e25852e25413474df0",
            "truth": {
              "confidence": 0.8,
              "strength": 0.7,
              "truth_model": "trueagi-pln-stv-finite-k1/v1"
            }
          }
        },
        "transition": {
          "context_id": "ctx",
          "evidence_id": "copy",
          "independence_id": null,
          "kind": "observation",
          "premise_revision_ids": [],
          "rule_id": null,
          "rule_revision": null,
          "transition_id": "probability-transition/v1:09ad9235b09383f3289e9f3da6b44fa48991f6def159289af0a59717be920a2f"
        }
      },
      "current": true,
      "disposition": "adequate_support",
      "eligible_classes": [],
      "id": "probability-belief/v1:411ccbb07e33ec27ec1951aef6b54bc14efd13e4b2be1ede87acb46a51eb04af",
      "orientation": "same",
      "provenance_valid": true
    }
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": null,
    "source": "obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb",
    "target": "operation:3b7b43096c2f898838662871fef80adc3aabae6a845554efedb90788eda6d04e",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "existing-execution:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "observed-goal:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "operation:3b7b43096c2f898838662871fef80adc3aabae6a845554efedb90788eda6d04e",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-copied-source / lawful / distinct_source

View `b65ed53a5816483a192180e5962668a78e86368b2985678a561490d02deae046`; complete: True; reason: COMPLETE.

A/B numerical: PASS / UNKNOWN. No execution authority.

- `obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528']; insufficient []; stale [].
- `obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb` (`source-b`, any): PASS; reasons []; witnesses ['probability-belief/v1:03dd654bde4d8d0bfbab0aaa826c037e3cfe17ddec8299bbf11af135e0da0f25']; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:3b7b43096c2f898838662871fef80adc3aabae6a845554efedb90788eda6d04e` | observation ['source-b'] | OBSERVATION_OPPORTUNITY | [] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "PASS",
    "B": "UNKNOWN",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  },
  {
    "category": "APPLICABILITY_REQUIRES_REVIEW",
    "detail": "current unclassified record remains visible",
    "record": {
      "adequate": true,
      "applicability": [
        {
          "class_id": "a",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "b",
          "eligible": false,
          "identity_match": true,
          "lineage_requirement": false
        },
        {
          "class_id": "derived",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "objection",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "revision",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        }
      ],
      "belief": {
        "accepted_at_revision": 12,
        "belief_revision_id": "probability-belief/v1:411ccbb07e33ec27ec1951aef6b54bc14efd13e4b2be1ede87acb46a51eb04af",
        "context_id": "ctx",
        "hard_policy_revision": "finite-hard-policy/v1",
        "interpretation": "scoped-estimate-alternatives/v1",
        "post_certificate_id": "probability-certificate/v1:c98d82ee316ae2c41db0e63f56de3a46155d4bb8a9aeed5a4bbf40c158bb2c86",
        "pre_certificate_id": "probability-certificate/v1:87318a66950dde5ca155bbf4bf2f0f37e66d1790af95d07f4bab9b9026bcfb4d",
        "probability_policy_revision": "semantic-input/v1",
        "proposal": {
          "assumptions": [
            "trusted-source-finite-estimate"
          ],
          "context_id": "ctx",
          "formula_id": "probability-observation/v1",
          "knowledge_revision": 11,
          "premise_ids": [],
          "proposal_id": "probability-proposal/v1:0c87c08fe49df91576e2384640e5722b2ea8e7069b801bbbf2e6790f155cf196",
          "support": {
            "ancestors": [],
            "conclusion": {
              "positive": true,
              "statement": {
                "arguments": [
                  "tested",
                  "healthy"
                ],
                "predicate": "pln:implication"
              }
            },
            "context_id": "ctx",
            "evidence_ids": [
              "copy"
            ],
            "lineage_roots": [
              "root:a"
            ],
            "support_id": "probability-observation/v1:630545f60779bf8b5f72dd37f397eb2d1917089da19f38e25852e25413474df0",
            "truth": {
              "confidence": 0.8,
              "strength": 0.7,
              "truth_model": "trueagi-pln-stv-finite-k1/v1"
            }
          }
        },
        "transition": {
          "context_id": "ctx",
          "evidence_id": "copy",
          "independence_id": null,
          "kind": "observation",
          "premise_revision_ids": [],
          "rule_id": null,
          "rule_revision": null,
          "transition_id": "probability-transition/v1:09ad9235b09383f3289e9f3da6b44fa48991f6def159289af0a59717be920a2f"
        }
      },
      "current": true,
      "disposition": "adequate_support",
      "eligible_classes": [],
      "id": "probability-belief/v1:411ccbb07e33ec27ec1951aef6b54bc14efd13e4b2be1ede87acb46a51eb04af",
      "orientation": "same",
      "provenance_valid": true
    }
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": null,
    "source": "obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb",
    "target": "operation:3b7b43096c2f898838662871fef80adc3aabae6a845554efedb90788eda6d04e",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "existing-execution:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "observed-goal:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "operation:3b7b43096c2f898838662871fef80adc3aabae6a845554efedb90788eda6d04e",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-copied-source / withdrawn / distinct_source

View `99a081d1a79067ddb7921745aff0ce4859d0e3eed3b8867bd602b3522f228a62`; complete: True; reason: COMPLETE.

A/B numerical: PASS / PASS. No execution authority.

- `obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528']; insufficient []; stale [].
- `obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb` (`source-b`, any): PASS; reasons []; witnesses ['probability-belief/v1:03dd654bde4d8d0bfbab0aaa826c037e3cfe17ddec8299bbf11af135e0da0f25']; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:3b7b43096c2f898838662871fef80adc3aabae6a845554efedb90788eda6d04e` | observation ['source-b'] | OBSERVATION_OPPORTUNITY | [] | [] |

Global review reasons (full objection records retained):

```json
[]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": null,
    "source": "obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb",
    "target": "operation:3b7b43096c2f898838662871fef80adc3aabae6a845554efedb90788eda6d04e",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "existing-execution:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "observed-goal:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "operation:3b7b43096c2f898838662871fef80adc3aabae6a845554efedb90788eda6d04e",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-freshness / initial / distinct_source

View `40efd901891d894aa6b6f7b406dc7659505ea4928c3507c6be62a5b2ea125c39`; complete: True; reason: COMPLETE.

A/B numerical: PASS / PASS. No execution authority.

- `obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528']; insufficient []; stale [].
- `obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb` (`source-b`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:256d224eb8f653baef613a0ca14600ae829f5252bfe5e588bb08ed10d4a40285` | observation ['source-a'] | OBSERVATION_OPPORTUNITY | [] | [] |

Global review reasons (full objection records retained):

```json
[]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": null,
    "source": "obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702",
    "target": "operation:256d224eb8f653baef613a0ca14600ae829f5252bfe5e588bb08ed10d4a40285",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "existing-execution:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "observed-goal:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "operation:256d224eb8f653baef613a0ca14600ae829f5252bfe5e588bb08ed10d4a40285",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-freshness / revoked / distinct_source

View `feef417d425ee26839678f6542dabe2390f61b76b7c913aec4e701ea56495db8`; complete: True; reason: COMPLETE.

A/B numerical: PASS / STALE. No execution authority.

- `obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702` (`forecast`, any): STALE; reasons ['STALE_SUPPORT']; witnesses []; insufficient []; stale ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528'].
- `obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb` (`source-b`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:256d224eb8f653baef613a0ca14600ae829f5252bfe5e588bb08ed10d4a40285` | observation ['source-a'] | OBSERVATION_OPPORTUNITY | [] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "PASS",
    "B": "STALE",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": null,
    "source": "obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702",
    "target": "operation:256d224eb8f653baef613a0ca14600ae829f5252bfe5e588bb08ed10d4a40285",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "existing-execution:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "observed-goal:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "operation:256d224eb8f653baef613a0ca14600ae829f5252bfe5e588bb08ed10d4a40285",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-freshness / replaced / distinct_source

View `efbeedb7affdc4c56b47993737ddd1bcc7ef490a33686f06b7ca09403f265a3d`; complete: True; reason: COMPLETE.

A/B numerical: PASS / PASS. No execution authority.

- `obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:7fb3613b29b6db9993ec08397aeb42cf138541e4547d01f66f816ef348fe0438']; insufficient []; stale ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528'].
- `obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb` (`source-b`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:256d224eb8f653baef613a0ca14600ae829f5252bfe5e588bb08ed10d4a40285` | observation ['source-a'] | OBSERVATION_OPPORTUNITY | [] | [] |

Global review reasons (full objection records retained):

```json
[]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": null,
    "source": "obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702",
    "target": "operation:256d224eb8f653baef613a0ca14600ae829f5252bfe5e588bb08ed10d4a40285",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "existing-execution:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "observed-goal:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "operation:256d224eb8f653baef613a0ca14600ae829f5252bfe5e588bb08ed10d4a40285",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-freshness / survivor / distinct_source

View `ba45e7ab4010eec30a6e440d53e79837e9aa5133a4a2353cab9cca6a3cbf0452`; complete: True; reason: COMPLETE.

A/B numerical: PASS / PASS. No execution authority.

- `obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:0515d8be08a934e1aee8df84f770edd97eabfbacc45599441d71dcff62f77037']; insufficient []; stale ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:7fb3613b29b6db9993ec08397aeb42cf138541e4547d01f66f816ef348fe0438'].
- `obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb` (`source-b`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:256d224eb8f653baef613a0ca14600ae829f5252bfe5e588bb08ed10d4a40285` | observation ['source-a'] | OBSERVATION_OPPORTUNITY | [] | [] |

Global review reasons (full objection records retained):

```json
[]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": null,
    "source": "obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702",
    "target": "operation:256d224eb8f653baef613a0ca14600ae829f5252bfe5e588bb08ed10d4a40285",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "existing-execution:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:35f323bfb18ade5b2d87a6643e9373640d77f08e20788f8d8ea9a5a098b6b702",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "obligation:e423d2b1eb799021dba5ca2454b742d9bedccd82240b018debad947660bc47bb",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "observed-goal:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:c6a403a6a270a07c9a4036a11fee7a3fd0b98704fc50997a2666de6d4c669fa4",
    "target": "operation:256d224eb8f653baef613a0ca14600ae829f5252bfe5e588bb08ed10d4a40285",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-objection / before / primary

View `8d7a9b693965cf05ac41c643c8f5f3479f89c2692ab58ca031301d12e576a6d7`; complete: True; reason: COMPLETE.

A/B numerical: PASS / PASS. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:0a68e6a46720eac334b773acff4efc4e3f8c797fc2e2be2d70a35417900eb629']; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16'] | [] |
| `operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0` | deduction ['r-objection', '1'] | INPUTS_PRESENT | ['probability-belief/v1:05fe175ecb60aeb2594fde721ed92e64db2c95dd2da9b3d2e54c8c0bfcbc2eb8', 'probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd', 'probability-belief/v1:a22bcf10cbbeaa58c347fd35ff66d48dd0923f1e40dde934e881536d462c3877', 'probability-belief/v1:098c075e073a8ca7ab99453124e3760e8e8c00c46aa81afd544250f8ce9d5f87', 'probability-belief/v1:3c4ee7106a7acfd6db489593853c930054a5e54d8f4bbaaa10fdbdb4c60a6b4c'] | [] |

Global review reasons (full objection records retained):

```json
[]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf",
    "target": "premise:9ccb4402d6ad1bc08557c5599b7b5c788f8d0227ab22fa8e0a3e8c147ae0a7bc",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 0,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:ce7dd8eb141416607ea302fa8cc4d160bcbe6d677751f747a42b422c166f6cc3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf",
    "target": "premise:9adebfdca1574a2169c7d112e1f9726d56e6b7fd7677359268b66f88fdd547c1",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:934805f556c9f4bbf051af60288a98fb7ceeb7051f687ab7836bc46a1c1ee68d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:3588921d8c843cb09aa46b4b469403d91d29f908dc9b7f92be84a2194e4905fd",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:8403ddeb3a2f3f25541d8347de9f522cf6215d20d956de979c0030eedc4bdd7b",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:1f16b616ea7475ecec5c6781f9e01f5144a0f8a6664f19dea9931c69e23f8873",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "target": "operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "target": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-objection / derived / primary

View `9867804d77f2384a8b82a2f7c4ec96578ce1fd0909fe2593a21b6a42ee96c91b`; complete: True; reason: COMPLETE.

A/B numerical: FAIL / FAIL. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:0a68e6a46720eac334b773acff4efc4e3f8c797fc2e2be2d70a35417900eb629']; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:86183a521b86bde0e88b6a44e5d2d1513e4e8e396552d5cf8ddac85f269ad2e7']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16'] | [] |
| `operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0` | deduction ['r-objection', '1'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:05fe175ecb60aeb2594fde721ed92e64db2c95dd2da9b3d2e54c8c0bfcbc2eb8', 'probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd', 'probability-belief/v1:a22bcf10cbbeaa58c347fd35ff66d48dd0923f1e40dde934e881536d462c3877', 'probability-belief/v1:098c075e073a8ca7ab99453124e3760e8e8c00c46aa81afd544250f8ce9d5f87', 'probability-belief/v1:3c4ee7106a7acfd6db489593853c930054a5e54d8f4bbaaa10fdbdb4c60a6b4c'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "FAIL"
  },
  {
    "category": "OBJECTION_REQUIRES_REVIEW",
    "detail": "strength_objection",
    "record": {
      "adequate": false,
      "applicability": [
        {
          "class_id": "a",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": false
        },
        {
          "class_id": "b",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": false
        },
        {
          "class_id": "derived",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "objection",
          "eligible": true,
          "identity_match": true,
          "lineage_requirement": true
        },
        {
          "class_id": "revision",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        }
      ],
      "belief": {
        "accepted_at_revision": 31,
        "belief_revision_id": "probability-belief/v1:86183a521b86bde0e88b6a44e5d2d1513e4e8e396552d5cf8ddac85f269ad2e7",
        "context_id": "ctx",
        "hard_policy_revision": "finite-hard-policy/v1",
        "interpretation": "scoped-estimate-alternatives/v1",
        "post_certificate_id": "probability-certificate/v1:db3b6c5d14411175eb35aad6960bc0e3901e2f731d091f25443edb5db9136d20",
        "pre_certificate_id": "probability-certificate/v1:c780affc494a0802a9ba057db4aa5736df6c3368833856a99c1b7960bfea5aaf",
        "probability_policy_revision": "semantic-input/v1",
        "proposal": {
          "assumptions": [
            "upstream-heuristic-deduction",
            "upstream-q>0.9999-uses-r"
          ],
          "context_id": "ctx",
          "formula_id": "trueagi-pln/4405956947c4b53c7ff01bd565aa3b114bc970a1/Truth_Deduction",
          "knowledge_revision": 30,
          "premise_ids": [
            "probability-observation/v1:e7189df51e613fa28e2db3909886f4773fe92f2f9175f3b65c6207d7fe5f8e10",
            "probability-observation/v1:ef592ca4a3d08e906b0721418cbaac1ff7abd4320b9971339712da7d269dcf08",
            "probability-observation/v1:0449a41ff7e8ed2760f950479f3a6a39618390715aefd0adae9e129bef5332b6",
            "probability-observation/v1:98c16e49e5ee31ee6877d8dbf5066f2ba4b850ad251865bcb5217d92a26fa5a1",
            "probability-observation/v1:6528d474b864a55e58da71f3cbaf15e9fa9009c15b8a5948409506efb0f1f63c"
          ],
          "proposal_id": "pln-proposal/v1:7de8bb875f6b55d570484ebb117913e9acb262ad897eb37a536892790a73ebe5",
          "support": {
            "ancestors": [
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "tested",
                    "weak"
                  ],
                  "predicate": "pln:implication"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "weak",
                    "healthy"
                  ],
                  "predicate": "pln:implication"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "healthy"
                  ],
                  "predicate": "pln:proposition"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "tested"
                  ],
                  "predicate": "pln:proposition"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "weak"
                  ],
                  "predicate": "pln:proposition"
                }
              }
            ],
            "conclusion": {
              "positive": true,
              "statement": {
                "arguments": [
                  "tested",
                  "healthy"
                ],
                "predicate": "pln:implication"
              }
            },
            "context_id": "ctx",
            "evidence_ids": [
              "input-0",
              "input-1",
              "input-2",
              "input-3",
              "input-4"
            ],
            "lineage_roots": [
              "root:input-0",
              "root:input-1",
              "root:input-2",
              "root:input-3",
              "root:input-4"
            ],
            "support_id": "pln-support/v1:6a9cdf673e96c13731f0f586522b0b4367de3651ccec50cf2e5a0f5a7b22226f",
            "truth": {
              "confidence": 0.0002000000000000001,
              "strength": 0.1,
              "truth_model": "trueagi-pln-stv-finite-k1/v1"
            }
          }
        },
        "transition": {
          "context_id": "ctx",
          "evidence_id": null,
          "independence_id": null,
          "kind": "deduction",
          "premise_revision_ids": [
            "probability-belief/v1:05fe175ecb60aeb2594fde721ed92e64db2c95dd2da9b3d2e54c8c0bfcbc2eb8",
            "probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd",
            "probability-belief/v1:a22bcf10cbbeaa58c347fd35ff66d48dd0923f1e40dde934e881536d462c3877",
            "probability-belief/v1:098c075e073a8ca7ab99453124e3760e8e8c00c46aa81afd544250f8ce9d5f87",
            "probability-belief/v1:3c4ee7106a7acfd6db489593853c930054a5e54d8f4bbaaa10fdbdb4c60a6b4c"
          ],
          "rule_id": "r-objection",
          "rule_revision": "1",
          "transition_id": "probability-transition/v1:bca14cde2e5ed809ffc5c9a9dc1c87b680c376eb67b9aae00ba89f6f0fcb48f0"
        }
      },
      "current": true,
      "disposition": "strength_objection",
      "eligible_classes": [
        "objection"
      ],
      "id": "probability-belief/v1:86183a521b86bde0e88b6a44e5d2d1513e4e8e396552d5cf8ddac85f269ad2e7",
      "orientation": "same",
      "provenance_valid": true
    }
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf",
    "target": "premise:9ccb4402d6ad1bc08557c5599b7b5c788f8d0227ab22fa8e0a3e8c147ae0a7bc",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 0,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:ce7dd8eb141416607ea302fa8cc4d160bcbe6d677751f747a42b422c166f6cc3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf",
    "target": "premise:9adebfdca1574a2169c7d112e1f9726d56e6b7fd7677359268b66f88fdd547c1",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:934805f556c9f4bbf051af60288a98fb7ceeb7051f687ab7836bc46a1c1ee68d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:3588921d8c843cb09aa46b4b469403d91d29f908dc9b7f92be84a2194e4905fd",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:8403ddeb3a2f3f25541d8347de9f522cf6215d20d956de979c0030eedc4bdd7b",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:1f16b616ea7475ecec5c6781f9e01f5144a0f8a6664f19dea9931c69e23f8873",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "target": "operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "target": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-objection / opposite / primary

View `cdeb744fde1986a9ab7a7beb9a6fbaf8d10bfa496ad25b48fd9486ed871784c1`; complete: True; reason: COMPLETE.

A/B numerical: FAIL / FAIL. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:0a68e6a46720eac334b773acff4efc4e3f8c797fc2e2be2d70a35417900eb629']; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:86183a521b86bde0e88b6a44e5d2d1513e4e8e396552d5cf8ddac85f269ad2e7']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16'] | [] |
| `operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0` | deduction ['r-objection', '1'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:05fe175ecb60aeb2594fde721ed92e64db2c95dd2da9b3d2e54c8c0bfcbc2eb8', 'probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd', 'probability-belief/v1:a22bcf10cbbeaa58c347fd35ff66d48dd0923f1e40dde934e881536d462c3877', 'probability-belief/v1:098c075e073a8ca7ab99453124e3760e8e8c00c46aa81afd544250f8ce9d5f87', 'probability-belief/v1:3c4ee7106a7acfd6db489593853c930054a5e54d8f4bbaaa10fdbdb4c60a6b4c'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "FAIL"
  },
  {
    "category": "OBJECTION_REQUIRES_REVIEW",
    "detail": "opposite_objection",
    "record": {
      "adequate": false,
      "applicability": [
        {
          "class_id": "a",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": false
        },
        {
          "class_id": "b",
          "eligible": true,
          "identity_match": true,
          "lineage_requirement": true
        },
        {
          "class_id": "derived",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "objection",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "revision",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        }
      ],
      "belief": {
        "accepted_at_revision": 34,
        "belief_revision_id": "probability-belief/v1:bc799fba85bfd42fdfb336be63649cf2126554f0801c8ac0edb9482b6f38c5c9",
        "context_id": "ctx",
        "hard_policy_revision": "finite-hard-policy/v1",
        "interpretation": "scoped-estimate-alternatives/v1",
        "post_certificate_id": "probability-certificate/v1:8c2aec340612ebb80a9b48a9a83a13f2f9f062ceeab840c5299a656fc6e2e4d0",
        "pre_certificate_id": "probability-certificate/v1:1358af3edd8ab1715e42b3117428a6bdeefb9e572a2425a08edec39d2b09bb21",
        "probability_policy_revision": "semantic-input/v1",
        "proposal": {
          "assumptions": [
            "trusted-source-finite-estimate"
          ],
          "context_id": "ctx",
          "formula_id": "probability-observation/v1",
          "knowledge_revision": 33,
          "premise_ids": [],
          "proposal_id": "probability-proposal/v1:f8b708221c23a25f42e583cc62a48e031bb1cd06ee4f2ab555852cf4a8833246",
          "support": {
            "ancestors": [],
            "conclusion": {
              "positive": false,
              "statement": {
                "arguments": [
                  "tested",
                  "healthy"
                ],
                "predicate": "pln:implication"
              }
            },
            "context_id": "ctx",
            "evidence_ids": [
              "opposite"
            ],
            "lineage_roots": [
              "root:b"
            ],
            "support_id": "probability-observation/v1:60f9a45b7a77f33704fef2bc7bcf44be48b0aaca6f3ed9a9670b968ce4a0408e",
            "truth": {
              "confidence": 0.05,
              "strength": 0.7,
              "truth_model": "trueagi-pln-stv-finite-k1/v1"
            }
          }
        },
        "transition": {
          "context_id": "ctx",
          "evidence_id": "opposite",
          "independence_id": null,
          "kind": "observation",
          "premise_revision_ids": [],
          "rule_id": null,
          "rule_revision": null,
          "transition_id": "probability-transition/v1:317845e1fc5d6dfa01a236aba80b7d1ee25855438de8ccac281ba589d1df4519"
        }
      },
      "current": true,
      "disposition": "opposite_objection",
      "eligible_classes": [
        "b"
      ],
      "id": "probability-belief/v1:bc799fba85bfd42fdfb336be63649cf2126554f0801c8ac0edb9482b6f38c5c9",
      "orientation": "opposite",
      "provenance_valid": true
    }
  },
  {
    "category": "OBJECTION_REQUIRES_REVIEW",
    "detail": "strength_objection",
    "record": {
      "adequate": false,
      "applicability": [
        {
          "class_id": "a",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": false
        },
        {
          "class_id": "b",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": false
        },
        {
          "class_id": "derived",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "objection",
          "eligible": true,
          "identity_match": true,
          "lineage_requirement": true
        },
        {
          "class_id": "revision",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        }
      ],
      "belief": {
        "accepted_at_revision": 31,
        "belief_revision_id": "probability-belief/v1:86183a521b86bde0e88b6a44e5d2d1513e4e8e396552d5cf8ddac85f269ad2e7",
        "context_id": "ctx",
        "hard_policy_revision": "finite-hard-policy/v1",
        "interpretation": "scoped-estimate-alternatives/v1",
        "post_certificate_id": "probability-certificate/v1:db3b6c5d14411175eb35aad6960bc0e3901e2f731d091f25443edb5db9136d20",
        "pre_certificate_id": "probability-certificate/v1:c780affc494a0802a9ba057db4aa5736df6c3368833856a99c1b7960bfea5aaf",
        "probability_policy_revision": "semantic-input/v1",
        "proposal": {
          "assumptions": [
            "upstream-heuristic-deduction",
            "upstream-q>0.9999-uses-r"
          ],
          "context_id": "ctx",
          "formula_id": "trueagi-pln/4405956947c4b53c7ff01bd565aa3b114bc970a1/Truth_Deduction",
          "knowledge_revision": 30,
          "premise_ids": [
            "probability-observation/v1:e7189df51e613fa28e2db3909886f4773fe92f2f9175f3b65c6207d7fe5f8e10",
            "probability-observation/v1:ef592ca4a3d08e906b0721418cbaac1ff7abd4320b9971339712da7d269dcf08",
            "probability-observation/v1:0449a41ff7e8ed2760f950479f3a6a39618390715aefd0adae9e129bef5332b6",
            "probability-observation/v1:98c16e49e5ee31ee6877d8dbf5066f2ba4b850ad251865bcb5217d92a26fa5a1",
            "probability-observation/v1:6528d474b864a55e58da71f3cbaf15e9fa9009c15b8a5948409506efb0f1f63c"
          ],
          "proposal_id": "pln-proposal/v1:7de8bb875f6b55d570484ebb117913e9acb262ad897eb37a536892790a73ebe5",
          "support": {
            "ancestors": [
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "tested",
                    "weak"
                  ],
                  "predicate": "pln:implication"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "weak",
                    "healthy"
                  ],
                  "predicate": "pln:implication"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "healthy"
                  ],
                  "predicate": "pln:proposition"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "tested"
                  ],
                  "predicate": "pln:proposition"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "weak"
                  ],
                  "predicate": "pln:proposition"
                }
              }
            ],
            "conclusion": {
              "positive": true,
              "statement": {
                "arguments": [
                  "tested",
                  "healthy"
                ],
                "predicate": "pln:implication"
              }
            },
            "context_id": "ctx",
            "evidence_ids": [
              "input-0",
              "input-1",
              "input-2",
              "input-3",
              "input-4"
            ],
            "lineage_roots": [
              "root:input-0",
              "root:input-1",
              "root:input-2",
              "root:input-3",
              "root:input-4"
            ],
            "support_id": "pln-support/v1:6a9cdf673e96c13731f0f586522b0b4367de3651ccec50cf2e5a0f5a7b22226f",
            "truth": {
              "confidence": 0.0002000000000000001,
              "strength": 0.1,
              "truth_model": "trueagi-pln-stv-finite-k1/v1"
            }
          }
        },
        "transition": {
          "context_id": "ctx",
          "evidence_id": null,
          "independence_id": null,
          "kind": "deduction",
          "premise_revision_ids": [
            "probability-belief/v1:05fe175ecb60aeb2594fde721ed92e64db2c95dd2da9b3d2e54c8c0bfcbc2eb8",
            "probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd",
            "probability-belief/v1:a22bcf10cbbeaa58c347fd35ff66d48dd0923f1e40dde934e881536d462c3877",
            "probability-belief/v1:098c075e073a8ca7ab99453124e3760e8e8c00c46aa81afd544250f8ce9d5f87",
            "probability-belief/v1:3c4ee7106a7acfd6db489593853c930054a5e54d8f4bbaaa10fdbdb4c60a6b4c"
          ],
          "rule_id": "r-objection",
          "rule_revision": "1",
          "transition_id": "probability-transition/v1:bca14cde2e5ed809ffc5c9a9dc1c87b680c376eb67b9aae00ba89f6f0fcb48f0"
        }
      },
      "current": true,
      "disposition": "strength_objection",
      "eligible_classes": [
        "objection"
      ],
      "id": "probability-belief/v1:86183a521b86bde0e88b6a44e5d2d1513e4e8e396552d5cf8ddac85f269ad2e7",
      "orientation": "same",
      "provenance_valid": true
    }
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf",
    "target": "premise:9ccb4402d6ad1bc08557c5599b7b5c788f8d0227ab22fa8e0a3e8c147ae0a7bc",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 0,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:ce7dd8eb141416607ea302fa8cc4d160bcbe6d677751f747a42b422c166f6cc3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf",
    "target": "premise:9adebfdca1574a2169c7d112e1f9726d56e6b7fd7677359268b66f88fdd547c1",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:934805f556c9f4bbf051af60288a98fb7ceeb7051f687ab7836bc46a1c1ee68d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:3588921d8c843cb09aa46b4b469403d91d29f908dc9b7f92be84a2194e4905fd",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:8403ddeb3a2f3f25541d8347de9f522cf6215d20d956de979c0030eedc4bdd7b",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "target": "premise:1f16b616ea7475ecec5c6781f9e01f5144a0f8a6664f19dea9931c69e23f8873",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "target": "operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "target": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:3b9bdf47caca42b8d72dc47a656d532f1b8fa2c431a3ace1a1fad2c266df3dcf",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:814d021cebef1750d21f7dbf733d12d6f4f5b3f93fd5a2eb59c4813e523dafc0",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-registry / initial / mandatory_weak

View `eb7723deb3eec5ad3f7df14cd73c8852cac861d448af13816291cefd9de6c64b`; complete: True; reason: COMPLETE.

A/B numerical: PASS / UNKNOWN. No execution authority.

- `obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528']; insufficient []; stale [].
- `obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].
- `obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6` (`weak-method`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a` | observation ['source-b'] | OBSERVATION_OPPORTUNITY | [] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "PASS",
    "B": "UNKNOWN",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": null,
    "source": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "target": "operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "existing-execution:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "observed-goal:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-registry / registered / mandatory_weak

View `97d573d0eb9f0cfc4840e69500bda230d65e9eafa994ca94778af4638999870e`; complete: True; reason: COMPLETE.

A/B numerical: PASS / UNKNOWN. No execution authority.

- `obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528']; insufficient []; stale [].
- `obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].
- `obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6` (`weak-method`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT']; witnesses []; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a` | observation ['source-b'] | OBSERVATION_OPPORTUNITY | [] | [] |
| `operation:7c21452150aa49b4cfb9bcf2b3ace8184cc2aecab18b020ab714807972e9a558` | deduction ['r-estimate', '1'] | MISSING_PREMISES | [None, None, None, None, None] | [0, 1, 2, 3, 4] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "PASS",
    "B": "UNKNOWN",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no direct observation route for this exact premise in the supported fragment",
    "node": "missing-premise:26499fbf034c0291d92e4821269a32ad9e186d2ab1a327925c689ce0971a5178"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no direct observation route for this exact premise in the supported fragment",
    "node": "missing-premise:2e3297153d836fdd0c8920f0e44c86026bf5b7ff9017f3b92314f43d3d7a9d12"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no direct observation route for this exact premise in the supported fragment",
    "node": "missing-premise:3f4b29ac0f8927a93d8c0dbed02de79163100f5ddff556a5d572daa4d355ed2c"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no direct observation route for this exact premise in the supported fragment",
    "node": "missing-premise:518a607649203e2c3f3f0545c5c1a0459252ef778243318b1e8db005235e49cc"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no direct observation route for this exact premise in the supported fragment",
    "node": "missing-premise:c8ff0fc965df6b54eb40827ed3753f0b44a923a032a1db1a66bad8405c203270"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:7c21452150aa49b4cfb9bcf2b3ace8184cc2aecab18b020ab714807972e9a558",
    "target": "missing-premise:26499fbf034c0291d92e4821269a32ad9e186d2ab1a327925c689ce0971a5178",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:7c21452150aa49b4cfb9bcf2b3ace8184cc2aecab18b020ab714807972e9a558",
    "target": "missing-premise:c8ff0fc965df6b54eb40827ed3753f0b44a923a032a1db1a66bad8405c203270",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:7c21452150aa49b4cfb9bcf2b3ace8184cc2aecab18b020ab714807972e9a558",
    "target": "missing-premise:518a607649203e2c3f3f0545c5c1a0459252ef778243318b1e8db005235e49cc",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:7c21452150aa49b4cfb9bcf2b3ace8184cc2aecab18b020ab714807972e9a558",
    "target": "missing-premise:2e3297153d836fdd0c8920f0e44c86026bf5b7ff9017f3b92314f43d3d7a9d12",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:7c21452150aa49b4cfb9bcf2b3ace8184cc2aecab18b020ab714807972e9a558",
    "target": "missing-premise:3f4b29ac0f8927a93d8c0dbed02de79163100f5ddff556a5d572daa4d355ed2c",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "target": "operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6",
    "target": "operation:7c21452150aa49b4cfb9bcf2b3ace8184cc2aecab18b020ab714807972e9a558",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "existing-execution:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "observed-goal:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:7c21452150aa49b4cfb9bcf2b3ace8184cc2aecab18b020ab714807972e9a558",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-registry / partial / mandatory_weak

View `6ddbb4bddfb8c746a81112a57efa197ee3aaa5307ce2b8586a8ddffa8d29e51b`; complete: True; reason: COMPLETE.

A/B numerical: PASS / UNKNOWN. No execution authority.

- `obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528']; insufficient []; stale [].
- `obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].
- `obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6` (`weak-method`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT']; witnesses []; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a` | observation ['source-b'] | OBSERVATION_OPPORTUNITY | [] | [] |
| `operation:4ced452516838b1b0ceba699b5af628012ab4dc1217e4505a076a033e1b24b01` | deduction ['r-estimate', '1'] | MISSING_PREMISES | ['probability-belief/v1:403ccafe1b9f28890aea43e476b33dd2dfd9cc8c85624fcab6c19f560551ad3d', 'probability-belief/v1:702fd57c670f9c6dbd962793d8779554082b37e1a1dd613aab6c5e82d7ea1769', None, 'probability-belief/v1:16161f4ce723bf755eac298e4956393a828e3c11b0776fa811b6c6fc8b99ff5e', 'probability-belief/v1:e9c71909666735e380d7ceeb86900bb50a265674d3dd80eb60c1dc457b5446ce'] | [2] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "PASS",
    "B": "UNKNOWN",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no direct observation route for this exact premise in the supported fragment",
    "node": "missing-premise:518a607649203e2c3f3f0545c5c1a0459252ef778243318b1e8db005235e49cc"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:4ced452516838b1b0ceba699b5af628012ab4dc1217e4505a076a033e1b24b01",
    "target": "premise:8acadac1c81054e742e170b876daa970144007e8049151bab2ad787a55967625",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:4ced452516838b1b0ceba699b5af628012ab4dc1217e4505a076a033e1b24b01",
    "target": "premise:aae0ecd47a1221853fc2b6be82271c16c30087e2af3778d8786f14f8d13523d2",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:4ced452516838b1b0ceba699b5af628012ab4dc1217e4505a076a033e1b24b01",
    "target": "missing-premise:518a607649203e2c3f3f0545c5c1a0459252ef778243318b1e8db005235e49cc",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:4ced452516838b1b0ceba699b5af628012ab4dc1217e4505a076a033e1b24b01",
    "target": "premise:39d440e951b5ec8aecbeb68f6a2b629cc0cd16c08a22d961234927ab34e8bc6d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:4ced452516838b1b0ceba699b5af628012ab4dc1217e4505a076a033e1b24b01",
    "target": "premise:8a2958860cad42461f2d8b3cac43121968ca1b5af14125d1d5dd96ebf8cb844f",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "target": "operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6",
    "target": "operation:4ced452516838b1b0ceba699b5af628012ab4dc1217e4505a076a033e1b24b01",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "existing-execution:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "observed-goal:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:4ced452516838b1b0ceba699b5af628012ab4dc1217e4505a076a033e1b24b01",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-registry / complete / mandatory_weak

View `eb50f27d1f46a83fd1e2c03c1abfa8a1c8937db96146c5d5d7d590b45623162c`; complete: True; reason: COMPLETE.

A/B numerical: PASS / UNKNOWN. No execution authority.

- `obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528']; insufficient []; stale [].
- `obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].
- `obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6` (`weak-method`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT']; witnesses []; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a` | observation ['source-b'] | OBSERVATION_OPPORTUNITY | [] | [] |
| `operation:fc7da500a8949a1b6b2f97cb8be7e21698596b0fd455ae68a23df0317401c88c` | deduction ['r-estimate', '1'] | INPUTS_PRESENT | ['probability-belief/v1:403ccafe1b9f28890aea43e476b33dd2dfd9cc8c85624fcab6c19f560551ad3d', 'probability-belief/v1:702fd57c670f9c6dbd962793d8779554082b37e1a1dd613aab6c5e82d7ea1769', 'probability-belief/v1:b1d85f2e26a40d06999d1c488fc464a3ec5d8a354844c12201bd1b1c1bcfa1b6', 'probability-belief/v1:16161f4ce723bf755eac298e4956393a828e3c11b0776fa811b6c6fc8b99ff5e', 'probability-belief/v1:e9c71909666735e380d7ceeb86900bb50a265674d3dd80eb60c1dc457b5446ce'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "PASS",
    "B": "UNKNOWN",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:fc7da500a8949a1b6b2f97cb8be7e21698596b0fd455ae68a23df0317401c88c",
    "target": "premise:8acadac1c81054e742e170b876daa970144007e8049151bab2ad787a55967625",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:fc7da500a8949a1b6b2f97cb8be7e21698596b0fd455ae68a23df0317401c88c",
    "target": "premise:aae0ecd47a1221853fc2b6be82271c16c30087e2af3778d8786f14f8d13523d2",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:fc7da500a8949a1b6b2f97cb8be7e21698596b0fd455ae68a23df0317401c88c",
    "target": "premise:7e398f28f6aee4ae83ae5624d3c54d5ab6bef22cab2700c2e067c6d4e9639bc5",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:fc7da500a8949a1b6b2f97cb8be7e21698596b0fd455ae68a23df0317401c88c",
    "target": "premise:39d440e951b5ec8aecbeb68f6a2b629cc0cd16c08a22d961234927ab34e8bc6d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:fc7da500a8949a1b6b2f97cb8be7e21698596b0fd455ae68a23df0317401c88c",
    "target": "premise:8a2958860cad42461f2d8b3cac43121968ca1b5af14125d1d5dd96ebf8cb844f",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "target": "operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6",
    "target": "operation:fc7da500a8949a1b6b2f97cb8be7e21698596b0fd455ae68a23df0317401c88c",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "existing-execution:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "observed-goal:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:fc7da500a8949a1b6b2f97cb8be7e21698596b0fd455ae68a23df0317401c88c",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-registry / revised / mandatory_weak

View `601e53e4173a39d3b3cbebfbbaabcf1ada63433fcb3ae6b04ef36f73ffa1248d`; complete: True; reason: COMPLETE.

A/B numerical: PASS / UNKNOWN. No execution authority.

- `obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528']; insufficient []; stale [].
- `obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].
- `obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6` (`weak-method`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a` | observation ['source-b'] | OBSERVATION_OPPORTUNITY | [] | [] |
| `operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04` | deduction ['r-estimate', '2'] | INPUTS_PRESENT | ['probability-belief/v1:403ccafe1b9f28890aea43e476b33dd2dfd9cc8c85624fcab6c19f560551ad3d', 'probability-belief/v1:702fd57c670f9c6dbd962793d8779554082b37e1a1dd613aab6c5e82d7ea1769', 'probability-belief/v1:b1d85f2e26a40d06999d1c488fc464a3ec5d8a354844c12201bd1b1c1bcfa1b6', 'probability-belief/v1:16161f4ce723bf755eac298e4956393a828e3c11b0776fa811b6c6fc8b99ff5e', 'probability-belief/v1:e9c71909666735e380d7ceeb86900bb50a265674d3dd80eb60c1dc457b5446ce'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "PASS",
    "B": "UNKNOWN",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  },
  {
    "category": "APPLICABILITY_REQUIRES_REVIEW",
    "detail": "registered relevant producer has no declared role; retained for investigation",
    "producer": {
      "available": true,
      "conclusion": {
        "positive": true,
        "statement": {
          "arguments": [
            "tested",
            "healthy"
          ],
          "predicate": "pln:implication"
        }
      },
      "identity": [
        "r-estimate",
        "2"
      ],
      "kind": "deduction",
      "record": {
        "deduction": {
          "p": "tested",
          "q": "weak",
          "r": "healthy"
        },
        "revision": "2",
        "rule_id": "r-estimate"
      },
      "requirements": [
        {
          "positive": true,
          "statement": {
            "arguments": [
              "tested"
            ],
            "predicate": "pln:proposition"
          }
        },
        {
          "positive": true,
          "statement": {
            "arguments": [
              "weak"
            ],
            "predicate": "pln:proposition"
          }
        },
        {
          "positive": true,
          "statement": {
            "arguments": [
              "healthy"
            ],
            "predicate": "pln:proposition"
          }
        },
        {
          "positive": true,
          "statement": {
            "arguments": [
              "tested",
              "weak"
            ],
            "predicate": "pln:implication"
          }
        },
        {
          "positive": true,
          "statement": {
            "arguments": [
              "weak",
              "healthy"
            ],
            "predicate": "pln:implication"
          }
        }
      ]
    }
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04",
    "target": "premise:8acadac1c81054e742e170b876daa970144007e8049151bab2ad787a55967625",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04",
    "target": "premise:aae0ecd47a1221853fc2b6be82271c16c30087e2af3778d8786f14f8d13523d2",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04",
    "target": "premise:7e398f28f6aee4ae83ae5624d3c54d5ab6bef22cab2700c2e067c6d4e9639bc5",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04",
    "target": "premise:39d440e951b5ec8aecbeb68f6a2b629cc0cd16c08a22d961234927ab34e8bc6d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04",
    "target": "premise:8a2958860cad42461f2d8b3cac43121968ca1b5af14125d1d5dd96ebf8cb844f",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "target": "operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "existing-execution:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "observed-goal:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:13b6eff9f33e631ad4759ec47ddcdcfdef84ee77aceb8603563844e7e63cfc5a",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-registry / unavailable / mandatory_weak

View `6d0a13791d7657250eb64b19a9770e871326fb00c3f0bdca0aea2f451f4cc6a9`; complete: True; reason: COMPLETE.

A/B numerical: PASS / UNKNOWN. No execution authority.

- `obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528']; insufficient []; stale [].
- `obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].
- `obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6` (`weak-method`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:899e491f6849e7f3c6114f295b714733e3b0d3be22be0af86d90aee19e517ff2` | observation ['source-b'] | UNAVAILABLE | [] | [] |
| `operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04` | deduction ['r-estimate', '2'] | INPUTS_PRESENT | ['probability-belief/v1:403ccafe1b9f28890aea43e476b33dd2dfd9cc8c85624fcab6c19f560551ad3d', 'probability-belief/v1:702fd57c670f9c6dbd962793d8779554082b37e1a1dd613aab6c5e82d7ea1769', 'probability-belief/v1:b1d85f2e26a40d06999d1c488fc464a3ec5d8a354844c12201bd1b1c1bcfa1b6', 'probability-belief/v1:16161f4ce723bf755eac298e4956393a828e3c11b0776fa811b6c6fc8b99ff5e', 'probability-belief/v1:e9c71909666735e380d7ceeb86900bb50a265674d3dd80eb60c1dc457b5446ce'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "PASS",
    "B": "UNKNOWN",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  },
  {
    "category": "APPLICABILITY_REQUIRES_REVIEW",
    "detail": "registered relevant producer has no declared role; retained for investigation",
    "producer": {
      "available": true,
      "conclusion": {
        "positive": true,
        "statement": {
          "arguments": [
            "tested",
            "healthy"
          ],
          "predicate": "pln:implication"
        }
      },
      "identity": [
        "r-estimate",
        "2"
      ],
      "kind": "deduction",
      "record": {
        "deduction": {
          "p": "tested",
          "q": "weak",
          "r": "healthy"
        },
        "revision": "2",
        "rule_id": "r-estimate"
      },
      "requirements": [
        {
          "positive": true,
          "statement": {
            "arguments": [
              "tested"
            ],
            "predicate": "pln:proposition"
          }
        },
        {
          "positive": true,
          "statement": {
            "arguments": [
              "weak"
            ],
            "predicate": "pln:proposition"
          }
        },
        {
          "positive": true,
          "statement": {
            "arguments": [
              "healthy"
            ],
            "predicate": "pln:proposition"
          }
        },
        {
          "positive": true,
          "statement": {
            "arguments": [
              "tested",
              "weak"
            ],
            "predicate": "pln:implication"
          }
        },
        {
          "positive": true,
          "statement": {
            "arguments": [
              "weak",
              "healthy"
            ],
            "predicate": "pln:implication"
          }
        }
      ]
    }
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04",
    "target": "premise:8acadac1c81054e742e170b876daa970144007e8049151bab2ad787a55967625",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04",
    "target": "premise:aae0ecd47a1221853fc2b6be82271c16c30087e2af3778d8786f14f8d13523d2",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04",
    "target": "premise:7e398f28f6aee4ae83ae5624d3c54d5ab6bef22cab2700c2e067c6d4e9639bc5",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04",
    "target": "premise:39d440e951b5ec8aecbeb68f6a2b629cc0cd16c08a22d961234927ab34e8bc6d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04",
    "target": "premise:8a2958860cad42461f2d8b3cac43121968ca1b5af14125d1d5dd96ebf8cb844f",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "target": "operation:899e491f6849e7f3c6114f295b714733e3b0d3be22be0af86d90aee19e517ff2",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "existing-execution:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:aecc023b0dafa394f9faa1efef9a2142151d74b6eaaebd1faa75f7d90c397169",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d5b8a7be8adb632481611cb8a619e06df3ee71b63e64b4d26c7d78897d154ade",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "obligation:d9cbf38a221280146e55f1c69815003ef8b1402eb6a64ca2408f9b828e167ba6",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "observed-goal:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:899e491f6849e7f3c6114f295b714733e3b0d3be22be0af86d90aee19e517ff2",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:fcd785174aa60791f97b8ab25294d0c6ee75f6287f4691537afeb4ef9b306b96",
    "target": "operation:f7541c0a207d4e21dc6d21aa146ff3b6c3c0079eda1c59b9cfddf22949e6fd04",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-registry / diagnostic-context / mandatory_weak

View `d60f96928ef3f1a9d20a35afa2a4bbccaff8c7c49ee4fe4a027945db319b2672`; complete: False; reason: TASK_SCOPE_MISMATCH.

A/B numerical: PASS / UNKNOWN. No execution authority.


| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|

Global review reasons (full objection records retained):

```json
[
  {
    "category": "SCOPE_OR_BUDGET_INCOMPLETE",
    "detail": "TASK_SCOPE_MISMATCH"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-registry / diagnostic-product / mandatory_weak

View `40120b1a5bb7a5a66b35b76611a7f4a6ae3c6c88e1a6b95d12076eb218350e48`; complete: False; reason: TASK_SCOPE_MISMATCH.

A/B numerical: PASS / UNKNOWN. No execution authority.


| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|

Global review reasons (full objection records retained):

```json
[
  {
    "category": "SCOPE_OR_BUDGET_INCOMPLETE",
    "detail": "TASK_SCOPE_MISMATCH"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-registry / diagnostic-time / mandatory_weak

View `49a84d36574add49e02a119a21adf5ca8c7a8431269c575c83d03b35f1ecaa67`; complete: False; reason: TASK_SCOPE_MISMATCH.

A/B numerical: PASS / UNKNOWN. No execution authority.


| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|

Global review reasons (full objection records retained):

```json
[
  {
    "category": "SCOPE_OR_BUDGET_INCOMPLETE",
    "detail": "TASK_SCOPE_MISMATCH"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-registry / diagnostic-partial / mandatory_weak

View `81ee596de0baf9f29ed822088d5e1b752fab7bbba0375031228fd838bee9d47a`; complete: False; reason: INCOMPLETE_INPUT.

A/B numerical: PASS / UNKNOWN. No execution authority.


| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|

Global review reasons (full objection records retained):

```json
[
  {
    "category": "SCOPE_OR_BUDGET_INCOMPLETE",
    "detail": "INCOMPLETE_INPUT"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## finite-registry / diagnostic-bound / mandatory_weak

View `dac6efc18a5d20553f96e94c533a7172f0671664b76a9e902e80b155e6565ce7`; complete: False; reason: NODE_BOUND.

A/B numerical: PASS / UNKNOWN. No execution authority.


| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|

Global review reasons (full objection records retained):

```json
[
  {
    "category": "SCOPE_OR_BUDGET_INCOMPLETE",
    "detail": "NODE_BOUND"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## native-method-gap / unregistered / primary

View `16f086f367813bd8fc432966417f1ef4ba4b92f0c7eb78be907c222ba85a1d44`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / UNKNOWN. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## native-method-gap / unregistered / shared_method

View `100a1d3088103fff19def89ffdfd58b41723037a6d210b44af662c73e70947e7`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / UNKNOWN. No execution authority.

- `obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].
- `obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1` (`method-review`, any): UNKNOWN; reasons ['MISSING_ASSESSMENT', 'NO_REGISTERED_ROUTE']; witnesses []; insufficient []; stale [].
- `obligation:dba14c8fbc14f001c1f99e60a4fda629a402f38a8935c34eab0d6cdc19d5ef10` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb"
  },
  {
    "category": "NO_REGISTERED_ROUTE",
    "detail": "no available unmaterialized declared route; repetition of existing evidence is not a repair",
    "obligation": "obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "existing-execution:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:dba14c8fbc14f001c1f99e60a4fda629a402f38a8935c34eab0d6cdc19d5ef10",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "observed-goal:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## native-method-gap / registered / primary

View `cb0f1a9816db53053a196c98bb27e728844685b8aea93de3b40494620c4f1e08`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / UNKNOWN. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT']; witnesses []; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42` | revision ['model-ab'] | INPUTS_PRESENT | ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16', 'probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "target": "premise:814bae8489f26313e58ed561c6b6ff80f10ce185ff31fbd56c97439c3b57b314",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "target": "premise:769b211778040ed09b0a6e9f487dbefb019814dd13c5101334ba7f52a466c6c3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "target": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## native-method-gap / registered / shared_method

View `2db80f73df955c92add6d91ac30c1837b2e09de1c244891690981f503f75b009`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / UNKNOWN. No execution authority.

- `obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb` (`method-assessment`, all): UNKNOWN; reasons ['MISSING_ASSESSMENT']; witnesses []; insufficient []; stale [].
- `obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1` (`method-review`, any): UNKNOWN; reasons ['MISSING_ASSESSMENT']; witnesses []; insufficient []; stale [].
- `obligation:dba14c8fbc14f001c1f99e60a4fda629a402f38a8935c34eab0d6cdc19d5ef10` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42` | revision ['model-ab'] | INPUTS_PRESENT | ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16', 'probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "target": "premise:814bae8489f26313e58ed561c6b6ff80f10ce185ff31fbd56c97439c3b57b314",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "target": "premise:769b211778040ed09b0a6e9f487dbefb019814dd13c5101334ba7f52a466c6c3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb",
    "target": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1",
    "target": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "existing-execution:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:dba14c8fbc14f001c1f99e60a4fda629a402f38a8935c34eab0d6cdc19d5ef10",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "observed-goal:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## native-method-gap / produced / primary

View `9c86491e8937071ca623677f90247527b9c664e9af6438da73e8476c38a1b8b6`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / PASS. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:c5fc4e3a6d794c12384c780df6710e40cb178f61226d4c2589c9f95d68a73acd']; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16', 'probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "UNKNOWN",
    "B": "PASS",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  },
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "target": "premise:814bae8489f26313e58ed561c6b6ff80f10ce185ff31fbd56c97439c3b57b314",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "target": "premise:769b211778040ed09b0a6e9f487dbefb019814dd13c5101334ba7f52a466c6c3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "target": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## native-method-gap / produced / shared_method

View `c3ab2157c2dc867664455014fcd180116d0c368b256e3cf91ca035f20cbfd32a`; complete: True; reason: COMPLETE.

A/B numerical: UNKNOWN / PASS. No execution authority.

- `obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:c5fc4e3a6d794c12384c780df6710e40cb178f61226d4c2589c9f95d68a73acd']; insufficient []; stale [].
- `obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1` (`method-review`, any): PASS; reasons []; witnesses ['probability-belief/v1:c5fc4e3a6d794c12384c780df6710e40cb178f61226d4c2589c9f95d68a73acd']; insufficient []; stale [].
- `obligation:dba14c8fbc14f001c1f99e60a4fda629a402f38a8935c34eab0d6cdc19d5ef10` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16', 'probability-belief/v1:ab1529b4ea4a78b1ec6fadfac5e64453134f0fdba16f6431421e768171bd8166'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "A": "UNKNOWN",
    "B": "PASS",
    "category": "POLICY_DISAGREEMENT",
    "detail": "both frozen judgments retained; no automatic policy choice"
  },
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "UNKNOWN"
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "target": "premise:814bae8489f26313e58ed561c6b6ff80f10ce185ff31fbd56c97439c3b57b314",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "target": "premise:769b211778040ed09b0a6e9f487dbefb019814dd13c5101334ba7f52a466c6c3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb",
    "target": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1",
    "target": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "existing-execution:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:530465172f9c026d90231b580896a98fb9cae2ed8796bcb20a27b876f6b242fb",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:a90e8aefc9219ea36042f9bdd9c6ae4be6c489c29fbd6702fba0e1b1f9afb8f1",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "obligation:dba14c8fbc14f001c1f99e60a4fda629a402f38a8935c34eab0d6cdc19d5ef10",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "observed-goal:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:f666964a3377d97947484c7000c835bde5e553a81126f2c41fffa5a6ec9d01e5",
    "target": "operation:3063c8e801570256559edfda7356c0f35354e25eb30ab8cdc749661c9f656c42",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## native-objection / before / primary

View `27792e327cc0faa793d2d3a59a29fa97f8b0b2c63e929b87ef75d736570beb43`; complete: True; reason: COMPLETE.

A/B numerical: PASS / PASS. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:0a68e6a46720eac334b773acff4efc4e3f8c797fc2e2be2d70a35417900eb629']; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient []; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16'] | [] |
| `operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d` | deduction ['r-objection', '1'] | INPUTS_PRESENT | ['probability-belief/v1:05fe175ecb60aeb2594fde721ed92e64db2c95dd2da9b3d2e54c8c0bfcbc2eb8', 'probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd', 'probability-belief/v1:a22bcf10cbbeaa58c347fd35ff66d48dd0923f1e40dde934e881536d462c3877', 'probability-belief/v1:098c075e073a8ca7ab99453124e3760e8e8c00c46aa81afd544250f8ce9d5f87', 'probability-belief/v1:3c4ee7106a7acfd6db489593853c930054a5e54d8f4bbaaa10fdbdb4c60a6b4c'] | [] |

Global review reasons (full objection records retained):

```json
[]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562",
    "target": "premise:cc4c6200cb8ba62064cca79740cb0f5bae135853c482ea8f16f016b25550e21f",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 0,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:555fb17c7df39053ac9ba44d02b2842bec0d3a17f8892fecd34c2e67201a26e1",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562",
    "target": "premise:13e9827abe63099fdbae314f9bd82a700e7792ea35cbe78d216d5977bbc0c784",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:57eca1975593d8719a9c4bd8eb3721ddd44ed2ed634780e4e062707c0e059dfe",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:8b6dc506675acb91c4426678ba1595e1ae65c5bf8f7fa319177d9704603bbb72",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:1cd57a476655fab07da920b54cf0153dd4ce4fcc42c6dd6edfab07ee012db41d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:4151ea19ae246c821dbf6d17b68829991c3fcc9affc32e35cdb90a6cdedae0d3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "target": "operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "target": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## native-objection / derived / primary

View `08c2e7149df822ec1c4c605c32df93551eb64ca175060cc70320c4ee58d3f91c`; complete: True; reason: COMPLETE.

A/B numerical: FAIL / FAIL. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:0a68e6a46720eac334b773acff4efc4e3f8c797fc2e2be2d70a35417900eb629']; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:86183a521b86bde0e88b6a44e5d2d1513e4e8e396552d5cf8ddac85f269ad2e7']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16'] | [] |
| `operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d` | deduction ['r-objection', '1'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:05fe175ecb60aeb2594fde721ed92e64db2c95dd2da9b3d2e54c8c0bfcbc2eb8', 'probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd', 'probability-belief/v1:a22bcf10cbbeaa58c347fd35ff66d48dd0923f1e40dde934e881536d462c3877', 'probability-belief/v1:098c075e073a8ca7ab99453124e3760e8e8c00c46aa81afd544250f8ce9d5f87', 'probability-belief/v1:3c4ee7106a7acfd6db489593853c930054a5e54d8f4bbaaa10fdbdb4c60a6b4c'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "FAIL"
  },
  {
    "category": "OBJECTION_REQUIRES_REVIEW",
    "detail": "strength_objection",
    "record": {
      "adequate": false,
      "applicability": [
        {
          "class_id": "a",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": false
        },
        {
          "class_id": "b",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": false
        },
        {
          "class_id": "derived",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "objection",
          "eligible": true,
          "identity_match": true,
          "lineage_requirement": true
        },
        {
          "class_id": "revision",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        }
      ],
      "belief": {
        "accepted_at_revision": 31,
        "belief_revision_id": "probability-belief/v1:86183a521b86bde0e88b6a44e5d2d1513e4e8e396552d5cf8ddac85f269ad2e7",
        "context_id": "ctx",
        "hard_policy_revision": "finite-hard-policy/v1",
        "interpretation": "scoped-estimate-alternatives/v1",
        "post_certificate_id": "probability-certificate/v1:d3a5308b518e4e33daff505e831b93b5695716a79c8fba7e4e751e9c2a13f4a9",
        "pre_certificate_id": "probability-certificate/v1:668b4c53128444817f1f3090446218f23db6622127a8cf058b44b340e17ba5a6",
        "probability_policy_revision": "semantic-input/v1",
        "proposal": {
          "assumptions": [
            "upstream-heuristic-deduction",
            "upstream-q>0.9999-uses-r"
          ],
          "context_id": "ctx",
          "formula_id": "trueagi-pln/4405956947c4b53c7ff01bd565aa3b114bc970a1/Truth_Deduction",
          "knowledge_revision": 30,
          "premise_ids": [
            "probability-observation/v1:e7189df51e613fa28e2db3909886f4773fe92f2f9175f3b65c6207d7fe5f8e10",
            "probability-observation/v1:ef592ca4a3d08e906b0721418cbaac1ff7abd4320b9971339712da7d269dcf08",
            "probability-observation/v1:0449a41ff7e8ed2760f950479f3a6a39618390715aefd0adae9e129bef5332b6",
            "probability-observation/v1:98c16e49e5ee31ee6877d8dbf5066f2ba4b850ad251865bcb5217d92a26fa5a1",
            "probability-observation/v1:6528d474b864a55e58da71f3cbaf15e9fa9009c15b8a5948409506efb0f1f63c"
          ],
          "proposal_id": "pln-proposal/v1:7de8bb875f6b55d570484ebb117913e9acb262ad897eb37a536892790a73ebe5",
          "support": {
            "ancestors": [
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "tested",
                    "weak"
                  ],
                  "predicate": "pln:implication"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "weak",
                    "healthy"
                  ],
                  "predicate": "pln:implication"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "healthy"
                  ],
                  "predicate": "pln:proposition"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "tested"
                  ],
                  "predicate": "pln:proposition"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "weak"
                  ],
                  "predicate": "pln:proposition"
                }
              }
            ],
            "conclusion": {
              "positive": true,
              "statement": {
                "arguments": [
                  "tested",
                  "healthy"
                ],
                "predicate": "pln:implication"
              }
            },
            "context_id": "ctx",
            "evidence_ids": [
              "input-0",
              "input-1",
              "input-2",
              "input-3",
              "input-4"
            ],
            "lineage_roots": [
              "root:input-0",
              "root:input-1",
              "root:input-2",
              "root:input-3",
              "root:input-4"
            ],
            "support_id": "pln-support/v1:6a9cdf673e96c13731f0f586522b0b4367de3651ccec50cf2e5a0f5a7b22226f",
            "truth": {
              "confidence": 0.0002000000000000001,
              "strength": 0.1,
              "truth_model": "trueagi-pln-stv-finite-k1/v1"
            }
          }
        },
        "transition": {
          "context_id": "ctx",
          "evidence_id": null,
          "independence_id": null,
          "kind": "deduction",
          "premise_revision_ids": [
            "probability-belief/v1:05fe175ecb60aeb2594fde721ed92e64db2c95dd2da9b3d2e54c8c0bfcbc2eb8",
            "probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd",
            "probability-belief/v1:a22bcf10cbbeaa58c347fd35ff66d48dd0923f1e40dde934e881536d462c3877",
            "probability-belief/v1:098c075e073a8ca7ab99453124e3760e8e8c00c46aa81afd544250f8ce9d5f87",
            "probability-belief/v1:3c4ee7106a7acfd6db489593853c930054a5e54d8f4bbaaa10fdbdb4c60a6b4c"
          ],
          "rule_id": "r-objection",
          "rule_revision": "1",
          "transition_id": "probability-transition/v1:bca14cde2e5ed809ffc5c9a9dc1c87b680c376eb67b9aae00ba89f6f0fcb48f0"
        }
      },
      "current": true,
      "disposition": "strength_objection",
      "eligible_classes": [
        "objection"
      ],
      "id": "probability-belief/v1:86183a521b86bde0e88b6a44e5d2d1513e4e8e396552d5cf8ddac85f269ad2e7",
      "orientation": "same",
      "provenance_valid": true
    }
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562",
    "target": "premise:cc4c6200cb8ba62064cca79740cb0f5bae135853c482ea8f16f016b25550e21f",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 0,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:555fb17c7df39053ac9ba44d02b2842bec0d3a17f8892fecd34c2e67201a26e1",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562",
    "target": "premise:13e9827abe63099fdbae314f9bd82a700e7792ea35cbe78d216d5977bbc0c784",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:57eca1975593d8719a9c4bd8eb3721ddd44ed2ed634780e4e062707c0e059dfe",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:8b6dc506675acb91c4426678ba1595e1ae65c5bf8f7fa319177d9704603bbb72",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:1cd57a476655fab07da920b54cf0153dd4ce4fcc42c6dd6edfab07ee012db41d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:4151ea19ae246c821dbf6d17b68829991c3fcc9affc32e35cdb90a6cdedae0d3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "target": "operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "target": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.

## native-objection / opposite / primary

View `026e5ee6cb86df58c24f3e2f8118d5ad259da744a57dfe8d81c45d6d42a8e3dd`; complete: True; reason: COMPLETE.

A/B numerical: FAIL / FAIL. No execution authority.

- `obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a` (`method-assessment`, all): PASS; reasons []; witnesses ['probability-belief/v1:0a68e6a46720eac334b773acff4efc4e3f8c797fc2e2be2d70a35417900eb629']; insufficient []; stale [].
- `obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829` (`forecast`, any): PASS; reasons []; witnesses ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16']; insufficient ['probability-belief/v1:86183a521b86bde0e88b6a44e5d2d1513e4e8e396552d5cf8ddac85f269ad2e7']; stale [].

| Exact operation node | Producer identity | Readiness | Exact ordered premises | Missing slots |
|---|---|---|---|---|
| `operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562` | revision ['model-ab'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528', 'probability-belief/v1:812eb36974e0fcac88a84dc40a71e369989a28790111cc56ec54c8cc91115f16'] | [] |
| `operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d` | deduction ['r-objection', '1'] | RESULT_ALREADY_RECORDED | ['probability-belief/v1:05fe175ecb60aeb2594fde721ed92e64db2c95dd2da9b3d2e54c8c0bfcbc2eb8', 'probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd', 'probability-belief/v1:a22bcf10cbbeaa58c347fd35ff66d48dd0923f1e40dde934e881536d462c3877', 'probability-belief/v1:098c075e073a8ca7ab99453124e3760e8e8c00c46aa81afd544250f8ce9d5f87', 'probability-belief/v1:3c4ee7106a7acfd6db489593853c930054a5e54d8f4bbaaa10fdbdb4c60a6b4c'] | [] |

Global review reasons (full objection records retained):

```json
[
  {
    "category": "LIVE_POLICY_BLOCK",
    "detail": "shadow interpretation cannot repair or replace live all-current policy",
    "status": "FAIL"
  },
  {
    "category": "OBJECTION_REQUIRES_REVIEW",
    "detail": "opposite_objection",
    "record": {
      "adequate": false,
      "applicability": [
        {
          "class_id": "a",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": false
        },
        {
          "class_id": "b",
          "eligible": true,
          "identity_match": true,
          "lineage_requirement": true
        },
        {
          "class_id": "derived",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "objection",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "revision",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        }
      ],
      "belief": {
        "accepted_at_revision": 34,
        "belief_revision_id": "probability-belief/v1:bc799fba85bfd42fdfb336be63649cf2126554f0801c8ac0edb9482b6f38c5c9",
        "context_id": "ctx",
        "hard_policy_revision": "finite-hard-policy/v1",
        "interpretation": "scoped-estimate-alternatives/v1",
        "post_certificate_id": "probability-certificate/v1:f685d88ed932766475f9e21f75bebb9b45e832e02cd7dfeb129c01a92e4bc433",
        "pre_certificate_id": "probability-certificate/v1:fb403da1c78db2977668c387c723751a2081c8d83a88cb837f03b7199d098504",
        "probability_policy_revision": "semantic-input/v1",
        "proposal": {
          "assumptions": [
            "trusted-source-finite-estimate"
          ],
          "context_id": "ctx",
          "formula_id": "probability-observation/v1",
          "knowledge_revision": 33,
          "premise_ids": [],
          "proposal_id": "probability-proposal/v1:f8b708221c23a25f42e583cc62a48e031bb1cd06ee4f2ab555852cf4a8833246",
          "support": {
            "ancestors": [],
            "conclusion": {
              "positive": false,
              "statement": {
                "arguments": [
                  "tested",
                  "healthy"
                ],
                "predicate": "pln:implication"
              }
            },
            "context_id": "ctx",
            "evidence_ids": [
              "opposite"
            ],
            "lineage_roots": [
              "root:b"
            ],
            "support_id": "probability-observation/v1:60f9a45b7a77f33704fef2bc7bcf44be48b0aaca6f3ed9a9670b968ce4a0408e",
            "truth": {
              "confidence": 0.05,
              "strength": 0.7,
              "truth_model": "trueagi-pln-stv-finite-k1/v1"
            }
          }
        },
        "transition": {
          "context_id": "ctx",
          "evidence_id": "opposite",
          "independence_id": null,
          "kind": "observation",
          "premise_revision_ids": [],
          "rule_id": null,
          "rule_revision": null,
          "transition_id": "probability-transition/v1:317845e1fc5d6dfa01a236aba80b7d1ee25855438de8ccac281ba589d1df4519"
        }
      },
      "current": true,
      "disposition": "opposite_objection",
      "eligible_classes": [
        "b"
      ],
      "id": "probability-belief/v1:bc799fba85bfd42fdfb336be63649cf2126554f0801c8ac0edb9482b6f38c5c9",
      "orientation": "opposite",
      "provenance_valid": true
    }
  },
  {
    "category": "OBJECTION_REQUIRES_REVIEW",
    "detail": "strength_objection",
    "record": {
      "adequate": false,
      "applicability": [
        {
          "class_id": "a",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": false
        },
        {
          "class_id": "b",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": false
        },
        {
          "class_id": "derived",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        },
        {
          "class_id": "objection",
          "eligible": true,
          "identity_match": true,
          "lineage_requirement": true
        },
        {
          "class_id": "revision",
          "eligible": false,
          "identity_match": false,
          "lineage_requirement": true
        }
      ],
      "belief": {
        "accepted_at_revision": 31,
        "belief_revision_id": "probability-belief/v1:86183a521b86bde0e88b6a44e5d2d1513e4e8e396552d5cf8ddac85f269ad2e7",
        "context_id": "ctx",
        "hard_policy_revision": "finite-hard-policy/v1",
        "interpretation": "scoped-estimate-alternatives/v1",
        "post_certificate_id": "probability-certificate/v1:d3a5308b518e4e33daff505e831b93b5695716a79c8fba7e4e751e9c2a13f4a9",
        "pre_certificate_id": "probability-certificate/v1:668b4c53128444817f1f3090446218f23db6622127a8cf058b44b340e17ba5a6",
        "probability_policy_revision": "semantic-input/v1",
        "proposal": {
          "assumptions": [
            "upstream-heuristic-deduction",
            "upstream-q>0.9999-uses-r"
          ],
          "context_id": "ctx",
          "formula_id": "trueagi-pln/4405956947c4b53c7ff01bd565aa3b114bc970a1/Truth_Deduction",
          "knowledge_revision": 30,
          "premise_ids": [
            "probability-observation/v1:e7189df51e613fa28e2db3909886f4773fe92f2f9175f3b65c6207d7fe5f8e10",
            "probability-observation/v1:ef592ca4a3d08e906b0721418cbaac1ff7abd4320b9971339712da7d269dcf08",
            "probability-observation/v1:0449a41ff7e8ed2760f950479f3a6a39618390715aefd0adae9e129bef5332b6",
            "probability-observation/v1:98c16e49e5ee31ee6877d8dbf5066f2ba4b850ad251865bcb5217d92a26fa5a1",
            "probability-observation/v1:6528d474b864a55e58da71f3cbaf15e9fa9009c15b8a5948409506efb0f1f63c"
          ],
          "proposal_id": "pln-proposal/v1:7de8bb875f6b55d570484ebb117913e9acb262ad897eb37a536892790a73ebe5",
          "support": {
            "ancestors": [
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "tested",
                    "weak"
                  ],
                  "predicate": "pln:implication"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "weak",
                    "healthy"
                  ],
                  "predicate": "pln:implication"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "healthy"
                  ],
                  "predicate": "pln:proposition"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "tested"
                  ],
                  "predicate": "pln:proposition"
                }
              },
              {
                "positive": true,
                "statement": {
                  "arguments": [
                    "weak"
                  ],
                  "predicate": "pln:proposition"
                }
              }
            ],
            "conclusion": {
              "positive": true,
              "statement": {
                "arguments": [
                  "tested",
                  "healthy"
                ],
                "predicate": "pln:implication"
              }
            },
            "context_id": "ctx",
            "evidence_ids": [
              "input-0",
              "input-1",
              "input-2",
              "input-3",
              "input-4"
            ],
            "lineage_roots": [
              "root:input-0",
              "root:input-1",
              "root:input-2",
              "root:input-3",
              "root:input-4"
            ],
            "support_id": "pln-support/v1:6a9cdf673e96c13731f0f586522b0b4367de3651ccec50cf2e5a0f5a7b22226f",
            "truth": {
              "confidence": 0.0002000000000000001,
              "strength": 0.1,
              "truth_model": "trueagi-pln-stv-finite-k1/v1"
            }
          }
        },
        "transition": {
          "context_id": "ctx",
          "evidence_id": null,
          "independence_id": null,
          "kind": "deduction",
          "premise_revision_ids": [
            "probability-belief/v1:05fe175ecb60aeb2594fde721ed92e64db2c95dd2da9b3d2e54c8c0bfcbc2eb8",
            "probability-belief/v1:20f477cdc28d6cf7b29b680794593a95021f9cb31a9afde78d3fabf5072a1ffd",
            "probability-belief/v1:a22bcf10cbbeaa58c347fd35ff66d48dd0923f1e40dde934e881536d462c3877",
            "probability-belief/v1:098c075e073a8ca7ab99453124e3760e8e8c00c46aa81afd544250f8ce9d5f87",
            "probability-belief/v1:3c4ee7106a7acfd6db489593853c930054a5e54d8f4bbaaa10fdbdb4c60a6b4c"
          ],
          "rule_id": "r-objection",
          "rule_revision": "1",
          "transition_id": "probability-transition/v1:bca14cde2e5ed809ffc5c9a9dc1c87b680c376eb67b9aae00ba89f6f0fcb48f0"
        }
      },
      "current": true,
      "disposition": "strength_objection",
      "eligible_classes": [
        "objection"
      ],
      "id": "probability-belief/v1:86183a521b86bde0e88b6a44e5d2d1513e4e8e396552d5cf8ddac85f269ad2e7",
      "orientation": "same",
      "provenance_valid": true
    }
  }
]
```

Typed dependency edges (the full JSON also contains every premise node and its belief record):

```json
[
  {
    "slot": 0,
    "source": "operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562",
    "target": "premise:cc4c6200cb8ba62064cca79740cb0f5bae135853c482ea8f16f016b25550e21f",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 0,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:555fb17c7df39053ac9ba44d02b2842bec0d3a17f8892fecd34c2e67201a26e1",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562",
    "target": "premise:13e9827abe63099fdbae314f9bd82a700e7792ea35cbe78d216d5977bbc0c784",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 1,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:57eca1975593d8719a9c4bd8eb3721ddd44ed2ed634780e4e062707c0e059dfe",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 2,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:8b6dc506675acb91c4426678ba1595e1ae65c5bf8f7fa319177d9704603bbb72",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 3,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:1cd57a476655fab07da920b54cf0153dd4ce4fcc42c6dd6edfab07ee012db41d",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": 4,
    "source": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "target": "premise:4151ea19ae246c821dbf6d17b68829991c3fcc9affc32e35cdb90a6cdedae0d3",
    "type": "AND_PREREQUISITE"
  },
  {
    "slot": null,
    "source": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "target": "operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "target": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "type": "OR_POSSIBLE_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "existing-execution:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "EXISTING_AUTHORITY_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:0d1614ab592e52b8bffbf519d4f223f2f4079c1393e956bcd253ca645aca2a2a",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "obligation:863f9840d7ab3dbc46a96ab81674c66de800b2059d7518fc224fb3f32d185829",
    "type": "AND_OBLIGATION"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "observed-goal:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "type": "OBSERVED_OUTCOME_REQUIREMENT"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:8f7ec3b0a4d81ed9a1e8d85aedf433b73db0e54f257cc76087358ade3bc28562",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  },
  {
    "slot": null,
    "source": "task:862790c54e5d59a65ab33d1b63bdaa9c2a666a8c53d0d8ba1d736258e13b4340",
    "target": "operation:c3c515f0494efec0fa51ec9df92414aef2b073ca86c0f6a9b2d24864036e217d",
    "type": "INVESTIGATE_REGISTERED_PRODUCER"
  }
]
```

Observed goal loss 10; lifecycle stage DRAFT. These are actual read-only projections.
