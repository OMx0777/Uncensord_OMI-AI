from duckduckgo_search import DDGS

def search(query):
    print(f"\n🔎 System: Searching DuckDuckGo for '{query}'...")
    output = ""
    try:
        # Get results (wt-wt = no region, safe search off)
        results = DDGS().text(keywords=query, region='wt-wt', max_results=3)
        
        if not results:
            return "System: No results found."

        for i, r in enumerate(results, 1):
            output += f"\n--- RESULT {i} ---\n"
            output += f"Title: {r.get('title')}\n"
            output += f"Link:  {r.get('href')}\n"
            output += f"Summary: {r.get('body')}\n"
            
    except Exception as e:
        return f"System: Search failed. Error: {e}"
    
    return output

# Allow testing via command line
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(search(" ".join(sys.argv[1:])))
