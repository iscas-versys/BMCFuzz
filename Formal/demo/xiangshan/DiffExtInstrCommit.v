
`include "DifftestMacros.v"
module DiffExtInstrCommit(
  input         clock,
  input         enable,
  input         io_valid,
  input         io_skip,
  input         io_isRVC,
  input         io_rfwen,
  input         io_fpwen,
  input         io_vecwen,
  input         io_v0wen,
  input  [ 7:0] io_wpdest,
  input  [ 7:0] io_wdest,
  input  [ 7:0] io_otherwpdest_0,
  input  [ 7:0] io_otherwpdest_1,
  input  [ 7:0] io_otherwpdest_2,
  input  [ 7:0] io_otherwpdest_3,
  input  [ 7:0] io_otherwpdest_4,
  input  [ 7:0] io_otherwpdest_5,
  input  [ 7:0] io_otherwpdest_6,
  input  [ 7:0] io_otherwpdest_7,
  input         io_otherV0Wen_0,
  input         io_otherV0Wen_1,
  input         io_otherV0Wen_2,
  input         io_otherV0Wen_3,
  input         io_otherV0Wen_4,
  input         io_otherV0Wen_5,
  input         io_otherV0Wen_6,
  input         io_otherV0Wen_7,
  input  [63:0] io_pc,
  input  [31:0] io_instr,
  input  [ 9:0] io_robIdx,
  input  [ 6:0] io_lqIdx,
  input  [ 6:0] io_sqIdx,
  input         io_isLoad,
  input         io_isStore,
  input  [ 7:0] io_nFused,
  input  [ 7:0] io_special,
  input  [ 7:0] io_coreid,
  input  [ 7:0] io_index
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_InstrCommit (
  input       bit io_skip,
  input       bit io_isRVC,
  input       bit io_rfwen,
  input       bit io_fpwen,
  input       bit io_vecwen,
  input       bit io_v0wen,
  input      byte io_wpdest,
  input      byte io_wdest,
  input      byte io_otherwpdest_0,
  input      byte io_otherwpdest_1,
  input      byte io_otherwpdest_2,
  input      byte io_otherwpdest_3,
  input      byte io_otherwpdest_4,
  input      byte io_otherwpdest_5,
  input      byte io_otherwpdest_6,
  input      byte io_otherwpdest_7,
  input       bit io_otherV0Wen_0,
  input       bit io_otherV0Wen_1,
  input       bit io_otherV0Wen_2,
  input       bit io_otherV0Wen_3,
  input       bit io_otherV0Wen_4,
  input       bit io_otherV0Wen_5,
  input       bit io_otherV0Wen_6,
  input       bit io_otherV0Wen_7,
  input   longint io_pc,
  input       int io_instr,
  input  shortint io_robIdx,
  input      byte io_lqIdx,
  input      byte io_sqIdx,
  input       bit io_isLoad,
  input       bit io_isStore,
  input      byte io_nFused,
  input      byte io_special,
  input      byte io_coreid,
  input      byte io_index
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_InstrCommit (io_skip, io_isRVC, io_rfwen, io_fpwen, io_vecwen, io_v0wen, io_wpdest, io_wdest, io_otherwpdest_0, io_otherwpdest_1, io_otherwpdest_2, io_otherwpdest_3, io_otherwpdest_4, io_otherwpdest_5, io_otherwpdest_6, io_otherwpdest_7, io_otherV0Wen_0, io_otherV0Wen_1, io_otherV0Wen_2, io_otherV0Wen_3, io_otherV0Wen_4, io_otherV0Wen_5, io_otherV0Wen_6, io_otherV0Wen_7, io_pc, io_instr, io_robIdx, io_lqIdx, io_sqIdx, io_isLoad, io_isStore, io_nFused, io_special, io_coreid, io_index);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
