#!/usr/bin/env python3
"""
Generate DSA solutions using local Ollama LLM.
Reads all problems from index.html, finds ones missing from SOLUTIONS,
generates structured solutions, and writes solutions.js.
"""

import json
import re
import subprocess
import sys
import time

OLLAMA_MODEL = "qwen2.5-coder:7b"

# All problems that already have SOLUTIONS entries (skip these)
EXISTING = {
    "s4","s5","a4","a7","a10","a11","a12","am1","am2","am3","am4","am5","am7",
    "am9","am10","am11","am12","ah1","ah2","ah3","ah7","ah9","ah10","ah11","ah12",
    "bs1","bs4","bs8","bs10","bs12","bs13","bsa1","bsa3","bsa6","bsa13","bs2d2",
    "bs2d3","str7","str14","strh5","llm1","llm2","llm3","llm4","llm8","llm12",
    "llm14","llh1","llh4","rec2","sub2","sub6","rh1","rh3","rh7","bit4","bit5",
    "sq7","sq8","sqm1","sqm5","sqm10","sqi1","sqi4","sw1","swh3","hpm1","hph5",
    "hph6","grm2","grm3","grm6","grm8","grm9","btm1","btm2","btm3","btm4",
    "btm5","btm6","btm11","bth2","bth3","bth9","bth11","bth14","bstp5","bstp6",
    "bstp12","gbd1","gbd3","gbd7","gbd10","gtopo3","gtopo5","gsp3","goa1",
    "gmst5","dp2","dp5","dp6","dp2d1","dp2d3","dps2","dps7","dps9","dpstr1",
    "dpstr9","dpstk2","dpstk3","dplis1","dpmcm4","dpsq1","t1","t6",
}

