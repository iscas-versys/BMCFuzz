
module DifftestArchEvent(
  input         clock,
  input         enable,
  input         io_valid,
  input  [31:0] io_interrupt,
  input  [31:0] io_exception,
  input  [63:0] io_exceptionPC,
  input  [31:0] io_exceptionInst,
  input  [ 7:0] io_coreid
);
`ifndef SYNTHESIS
`ifdef DIFFTEST

import "DPI-C" function void v_difftest_ArchEvent (
  input       int io_interrupt,
  input       int io_exception,
  input   longint io_exceptionPC,
  input       int io_exceptionInst,
  input      byte io_coreid
);


  always @(posedge gbl_clk) begin
    if (enable)
      v_difftest_ArchEvent (io_interrupt, io_exception, io_exceptionPC, io_exceptionInst, io_coreid);
  end
`endif
`endif
endmodule
