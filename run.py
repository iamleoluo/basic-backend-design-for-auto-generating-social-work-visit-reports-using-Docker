from prompt_core.prompt import PromptManager, PromptLibrary
import json

if __name__ == "__main__":
    with open("run.json", "r", encoding="utf-8") as f:
        run_data = json.load(f)

    input_file = run_data.get("input_file", "input.txt")
    default_model_id = run_data.get("default_model_id")
    steps = run_data.get("steps", [])

    prompt_lib = PromptLibrary("run.json")
    pm = PromptManager(default_model_id=default_model_id)
    conversation_id = "myconv"
    pm.create_conversation(conversation_id)

    with open(input_file, "r", encoding="utf-8") as f:
        input_text = f.read()

    for step in steps:
        label = step.get("label")
        model_id = step.get("model_id")
        temperature = step.get("temperature")
        prompt = prompt_lib.get_prompt(label)
        if not prompt:
            continue
        if "template" in prompt:
            q = prompt["template"].format(input=input_text)
        else:
            q = prompt.get("question", "")
        print("-----------------------------------------")
        print(f"[Q] {q}")
        print(f"[AI] {pm.chat(conversation_id, q, model_id=model_id, temperature=temperature)}")
        print("-----------------------------------------")
    print("=== 對話歷史 ===")
    for msg in pm.get_conversation_history(conversation_id):
        print(f"[{msg['role']}] {msg['content']}")
        print("-----------------------------------------")

    pm.clear_conversation(conversation_id)