# Full problem list extracted from the DATA array in index.html
PROBLEMS = [
    # Basics
    ("b1","User Input / Output","basics"),
    ("b2","Data Types","basics"),
    ("b3","If Else statements","basics"),
    ("b4","Switch Statement","basics"),
    ("b5","What are arrays and strings","basics"),
    ("b6","For loops","basics"),
    ("b7","While loops","basics"),
    ("b8","Functions Pass by Value Pass by Reference","basics"),
    ("b9","Time Complexity","basics"),
    ("m1","Count Digits","math"),
    ("m2","Reverse a Number","math"),
    ("m3","Check Palindrome Number","math"),
    ("m4","GCD HCF of two numbers","math"),
    ("m5","Armstrong Numbers","math"),
    ("m6","Print all Divisors of a number","math"),
    ("m7","Check for Prime","math"),
    ("r1","Print something N times using recursion","recursion"),
    ("r2","Print 1 to N using recursion","recursion"),
    ("r3","Print N to 1 using recursion","recursion"),
    ("r4","Sum of first N numbers using recursion","recursion"),
    ("r5","Factorial of N using recursion","recursion"),
    ("r6","Reverse an array using recursion","recursion"),
    ("r7","Check if string is palindrome using recursion","recursion"),
    ("r8","Fibonacci Number","recursion"),
    ("h1","Hashing Theory and concept","hashing"),
    ("h2","Count frequency of each element in array","hashing"),
    ("h3","Find highest and lowest frequency element","hashing"),
    # Sorting
    ("s1","Selection Sort","sorting"),
    ("s2","Bubble Sort","sorting"),
    ("s3","Insertion Sort","sorting"),
    ("s6","Recursive Bubble Sort","sorting"),
    ("s7","Recursive Insertion Sort","sorting"),
    # Arrays Easy
    ("a1","Find Largest Element in an Array","arrays"),
    ("a2","Find Second Largest Element in an Array","arrays"),
    ("a3","Check if array is sorted","arrays"),
    ("a5","Left Rotate array by one place","arrays"),
    ("a6","Left rotate array by D places","arrays"),
    ("a8","Linear Search","arrays"),
    ("a9","Find the Union of two sorted arrays","arrays"),
    ("a13","Longest subarray with given sum K positives only","arrays"),
    # Arrays Medium
    ("am6","Rearrange array in alternating positive negative","arrays"),
    ("am8","Leaders in an Array","arrays"),
    ("am13","Count subarrays with given sum K","arrays"),
    # Arrays Hard
    ("ah4","4-Sum find quads that add up to target","arrays"),
    ("ah5","Largest Subarray with 0 Sum","arrays"),
    ("ah6","Count subarrays with given XOR K","arrays"),
    ("ah8","Merge two sorted arrays without extra space","arrays"),
    # Binary Search
    ("bs2","Implement Lower Bound","binary search"),
    ("bs3","Implement Upper Bound","binary search"),
    ("bs5","Floor and Ceil in Sorted Array","binary search"),
    ("bs6","First and last occurrence in sorted array","binary search"),
    ("bs7","Count occurrences in sorted array with duplicates","binary search"),
    ("bs9","Search in Rotated Sorted Array II with duplicates","binary search"),
    ("bs11","Find how many times array has been rotated","binary search"),
    ("bsa2","Find Nth root of a number using binary search","binary search"),
    ("bsa4","Minimum days to make M bouquets","binary search"),
    ("bsa5","Find the smallest divisor given threshold","binary search"),
    ("bsa7","Kth Missing Positive Number","binary search"),
    ("bsa8","Aggressive Cows binary search","binary search"),
    ("bsa9","Book Allocation Problem binary search","binary search"),
    ("bsa10","Split array into largest sum binary search","binary search"),
    ("bsa11","Painter partition problem binary search","binary search"),
    ("bsa12","Minimize maximum distance to gas station","binary search"),
    ("bsa14","Kth element of two sorted arrays","binary search"),
    ("bs2d1","Find row with maximum number of 1s in binary matrix","binary search"),
    ("bs2d4","Find Peak Element in 2D Matrix","binary search"),
    ("bs2d5","Matrix Median","binary search"),
    # Strings
    ("str1","Remove Outermost Parentheses","strings"),
    ("str2","Reverse Words in a String","strings"),
    ("str3","Largest Odd Number in a String","strings"),
    ("str4","Longest Common Prefix","strings"),
    ("str5","Isomorphic Strings","strings"),
    ("str6","Check if one string is rotation of another","strings"),
    ("str8","Sort Characters By Frequency","strings"),
    ("str9","Maximum Nesting Depth of Parentheses","strings"),
    ("str10","Roman to Integer","strings"),
    ("str11","Integer to Roman","strings"),
    ("str12","Implement Atoi string to integer","strings"),
    ("str13","Count Number of Substrings with k distinct chars","strings"),
    ("str15","Sum of Beauty of All Substrings","strings"),
    ("strh1","Minimum bracket reversals to balance expression","strings"),
    ("strh2","Count and Say","strings"),
    ("strh3","Rabin Karp algorithm string hashing","strings"),
    ("strh4","Z-Function string algorithm","strings"),
    ("strh6","Minimum chars to insert to make string palindrome","strings"),
    ("strh7","Shortest Palindrome","strings"),
    ("strh8","Longest happy prefix KMP","strings"),
    ("strh9","Count Palindromic Substrings","strings"),
    # Linked List
    ("ll1","Introduction to Linked List","linked list"),
    ("ll2","Inserting a node in Linked List","linked list"),
    ("ll3","Deleting a node in Linked List","linked list"),
    ("ll4","Find the length of linked list","linked list"),
    ("ll5","Search an element in Linked List","linked list"),
    ("dll1","Introduction to Doubly Linked List","linked list"),
    ("dll2","Insert a node in Doubly Linked List","linked list"),
    ("dll3","Delete a node in Doubly Linked List","linked list"),
    ("dll4","Reverse a Doubly Linked List","linked list"),
    ("llm5","Length of Loop in Linked List","linked list"),
    ("llm6","Check if Linked List is palindrome","linked list"),
    ("llm7","Segregate odd and even nodes in Linked List","linked list"),
    ("llm9","Delete the middle node of Linked List","linked list"),
    ("llm10","Sort Linked List using merge sort","linked list"),
    ("llm11","Sort Linked List of 0s 1s and 2s","linked list"),
    ("llm13","Add 1 to number represented by Linked List","linked list"),
    ("llh2","Rotate a Linked List","linked list"),
    ("llh3","Flattening of Linked List","linked list"),
    # Recursion Advanced
    ("rec1","Recursive Implementation of atoi","recursion"),
    ("rec3","Count Good numbers","recursion"),
    ("rec4","Sort a stack using recursion","recursion"),
    ("rec5","Reverse a stack using recursion","recursion"),
    ("sub1","Generate all binary strings using recursion","recursion"),
    ("sub3","Print all subsequences Power Set","recursion"),
    ("sub4","Count all subsequences with sum K","recursion"),
    ("sub5","Check if there exists subsequence with sum K","recursion"),
    ("sub7","Combination Sum II","recursion"),
    ("sub8","Subset Sum I print all sums","recursion"),
    ("sub9","Subset Sum II unique subsets","recursion"),
    ("sub10","Combination Sum III","recursion"),
    ("sub11","Letter Combinations of Phone Number","recursion"),
    ("rh2","Word Search in grid","recursion"),
    ("rh4","Rat in a Maze","recursion"),
    ("rh5","Word Break II","recursion"),
    ("rh6","M coloring problem graph coloring","recursion"),
    ("rh8","Expression Add Operators","recursion"),
    # Bit Manipulation
    ("bit4","Check if number is power of 2","bit manipulation"),
    ("bit6","Set or Unset the rightmost unset bit","bit manipulation"),
    ("biti6","Generate Power Set using bit manipulation","bit manipulation"),
    ("bita1","Print Prime Factors of a Number","bit manipulation"),
    ("bita2","All Divisors of a Number","bit manipulation"),
    ("bita4","Find Prime Factorisation using Sieve","bit manipulation"),
    # Stack & Queue
    ("sq3","Implement Stack using Queue","stack queue"),
    ("sq4","Implement Queue using Stack","stack queue"),
    ("sq5","Implement Stack using Linked List","stack queue"),
    ("sq6","Implement Queue using Linked List","stack queue"),
    ("sqp1","Infix to Postfix conversion using stack","stack queue"),
    ("sqp2","Prefix to Infix conversion","stack queue"),
    ("sqp3","Prefix to Postfix conversion","stack queue"),
    ("sqp4","Postfix to Prefix conversion","stack queue"),
    ("sqp5","Postfix to Infix conversion","stack queue"),
    ("sqp6","Convert Infix to Prefix notation","stack queue"),
    ("sqm2","Next Greater Element II circular array","stack queue"),
    ("sqm3","Next Smaller Element","stack queue"),
    ("sqm4","Number of NGEs to the right","stack queue"),
    ("sqm6","Sum of Subarray Minimum","stack queue"),
    ("sqm7","Asteroid Collision","stack queue"),
    ("sqm8","Sum of subarray ranges","stack queue"),
    ("sqm9","Remove k Digits to make smallest number","stack queue"),
    ("sqm11","Maximal Rectangle in binary matrix","stack queue"),
    ("sqi2","Stock span problem","stack queue"),
    ("sqi3","The Celebrity Problem","stack queue"),
    ("sqi5","LFU cache implementation","stack queue"),
    # Sliding Window
    ("sw2","Max Consecutive Ones III with flips","sliding window"),
    ("sw3","Fruit Into Baskets two pointers","sliding window"),
    ("sw4","Longest Repeating Character Replacement","sliding window"),
    ("sw5","Binary Subarrays with Sum","sliding window"),
    ("sw6","Count number of Nice subarrays","sliding window"),
    ("sw7","Number of Substrings Containing All Three Characters","sliding window"),
    ("sw8","Maximum Points You Can Obtain from Cards","sliding window"),
    ("swh1","Longest Substring with At Most K Distinct Characters","sliding window"),
    ("swh2","Subarrays with K Different Integers","sliding window"),
    ("swh4","Minimum Window containing Subsequence","sliding window"),
    # Heaps
    ("hp1","Introduction to Priority Queues using Binary Heaps","heaps"),
    ("hp2","Min Heap and Max Heap implementation","heaps"),
    ("hp3","Check if array represents min heap","heaps"),
    ("hp4","Convert min Heap to max Heap","heaps"),
    ("hpm2","Kth smallest element in array or matrix","heaps"),
    ("hpm3","Sort K sorted array using heap","heaps"),
    ("hpm4","Merge M sorted Lists","heaps"),
    ("hpm5","Replace each array element by its rank","heaps"),
    ("hpm6","Task Scheduler","heaps"),
    ("hpm7","Hands of Straights","heaps"),
    ("hph1","Design Twitter using heap","heaps"),
    ("hph2","Connect n ropes with minimum cost","heaps"),
    ("hph3","Kth largest element in a stream","heaps"),
    ("hph4","Maximum Sum Combination using heap","heaps"),
    # Greedy
    ("gr1","Assign Cookies greedy","greedy"),
    ("gr4","Lemonade Change greedy","greedy"),
    ("gr5","Valid Parenthesis Checker","greedy"),
    ("grm1","N meetings in one room","greedy"),
    ("grm4","Minimum number of platforms for railway station","greedy"),
    ("grm5","Job sequencing Problem","greedy"),
    ("grm7","Shortest Job First CPU Scheduling","greedy"),
    # Binary Tree
    ("bt1","Introduction to Trees","binary tree"),
    ("bt2","Binary Tree Representation","binary tree"),
    ("bt3","Binary Tree Traversals overview","binary tree"),
    ("btm7","Boundary Traversal of Binary Tree","binary tree"),
    ("btm8","Vertical Order Traversal of Binary Tree","binary tree"),
    ("btm9","Top View of Binary Tree","binary tree"),
    ("btm10","Bottom View of Binary Tree","binary tree"),
    ("btm12","Symmetric Binary Tree","binary tree"),
    ("bth1","Root to Node Path in Binary Tree","binary tree"),
    ("bth4","Check for Children Sum Property in Binary Tree","binary tree"),
    ("bth5","Print all Nodes at distance K in Binary Tree","binary tree"),
    ("bth6","Minimum time to BURN Binary Tree from a Node","binary tree"),
    ("bth7","Count total Nodes in a COMPLETE Binary Tree","binary tree"),
    ("bth8","Requirements to construct a Unique Binary Tree","binary tree"),
    ("bth10","Construct Binary Tree from Postorder and Inorder","binary tree"),
    ("bth12","Morris Preorder Traversal of Binary Tree","binary tree"),
    ("bth13","Morris Inorder Traversal of Binary Tree","binary tree"),
    # BST
    ("bst1","Introduction to Binary Search Tree","bst"),
    ("bst2","Search in a Binary Search Tree","bst"),
    ("bst3","Find Min and Max in BST","bst"),
    ("bstp1","Ceil in a Binary Search Tree","bst"),
    ("bstp2","Floor in a Binary Search Tree","bst"),
    ("bstp3","Insert a node in Binary Search Tree","bst"),
    ("bstp4","Delete a Node in Binary Search Tree","bst"),
    ("bstp7","LCA in Binary Search Tree","bst"),
    ("bstp8","Construct BST from preorder traversal","bst"),
    ("bstp9","Inorder Successor and Predecessor in BST","bst"),
    ("bstp10","BST iterator implementation","bst"),
    ("bstp11","Two Sum In BST","bst"),
    # Graphs
    ("g1","Graph and Types introduction","graphs"),
    ("g2","Graph Representation adjacency list matrix","graphs"),
    ("g3","Connected Components in graph","graphs"),
    ("g4","BFS Breadth First Search","graphs"),
    ("g5","DFS Depth First Search","graphs"),
    ("gbd2","Connected Components Problem in Matrix","graphs"),
    ("gbd4","Flood Fill algorithm","graphs"),
    ("gbd5","Cycle Detection in undirected graph BFS","graphs"),
    ("gbd6","Cycle Detection in undirected graph DFS","graphs"),
    ("gbd8","Surrounded Regions replace Os with Xs","graphs"),
    ("gbd9","Number of Enclaves","graphs"),
    ("gbd11","Word Ladder II","graphs"),
    ("gbd12","Number of Distinct Islands","graphs"),
    ("gbd13","Bipartite Check using BFS","graphs"),
    ("gbd14","Bipartite Check using DFS","graphs"),
    ("gtopo1","Topological Sort DFS","graphs"),
    ("gtopo2","Kahn's Algorithm BFS topological sort","graphs"),
    ("gtopo4","Cycle Detection in Directed Graph DFS","graphs"),
    ("gtopo6","Find eventual safe states","graphs"),
    ("gtopo7","Alien dictionary topological sort","graphs"),
    ("gsp1","Shortest Path in undirected graph unit weights","graphs"),
    ("gsp2","Shortest Path in DAG","graphs"),
    ("gsp4","Bellman Ford Algorithm","graphs"),
    ("gsp5","Floyd Warshall Algorithm all pairs shortest path","graphs"),
    ("gsp6","Find city with smallest number of neighbors threshold","graphs"),
    ("gsp7","Number of ways to arrive at destination","graphs"),
    ("gsp8","Minimum Multiplications to reach End","graphs"),
    ("gsp9","Cheapest Flights Within K Stops","graphs"),
    ("gmst1","Minimum Spanning Tree concept","graphs"),
    ("gmst2","Prim's Algorithm MST","graphs"),
    ("gmst3","Disjoint Set Union Find with path compression","graphs"),
    ("gmst4","Kruskal's Algorithm MST","graphs"),
    ("gmst6","Most stones removed same row or column","graphs"),
    ("gmst7","Accounts Merge union find","graphs"),
    ("gmst8","Number of islands II dynamic","graphs"),
    ("gmst9","Making a Large Island","graphs"),
    ("gmst10","Swim in rising water","graphs"),
    ("goa2","Articulation Point in graph","graphs"),
    ("goa3","Kosaraju's Algorithm Strongly Connected Components","graphs"),
    # DP
    ("dp1","Dynamic Programming Introduction memoization tabulation","dp"),
    ("dp3","Frog Jump DP","dp"),
    ("dp4","Frog Jump with K distances DP","dp"),
    ("dp7","Ninja Training DP","dp"),
    ("dp2d2","Grid Unique Paths 2 with obstacles","dp"),
    ("dp2d4","Minimum path sum in Triangular Grid","dp"),
    ("dp2d5","Maximum path sum in matrix","dp"),
    ("dp2d6","Chocolate Pickup 3D DP","dp"),
    ("dps1","Subset Sum Equal to Target","dp"),
    ("dps3","Partition Set Into 2 Subsets Min Absolute Sum Diff","dp"),
    ("dps4","Count Subsets with Sum K","dp"),
    ("dps5","Count Partitions with Given Difference","dp"),
    ("dps6","0/1 Knapsack problem","dp"),
    ("dps8","Target Sum DP","dp"),
    ("dps10","Unbounded Knapsack","dp"),
    ("dps11","Rod Cutting Problem DP","dp"),
    ("dpstr2","Print Longest Common Subsequence","dp"),
    ("dpstr3","Longest Common Substring DP","dp"),
    ("dpstr4","Longest Palindromic Subsequence","dp"),
    ("dpstr5","Minimum insertions to make string palindrome","dp"),
    ("dpstr6","Minimum Insertions Deletions to Convert String","dp"),
    ("dpstr7","Shortest Common Supersequence","dp"),
    ("dpstr8","Distinct Subsequences count","dp"),
    ("dpstr10","Wildcard Pattern Matching","dp"),
    ("dpstk1","Best Time to Buy and Sell Stock","dp"),
    ("dpstk4","Buy and Sell Stocks IV at most k transactions","dp"),
    ("dpstk5","Buy and Sell Stocks With Cooldown","dp"),
    ("dpstk6","Buy and Sell Stocks With Transaction Fee","dp"),
    ("dplis2","Print Longest Increasing Subsequence","dp"),
    ("dplis3","Longest Increasing Subsequence binary search","dp"),
    ("dplis4","Largest Divisible Subset","dp"),
    ("dplis5","Longest String Chain","dp"),
    ("dplis6","Longest Bitonic Subsequence","dp"),
    ("dplis7","Number of Longest Increasing Subsequences","dp"),
    ("dpmcm1","Matrix Chain Multiplication","dp"),
    ("dpmcm2","Matrix Chain Multiplication Bottom Up","dp"),
    ("dpmcm3","Minimum Cost to Cut the Stick","dp"),
    ("dpmcm5","Evaluate Boolean Expression to True","dp"),
    ("dpmcm6","Palindrome Partitioning II min cuts","dp"),
    ("dpmcm7","Partition Array for Maximum Sum","dp"),
    ("dpsq2","Count Square Submatrices with All Ones","dp"),
    # Tries
    ("t1","Implement Trie INSERT SEARCH STARTSWITH","trie"),
    ("t2","Implement Trie II count words prefix count","trie"),
    ("t3","Longest String with All Prefixes","trie"),
    ("t4","Number of Distinct Substrings using Trie","trie"),
    ("t5","Bit Prerequisites for Trie XOR problems","trie"),
    ("t7","Maximum XOR With an Element From Array","trie"),
]

