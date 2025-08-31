
`include "DifftestMacros.v"
module DiffExtSyncCustomMflushpwrEvent(
  input         clock,
  input         enable,
  input         io_valid,
  input         io_l2FlushDone,
  input  [ 7:0] io_coreid
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_SyncCustomMflushpwrEvent (
  input       bit io_l2FlushDone,
  input      byte io_coreid
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_SyncCustomMflushpwrEvent (io_l2FlushDone, io_coreid);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
