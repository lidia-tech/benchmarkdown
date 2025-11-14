from collections import defaultdict
import numpy as np
from rapidfuzz import distance

import os
import pandas as pd

import re
import pandas as pd
from fuzzywuzzy import process
from difflib import SequenceMatcher

"""
textstruct — Markdown text + structure similarity utilities

Summary
-------
This module provides utilities to compare Markdown-like documents using:
- a text similarity measure (normalized Levenshtein via rapidfuzz),
- heading/Table-of-Contents (ToC) extraction and fuzzy/unified ToC matching,
- graph-based representations of document structure (parent/child, full descendants),
- a simple Graph Edit Distance based structural similarity,
- a combined text+structure score.

Primary use
-----------
Compute similarity between two Markdown documents by combining raw text similarity
and structural similarity derived from headings (lines starting with '#').

"""

# ================ ToC transformations ================

def toc_extract(text):
    """ ToC Extraction:
        Parse input text into header tuples and a dict:
        - headers: list of tuples (line_index, level, title)
        - headers_dict: {'loc_index': [...], 'level': [...], 'header': [...]}
        Headers are lines matching r'^(#+)\s+(.*)'. line_index is the line number (0-based). 
    """
    lines = text.strip().split("\n")
    headers = []
    headers_dict = {'loc_index' : [], 'level' : [], 'header' : []}

    for i, line in enumerate(lines):
        match = re.match(r"^(#+)\s+(.*)", line)
        if match:
            level = len(match.group(1))  # number of # = level
            title = match.group(2).strip()
            headers.append((i, level, title))
            headers_dict['loc_index'].append(i)
            headers_dict['level'].append(level)
            headers_dict['header'].append(title)
    
    return headers, headers_dict

def toc_vis(text):
    """ ToC visualization:
    Return a string containing only the header lines (ToC text) extracted from text.
    """
    toc = "\n".join(
        line for line in text.splitlines()
        # Regex: start of line (^), one or more '#' (#+), space, then capture the rest (.+)
        if re.match(r'^\s*#+\s', line)
    )
    return toc

def toc_exact_unify(toc_dict1, toc_dict2):
    """ Exact join ToC headers unification:
        Align two ToC header dictionaries by exact loc_index match.
        Returns:
        - toc1_index, toc2_index: lists of (index, global_level, header)
        - total_nodes: int
        - node_recall: matched nodes / ground-truth nodes
        Note: this routine builds a common index starting at 1 for merged rows. 
    """

    df1 = pd.DataFrame(toc_dict1).rename(columns= {'level' : 'level1'})
    df2 = pd.DataFrame(toc_dict2).rename(columns= {'level' : 'level2'})

    # Header level from 0
    shift1 = df1.level1.min()
    df1['global_level1'] = df1['level1'] - shift1
    max_level1 = df1.global_level1.max()
    shift2 = df2.level2.min()
    df2['global_level2'] = df2['level2'] - shift2
    max_level2 = df2.global_level2.max()

    # Join text indeces of headers 
    merged = df1.merge(df2, on="loc_index", how="outer").drop(['level1','level2','global_level1','global_level2'], axis = 1)

    # add common index
    merged.insert(0, "index", range(1, len(merged) + 1))

    # share common index
    df1 = df1.merge(merged, on = "loc_index", how = "inner")
    df2 = df2.merge(merged, on = "loc_index", how = "inner")
    df1_ar = df1.to_dict()
    df2_ar = df2.to_dict()

    toc1_index = []
    for i in range(len(df1_ar['index'])):
        index = df1_ar['index'][i]
        level = df1_ar['global_level1'][i]
        header = df1_ar['header'][i]
        toc1_index.append((index,level,header))
    
    toc2_index = []
    for i in range(len(df2_ar['index'])):
        index = df2_ar['index'][i]
        level = df2_ar['global_level2'][i]
        header = df2_ar['header'][i]
        toc2_index.append((index,level,header))

    # Compute additional parameters
    
    # Total nodes
    try:
        max(merged.index)
        total_nodes = max(merged.index) + 1
    except: 
        total_nodes = 0
    
    # Ground truth nodes
    toc1_nodes = df1.level1.count()
    
    # Connected nodes
    inner = df1.merge(df2, on="loc_index", how="inner").reset_index()
    con_nodes = inner.level1.count()
            
    node_recall = con_nodes/toc1_nodes

    return toc1_index, toc2_index, total_nodes, node_recall

