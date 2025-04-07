
module DifftestInstrCommit(
  input         clock,
  input         enable,
  input         io_valid,
  input         io_skip,
  input         io_isRVC,
  input         io_rfwen,
  input         io_fpwen,
  input         io_vecwen,
  input  [ 4:0] io_wpdest,
  input  [ 7:0] io_wdest,
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
`ifndef SYNTHESIS
`ifdef DIFFTEST

import "DPI-C" function void v_difftest_InstrCommit (
  input       bit io_skip,
  input       bit io_isRVC,
  input       bit io_rfwen,
  input       bit io_fpwen,
  input       bit io_vecwen,
  input      byte io_wpdest,
  input      byte io_wdest,
  input   longint io_pc,
  input       int io_instr,
  input       int io_robIdx,
  input      byte io_lqIdx,
  input      byte io_sqIdx,
  input       bit io_isLoad,
  input       bit io_isStore,
  input      byte io_nFused,
  input      byte io_special,
  input      byte io_coreid,
  input      byte io_index
);


  always @(posedge gbl_clk) begin
    if (enable)
      v_difftest_InstrCommit (io_skip, io_isRVC, io_rfwen, io_fpwen, io_vecwen, io_wpdest, io_wdest, io_pc, io_instr, io_robIdx, io_lqIdx, io_sqIdx, io_isLoad, io_isStore, io_nFused, io_special, io_coreid, io_index);
  end
`endif
`endif
endmodule
