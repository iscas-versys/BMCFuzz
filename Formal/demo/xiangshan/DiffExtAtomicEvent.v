
`include "DifftestMacros.v"
module DiffExtAtomicEvent(
  input         clock,
  input         enable,
  input         io_valid,
  input  [63:0] io_addr,
  input  [63:0] io_data_0,
  input  [63:0] io_data_1,
  input  [15:0] io_mask,
  input  [63:0] io_cmp_0,
  input  [63:0] io_cmp_1,
  input  [ 7:0] io_fuop,
  input  [63:0] io_out_0,
  input  [63:0] io_out_1,
  input  [ 7:0] io_coreid
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_AtomicEvent (
  input   longint io_addr,
  input   longint io_data_0,
  input   longint io_data_1,
  input  shortint io_mask,
  input   longint io_cmp_0,
  input   longint io_cmp_1,
  input      byte io_fuop,
  input   longint io_out_0,
  input   longint io_out_1,
  input      byte io_coreid
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_AtomicEvent (io_addr, io_data_0, io_data_1, io_mask, io_cmp_0, io_cmp_1, io_fuop, io_out_0, io_out_1, io_coreid);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
