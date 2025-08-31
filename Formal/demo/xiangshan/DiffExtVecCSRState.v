
`include "DifftestMacros.v"
module DiffExtVecCSRState(
  input         clock,
  input         enable,
  input  [63:0] io_vstart,
  input  [63:0] io_vxsat,
  input  [63:0] io_vxrm,
  input  [63:0] io_vcsr,
  input  [63:0] io_vl,
  input  [63:0] io_vtype,
  input  [63:0] io_vlenb,
  input  [ 7:0] io_coreid
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_VecCSRState (
  input   longint io_vstart,
  input   longint io_vxsat,
  input   longint io_vxrm,
  input   longint io_vcsr,
  input   longint io_vl,
  input   longint io_vtype,
  input   longint io_vlenb,
  input      byte io_coreid
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_VecCSRState (io_vstart, io_vxsat, io_vxrm, io_vcsr, io_vl, io_vtype, io_vlenb, io_coreid);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
