import json
import sys
import re
from pathlib import Path
from datetime import datetime

def parse_prompts_file(prompts_file: Path):
    with open(prompts_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    prompts = data.get('prompts', [])
    pipeline_metrics = []
    security_issues_all = []
    
    # Sort prompts by timestamp
    prompts.sort(key=lambda x: x.get('timestamp', ''))
    
    iteration_count = 0
    start_time = None
    
    for i, prompt in enumerate(prompts):
        timestamp_str = prompt.get('timestamp')
        if not timestamp_str:
            continue
            
        current_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        
        if start_time is None:
            start_time = current_time
            
        # We are interested in the evaluation agent's response
        if prompt.get('agent') == 'evaluation_agent':
            iteration_count += 1
            response_str = prompt.get('response', '')
            
            # Extract JSON from response
            try:
                if "```" in response_str:
                    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response_str)
                    if json_match:
                        response_str = json_match.group(1).strip()
                
                eval_data = json.loads(response_str)
                
                # Calculate execution time (delta from previous prompt or start)
                # Ideally, this should be the time since the *start* of this iteration's testing
                # For simplicity, we'll take the time since the last evaluation (or start for the first one)
                # A better approximation might be the time since the 'implementation_agent' call that preceded this
                
                execution_time = 0.0
                # Find the preceding implementation agent call
                for j in range(i - 1, -1, -1):
                    prev_prompt = prompts[j]
                    if prev_prompt.get('agent') in ('implementation_agent', 'implementation_agent_improvement'):
                        prev_time = datetime.strptime(prev_prompt.get('timestamp'), "%Y-%m-%d %H:%M:%S")
                        execution_time = (current_time - prev_time).total_seconds()
                        break
                
                if execution_time == 0.0 and i > 0:
                     prev_time = datetime.strptime(prompts[i-1].get('timestamp'), "%Y-%m-%d %H:%M:%S")
                     execution_time = (current_time - prev_time).total_seconds()

                
                metrics = {
                    "iteration": iteration_count,
                    "timestamp": timestamp_str,
                    "execution_time_seconds": execution_time,
                    "code_coverage_percentage": eval_data.get("code_coverage_percentage", 0.0),
                    "security_issues_count": len(eval_data.get("security_issues", [])),
                    "tests_total": eval_data.get("execution_summary", {}).get("total_tests", 0),
                    "tests_passed": eval_data.get("execution_summary", {}).get("passed", 0),
                    "tests_failed": eval_data.get("execution_summary", {}).get("failed", 0)
                }
                pipeline_metrics.append(metrics)
                
                # Collect security issues from the FINAL iteration (or all, but usually we want the current state)
                # Let's collect all distinct ones encountered, or just the latest set. 
                # The user wants "Security Vulnerabilities Distribution", which implies the *current* state of the code.
                # So we should probably take the issues from the latest evaluation.
                security_issues_all = eval_data.get("security_issues", [])
                
            except (json.JSONDecodeError, ValueError):
                continue

    # Process security distribution
    security_distribution = {}
    for issue in security_issues_all:
        issue_type = issue.get('issue', 'Unknown')
        # Normalize slightly
        issue_type = issue_type.split(':')[0].strip() 
        if issue_type in security_distribution:
            security_distribution[issue_type]['count'] += 1
        else:
            security_distribution[issue_type] = {
                'type': issue_type,
                'count': 1,
                'severity': issue.get('severity', 'unknown')
            }
            
    security_dist_list = list(security_distribution.values())
    
    return {
        "pipeline_metrics": pipeline_metrics,
        "security_distribution": security_dist_list,
        "security_issues_list": security_issues_all,
        "summary": {
            "total_iterations": iteration_count,
            "final_coverage": pipeline_metrics[-1]['code_coverage_percentage'] if pipeline_metrics else 0.0,
            "final_security_issues": len(security_issues_all)
        }
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_dashboard_data.py <tests_directory>")
        sys.exit(1)
        
    tests_dir = Path(sys.argv[1])
    if not tests_dir.exists():
        print(f"Error: Directory {tests_dir} does not exist")
        sys.exit(1)
        
    # Find the latest prompts file
    prompts_files = list(tests_dir.glob("prompts_*.json"))
    if not prompts_files:
        print(f"Error: No prompts_*.json files found in {tests_dir}")
        sys.exit(1)
        
    # Sort by modification time, newest first
    prompts_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    latest_prompts = prompts_files[0]
    
    print(f"Processing {latest_prompts}...")
    
    dashboard_data = parse_prompts_file(latest_prompts)
    
    output_file = tests_dir / "dashboard_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=2)
        
    print(f"Generated {output_file}")

if __name__ == "__main__":
    main()
