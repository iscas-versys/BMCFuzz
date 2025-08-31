
`include "DifftestMacros.v"
module DiffExtMhpmeventOverflowEvent(
  input         clock,
  input         enable,
  input         io_valid,
  input  [63:0] io_mhpmeventOverflow,
  input  [ 7:0] io_coreid
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_MhpmeventOverflowEvent (
  input   longint io_mhpmeventOverflow,
  input      byte io_coreid
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_MhpmeventOverflowEvent (io_mhpmeventOverflow, io_coreid);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