def toc_fuzzy_unify(toc_dict1, toc_dict2, threshold):
    """ Fuzzy join ToC headers unification:
        Fuzzy matching of headers across two toc_dicts using fuzzywuzzy.process.
        Returns:
        - toc1_index, toc2_index: unique lists of (index, global_level, header)
        - total_nodes, node_recall
        Note: The returned common index is used downstream to build graphs and matrices.
    """

    df1 = pd.DataFrame(toc_dict1).rename(columns= {1 : 'level'})
    df2 = pd.DataFrame(toc_dict2).rename(columns= {1 : 'level'})

    # Header level from 0
    shift1 = df1['level'].min()
    df1['global_level'] = df1['level'] - shift1

    if len(toc_dict2['level']) > 0:
        shift2 = df2['level'].min()
        df2['global_level'] = df2['level'] - shift2
    else: 
        shift2 = 0

    # Join text indeces of headers
    matches1 = []
    inner_matches = []
    for item in df1['header']:
        ind1 = df1[df1['header'] == item]['loc_index'].values[0]
        if len(toc_dict2['level']) > 0:
            match = process.extractOne(item, df2['header'])
        else:
            match = (0,0,0)

        if match[1] > threshold:
            matches1.append((ind1, item, None, match[0], match[1]))
            inner_matches.append((ind1, item, None, match[0], match[1]))
        else: 
            matches1.append((ind1, item, None, None    , 0))

    matches2 = matches1
    matches_header2 = [x[1] for x in matches2]

    for item in df2['header']:
        if len(toc_dict2['level']) > 0:
            if item not in matches_header2:
                ind2 = df2[df2['header'] == item]['loc_index'].values[0]
                match = process.extractOne(item, df1['header'])
                if match[1] > threshold:
                    matches2.append((None, match[0], ind2, item, match[1]))
                else: 
                    matches2.append((None, None, ind2, item, 0))
            else:
                matches2
        
    merged = pd.DataFrame(matches2, columns=['index1', 'header1', 'index2', 'header2', 'score'])
    merged = merged.fillna(0)
    merged['loc_index'] = merged.index1 + merged.index2
    merged = merged.drop(['index1','index2'], axis = 1)
    merged = merged.sort_values(by = 'loc_index')

    # add common index
    merged = merged.reset_index().reset_index().drop(['index'],axis=1).rename(columns={'level_0' : 'index'})

    # share common index
    toc1_index = []
    toc2_index = []

    df1 = df1.merge(merged, left_on = "header", right_on = 'header1', how = "inner")
    df1_ar = df1.to_dict()

    for i in range(len(df1_ar['index'])):
        index = df1_ar['index'][i]
        level = df1_ar['global_level'][i]
        header = df1_ar['header'][i]
        toc1_index.append((index,level,header))  

    if len(matches2) > 0:
        df2 = df2.merge(merged, left_on = "header", right_on = 'header2', how = "inner")
        df2_ar = df2.to_dict()
        
        for i in range(len(df2_ar['index'])):
            index = df2_ar['index'][i]
            level = df2_ar['global_level'][i]
            header = df2_ar['header'][i]
            toc2_index.append((index,level,header))

    toc1_index_df = pd.DataFrame(toc1_index)
    toc1_index_dict_unique = toc1_index_df.groupby([2,1])[0].min().reset_index().sort_values(0,ascending=True).to_dict()
    toc1_index_unique = []
    for i in range(len(toc1_index_dict_unique[0])):
        item = (toc1_index_dict_unique[0][i], toc1_index_dict_unique[1][i], toc1_index_dict_unique[2][i])
        toc1_index_unique.append(item)
    toc1_index_unique.sort()

    toc2_index_df = pd.DataFrame(toc2_index)
    toc2_index_dict_unique = toc2_index_df.groupby([2,1])[0].min().reset_index().sort_values(0,ascending=True).to_dict()
    toc2_index_unique = []
    for i in range(len(toc2_index_dict_unique[0])):
        item = (toc2_index_dict_unique[0][i], toc2_index_dict_unique[1][i], toc2_index_dict_unique[2][i])
        toc2_index_unique.append(item)
    toc2_index_unique.sort()

    # Compute additional parameters
    
    # Total nodes
    try:
        max(merged.index)
        total_nodes = max(merged.index) + 1
    except: 
        total_nodes = 0
    
    # Ground truth nodes
    toc1_nodes = df1.level.count()
    
    # Connected nodes
    if len(inner_matches) > 0:
        inner = pd.DataFrame(inner_matches)
        con_nodes = inner[1].count()
    else: 
        con_nodes = 0
    
    node_recall = con_nodes/toc1_nodes

    return toc1_index_unique, toc2_index_unique, total_nodes, node_recall

