
module DifftestStoreEvent(
  input         clock,
  input         enable,
  input         io_valid,
  input  [63:0] io_addr,
  input  [63:0] io_data,
  input  [ 7:0] io_mask,
  input  [ 7:0] io_coreid,
  input  [ 7:0] io_index
);
`ifndef SYNTHESIS
`ifdef DIFFTEST

import "DPI-C" function void v_difftest_StoreEvent (
  input   longint io_addr,
  input   longint io_data,
  input      byte io_mask,
  input      byte io_coreid,
  input      byte io_index
);


  always @(posedge gbl_clk) begin
    if (enable)
      v_difftest_StoreEvent (io_addr, io_data, io_mask, io_coreid, io_index);
  end
`endif
`endif
endmodule
