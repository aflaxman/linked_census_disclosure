# Simulation study of disclosure risk in demonstration DHC data from
Updated August 2022

Plan of Work:

For each block, reconstruct age/sex/race structure for people under age 18:

1. In SF1 (call this ReMF)

2. In DHC (I don't have a catchy name for this yet)

Simulate linking ReMF with a corresponding block in 2020 under 4 scenarios:

1. No privacy --- link on PIK (unique person identification key)
2. No DAS --- link on age, race, block
3. Swapping only --- link on age, race, block
4. Swapping in 2010, TDA in 2020 --- link on age, race, block

Hypothesis:

1 will have a lot of links, 2 will have many less but still a lot, 3
will have 5-10% less than 2, and 4 will have none.

