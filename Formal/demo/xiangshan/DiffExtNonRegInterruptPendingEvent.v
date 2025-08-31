
`include "DifftestMacros.v"
module DiffExtNonRegInterruptPendingEvent(
  input         clock,
  input         enable,
  input         io_valid,
  input         io_platformIRPMeip,
  input         io_platformIRPMtip,
  input         io_platformIRPMsip,
  input         io_platformIRPSeip,
  input         io_platformIRPStip,
  input         io_platformIRPVseip,
  input         io_platformIRPVstip,
  input         io_fromAIAMeip,
  input         io_fromAIASeip,
  input         io_localCounterOverflowInterruptReq,
  input  [ 7:0] io_coreid
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
`ifdef DIFFTEST
`ifndef CONFIG_DIFFTEST_FPGA

import "DPI-C" function void v_difftest_NonRegInterruptPendingEvent (
  input       bit io_platformIRPMeip,
  input       bit io_platformIRPMtip,
  input       bit io_platformIRPMsip,
  input       bit io_platformIRPSeip,
  input       bit io_platformIRPStip,
  input       bit io_platformIRPVseip,
  input       bit io_platformIRPVstip,
  input       bit io_fromAIAMeip,
  input       bit io_fromAIASeip,
  input       bit io_localCounterOverflowInterruptReq,
  input      byte io_coreid
);


  always @(posedge clock) begin
    if (enable)
      v_difftest_NonRegInterruptPendingEvent (io_platformIRPMeip, io_platformIRPMtip, io_platformIRPMsip, io_platformIRPSeip, io_platformIRPStip, io_platformIRPVseip, io_platformIRPVstip, io_fromAIAMeip, io_fromAIASeip, io_localCounterOverflowInterruptReq, io_coreid);
  end
`endif // CONFIG_DIFFTEST_FPGA
`endif // DIFFTEST
`endif // SYNTHESIS
endmodule
