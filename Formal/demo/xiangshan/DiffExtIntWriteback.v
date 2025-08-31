
`include "DifftestMacros.v"
module DiffExtIntWriteback(
  input         clock,
  input         enable,
  input         io_valid,
  input  [ 5:0] io_address,
  input  [63:0] io_data,
  input  [ 7:0] io_coreid
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_IntWriteback (
  input      byte io_address,
  input   longint io_data,
  input      byte io_coreid
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_IntWriteback (io_address, io_data, io_coreid);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
