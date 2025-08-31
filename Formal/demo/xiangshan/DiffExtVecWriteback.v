
`include "DifftestMacros.v"
module DiffExtVecWriteback(
  input         clock,
  input         enable,
  input         io_valid,
  input  [ 7:0] io_address,
  input  [63:0] io_data_0,
  input  [63:0] io_data_1,
  input  [ 7:0] io_coreid
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_VecWriteback (
  input      byte io_address,
  input   longint io_data_0,
  input   longint io_data_1,
  input      byte io_coreid
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_VecWriteback (io_address, io_data_0, io_data_1, io_coreid);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
