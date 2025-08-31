
module PrintCommitIDModule(
  input [5:0] hartID,
  input [39:0] commitID,
  input dirty
);
  wire _dummy_unused = 1'b1;
`ifndef SYNTHESIS
  initial begin
    $fwrite(32'h80000001, "Core %d's Commit SHA is: %h, dirty: %d\n", hartID, commitID, dirty);
  end
`endif

endmodule
