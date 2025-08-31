module FormalTop;
(* gclk *) wire glb_clk;
wire clock;
wire reset;

wire         auto_memBlock_inner_buffers_out_a_ready;
wire         auto_memBlock_inner_buffers_out_a_valid;
wire         auto_memBlock_inner_buffers_out_a_bits_opcode;
wire         auto_memBlock_inner_buffers_out_a_bits_param;
wire [3:0]   auto_memBlock_inner_buffers_out_a_bits_size;
wire [2:0]   auto_memBlock_inner_buffers_out_a_bits_source;
wire [2:0]   auto_memBlock_inner_buffers_out_a_bits_address;
wire [1:0]   auto_memBlock_inner_buffers_out_a_bits_mask;
wire [47:0]  auto_memBlock_inner_buffers_out_a_bits_data;
wire [7:0]   auto_memBlock_inner_buffers_out_a_bits_corrupt;
wire [63:0]  auto_memBlock_inner_buffers_out_d_ready;
wire         auto_memBlock_inner_buffers_out_d_valid;
wire         auto_memBlock_inner_buffers_out_d_bits_opcode;
wire         auto_memBlock_inner_buffers_out_d_bits_param;
wire [3:0]   auto_memBlock_inner_buffers_out_d_bits_size;
wire [1:0]   auto_memBlock_inner_buffers_out_d_bits_source;
wire [2:0]   auto_memBlock_inner_buffers_out_d_bits_sink;
wire [1:0]   auto_memBlock_inner_buffers_out_d_bits_denied;
wire         auto_memBlock_inner_buffers_out_d_bits_data;
wire         auto_memBlock_inner_buffers_out_d_bits_corrupt;
wire [63:0]  auto_memBlock_inner_frontendBridge_instr_uncache_out_a_ready;
wire         auto_memBlock_inner_frontendBridge_instr_uncache_out_a_valid;
wire         auto_memBlock_inner_frontendBridge_instr_uncache_out_a_bits_param;
wire         auto_memBlock_inner_frontendBridge_instr_uncache_out_a_bits_address;
wire [2:0]   auto_memBlock_inner_frontendBridge_instr_uncache_out_a_bits_corrupt;
wire [47:0]  auto_memBlock_inner_frontendBridge_instr_uncache_out_d_ready;
wire         auto_memBlock_inner_frontendBridge_instr_uncache_out_d_valid;
wire         auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_opcode;
wire         auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_param;
wire [3:0]   auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_size;
wire [1:0]   auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_source;
wire [2:0]   auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_sink;
wire         auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_denied;
wire         auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_data;
wire         auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_corrupt;
wire [63:0]  auto_memBlock_inner_frontendBridge_icachectrl_in_a_ready;
wire         auto_memBlock_inner_frontendBridge_icachectrl_in_a_valid;
wire         auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_opcode;
wire         auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_param;
wire [3:0]   auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_size;
wire [2:0]   auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_source;
wire [1:0]   auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_address;
wire [2:0]   auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_mask;
wire [29:0]  auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_data;
wire [7:0]   auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_corrupt;
wire [63:0]  auto_memBlock_inner_frontendBridge_icachectrl_in_d_ready;
wire         auto_memBlock_inner_frontendBridge_icachectrl_in_d_valid;
wire         auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_opcode;
wire         auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_param;
wire [3:0]   auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_size;
wire [1:0]   auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_source;
wire [1:0]   auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_sink;
wire [2:0]   auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_denied;
wire         auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_data;
wire         auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_corrupt;
wire [63:0]  auto_memBlock_inner_frontendBridge_icache_out_a_ready;
wire         auto_memBlock_inner_frontendBridge_icache_out_a_valid;
wire         auto_memBlock_inner_frontendBridge_icache_out_a_bits_opcode;
wire         auto_memBlock_inner_frontendBridge_icache_out_a_bits_param;
wire [3:0]   auto_memBlock_inner_frontendBridge_icache_out_a_bits_size;
wire [2:0]   auto_memBlock_inner_frontendBridge_icache_out_a_bits_source;
wire [2:0]   auto_memBlock_inner_frontendBridge_icache_out_a_bits_address;
wire [3:0]   auto_memBlock_inner_frontendBridge_icache_out_a_bits_user_reqSource;
wire [47:0]  auto_memBlock_inner_frontendBridge_icache_out_a_bits_user_needHint;
wire [4:0]   auto_memBlock_inner_frontendBridge_icache_out_a_bits_mask;
wire         auto_memBlock_inner_frontendBridge_icache_out_a_bits_data;
wire [31:0]  auto_memBlock_inner_frontendBridge_icache_out_a_bits_corrupt;
wire [255:0] auto_memBlock_inner_frontendBridge_icache_out_d_ready;
wire         auto_memBlock_inner_frontendBridge_icache_out_d_valid;
wire         auto_memBlock_inner_frontendBridge_icache_out_d_bits_opcode;
wire         auto_memBlock_inner_frontendBridge_icache_out_d_bits_param;
wire [3:0]   auto_memBlock_inner_frontendBridge_icache_out_d_bits_size;
wire [1:0]   auto_memBlock_inner_frontendBridge_icache_out_d_bits_source;
wire [2:0]   auto_memBlock_inner_frontendBridge_icache_out_d_bits_sink;
wire [3:0]   auto_memBlock_inner_frontendBridge_icache_out_d_bits_denied;
wire [8:0]   auto_memBlock_inner_frontendBridge_icache_out_d_bits_data;
wire         auto_memBlock_inner_frontendBridge_icache_out_d_bits_corrupt;
wire [255:0] auto_memBlock_inner_ptw_to_l2_buffer_out_a_ready;
wire         auto_memBlock_inner_ptw_to_l2_buffer_out_a_valid;
wire         auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_opcode;
wire         auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_param;
wire [3:0]   auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_size;
wire [2:0]   auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_source;
wire [2:0]   auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_address;
wire [2:0]   auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_user_reqSource;
wire [47:0]  auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_mask;
wire [4:0]   auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_data;
wire [31:0]  auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_corrupt;
wire [255:0] auto_memBlock_inner_ptw_to_l2_buffer_out_d_ready;
wire         auto_memBlock_inner_ptw_to_l2_buffer_out_d_valid;
wire         auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_opcode;
wire         auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_param;
wire [3:0]   auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_size;
wire [1:0]   auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_source;
wire [2:0]   auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_sink;
wire [2:0]   auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_denied;
wire [8:0]   auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_data;
wire         auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_corrupt;
wire [255:0] auto_memBlock_inner_beu_local_int_sink_in_0;
wire         auto_memBlock_inner_nmi_int_sink_in_0;
wire         auto_memBlock_inner_nmi_int_sink_in_1;
wire         auto_memBlock_inner_plic_int_sink_in_1_0;
wire         auto_memBlock_inner_plic_int_sink_in_0_0;
wire         auto_memBlock_inner_debug_int_sink_in_0;
wire         auto_memBlock_inner_clint_int_sink_in_0;
wire         auto_memBlock_inner_clint_int_sink_in_1;
wire         auto_memBlock_inner_dcache_client_out_a_ready;
wire         auto_memBlock_inner_dcache_client_out_a_valid;
wire         auto_memBlock_inner_dcache_client_out_a_bits_opcode;
wire         auto_memBlock_inner_dcache_client_out_a_bits_param;
wire [3:0]   auto_memBlock_inner_dcache_client_out_a_bits_size;
wire [2:0]   auto_memBlock_inner_dcache_client_out_a_bits_source;
wire [2:0]   auto_memBlock_inner_dcache_client_out_a_bits_address;
wire [3:0]   auto_memBlock_inner_dcache_client_out_a_bits_user_vaddr;
wire [47:0]  auto_memBlock_inner_dcache_client_out_a_bits_user_reqSource;
wire [43:0]  auto_memBlock_inner_dcache_client_out_a_bits_user_needHint;
wire [4:0]   auto_memBlock_inner_dcache_client_out_a_bits_echo_isKeyword;
wire         auto_memBlock_inner_dcache_client_out_a_bits_mask;
wire         auto_memBlock_inner_dcache_client_out_a_bits_data;
wire [31:0]  auto_memBlock_inner_dcache_client_out_a_bits_corrupt;
wire [255:0] auto_memBlock_inner_dcache_client_out_b_ready;
wire         auto_memBlock_inner_dcache_client_out_b_valid;
wire         auto_memBlock_inner_dcache_client_out_b_bits_opcode;
wire         auto_memBlock_inner_dcache_client_out_b_bits_param;
wire [2:0]   auto_memBlock_inner_dcache_client_out_b_bits_size;
wire [1:0]   auto_memBlock_inner_dcache_client_out_b_bits_source;
wire [2:0]   auto_memBlock_inner_dcache_client_out_b_bits_address;
wire [3:0]   auto_memBlock_inner_dcache_client_out_b_bits_mask;
wire [47:0]  auto_memBlock_inner_dcache_client_out_b_bits_data;
wire [31:0]  auto_memBlock_inner_dcache_client_out_b_bits_corrupt;
wire [255:0] auto_memBlock_inner_dcache_client_out_c_ready;
wire         auto_memBlock_inner_dcache_client_out_c_valid;
wire         auto_memBlock_inner_dcache_client_out_c_bits_opcode;
wire         auto_memBlock_inner_dcache_client_out_c_bits_param;
wire [2:0]   auto_memBlock_inner_dcache_client_out_c_bits_size;
wire [2:0]   auto_memBlock_inner_dcache_client_out_c_bits_source;
wire [2:0]   auto_memBlock_inner_dcache_client_out_c_bits_address;
wire [3:0]   auto_memBlock_inner_dcache_client_out_c_bits_user_vaddr;
wire [47:0]  auto_memBlock_inner_dcache_client_out_c_bits_user_reqSource;
wire [43:0]  auto_memBlock_inner_dcache_client_out_c_bits_user_needHint;
wire [4:0]   auto_memBlock_inner_dcache_client_out_c_bits_echo_isKeyword;
wire         auto_memBlock_inner_dcache_client_out_c_bits_data;
wire         auto_memBlock_inner_dcache_client_out_c_bits_corrupt;
wire [255:0] auto_memBlock_inner_dcache_client_out_d_ready;
wire         auto_memBlock_inner_dcache_client_out_d_valid;
wire         auto_memBlock_inner_dcache_client_out_d_bits_opcode;
wire         auto_memBlock_inner_dcache_client_out_d_bits_param;
wire [3:0]   auto_memBlock_inner_dcache_client_out_d_bits_size;
wire [1:0]   auto_memBlock_inner_dcache_client_out_d_bits_source;
wire [2:0]   auto_memBlock_inner_dcache_client_out_d_bits_sink;
wire [3:0]   auto_memBlock_inner_dcache_client_out_d_bits_denied;
wire [8:0]   auto_memBlock_inner_dcache_client_out_d_bits_echo_isKeyword;
wire         auto_memBlock_inner_dcache_client_out_d_bits_data;
wire         auto_memBlock_inner_dcache_client_out_d_bits_corrupt;
wire [255:0] auto_memBlock_inner_dcache_client_out_e_ready;
wire         auto_memBlock_inner_dcache_client_out_e_valid;
wire         auto_memBlock_inner_dcache_client_out_e_bits_sink;
wire         io_hartId;
wire [8:0]   io_msiInfo_valid;
wire [5:0]   io_msiInfo_bits;
wire         io_clintTime_valid;
wire [10:0]  io_clintTime_bits;
wire         io_reset_vector;
wire [63:0]  io_cpu_halt;
wire [47:0]  io_l2_flush_done;
wire         io_l2_flush_en;
wire         io_power_down_en;
wire         io_cpu_critical_error;
wire         io_resetInFrontend;
wire         io_traceCoreInterface_fromEncoder_enable;
wire         io_traceCoreInterface_fromEncoder_stall;
wire         io_traceCoreInterface_toEncoder_priv;
wire         io_traceCoreInterface_toEncoder_trap_cause;
wire [2:0]   io_traceCoreInterface_toEncoder_trap_tval;
wire [63:0]  io_traceCoreInterface_toEncoder_groups_0_valid;
wire [49:0]  io_traceCoreInterface_toEncoder_groups_0_bits_iaddr;
wire         io_traceCoreInterface_toEncoder_groups_0_bits_itype;
wire [49:0]  io_traceCoreInterface_toEncoder_groups_0_bits_iretire;
wire [3:0]   io_traceCoreInterface_toEncoder_groups_0_bits_ilastsize;
wire [6:0]   io_traceCoreInterface_toEncoder_groups_1_valid;
wire         io_traceCoreInterface_toEncoder_groups_1_bits_iaddr;
wire         io_traceCoreInterface_toEncoder_groups_1_bits_itype;
wire [49:0]  io_traceCoreInterface_toEncoder_groups_1_bits_iretire;
wire [3:0]   io_traceCoreInterface_toEncoder_groups_1_bits_ilastsize;
wire [6:0]   io_traceCoreInterface_toEncoder_groups_2_valid;
wire         io_traceCoreInterface_toEncoder_groups_2_bits_iaddr;
wire         io_traceCoreInterface_toEncoder_groups_2_bits_itype;
wire [49:0]  io_traceCoreInterface_toEncoder_groups_2_bits_iretire;
wire [3:0]   io_traceCoreInterface_toEncoder_groups_2_bits_ilastsize;
wire [6:0]   io_perfEvents_1_value;
wire         io_perfEvents_2_value;
wire [5:0]   io_perfEvents_3_value;
wire [5:0]   io_perfEvents_4_value;
wire [5:0]   io_perfEvents_5_value;
wire [5:0]   io_perfEvents_6_value;
wire [5:0]   io_perfEvents_7_value;
wire [5:0]   io_perfEvents_8_value;
wire [5:0]   io_perfEvents_9_value;
wire [5:0]   io_perfEvents_10_value;
wire [5:0]   io_perfEvents_11_value;
wire [5:0]   io_perfEvents_12_value;
wire [5:0]   io_perfEvents_13_value;
wire [5:0]   io_perfEvents_14_value;
wire [5:0]   io_perfEvents_15_value;
wire [5:0]   io_perfEvents_16_value;
wire [5:0]   io_perfEvents_17_value;
wire [5:0]   io_perfEvents_18_value;
wire [5:0]   io_perfEvents_19_value;
wire [5:0]   io_perfEvents_20_value;
wire [5:0]   io_perfEvents_21_value;
wire [5:0]   io_perfEvents_22_value;
wire [5:0]   io_perfEvents_23_value;
wire [5:0]   io_perfEvents_24_value;
wire [5:0]   io_beu_errors_icache_ecc_error_valid;
wire [5:0]   io_beu_errors_icache_ecc_error_bits;
wire         io_beu_errors_dcache_ecc_error_valid;
wire [47:0]  io_beu_errors_dcache_ecc_error_bits;
wire         io_beu_errors_uncache_ecc_error_valid;
wire [47:0]  io_beu_errors_uncache_ecc_error_bits;
wire         io_l2_hint_valid;
wire [47:0]  io_l2_hint_bits_sourceId;
wire         io_l2_hint_bits_isKeyword;
wire [1:0]   io_topDownInfo_l2Miss;
wire         io_topDownInfo_l3Miss;
wire         io_dft_ram_hold;
wire         io_dft_ram_bypass;
wire         io_dft_ram_bp_clken;
wire         io_dft_ram_aux_clk;
wire         io_dft_ram_aux_ckbp;
wire         io_dft_ram_mcp_hold;
wire         io_dft_cgen;