# ================= Graph representation ====================

def disconnected_sparse_graph(headers):
    """ Build a parent->direct-children mapping (sparse) from headers list:
        headers: list of (line_num, level, header)
        Returns dict: {parent_line_num: [child_line_nums], ...}
    """
    graph = defaultdict(list)
    stack = []

    for line_num, level, header in headers:
        # Pop until we find the FIRST descendant
        while stack and stack[-1][1] >= level:
            stack.pop()
        if stack:
            parent_line, parent_level = stack[-1]
            graph[parent_line].append(line_num)

        stack.append((line_num, level))
        
        # Ensure node exists in graph (even if no children)
        if line_num not in graph:
            graph[line_num] = []
    return dict(graph)

def disconnected_full_graph(graph):
    """ Convert sparse immediate-child graph into mapping of node -> all descendants. """
    dict(graph)
    def dfs(node):
        desc = set()
        for child in graph[node]:
            desc.add(child) 
            desc |= dfs(child) # bitwise or (+= for sets)
        return desc

    # Find all descendants (recursion)
    return {node: sorted(dfs(node)) for node in graph}

def connected_graph(disc_graph, headers):
    """ Add edges between successive header nodes if missing (connects adjacent nodes),
        producing a connected graph. 
    """
    graph = disc_graph.copy() 

    for (line_num, _, _), (next_line, _, _) in zip(headers, headers[1:]):
        if next_line not in set(disc_graph[line_num]):
            graph[line_num].append(next_line)         
    return dict(graph)

# ============== Matrix Representation ===============

def graph_to_matrix(graph, m):
    """ Convert adjacency mapping (int keys -> list of int children) to an m x m numpy
        adjacency matrix (1.0 for edge presence). 
    """
    matrix = np.zeros((m,m))

    for i in graph:
        for j in graph[i]:
            matrix[i][j] = 1     
    return matrix

# Mask for the weighted matrix
def mask_vector(toc, mask, max_index):
    """ Build a vector of length max_index applying mask[level] to each node:
        toc: iterable of tuples (index, level, header) where index is 1-based.
        Returns numpy array of length max_index.  """
    mv = np.zeros(max_index)
    for item in toc:
        mv[item[0]-1] = mask[item[1]]
    return mv

def GED(matrix1, matrix2):
    """ Graph Edit Distance: compute simple graph-edit distance as sum of absolute difference between two
        adjacency matrices (L0-like measure: count of differing cells).     
    """
    # Diff matrix
    matrix_diff = matrix1 - matrix2
    # 0-norm
    GED = sum(sum(np.abs(matrix_diff)))

    return GED

def GED_norm_factor(matrix1_full_w,matrix2_full_w):
    """ GED Normalization factor: Compute a normalization factor for GED using node depths/weights. """
    m = matrix1_full_w.shape[0]

    matrix1_deep = []
    matrix2_deep = []
    for i in range(m):
        matrix1_deep.append(sum(matrix1_full_w[i]))
        matrix2_deep.append(sum(matrix2_full_w[i]))

    h1 = sum(1 for x in matrix1_deep if x != 0)
    h2 = sum(1 for x in matrix2_deep if x != 0)

    max_deep1 = max(matrix1_deep)
    max_deep2 = max(matrix2_deep)

    if h2 >= h1: norm_factor = h1 * max_deep1
    else: norm_factor = h2 * max_deep2
    
    return norm_factor

# ========== Graph Edit Distance ==============

