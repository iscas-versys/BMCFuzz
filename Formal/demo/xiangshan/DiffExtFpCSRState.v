
`include "DifftestMacros.v"
module DiffExtFpCSRState(
  input         clock,
  input         enable,
  input  [63:0] io_fcsr,
  input  [ 7:0] io_coreid
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_FpCSRState (
  input   longint io_fcsr,
  input      byte io_coreid
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_FpCSRState (io_fcsr, io_coreid);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
