
module DifftestCSRState(
  input         clock,
  input         enable,
  input  [63:0] io_privilegeMode,
  input  [63:0] io_mstatus,
  input  [63:0] io_sstatus,
  input  [63:0] io_mepc,
  input  [63:0] io_sepc,
  input  [63:0] io_mtval,
  input  [63:0] io_stval,
  input  [63:0] io_mtvec,
  input  [63:0] io_stvec,
  input  [63:0] io_mcause,
  input  [63:0] io_scause,
  input  [63:0] io_satp,
  input  [63:0] io_mip,
  input  [63:0] io_mie,
  input  [63:0] io_mscratch,
  input  [63:0] io_sscratch,
  input  [63:0] io_mideleg,
  input  [63:0] io_medeleg,
  input  [ 7:0] io_coreid
);
`ifndef SYNTHESIS
`ifdef DIFFTEST

import "DPI-C" function void v_difftest_CSRState (
  input   longint io_privilegeMode,
  input   longint io_mstatus,
  input   longint io_sstatus,
  input   longint io_mepc,
  input   longint io_sepc,
  input   longint io_mtval,
  input   longint io_stval,
  input   longint io_mtvec,
  input   longint io_stvec,
  input   longint io_mcause,
  input   longint io_scause,
  input   longint io_satp,
  input   longint io_mip,
  input   longint io_mie,
  input   longint io_mscratch,
  input   longint io_sscratch,
  input   longint io_mideleg,
  input   longint io_medeleg,
  input      byte io_coreid
);


  always @(posedge gbl_clk) begin
    if (enable)
      v_difftest_CSRState (io_privilegeMode, io_mstatus, io_sstatus, io_mepc, io_sepc, io_mtval, io_stval, io_mtvec, io_stvec, io_mcause, io_scause, io_satp, io_mip, io_mie, io_mscratch, io_sscratch, io_mideleg, io_medeleg, io_coreid);
  end
`endif
`endif
endmodule
