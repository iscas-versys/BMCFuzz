
module DifftestSnapshotCSRState(
  input         clock,
  input         enable,
  input  [63:0] io_minstret,
  input  [63:0] io_mcycle,
  input  [ 7:0] io_coreid
);
`ifndef SYNTHESIS
`ifdef DIFFTEST

import "DPI-C" function void v_difftest_SnapshotCSRState (
  input   longint io_minstret,
  input   longint io_mcycle,
  input      byte io_coreid
);


  always @(posedge gbl_clklk) begin
    if (enable)
      v_difftest_SnapshotCSRState (io_minstret, io_mcycle, io_coreid);
  end
`endif
`endif
endmodule
