
module DifftestTrapEvent(
  input         clock,
  input         enable,
  input         io_hasTrap,
  input  [63:0] io_cycleCnt,
  input  [63:0] io_instrCnt,
  input         io_hasWFI,
  input  [31:0] io_code,
  input  [63:0] io_pc,
  input  [ 7:0] io_coreid
);
`ifndef SYNTHESIS
`ifdef DIFFTEST

import "DPI-C" function void v_difftest_TrapEvent (
  input       bit io_hasTrap,
  input   longint io_cycleCnt,
  input   longint io_instrCnt,
  input       bit io_hasWFI,
  input       int io_code,
  input   longint io_pc,
  input      byte io_coreid
);


  always @(posedge gbl_clk) begin
    if (enable)
      v_difftest_TrapEvent (io_hasTrap, io_cycleCnt, io_instrCnt, io_hasWFI, io_code, io_pc, io_coreid);
  end
`endif
`endif
endmodule
