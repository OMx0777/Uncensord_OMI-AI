from googlesearch import search
import sys

def get_results(query):
    print(f"\n🔎 System: Googling '{query}'...")
    output = ""
    try:
        # advanced=True gets the title and description automatically
        results = list(search(query, num_results=3, advanced=True))
        
        if not results:
            return "System: No results found."

        for i, r in enumerate(results, 1):
            output += f"\n--- RESULT {i} ---\n"
            output += f"Title: {r.title}\n"
            output += f"Link:  {r.url}\n"
            output += f"Summary: {r.description}\n"
            
    except Exception as e:
        return f"System: Search failed. Error: {e}"
    
    return output

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(get_results(" ".join(sys.argv[1:])))
