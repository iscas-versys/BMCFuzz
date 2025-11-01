# BMCFuzz: Hybrid Verification of Processors by Synergistic Integration of Bound Model Checking and Fuzzing

## Abstract
Modern processors are becoming increasingly complex, making them hard to be bug-free. Bounded model checking (BMC) and coverage-guided fuzzing (CGF) are two main complementary techniques for verifying processor designs. BMC can exhaustively explore the state-space up to a given bound, but suffers from the severe state-space explosion problem, thus limited to a smaller bound for realistic processor designs. CGF is efficient and scalable for verifying large-scale complex designs, but struggles with the coverage due to the difficult in generating comprehensive and diverse seeds. To bring the best of both worlds, we propose BMCFuzz, a novel two-way hybrid verification approach that synergistically integrates BMC and fuzzing.

We implement BMCFuzz in a fully open-source tool and evaluate in on three widely-used open-source RISC-V processor designs (i.e., NutShell, Rocket, and BOOM). Experimental results show that BMCFuzz achieves higher coverage compared to the state-of-the-art methods and discover 3 previously unknown vulnerabilities, demonstrating the potential of BMCFuzz as a powerful, open-source tool for advancing processor design and verification.

You can also see slides: [Slides](https://github.com/iscas-versys/BMCFuzz/blob/main/BMCFuzz_slides.pdf)
## DUTs

* [NutShell](https://github.com/OSCPU/NutShell)
* [Rocket](https://github.com/chipsalliance/rocket-chip)
* [BOOM](https://github.com/riscv-boom/riscv-boom)


## Contact

For more details, you can contact Shidong Shen [shensd@ios.ac.cn](mailto:shensd@ios.ac.cn) for further information.


You may also cite the following paper for reference:

```bibtex
@inproceedings{shen2025bmcfuzz,
  title     = {BMCFuzz: Hybrid Verification of Processors by Synergistic Integration of Bound Model Checking and Fuzzing},
  author    = {Shidong Shen and Jinyu Liu and Weizhi Feng and Fu Song and Zhilin Wu},
  booktitle = {International Conference on Computer-Aided Design (ICCAD)},
  year      = {2025}
}