PROMPT_TEMPLATE = """You are a DSA expert. For the problem: "{name}" (topic: {topic})

Provide concise solution approaches in this EXACT JSON format only, no other text:
[
  {{"label": "brute", "tc": "O(?)", "sc": "O(?)", "desc": "One or two sentences explaining the naive approach and its key idea."}},
  {{"label": "optimal", "tc": "O(?)", "sc": "O(?)", "desc": "One or two sentences explaining the optimal algorithm and its key insight."}}
]

Rules:
- Use "brute", "better", or "optimal" for label (include "better" only if there's a meaningful intermediate step)
- Keep desc to max 2 sentences, focus on the algorithm insight
- Be specific about complexity (e.g. O(n log n) not O(n*logn))
- If it's a concept/intro problem (not a coding problem), return: [{{"label":"optimal","tc":"O(1)","sc":"O(1)","desc":"Core concept: explain the main idea in one sentence."}}]
- Return ONLY the JSON array, nothing else"""


def call_ollama(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """Call Ollama API via CLI."""
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=60
    )
    return result.stdout.strip()


def parse_json(text: str):
    """Extract JSON array from response."""
    text = text.strip()
    # Find JSON array
    start = text.find('[')
    end = text.rfind(']') + 1
    if start == -1 or end == 0:
        return None
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        # Try to fix common issues
        chunk = text[start:end]
        chunk = re.sub(r',\s*]', ']', chunk)  # trailing comma
        chunk = re.sub(r',\s*}', '}', chunk)  # trailing comma in obj
        try:
            return json.loads(chunk)
        except:
            return None


