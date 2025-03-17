
module DifftestLrScEvent(
  input         clock,
  input         enable,
  input         io_valid,
  input         io_success,
  input  [ 7:0] io_coreid
);
`ifndef SYNTHESIS
`ifdef DIFFTEST

import "DPI-C" function void v_difftest_LrScEvent (
  input       bit io_success,
  input      byte io_coreid
);


  always @(posedge gbl_clk) begin
    if (enable)
      v_difftest_LrScEvent (io_success, io_coreid);
  end
`endif
`endif
endmodule