reg reg_reset = 1'b1;
always @(posedge glb_clk) begin
  if (reg_reset) begin
    reg_reset <= 1'b0;
  end
end

assign clock = glb_clk;
assign reset = reg_reset;

XSCore dut(
  .clock,
  .reset,
  .auto_memBlock_inner_buffers_out_a_ready,
  .auto_memBlock_inner_buffers_out_a_valid,
  .auto_memBlock_inner_buffers_out_a_bits_opcode,
  .auto_memBlock_inner_buffers_out_a_bits_param,
  .auto_memBlock_inner_buffers_out_a_bits_size,
  .auto_memBlock_inner_buffers_out_a_bits_source,
  .auto_memBlock_inner_buffers_out_a_bits_address,
  .auto_memBlock_inner_buffers_out_a_bits_mask,
  .auto_memBlock_inner_buffers_out_a_bits_data,
  .auto_memBlock_inner_buffers_out_a_bits_corrupt,
  .auto_memBlock_inner_buffers_out_d_ready,
  .auto_memBlock_inner_buffers_out_d_valid,
  .auto_memBlock_inner_buffers_out_d_bits_opcode,
  .auto_memBlock_inner_buffers_out_d_bits_param,
  .auto_memBlock_inner_buffers_out_d_bits_size,
  .auto_memBlock_inner_buffers_out_d_bits_source,
  .auto_memBlock_inner_buffers_out_d_bits_sink,
  .auto_memBlock_inner_buffers_out_d_bits_denied,
  .auto_memBlock_inner_buffers_out_d_bits_data,
  .auto_memBlock_inner_buffers_out_d_bits_corrupt,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_a_ready,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_a_valid,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_a_bits_param,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_a_bits_address,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_a_bits_corrupt,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_d_ready,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_d_valid,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_opcode,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_param,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_size,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_source,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_sink,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_denied,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_data,
  .auto_memBlock_inner_frontendBridge_instr_uncache_out_d_bits_corrupt,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_a_ready,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_a_valid,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_opcode,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_param,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_size,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_source,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_address,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_mask,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_data,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_a_bits_corrupt,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_d_ready,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_d_valid,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_opcode,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_param,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_size,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_source,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_sink,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_denied,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_data,
  .auto_memBlock_inner_frontendBridge_icachectrl_in_d_bits_corrupt,
  .auto_memBlock_inner_frontendBridge_icache_out_a_ready,
  .auto_memBlock_inner_frontendBridge_icache_out_a_valid,
  .auto_memBlock_inner_frontendBridge_icache_out_a_bits_opcode,
  .auto_memBlock_inner_frontendBridge_icache_out_a_bits_param,
  .auto_memBlock_inner_frontendBridge_icache_out_a_bits_size,
  .auto_memBlock_inner_frontendBridge_icache_out_a_bits_source,
  .auto_memBlock_inner_frontendBridge_icache_out_a_bits_address,
  .auto_memBlock_inner_frontendBridge_icache_out_a_bits_user_reqSource,
  .auto_memBlock_inner_frontendBridge_icache_out_a_bits_user_needHint,
  .auto_memBlock_inner_frontendBridge_icache_out_a_bits_mask,
  .auto_memBlock_inner_frontendBridge_icache_out_a_bits_data,
  .auto_memBlock_inner_frontendBridge_icache_out_a_bits_corrupt,
  .auto_memBlock_inner_frontendBridge_icache_out_d_ready,
  .auto_memBlock_inner_frontendBridge_icache_out_d_valid,
  .auto_memBlock_inner_frontendBridge_icache_out_d_bits_opcode,
  .auto_memBlock_inner_frontendBridge_icache_out_d_bits_param,
  .auto_memBlock_inner_frontendBridge_icache_out_d_bits_size,
  .auto_memBlock_inner_frontendBridge_icache_out_d_bits_source,
  .auto_memBlock_inner_frontendBridge_icache_out_d_bits_sink,
  .auto_memBlock_inner_frontendBridge_icache_out_d_bits_denied,
  .auto_memBlock_inner_frontendBridge_icache_out_d_bits_data,
  .auto_memBlock_inner_frontendBridge_icache_out_d_bits_corrupt,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_a_ready,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_a_valid,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_opcode,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_param,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_size,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_source,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_address,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_user_reqSource,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_mask,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_data,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_a_bits_corrupt,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_d_ready,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_d_valid,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_opcode,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_param,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_size,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_source,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_sink,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_denied,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_data,
  .auto_memBlock_inner_ptw_to_l2_buffer_out_d_bits_corrupt,
  .auto_memBlock_inner_beu_local_int_sink_in_0,
  .auto_memBlock_inner_nmi_int_sink_in_0,
  .auto_memBlock_inner_nmi_int_sink_in_1,
  .auto_memBlock_inner_plic_int_sink_in_1_0,
  .auto_memBlock_inner_plic_int_sink_in_0_0,
  .auto_memBlock_inner_debug_int_sink_in_0,
  .auto_memBlock_inner_clint_int_sink_in_0,
  .auto_memBlock_inner_clint_int_sink_in_1,
  .auto_memBlock_inner_dcache_client_out_a_ready,
  .auto_memBlock_inner_dcache_client_out_a_valid,
  .auto_memBlock_inner_dcache_client_out_a_bits_opcode,
  .auto_memBlock_inner_dcache_client_out_a_bits_param,
  .auto_memBlock_inner_dcache_client_out_a_bits_size,
  .auto_memBlock_inner_dcache_client_out_a_bits_source,
  .auto_memBlock_inner_dcache_client_out_a_bits_address,
  .auto_memBlock_inner_dcache_client_out_a_bits_user_vaddr,
  .auto_memBlock_inner_dcache_client_out_a_bits_user_reqSource,
  .auto_memBlock_inner_dcache_client_out_a_bits_user_needHint,
  .auto_memBlock_inner_dcache_client_out_a_bits_echo_isKeyword,
  .auto_memBlock_inner_dcache_client_out_a_bits_mask,
  .auto_memBlock_inner_dcache_client_out_a_bits_data,
  .auto_memBlock_inner_dcache_client_out_a_bits_corrupt,
  .auto_memBlock_inner_dcache_client_out_b_ready,
  .auto_memBlock_inner_dcache_client_out_b_valid,
  .auto_memBlock_inner_dcache_client_out_b_bits_opcode,
  .auto_memBlock_inner_dcache_client_out_b_bits_param,
  .auto_memBlock_inner_dcache_client_out_b_bits_size,
  .auto_memBlock_inner_dcache_client_out_b_bits_source,
  .auto_memBlock_inner_dcache_client_out_b_bits_address,
  .auto_memBlock_inner_dcache_client_out_b_bits_mask,
  .auto_memBlock_inner_dcache_client_out_b_bits_data,
  .auto_memBlock_inner_dcache_client_out_b_bits_corrupt,
  .auto_memBlock_inner_dcache_client_out_c_ready,
  .auto_memBlock_inner_dcache_client_out_c_valid,
  .auto_memBlock_inner_dcache_client_out_c_bits_opcode,
  .auto_memBlock_inner_dcache_client_out_c_bits_param,
  .auto_memBlock_inner_dcache_client_out_c_bits_size,
  .auto_memBlock_inner_dcache_client_out_c_bits_source,
  .auto_memBlock_inner_dcache_client_out_c_bits_address,
  .auto_memBlock_inner_dcache_client_out_c_bits_user_vaddr,
  .auto_memBlock_inner_dcache_client_out_c_bits_user_reqSource,
  .auto_memBlock_inner_dcache_client_out_c_bits_user_needHint,
  .auto_memBlock_inner_dcache_client_out_c_bits_echo_isKeyword,
  .auto_memBlock_inner_dcache_client_out_c_bits_data,
  .auto_memBlock_inner_dcache_client_out_c_bits_corrupt,
  .auto_memBlock_inner_dcache_client_out_d_ready,
  .auto_memBlock_inner_dcache_client_out_d_valid,
  .auto_memBlock_inner_dcache_client_out_d_bits_opcode,
  .auto_memBlock_inner_dcache_client_out_d_bits_param,
  .auto_memBlock_inner_dcache_client_out_d_bits_size,
  .auto_memBlock_inner_dcache_client_out_d_bits_source,
  .auto_memBlock_inner_dcache_client_out_d_bits_sink,
  .auto_memBlock_inner_dcache_client_out_d_bits_denied,
  .auto_memBlock_inner_dcache_client_out_d_bits_echo_isKeyword,
  .auto_memBlock_inner_dcache_client_out_d_bits_data,
  .auto_memBlock_inner_dcache_client_out_d_bits_corrupt,
  .auto_memBlock_inner_dcache_client_out_e_ready,
  .auto_memBlock_inner_dcache_client_out_e_valid,
  .auto_memBlock_inner_dcache_client_out_e_bits_sink,
  .io_hartId,
  .io_msiInfo_valid,
  .io_msiInfo_bits,
  .io_clintTime_valid,
  .io_clintTime_bits,
  .io_reset_vector,
  .io_cpu_halt,
  .io_l2_flush_done,
  .io_l2_flush_en,
  .io_power_down_en,
  .io_cpu_critical_error,
  .io_resetInFrontend,
  .io_traceCoreInterface_fromEncoder_enable,
  .io_traceCoreInterface_fromEncoder_stall,
  .io_traceCoreInterface_toEncoder_priv,
  .io_traceCoreInterface_toEncoder_trap_cause,
  .io_traceCoreInterface_toEncoder_trap_tval,
  .io_traceCoreInterface_toEncoder_groups_0_valid,
  .io_traceCoreInterface_toEncoder_groups_0_bits_iaddr,
  .io_traceCoreInterface_toEncoder_groups_0_bits_itype,
  .io_traceCoreInterface_toEncoder_groups_0_bits_iretire,
  .io_traceCoreInterface_toEncoder_groups_0_bits_ilastsize,
  .io_traceCoreInterface_toEncoder_groups_1_valid,
  .io_traceCoreInterface_toEncoder_groups_1_bits_iaddr,
  .io_traceCoreInterface_toEncoder_groups_1_bits_itype,
  .io_traceCoreInterface_toEncoder_groups_1_bits_iretire,
  .io_traceCoreInterface_toEncoder_groups_1_bits_ilastsize,
  .io_traceCoreInterface_toEncoder_groups_2_valid,
  .io_traceCoreInterface_toEncoder_groups_2_bits_iaddr,
  .io_traceCoreInterface_toEncoder_groups_2_bits_itype,
  .io_traceCoreInterface_toEncoder_groups_2_bits_iretire,
  .io_traceCoreInterface_toEncoder_groups_2_bits_ilastsize,
  .io_perfEvents_1_value,
  .io_perfEvents_2_value,
  .io_perfEvents_3_value,
  .io_perfEvents_4_value,
  .io_perfEvents_5_value,
  .io_perfEvents_6_value,
  .io_perfEvents_7_value,
  .io_perfEvents_8_value,
  .io_perfEvents_9_value,
  .io_perfEvents_10_value,
  .io_perfEvents_11_value,
  .io_perfEvents_12_value,
  .io_perfEvents_13_value,
  .io_perfEvents_14_value,
  .io_perfEvents_15_value,
  .io_perfEvents_16_value,
  .io_perfEvents_17_value,
  .io_perfEvents_18_value,
  .io_perfEvents_19_value,
  .io_perfEvents_20_value,
  .io_perfEvents_21_value,
  .io_perfEvents_22_value,
  .io_perfEvents_23_value,
  .io_perfEvents_24_value,
  .io_beu_errors_icache_ecc_error_valid,
  .io_beu_errors_icache_ecc_error_bits,
  .io_beu_errors_dcache_ecc_error_valid,
  .io_beu_errors_dcache_ecc_error_bits,
  .io_beu_errors_uncache_ecc_error_valid,
  .io_beu_errors_uncache_ecc_error_bits,
  .io_l2_hint_valid,
  .io_l2_hint_bits_sourceId,
  .io_l2_hint_bits_isKeyword,
  .io_topDownInfo_l2Miss,
  .io_topDownInfo_l3Miss,
  .io_dft_ram_hold,
  .io_dft_ram_bypass,
  .io_dft_ram_bp_clken,
  .io_dft_ram_aux_clk,
  .io_dft_ram_aux_ckbp,
  .io_dft_ram_mcp_hold,
  .io_dft_cgen
);
endmodule