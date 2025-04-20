# BMCFuzz: Hybrid Verification of Processors by Synergistic Integration of Bound Model Checking and Fuzzing

## Abstract
Modern processors are becoming increasingly complex, making them hard to be bug-free. Bounded model checking (BMC) and coverage-guided fuzzing (CGF) are two main complementary techniques for verifying processor designs. BMC can exhaustively explore the state-space up to a given bound, but suffers from the severe state-space explosion problem, thus limited to a smaller bound for realistic processor designs. CGF is efficient and scalable for verifying large-scale complex designs, but struggles with the coverage due to the difficult in generating comprehensive and diverse seeds. To bring the best of both worlds, we propose BMCFuzz, a novel two-way hybrid verification approach that synergistically integrates BMC and fuzzing.

Specifically, BMCFuzz alternatively switches BMC and fuzzing according to their performance in improving coverage, where fuzzing is leveraged to quickly explore the state space, detect flaws, and moreover record snapshots that are crucial valuations of all the circuit-level registers, while BMC with selected valuable snapshots as initial states is utilized to exhaustively explore uncovered points. Moreover, the witnesses of BMC are further used to generate seeds for fuzzing. This synergistic integration of BMC-CGF process helps BMC alleviate the state-space explosion problem and feeds fuzzing with more comprehensive and diverse seeds.

We implement BMCFuzz in a fully open-source tool and evaluate in on three widely-used open-source RISC-V processor designs (i.e., NutShell, Rocket, and BOOM). Experimental results show that BMCFuzz achieves higher coverage compared to the state-of-the-art methods and discover 3 previously unknown vulnerabilities, demonstrating the potential of BMCFuzz as a powerful, open-source tool for advancing processor design and verification.


## DUTs

* [NutShell](https://github.com/OSCPU/NutShell)
* [Rocket](https://github.com/chipsalliance/rocket-chip)
* [BOOM](https://github.com/riscv-boom/riscv-boom)
