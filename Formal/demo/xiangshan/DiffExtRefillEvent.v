
`include "DifftestMacros.v"
module DiffExtRefillEvent(
  input         clock,
  input         enable,
  input         io_valid,
  input  [63:0] io_addr,
  input  [63:0] io_data_0,
  input  [63:0] io_data_1,
  input  [63:0] io_data_2,
  input  [63:0] io_data_3,
  input  [63:0] io_data_4,
  input  [63:0] io_data_5,
  input  [63:0] io_data_6,
  input  [63:0] io_data_7,
  input  [ 7:0] io_idtfr,
  input  [ 7:0] io_coreid,
  input  [ 7:0] io_index
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_RefillEvent (
  input   longint io_addr,
  input   longint io_data_0,
  input   longint io_data_1,
  input   longint io_data_2,
  input   longint io_data_3,
  input   longint io_data_4,
  input   longint io_data_5,
  input   longint io_data_6,
  input   longint io_data_7,
  input      byte io_idtfr,
  input      byte io_coreid,
  input      byte io_index
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_RefillEvent (io_addr, io_data_0, io_data_1, io_data_2, io_data_3, io_data_4, io_data_5, io_data_6, io_data_7, io_idtfr, io_coreid, io_index);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
