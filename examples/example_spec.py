# Example specification for test matrix generation

spec = {
    "project_name": "AHB-Lite Verification",
    "short_description": "Verify AHB-Lite interface with bursts and IDLE behavior",
    "dut": "u_core.core_i.if_stage_i",
    "methodology": "UVM",
    "simulator": "VCS",
    "stimulus": "constrained-random",
    
    # Features to verify - will generate test scenarios for each
    "features": [
        "handshake",
        "burst transfers",
        "idle insertion",
        "error response",
    ],
    
    # Coverage bins - will be mapped to test scenarios
    "coverage": [
        "fsm_states",
        "burst_lengths",
        "addr_alignments",
    ]
}