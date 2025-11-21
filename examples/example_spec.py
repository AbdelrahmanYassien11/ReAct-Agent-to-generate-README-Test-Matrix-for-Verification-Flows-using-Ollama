# Example spec as a Python dict (no JSON/YAML required)
spec = {
    "project_name": "AHB-Lite Verification",
    "short_description": "Verify a simple AHB-Lite-like interface with bursts and IDLE behavior.",
    "dut": "u_core.core_i.if_stage_i",
    "methodology": "UVM",
    "simulator": "VCS",
    "stimulus": "constrained-random",
    "features": [
        "handshake",
        "burst transfers",
        "idle insertion",
        "error response",
    ],
    "coverage": [
        "fsm_states",
        "burst_lengths",
        "addr_alignments",
    ]
}
