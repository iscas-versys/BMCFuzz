
`include "DifftestMacros.v"
module DiffExtLoadEvent(
  input         clock,
  input         enable,
  input         io_valid,
  input  [63:0] io_paddr,
  input  [ 7:0] io_opType,
  input         io_isAtomic,
  input         io_isLoad,
  input         io_isVLoad,
  input  [ 7:0] io_coreid,
  input  [ 7:0] io_index
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_LoadEvent (
  input   longint io_paddr,
  input      byte io_opType,
  input       bit io_isAtomic,
  input       bit io_isLoad,
  input       bit io_isVLoad,
  input      byte io_coreid,
  input      byte io_index
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_LoadEvent (io_paddr, io_opType, io_isAtomic, io_isLoad, io_isVLoad, io_coreid, io_index);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
