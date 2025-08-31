
`include "DifftestMacros.v"
module DiffExtHCSRState(
  input         clock,
  input         enable,
  input  [63:0] io_virtMode,
  input  [63:0] io_mtval2,
  input  [63:0] io_mtinst,
  input  [63:0] io_hstatus,
  input  [63:0] io_hideleg,
  input  [63:0] io_hedeleg,
  input  [63:0] io_hcounteren,
  input  [63:0] io_htval,
  input  [63:0] io_htinst,
  input  [63:0] io_hgatp,
  input  [63:0] io_vsstatus,
  input  [63:0] io_vstvec,
  input  [63:0] io_vsepc,
  input  [63:0] io_vscause,
  input  [63:0] io_vstval,
  input  [63:0] io_vsatp,
  input  [63:0] io_vsscratch,
  input  [ 7:0] io_coreid
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_HCSRState (
  input   longint io_virtMode,
  input   longint io_mtval2,
  input   longint io_mtinst,
  input   longint io_hstatus,
  input   longint io_hideleg,
  input   longint io_hedeleg,
  input   longint io_hcounteren,
  input   longint io_htval,
  input   longint io_htinst,
  input   longint io_hgatp,
  input   longint io_vsstatus,
  input   longint io_vstvec,
  input   longint io_vsepc,
  input   longint io_vscause,
  input   longint io_vstval,
  input   longint io_vsatp,
  input   longint io_vsscratch,
  input      byte io_coreid
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_HCSRState (io_virtMode, io_mtval2, io_mtinst, io_hstatus, io_hideleg, io_hedeleg, io_hcounteren, io_htval, io_htinst, io_hgatp, io_vsstatus, io_vstvec, io_vsepc, io_vscause, io_vstval, io_vsatp, io_vsscratch, io_coreid);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