def validate_steps(steps):
    """Validate solution steps have required fields."""
    if not isinstance(steps, list) or len(steps) == 0:
        return False
    for s in steps:
        if not all(k in s for k in ['label', 'tc', 'sc', 'desc']):
            return False
        if s['label'] not in ['brute', 'better', 'optimal', 'iterative', 'recursive', 'dfs', 'bfs', 'dp', 'greedy', 'union-find']:
            s['label'] = 'optimal'  # normalize
    return True


def generate_solution(pid: str, name: str, topic: str) -> list:
    """Generate solution for a problem."""
    prompt = PROMPT_TEMPLATE.format(name=name, topic=topic)

    for attempt in range(3):
        try:
            response = call_ollama(prompt)
            steps = parse_json(response)
            if steps and validate_steps(steps):
                return steps
            print(f"  Attempt {attempt+1} failed to parse JSON, retrying...", file=sys.stderr)
            time.sleep(1)
        except subprocess.TimeoutExpired:
            print(f"  Timeout on {pid}, retrying...", file=sys.stderr)
            time.sleep(2)
        except Exception as e:
            print(f"  Error on {pid}: {e}", file=sys.stderr)
            time.sleep(2)

    return [{"label": "optimal", "tc": "O(?)", "sc": "O(?)", "desc": f"See TakeUForward for detailed solution to {name}."}]


def main():
    results = {}
    to_process = [(pid, name, topic) for pid, name, topic in PROBLEMS if pid not in EXISTING]

    print(f"Generating solutions for {len(to_process)} problems...", file=sys.stderr)

    for i, (pid, name, topic) in enumerate(to_process):
        print(f"[{i+1}/{len(to_process)}] {pid}: {name}", file=sys.stderr)
        steps = generate_solution(pid, name, topic)
        results[pid] = {"steps": steps}

        # Write incrementally every 10 problems
        if (i + 1) % 10 == 0 or i == len(to_process) - 1:
            with open("solutions_generated.json", "w") as f:
                json.dump(results, f, indent=2)
            print(f"  Saved {len(results)} solutions so far", file=sys.stderr)

    # Final output as JS
    print("// AUTO-GENERATED SOLUTIONS - DO NOT EDIT MANUALLY")
    print("const GENERATED_SOLUTIONS = " + json.dumps(results, indent=2) + ";")


if __name__ == "__main__":
    main()
