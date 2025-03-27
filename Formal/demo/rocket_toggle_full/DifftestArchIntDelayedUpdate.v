
module DifftestArchIntDelayedUpdate(
  input         clock,
  input         enable,
  input         io_valid,
  input  [ 4:0] io_address,
  input  [63:0] io_data,
  input         io_nack,
  input  [ 7:0] io_coreid,
  input  [ 7:0] io_index
);
`ifndef SYNTHESIS
`ifdef DIFFTEST

import "DPI-C" function void v_difftest_ArchIntDelayedUpdate (
  input      byte io_address,
  input   longint io_data,
  input       bit io_nack,
  input      byte io_coreid,
  input      byte io_index
);


  always @(posedge gbl_clk) begin
    if (enable)
      v_difftest_ArchIntDelayedUpdate (io_address, io_data, io_nack, io_coreid, io_index);
  end
`endif
`endif
endmodule
