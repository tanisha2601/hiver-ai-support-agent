import argparse
import json
from src.agent import run_agent

def interactive_mode():
    print("==================================================")
    print("   Hiver AI Customer Support Agent - CLI Demo")
    print("==================================================")
    print("Type 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            customer_msg = input("Customer message:\n> ")
            if customer_msg.lower() in ['quit', 'exit']:
                break
                
            context = input("\nContext (optional):\n> ")
            if not context.strip():
                context = None
                
            print("\nProcessing...")
            result = run_agent(customer_msg, context=context)
            
            print("\n================ OUTPUT ================")
            print(f"Intent:\n{result['intent']}\n")
            print(f"Confidence:\n{result['intent_confidence']:.4f}\n")
            print("Retrieved examples:")
            for i, ex in enumerate(result['retrieved_examples'][:3]):
                print(f"{i+1}. {ex['historical_customer_text'][:50]}... -> {ex['historical_brand_response'][:50]}...")
            print()
            print(f"Grounding:\n{result['grounding_status']} ({result['grounding_score']:.4f})\n")
            print(f"Suggested response:\n{result['response']}\n")
            print(f"Decision:\n{result['decision']}\n")
            print(f"Reason:\n{result['decision_reason']}")
            print("========================================\n")
            
        except KeyboardInterrupt:
            break
            
def single_run(message, context):
    result = run_agent(message, context=context)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the AI Support Agent")
    parser.add_argument("--message", type=str, help="Customer message for non-interactive run")
    parser.add_argument("--context", type=str, help="Previous context for non-interactive run")
    args = parser.parse_args()
    
    if args.message:
        single_run(args.message, args.context)
    else:
        interactive_mode()
