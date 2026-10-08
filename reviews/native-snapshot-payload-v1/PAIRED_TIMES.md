# Paired wall times

Two serial sweeps of six fixed parent tasks; local descriptive reproducibility only. Negative differences favor compact; zero is neutral; positive differences favor comparator.

| Sweep | Mode | Parent | Scan s | Full s | Compact s | Compact minus full s | Compact minus scan s |
|---|---|---|---:|---:|---:|---:|---:|
| 0 | finite | two-hop | 6.386024 | 10.848118 | 11.787728 | 0.939610 | 5.401705 |
| 0 | finite | three-hop | 7.757688 | 12.287382 | 12.496764 | 0.209382 | 4.739076 |
| 0 | finite | shared | 8.607409 | 13.239674 | 13.480984 | 0.241309 | 4.873574 |
| 0 | finite | unavailable | 1.277083 | 2.718648 | 2.744793 | 0.026145 | 1.467710 |
| 0 | finite | replacement | 7.322398 | 11.393364 | 11.420181 | 0.026817 | 4.097783 |
| 0 | finite | adverse | 2.517144 | 5.019660 | 4.825272 | -0.194388 | 2.308128 |
| 0 | native | two-hop | 7.840758 | 11.879571 | 11.876379 | -0.003191 | 4.035621 |
| 0 | native | three-hop | 8.736051 | 15.822669 | 16.825381 | 1.002713 | 8.089330 |
| 0 | native | shared | 11.784675 | 16.699757 | 14.815897 | -1.883860 | 3.031222 |
| 0 | native | unavailable | 1.776850 | 3.112171 | 3.343273 | 0.231101 | 1.566423 |
| 0 | native | replacement | 8.614654 | 12.708971 | 12.506268 | -0.202703 | 3.891614 |
| 0 | native | adverse | 3.499793 | 6.108440 | 6.011141 | -0.097299 | 2.511348 |
| 1 | finite | two-hop | 6.731736 | 10.936838 | 10.762407 | -0.174431 | 4.030671 |
| 1 | finite | three-hop | 7.856983 | 12.747753 | 12.450638 | -0.297115 | 4.593655 |
| 1 | finite | shared | 8.525303 | 13.403416 | 13.677317 | 0.273900 | 5.152014 |
| 1 | finite | unavailable | 1.287393 | 2.847411 | 2.691039 | -0.156371 | 1.403646 |
| 1 | finite | replacement | 7.085803 | 11.266084 | 11.758217 | 0.492133 | 4.672414 |
| 1 | finite | adverse | 2.704568 | 5.067144 | 5.343583 | 0.276439 | 2.639015 |
| 1 | native | two-hop | 7.512316 | 12.387705 | 12.020440 | -0.367265 | 4.508124 |
| 1 | native | three-hop | 8.787292 | 13.531241 | 13.711365 | 0.180124 | 4.924073 |
| 1 | native | shared | 9.781132 | 14.661536 | 14.828359 | 0.166823 | 5.047226 |
| 1 | native | unavailable | 1.808670 | 3.374785 | 3.205823 | -0.168962 | 1.397153 |
| 1 | native | replacement | 7.950400 | 12.770689 | 12.598613 | -0.172076 | 4.648214 |
| 1 | native | adverse | 3.687472 | 6.187115 | 6.092393 | -0.094723 | 2.404921 |

## Variability between sweeps

| Arm | Mode | Parent | Sweep 0 s | Sweep 1 s | Range s |
|---|---|---|---:|---:|---:|
| MH-scan | finite | two-hop | 6.386024 | 6.731736 | 0.345712 |
| MH-scan | finite | three-hop | 7.757688 | 7.856983 | 0.099295 |
| MH-scan | finite | shared | 8.607409 | 8.525303 | 0.082106 |
| MH-scan | finite | unavailable | 1.277083 | 1.287393 | 0.010311 |
| MH-scan | finite | replacement | 7.322398 | 7.085803 | 0.236595 |
| MH-scan | finite | adverse | 2.517144 | 2.704568 | 0.187424 |
| MH-scan | native | two-hop | 7.840758 | 7.512316 | 0.328443 |
| MH-scan | native | three-hop | 8.736051 | 8.787292 | 0.051241 |
| MH-scan | native | shared | 11.784675 | 9.781132 | 2.003543 |
| MH-scan | native | unavailable | 1.776850 | 1.808670 | 0.031821 |
| MH-scan | native | replacement | 8.614654 | 7.950400 | 0.664254 |
| MH-scan | native | adverse | 3.499793 | 3.687472 | 0.187679 |
| MH-native-session-full | finite | two-hop | 10.848118 | 10.936838 | 0.088719 |
| MH-native-session-full | finite | three-hop | 12.287382 | 12.747753 | 0.460371 |
| MH-native-session-full | finite | shared | 13.239674 | 13.403416 | 0.163742 |
| MH-native-session-full | finite | unavailable | 2.718648 | 2.847411 | 0.128762 |
| MH-native-session-full | finite | replacement | 11.393364 | 11.266084 | 0.127280 |
| MH-native-session-full | finite | adverse | 5.019660 | 5.067144 | 0.047484 |
| MH-native-session-full | native | two-hop | 11.879571 | 12.387705 | 0.508134 |
| MH-native-session-full | native | three-hop | 15.822669 | 13.531241 | 2.291428 |
| MH-native-session-full | native | shared | 16.699757 | 14.661536 | 2.038221 |
| MH-native-session-full | native | unavailable | 3.112171 | 3.374785 | 0.262614 |
| MH-native-session-full | native | replacement | 12.708971 | 12.770689 | 0.061719 |
| MH-native-session-full | native | adverse | 6.108440 | 6.187115 | 0.078676 |
| MH-native-session-compact | finite | two-hop | 11.787728 | 10.762407 | 1.025322 |
| MH-native-session-compact | finite | three-hop | 12.496764 | 12.450638 | 0.046127 |
| MH-native-session-compact | finite | shared | 13.480984 | 13.677317 | 0.196333 |
| MH-native-session-compact | finite | unavailable | 2.744793 | 2.691039 | 0.053754 |
| MH-native-session-compact | finite | replacement | 11.420181 | 11.758217 | 0.338036 |
| MH-native-session-compact | finite | adverse | 4.825272 | 5.343583 | 0.518311 |
| MH-native-session-compact | native | two-hop | 11.876379 | 12.020440 | 0.144060 |
| MH-native-session-compact | native | three-hop | 16.825381 | 13.711365 | 3.114017 |
| MH-native-session-compact | native | shared | 14.815897 | 14.828359 | 0.012461 |
| MH-native-session-compact | native | unavailable | 3.343273 | 3.205823 | 0.137450 |
| MH-native-session-compact | native | replacement | 12.506268 | 12.598613 | 0.092346 |
| MH-native-session-compact | native | adverse | 6.011141 | 6.092393 | 0.081252 |
