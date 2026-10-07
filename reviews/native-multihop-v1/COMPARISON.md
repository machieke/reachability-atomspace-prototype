# Native multi-hop retrieval comparison

Measured source: `068770ea5f7970bfaf65aabfdae3fcfe3d983226`. Six parents, two retrieval arms and two formula modes. Timing is descriptive.

| Structure | Retrieval | Formula | Depth | Calls | Completion | J world / certified | Wall seconds |
|---|---|---|---:|---:|---|---|---:|
| two-hop | MH-scan | finite | 2 | 2 | 3 | 30 / 30 | 6.476 |
| three-hop | MH-scan | finite | 3 | 3 | 3 | 30 / 30 | 7.43 |
| shared | MH-scan | finite | 3 | 4 | 3 | 30 / 30 | 8.534 |
| unavailable | MH-scan | finite | 0 | 0 | None | 90 / 90 | 1.192 |
| replacement | MH-scan | finite | 2 | 3 | 3 | 30 / 30 | 6.857 |
| adverse | MH-scan | finite | 2 | 3 | None | 90 / 90 | 2.49 |
| two-hop | MH-scan | native | 2 | 2 | 3 | 30 / 30 | 7.55 |
| three-hop | MH-scan | native | 3 | 3 | 3 | 30 / 30 | 8.813 |
| shared | MH-scan | native | 3 | 4 | 3 | 30 / 30 | 9.536 |
| unavailable | MH-scan | native | 0 | 0 | None | 90 / 90 | 1.587 |
| replacement | MH-scan | native | 2 | 3 | 3 | 30 / 30 | 8.047 |
| adverse | MH-scan | native | 2 | 3 | None | 90 / 90 | 3.403 |
| two-hop | MH-native | finite | 2 | 2 | 3 | 30 / 30 | 15.448 |
| three-hop | MH-native | finite | 3 | 3 | 3 | 30 / 30 | 16.875 |
| shared | MH-native | finite | 3 | 4 | 3 | 30 / 30 | 17.866 |
| unavailable | MH-native | finite | 0 | 0 | None | 90 / 90 | 4.207 |
| replacement | MH-native | finite | 2 | 3 | 3 | 30 / 30 | 15.956 |
| adverse | MH-native | finite | 2 | 3 | None | 90 / 90 | 7.037 |
| two-hop | MH-native | native | 2 | 2 | 3 | 30 / 30 | 16.419 |
| three-hop | MH-native | native | 3 | 3 | 3 | 30 / 30 | 17.969 |
| shared | MH-native | native | 3 | 4 | 3 | 30 / 30 | 19.023 |
| unavailable | MH-native | native | 0 | 0 | None | 90 / 90 | 4.761 |
| replacement | MH-native | native | 2 | 3 | 3 | 30 / 30 | 17.261 |
| adverse | MH-native | native | 2 | 3 | None | 90 / 90 | 8.165 |
