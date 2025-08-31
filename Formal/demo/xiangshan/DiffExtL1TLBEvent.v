
`include "DifftestMacros.v"
module DiffExtL1TLBEvent(
  input         clock,
  input         enable,
  input         io_valid,
  input  [63:0] io_satp,
  input  [63:0] io_vpn,
  input  [63:0] io_ppn,
  input  [63:0] io_vsatp,
  input  [63:0] io_hgatp,
  input  [ 1:0] io_s2xlate,
  input  [ 7:0] io_coreid,
  input  [ 7:0] io_index
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_L1TLBEvent (
  input   longint io_satp,
  input   longint io_vpn,
  input   longint io_ppn,
  input   longint io_vsatp,
  input   longint io_hgatp,
  input      byte io_s2xlate,
  input      byte io_coreid,
  input      byte io_index
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_L1TLBEvent (io_satp, io_vpn, io_ppn, io_vsatp, io_hgatp, io_s2xlate, io_coreid, io_index);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
