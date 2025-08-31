
`include "DifftestMacros.v"
module DiffExtL2TLBEvent(
  input         clock,
  input         enable,
  input         io_valid,
  input         io_valididx_0,
  input         io_valididx_1,
  input         io_valididx_2,
  input         io_valididx_3,
  input         io_valididx_4,
  input         io_valididx_5,
  input         io_valididx_6,
  input         io_valididx_7,
  input  [63:0] io_satp,
  input  [63:0] io_vpn,
  input  [ 1:0] io_pbmt,
  input  [ 1:0] io_g_pbmt,
  input  [63:0] io_ppn_0,
  input  [63:0] io_ppn_1,
  input  [63:0] io_ppn_2,
  input  [63:0] io_ppn_3,
  input  [63:0] io_ppn_4,
  input  [63:0] io_ppn_5,
  input  [63:0] io_ppn_6,
  input  [63:0] io_ppn_7,
  input  [ 7:0] io_perm,
  input  [ 7:0] io_level,
  input         io_pf,
  input         io_pteidx_0,
  input         io_pteidx_1,
  input         io_pteidx_2,
  input         io_pteidx_3,
  input         io_pteidx_4,
  input         io_pteidx_5,
  input         io_pteidx_6,
  input         io_pteidx_7,
  input  [63:0] io_vsatp,
  input  [63:0] io_hgatp,
  input  [63:0] io_gvpn,
  input  [ 7:0] io_g_perm,
  input  [ 7:0] io_g_level,
  input  [63:0] io_s2ppn,
  input         io_gpf,
  input  [ 1:0] io_s2xlate,
  input  [ 7:0] io_coreid,
  input  [ 7:0] io_index
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_L2TLBEvent (
  input       bit io_valididx_0,
  input       bit io_valididx_1,
  input       bit io_valididx_2,
  input       bit io_valididx_3,
  input       bit io_valididx_4,
  input       bit io_valididx_5,
  input       bit io_valididx_6,
  input       bit io_valididx_7,
  input   longint io_satp,
  input   longint io_vpn,
  input      byte io_pbmt,
  input      byte io_g_pbmt,
  input   longint io_ppn_0,
  input   longint io_ppn_1,
  input   longint io_ppn_2,
  input   longint io_ppn_3,
  input   longint io_ppn_4,
  input   longint io_ppn_5,
  input   longint io_ppn_6,
  input   longint io_ppn_7,
  input      byte io_perm,
  input      byte io_level,
  input       bit io_pf,
  input       bit io_pteidx_0,
  input       bit io_pteidx_1,
  input       bit io_pteidx_2,
  input       bit io_pteidx_3,
  input       bit io_pteidx_4,
  input       bit io_pteidx_5,
  input       bit io_pteidx_6,
  input       bit io_pteidx_7,
  input   longint io_vsatp,
  input   longint io_hgatp,
  input   longint io_gvpn,
  input      byte io_g_perm,
  input      byte io_g_level,
  input   longint io_s2ppn,
  input       bit io_gpf,
  input      byte io_s2xlate,
  input      byte io_coreid,
  input      byte io_index
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_L2TLBEvent (io_valididx_0, io_valididx_1, io_valididx_2, io_valididx_3, io_valididx_4, io_valididx_5, io_valididx_6, io_valididx_7, io_satp, io_vpn, io_pbmt, io_g_pbmt, io_ppn_0, io_ppn_1, io_ppn_2, io_ppn_3, io_ppn_4, io_ppn_5, io_ppn_6, io_ppn_7, io_perm, io_level, io_pf, io_pteidx_0, io_pteidx_1, io_pteidx_2, io_pteidx_3, io_pteidx_4, io_pteidx_5, io_pteidx_6, io_pteidx_7, io_vsatp, io_hgatp, io_gvpn, io_g_perm, io_g_level, io_s2ppn, io_gpf, io_s2xlate, io_coreid, io_index);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