def GED_sim(GED, GED_norm_factor):
    """ Convert absolute GED into a similarity score in (0,1] 
        using normalization and exponential mapping. 
    """
    GED_sim = (1 - GED/GED_norm_factor)
    GED_sim_exp = np.exp(4*(GED_sim-1))

    return GED_sim_exp

# ============ Final Metrics ================

def text_score(text1,text2): 
    """ Normalized Levenshtein similarity
        Return character-based percentage similarity in the range of [0,1] between two strings. 
    """
    return distance.Levenshtein.normalized_similarity(text1, text2)

def header_score(text1, text2, similarity_threshold=0.8):
    """ Compute F1 between lists of headings in two texts using fuzzy matching
        (SequenceMatcher ratio). The similarity_threshold controls match acceptance. 
    """
    # Extract headers
    toc1 = toc_extract(text1)
    heading1 = toc1[1]['header']

    toc2 = toc_extract(text2)
    heading2 = toc2[1]['header']

    # Normalize headings (optional)
    heading1 = [h.strip().lower() for h in heading1]
    heading2 = [h.strip().lower() for h in heading2]

    matched_1 = set()
    matched_2 = set()

    # Fuzzy matching: find best matches above threshold
    for i, h1 in enumerate(heading1):
        for j, h2 in enumerate(heading2):
            sim = SequenceMatcher(None, h1, h2).ratio()
            if sim >= similarity_threshold:
                matched_1.add(i)
                matched_2.add(j)
                break  # stop once we find one sufficiently good match

    tp = len(matched_1)
    fp = len(heading2) - len(matched_2)
    fn = len(heading1) - len(matched_1)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return f1

def structure_score(toc_dict1, toc_dict2, fuzzy_th, mask):
    """ High-level structure similarity computation:
      - produces common indexing via toc_fuzzy_unify
      - builds sparse/full/connected graphs for both documents
      - constructs adjacency matrices and computes GED similarity
        Returns (graph_similarity, node_recall). If an error occurs, returns (0,0).
    """ 

    # Common indexing without headers
    try:
        toc1_index, toc2_index, total_nodes, node_recall = toc_fuzzy_unify(toc_dict1, toc_dict2, fuzzy_th)
        # toc1_index, toc2_index, total_nodes = exact_unify(toc_dict1, toc_dict2)

        # Sparse disconnected graph
        graph1_sparse_d = disconnected_sparse_graph(toc1_index)
        graph2_graph_sparse_d = disconnected_sparse_graph(toc2_index)

        # Full disconnected graph
        graph1_full_d = disconnected_full_graph(graph1_sparse_d)
        graph2_full_d = disconnected_full_graph(graph2_graph_sparse_d)

        # Full connected graph
        graph1_full = connected_graph(graph1_full_d, toc1_index)
        graph2_full = connected_graph(graph2_full_d, toc2_index)

        # Weighted vector
        vector1 = mask_vector(toc1_index, mask, total_nodes)
        vector2 = mask_vector(toc2_index, mask, total_nodes)

        # Matrix representation
        matrix1_full = graph_to_matrix(graph1_full, total_nodes)
        matrix2_full = graph_to_matrix(graph2_full, total_nodes)

        # # Weighted matrix representation
        # matrix1_full_w = matrix1_full * vector1
        # matrix2_full_w = matrix2_full * vector2

        matrix1_full_w = matrix1_full
        matrix2_full_w = matrix2_full

        # GED computation
        ged_abs = GED(matrix1_full_w, matrix2_full_w)
        ged_norm_factor = GED_norm_factor(matrix1_full_w,matrix2_full_w)

        # Graph simmilarity
        graph_sim = GED_sim(ged_abs, ged_norm_factor)

        return graph_sim, node_recall
    except: return 0, 0

def final_score(text1, text2, fuzzy_th, mask):
    
    toc1, toc_dict1 = toc_extract(text1)
    toc2, toc_dict2 = toc_extract(text2)

    # Text score
    t_score = text_score(text1, text2)
    # Heading score
    h_score = header_score(text1, text2)
    # Structure score
    s_score, _ = structure_score(toc_dict1, toc_dict2, fuzzy_th, mask)

    return t_score, h_score, s_score