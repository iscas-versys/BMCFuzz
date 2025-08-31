
`include "DifftestMacros.v"
module DiffExtArchEvent(
  input         clock,
  input         enable,
  input         io_valid,
  input  [31:0] io_interrupt,
  input  [31:0] io_exception,
  input  [63:0] io_exceptionPC,
  input  [31:0] io_exceptionInst,
  input         io_hasNMI,
  input         io_virtualInterruptIsHvictlInject,
  input         io_irToHS,
  input         io_irToVS,
  input  [ 7:0] io_coreid
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_ArchEvent (
  input       int io_interrupt,
  input       int io_exception,
  input   longint io_exceptionPC,
  input       int io_exceptionInst,
  input       bit io_hasNMI,
  input       bit io_virtualInterruptIsHvictlInject,
  input       bit io_irToHS,
  input       bit io_irToVS,
  input      byte io_coreid
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_ArchEvent (io_interrupt, io_exception, io_exceptionPC, io_exceptionInst, io_hasNMI, io_virtualInterruptIsHvictlInject, io_irToHS, io_irToVS, io_coreid);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
