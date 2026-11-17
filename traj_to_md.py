import json
import os

def extract_agent_logs(json_data, output_file="agent_trajectory.md"):
    md_content = []
    md_content.append("# Agent Trajectory & Execution Logs\n")
    md_content.append("This file contains the consolidated thoughts, subagent paths, and tool usage extracted from the execution artifacts.\n")
    md_content.append("--- \n")

    # Global counter for chronological agent actions/steps
    step_num = 1

    # 1. Process Subagent Trajectories
    subagents = json_data.get("subagent_trajectories", [])
    if subagents:
        md_content.append("## 🤖 Subagent Trajectories\n")
        for i, sub in enumerate(subagents):
            md_content.append(f"### Subagent [{i+1}]\n")
            meta = sub.get("meta", {})
            md_content.append(f"- **Description:** {meta.get('description', 'N/A')}\n")
            md_content.append(f"- **Type:** {meta.get('subagent_type', 'N/A')}\n")
            
            turns = sub.get("turns", [])
            for turn_idx, turn in enumerate(turns):
                role = turn.get("message", {}).get("role", turn.get("type", "unknown"))
                if role == "assistant":
                    content_list = turn.get("message", {}).get("content", [])
                    for content in content_list:
                        # Extract Subagent Thoughts
                        if content.get("type") == "thinking":
                            thought = content.get("thinking", "").strip()
                            if thought:
                                md_content.append(f"> 👀 **Step {step_num} - Subagent Thought (Turn {turn_idx+1}):**\n> {thought}\n\n")
                                step_num += 1
                        # Extract Subagent Tool Calls
                        elif content.get("type") == "tool_use":
                            tool_name = content.get("name", "unknown_tool")
                            tool_input = json.dumps(content.get("input", {}), indent=2)
                            md_content.append(f"🛠️ **Step {step_num} - Subagent Tool Execution:** `{tool_name}`\n")
                            md_content.append(f"```json\n{tool_input}\n```\n")
                            step_num += 1
                # Note: 'user' block containing tool responses has been intentionally removed
            md_content.append("---\n")

    # 2. Process Main Agent Turns
    main_turns = json_data.get("turns", [])
    if main_turns:
        md_content.append("## 🧠 Main Agent Trajectory\n")
        for turn_idx, turn in enumerate(main_turns):
            md_content.append(f"### Turn {turn_idx + 1}\n")
            
            # Check raw stdout items inside the turn block
            raw_items = turn.get("agent_stdout_parsed", [])
            for item in raw_items:
                item_type = item.get("type")
                
                if item_type == "assistant":
                    message = item.get("message", {})
                    contents = message.get("content", [])
                    for content in contents:
                        # Extract Main Agent Thoughts
                        if content.get("type") == "thinking":
                            thought = content.get("thinking", "").strip()
                            if thought:
                                md_content.append(f"> 💭 **Step {step_num} - Main Agent Thought:**\n> {thought}\n\n")
                                step_num += 1
                        
                        # Extract Main Agent Text Explanations
                        elif content.get("type") == "text":
                            text_body = content.get("text", "").strip()
                            if text_body:
                                md_content.append(f"🗣️ **Step {step_num} - Agent Message:**\n{text_body}\n\n")
                                step_num += 1
                        
                        # Extract Main Agent Tool Actions
                        elif content.get("type") == "tool_use":
                            tool_name = content.get("name", "unknown_tool")
                            tool_input = json.dumps(content.get("input", {}), indent=2)
                            md_content.append(f"⚙️ **Step {step_num} - Action - Tool Call:** `{tool_name}`\n")
                            md_content.append(f"```json\n{tool_input}\n```\n")
                            step_num += 1
                
                # Note: 'user' block containing main agent tool results has been intentionally removed
            md_content.append("---\n")

    # Write out file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("".join(md_content))
        
    print(f"Successfully generated clean trajectory markdown at: {output_file}")

# Example Usage
if __name__ == "__main__":
    input_filename = "smoke_results_agent_testgen_dry_run/Avaiga__taipy-1042@a76a34b/trajectory.json"
    
    if os.path.exists(input_filename):
        with open(input_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        extract_agent_logs(data)
    else:
        print(f"Please save your JSON dataset into '{input_filename}' file to process.")