
`include "DifftestMacros.v"
module DiffExtDebugMode(
  input         clock,
  input         enable,
  input         io_debugMode,
  input  [63:0] io_dcsr,
  input  [63:0] io_dpc,
  input  [63:0] io_dscratch0,
  input  [63:0] io_dscratch1,
  input  [ 7:0] io_coreid
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_DebugMode (
  input       bit io_debugMode,
  input   longint io_dcsr,
  input   longint io_dpc,
  input   longint io_dscratch0,
  input   longint io_dscratch1,
  input      byte io_coreid
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_DebugMode (io_debugMode, io_dcsr, io_dpc, io_dscratch0, io_dscratch1, io_coreid);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
