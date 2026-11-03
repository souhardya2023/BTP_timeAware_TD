# Do the real-data patterns appear in the synthetic histories?
150 projects, 1321 instances, 11927 instance-releases, 1806 interest events (15.1% of instance-releases)

regime                               ar_clock  baseline  contagion     decay    sticky        ALL
projects                               15.000    90.000     15.000    15.000    15.000    150.000
inst-releases                        1037.000  7577.000    838.000  1309.000  1166.000  11927.000
events                                166.000   927.000    175.000    83.000   455.000   1806.000
event rate                              0.160     0.122      0.209     0.063     0.390      0.151
gini                                    0.749     0.779      0.775     0.911     0.570      0.773
top10% share                            0.522     0.572      0.564     0.841     0.403      0.572
never pay                               0.583     0.557      0.559     0.781     0.163      0.544
P(ev|ev,lag1)                           0.476     0.326      0.532     0.640     0.577      0.435
P(ev|ev,lag3)                           0.387     0.336      0.521     0.554     0.493      0.405
P(ev|ev,lag5)                           0.509     0.287      0.532     0.511     0.507      0.389
P(ev | last event 1 releases ago)       0.476     0.326      0.532     0.640     0.577      0.435
P(ev | last event 2 releases ago)       0.390     0.257      0.412     0.273     0.438      0.312
P(ev | last event 3-4 releases ago)     0.268     0.250      0.257     0.143     0.317      0.257
P(ev | last event 5+ releases ago)      0.438     0.195      0.312     0.013     0.243      0.186
P(ev|none,lag1)                         0.102     0.089      0.110     0.028     0.261      0.096
neighbour ratio                         1.401     0.791      1.806     3.329     0.715      1.260
enrichment                              0.415     0.290      0.602     0.131     0.746      0.345
debt share of code                      0.071     0.112      0.138     0.140     0.140      0.115
debt share of edits                     0.029     0.032      0.083     0.018     0.105      0.040
groups                                 31.000   174.000     32.000    31.000    46.000    314.000
cap20 persistence                       0.526     0.576      0.644     0.639     0.488      0.588
cap20 oracle long-run                   0.621     0.635      0.768     0.735     0.502      0.631
cap20 random                            0.280     0.263      0.309     0.207     0.205      0.250
clock autocorr                          0.209    -0.002      0.151     0.610     0.216      0.104
activity autocorr (generator clock)     0.439    -0.172     -0.222    -0.157    -0.046     -0.102
top20% releases share of interest       0.486     0.628      0.435     0.742     0.435      0.584
ICC instance                            0.285     0.241      0.454     0.371     0.237      0.309
ICC release                             0.036     0.122      0.114     0.071     0.195      0.174

Reading guide (real data of the 9 projects: event rate 7.8 %, Gini 0.83, never-pay 46 %, P(ev|ev) 0.2-0.25 at every lag against 0.07, neighbour ratio 1.1,
enrichment 0.39, persistence 39 % = oracle long-run 38 % at the top 20 %, clock autocorrelation -0.01, ICC release 0.28 against instance 0.13).