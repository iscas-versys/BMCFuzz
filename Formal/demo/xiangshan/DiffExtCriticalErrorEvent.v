
`include "DifftestMacros.v"
module DiffExtCriticalErrorEvent(
  input         clock,
  input         enable,
  input         io_valid,
  input         io_criticalError,
  input  [ 7:0] io_coreid
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_CriticalErrorEvent (
  input       bit io_criticalError,
  input      byte io_coreid
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_CriticalErrorEvent (io_criticalError, io_coreid);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
