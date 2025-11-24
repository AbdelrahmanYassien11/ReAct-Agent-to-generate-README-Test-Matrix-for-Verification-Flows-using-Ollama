"""
test_simple.py - Test with mocked LLM response
"""
from agent_loop import SimpleExecutor
from tools import write_testmatrix

# Mock LLM that returns a test matrix table
def mock_llm(prompt: str) -> str:
    return """| Scenario ID | Feature | Preconditions | Stimulus | Test Steps | Expected Result | Coverage Bin | Priority |
|-------------|---------|---------------|----------|------------|-----------------|--------------|----------|
| T001 | Handshake | Reset complete | Valid request | 1) Drive request signal 2) Wait for response 3) Check timing | Response within 3 cycles | fsm_states | high |
| T002 | Burst transfer | Address aligned | Burst of 4 beats | 1) Issue burst request 2) Monitor data 3) Verify order | All 4 beats transferred correctly | burst_lengths | high |
| T003 | IDLE insertion | Active transfer | Insert IDLE cycle | 1) Start transfer 2) Insert IDLE 3) Resume | Transfer resumes correctly after IDLE | fsm_states | medium |
| T004 | Error response | Invalid address | Access to protected region | 1) Send invalid request 2) Check error signal 3) Verify no data | Error signal asserted, no data transfer | error_response | high |
| T005 | Address alignment | Misaligned address | Write with odd address | 1) Drive misaligned address 2) Observe behavior | Error or auto-correction as per spec | addr_alignments | medium |
| T006 | Back-to-back bursts | Previous burst complete | Two consecutive bursts | 1) Complete burst 1 2) Immediately start burst 2 | Both bursts complete without gaps | burst_lengths | medium |
| T007 | Maximum burst | Reset state | Burst of maximum length | 1) Configure max burst 2) Execute 3) Verify count | All beats transferred correctly | burst_lengths | low |
| T008 | IDLE during burst | Mid-burst state | IDLE insertion in burst | 1) Start burst 2) Insert IDLE mid-burst 3) Complete | Burst completes correctly after IDLE | fsm_states | medium |"""

if __name__ == '__main__':
    executor = SimpleExecutor(llm_call=mock_llm)
    spec = {
        "project_name": "Test Project",
        "features": ["handshake", "burst", "idle"],
        "coverage": ["fsm_states", "burst_lengths"]
    }
    
    result = executor.run("System prompt", spec)
    
    print("=== Result ===")
    print(f"Content length: {len(result['content'])} chars")
    print(f"\nFirst 200 chars:\n{result['content'][:200]}")
    
    # Test writing
    status = write_testmatrix("output", result["content"])
    print(f"\n{status}")